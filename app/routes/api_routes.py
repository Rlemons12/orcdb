from flask import Blueprint, jsonify, request, current_app
from pathlib import Path
import subprocess
import threading
import time
import sys
import os
from datetime import datetime
from app.services.report_catalog import build_script_arguments, get_report, get_report_catalog

# api_routes.py
bp = Blueprint('api_routes', __name__, url_prefix='/api')


# In-memory job tracking (use Redis/database for production)
active_jobs = {}
job_history = []


@bp.route('/reports/available')
def available_reports():
    """Get list of available report types"""
    project_root = current_app.config['PROJECT_ROOT']
    return jsonify(get_report_catalog(project_root))


@bp.route('/reports/run', methods=['POST'])
def run_report():
    """Execute a report generation script"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        report_id = data.get('report_id')
        email_to = data.get('email_to')
        email_cc = data.get('email_cc')
        argument_values = data.get('arguments') or {}
        if not isinstance(argument_values, dict):
            return jsonify({'error': 'arguments must be a JSON object'}), 400

        if not report_id:
            return jsonify({'error': 'report_id is required'}), 400

        project_root = current_app.config['PROJECT_ROOT']
        report_config = get_report(project_root, report_id)
        if not report_config:
            return jsonify({'error': 'Invalid report_id'}), 400
        try:
            script_arguments = build_script_arguments(report_config, argument_values)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        script_path = project_root / "scripts" / report_config['script']

        if not script_path.exists():
            return jsonify({
                'error': 'Report script not found',
                'script_path': str(script_path),
                'message': f'Could not find {report_config["script"]} in {project_root / "scripts"}'
            }), 404

        # Create job ID
        job_id = f"{report_id}_{time.time_ns()}"

        # Initialize job tracking
        active_jobs[job_id] = {
            'id': job_id,
            'report_id': report_id,
            'name': report_config['name'],
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'progress': 0,
            'email_to': email_to,
            'email_cc': email_cc,
            'arguments': argument_values,
        }

        # 🔑 Capture the Flask app object explicitly
        app = current_app._get_current_object()

        # Run in background thread WITH app context
        thread = threading.Thread(
            target=execute_report_script,
            args=(app, job_id, script_path, project_root, script_arguments, email_to, email_cc),
            daemon=True
        )
        thread.start()

        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'message': f'Report generation started: {report_config["name"]}'
        })

    except Exception as e:
        current_app.logger.exception("run_report failed")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@bp.route('/jobs/<job_id>')
def job_status(job_id):
    """Get status of a running or completed job"""
    # Check active jobs
    if job_id in active_jobs:
        return jsonify(active_jobs[job_id])

    # Check history
    for job in job_history:
        if job['id'] == job_id:
            return jsonify(job)

    return jsonify({'error': 'Job not found'}), 404


@bp.route('/jobs')
def all_jobs():
    """Get all jobs (active and recent history)"""
    all_jobs_list = list(active_jobs.values())
    all_jobs_list.extend(job_history[-20:])  # Last 20 from history

    # Sort by start time, newest first
    all_jobs_list.sort(
        key=lambda x: x.get('started_at', ''),
        reverse=True
    )

    return jsonify(all_jobs_list)


def execute_report_script(
    app,
    job_id: str,
    script_path: Path,
    project_root: Path,
    script_arguments: list[str],
    email_to=None,
    email_cc=None
):
    """
    Execute a report script in a background thread, track job state,
    discover generated files deterministically, and optionally email results.
    """
    import sys
    import subprocess
    import time
    from datetime import datetime
    pythoncom = None
    try:
        import pythoncom as _pythoncom
        pythoncom = _pythoncom
        pythoncom.CoInitialize()
    except ImportError:
        pass

    try:
        with app.app_context():
            app.logger.info(
                "Starting report execution",
                extra={
                    "job_id": job_id,
                    "script": str(script_path)
                }
            )

            # -----------------------------
            # Mark job running
            # -----------------------------
            active_jobs[job_id]['status'] = 'running'
            active_jobs[job_id]['progress'] = 10

            # -----------------------------
            # Run the report script
            # -----------------------------
            before_files = snapshot_report_files(project_root / "outputs")
            environment = os.environ.copy()
            existing_pythonpath = environment.get("PYTHONPATH")
            environment["PYTHONPATH"] = str(project_root) + (
                os.pathsep + existing_pythonpath if existing_pythonpath else ""
            )
            result = subprocess.run(
                [sys.executable, str(script_path), *script_arguments],
                cwd=str(project_root),
                env=environment,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                active_jobs[job_id].update({
                    'status': 'failed',
                    'progress': 0,
                    'completed_at': datetime.now().isoformat(),
                    'error': result.stderr[-1000:] if result.stderr else 'Unknown error',
                    'output': result.stdout[-1000:] if result.stdout else ''
                })

                app.logger.error(
                    "Report script failed",
                    extra={
                        "job_id": job_id,
                        "stderr": result.stderr
                    }
                )
                return

            # -----------------------------
            # Script succeeded
            # -----------------------------
            active_jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'completed_at': datetime.now().isoformat(),
                'output': result.stdout[-1000:] if result.stdout else ''
            })

            # -----------------------------
            # Discover generated files (deterministic)
            # -----------------------------
            generated_files = find_generated_report_files(
                project_root / "outputs", before_files
            )

            active_jobs[job_id]['generated_files'] = [
                str(f) for f in generated_files
            ]

            app.logger.info(
                "Report files discovered",
                extra={
                    "job_id": job_id,
                    "files": active_jobs[job_id]['generated_files']
                }
            )

            # -----------------------------
            # Email handling (NO silent skip)
            # -----------------------------
            if email_to:
                if not generated_files:
                    active_jobs[job_id]['email_sent'] = False
                    active_jobs[job_id]['email_status'] = 'No report files found'

                    app.logger.warning(
                        "Email requested but no report files found",
                        extra={"job_id": job_id}
                    )
                else:
                    try:
                        send_report_email(
                            job_id=job_id,
                            report_name=active_jobs[job_id]['name'],
                            email_to=email_to,
                            email_cc=email_cc,
                            attachments=generated_files
                        )

                        active_jobs[job_id]['email_sent'] = True
                        active_jobs[job_id]['email_status'] = 'Email sent successfully'

                        app.logger.info(
                            "Report email sent",
                            extra={
                                "job_id": job_id,
                                "to": email_to
                            }
                        )

                    except Exception as e:
                        active_jobs[job_id]['email_sent'] = False
                        active_jobs[job_id]['email_status'] = f'Email failed: {e}'

                        app.logger.exception(
                            "Failed to send report email",
                            extra={"job_id": job_id}
                        )

    except subprocess.TimeoutExpired:
        with app.app_context():
            active_jobs[job_id].update({
                'status': 'failed',
                'error': 'Script execution timeout (5 minutes)',
                'completed_at': datetime.now().isoformat()
            })
            app.logger.error("Report execution timed out", extra={"job_id": job_id})

    except Exception as e:
        with app.app_context():
            active_jobs[job_id].update({
                'status': 'failed',
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            })
            app.logger.exception("Unhandled error during report execution")

    finally:
        if pythoncom:
            pythoncom.CoUninitialize()

        # -----------------------------
        # Move job to history after delay
        # -----------------------------
        def move_to_history():
            time.sleep(60)
            if job_id in active_jobs:
                job_history.append(active_jobs.pop(job_id))
                while len(job_history) > 100:
                    job_history.pop(0)

        threading.Thread(
            target=move_to_history,
            daemon=True
        ).start()




def snapshot_report_files(output_dir: Path) -> dict[Path, tuple[int, int]]:
    snapshot = {}
    if not output_dir.exists():
        return snapshot
    for path in output_dir.rglob("*.xlsx"):
        if path.name.startswith("~$"):
            continue
        try:
            stat = path.stat()
            snapshot[path.resolve()] = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            continue
    return snapshot


def find_generated_report_files(output_dir: Path, before: dict[Path, tuple[int, int]]) -> list[Path]:
    changed = []
    for path, signature in snapshot_report_files(output_dir).items():
        if before.get(path) != signature:
            changed.append(path)
    return sorted(changed, key=lambda path: path.stat().st_mtime, reverse=True)



def send_report_email(job_id: str, report_name: str, email_to, email_cc=None, attachments=None):
    """Send email notification with report attachment"""
    try:
        # Import email service
        from email_service.email_client import EmailClient

        # Prepare email
        subject = f"Report Generated: {report_name}"

        body = f"""
<html>
<body>
    <h2>Report Generation Complete</h2>
    <p>Your requested report has been successfully generated.</p>

    <table style="border-collapse: collapse; margin: 20px 0;">
        <tr>
            <td style="padding: 8px; font-weight: bold;">Report:</td>
            <td style="padding: 8px;">{report_name}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Job ID:</td>
            <td style="padding: 8px;">{job_id}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Generated:</td>
            <td style="padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
        </tr>
        <tr>
            <td style="padding: 8px; font-weight: bold;">Attachments:</td>
            <td style="padding: 8px;">{len(attachments) if attachments else 0} file(s)</td>
        </tr>
    </table>

    <p>The report file(s) are attached to this email.</p>

    <p style="color: #666; font-size: 12px; margin-top: 30px;">
        This is an automated message from the Oracle DB Reporting System
        designed and created by Robert Lemons for Otsuka ICU Medical LLC 
        Mainenace Department.
    </p>
</body>
</html>
"""

        # Send email
        client = EmailClient()
        client.send_email(
            to=email_to if isinstance(email_to, list) else [email_to],
            subject=subject,
            body=body,
            attachments=[str(f) for f in attachments] if attachments else None,
            html=True,
            cc=email_cc if isinstance(email_cc, list) else ([email_cc] if email_cc else None)
        )

        active_jobs[job_id]['email_sent'] = True
        active_jobs[job_id]['email_status'] = 'Email sent successfully'

    except Exception as e:
        active_jobs[job_id]['email_sent'] = False
        active_jobs[job_id]['email_status'] = f'Email failed: {str(e)}'


@bp.route('/system/status')
def system_status():
    """Get system status information"""
    output_dir = current_app.config['OUTPUT_BASE_DIR']

    # Count total reports
    total_reports = 0
    if output_dir.exists():
        for category_dir in output_dir.iterdir():
            if category_dir.is_dir():
                total_reports += len(list(category_dir.glob("*.xlsx")))

    # Check email service availability
    email_status = 'unknown'
    try:
        from email_service.email_client import EmailClient
        client = EmailClient()
        if client.outlook.available:
            email_status = 'outlook_available'
        else:
            email_status = 'smtp_only'
    except Exception:
        email_status = 'unavailable'

    return jsonify({
        'status': 'operational',
        'active_jobs': len(active_jobs),
        'total_reports': total_reports,
        'email_service': email_status,
        'timestamp': datetime.now().isoformat()
    })


@bp.route('/reports/email_existing_report', methods=['POST'])
def email_existing_report():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        report_path = data.get('report_path')
        email_to = data.get('email_to')
        email_cc = data.get('email_cc')

        if not report_path:
            return jsonify({'error': 'report_path is required'}), 400

        if not email_to:
            return jsonify({'error': 'email_to is required'}), 400

        output_dir = current_app.config['OUTPUT_BASE_DIR'].resolve()
        file_path = (output_dir / report_path).resolve()

        try:
            file_path.relative_to(output_dir)
        except ValueError:
            return jsonify({'error': 'Invalid file path'}), 403

        if not file_path.exists():
            return jsonify({'error': 'Report file not found'}), 404

        # Capture app + logger
        app = current_app._get_current_object()

        def background_email():
            import pythoncom
            pythoncom.CoInitialize()
            try:
                with app.app_context():
                    send_existing_report_email(
                        file_path=file_path,
                        email_to=email_to,
                        email_cc=email_cc
                    )
            finally:
                pythoncom.CoUninitialize()

        thread = threading.Thread(
            target=background_email,
            daemon=True
        )
        thread.start()

        return jsonify({
            'success': True,
            'message': f'Email is being sent to {email_to}',
            'file': file_path.name
        })

    except Exception as e:
        current_app.logger.exception("email_existing_report failed")
        return jsonify({
            'error': 'Failed to send email',
            'message': str(e)
        }), 500

def send_report_email(job_id: str, report_name: str, email_to, email_cc=None, attachments=None):
    """
    Send email notification with report attachment
    This runs inside execute_report_script() which already initialized COM.
    """
    import win32com.client as win32

    # Normalize email fields
    if isinstance(email_to, str):
        email_to = [addr.strip() for addr in email_to.split(",")]

    if email_cc and isinstance(email_cc, str):
        email_cc = [addr.strip() for addr in email_cc.split(",")]

    subject = f"Report Generated: {report_name}"

    body = f"""
<html>
<body>
    <h2>Report Generation Complete</h2>
    <p>Your requested report has been successfully generated.</p>

    <p><strong>Report:</strong> {report_name}</p>
    <p><strong>Job ID:</strong> {job_id}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <p>The report file is attached.</p>

    <hr>
    <p style="font-size:12px;color:#666;">
        LemonAide DB Reporting System
    </p>
</body>
</html>
"""

    outlook = win32.Dispatch("outlook.application")
    mail = outlook.CreateItem(0)

    mail.Subject = subject
    mail.HTMLBody = body

    mail.To = "; ".join(email_to)

    if email_cc:
        mail.CC = "; ".join(email_cc)

    if attachments:
        for file in attachments:
            mail.Attachments.Add(str(file))

    mail.Send()



def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

@bp.route('/__probe', methods=['GET'])
def api_probe():
    return {'api_routes': 'alive'}
