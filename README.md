# Oracle DB Reporting System - Web Frontend

A modern web interface for managing and generating Oracle database reports.

## Features

✨ **Dashboard Overview**
- Real-time statistics on generated reports
- Quick access to recent reports
- System status monitoring

📊 **Report Management**
- Browse reports by category
- Download reports in Excel format
- Preview report metadata
- Search and filter capabilities

🚀 **Report Generation**
- On-demand report generation via web interface
- Real-time job status tracking
- Background task execution
- Automatic notification on completion

🎨 **Modern UI/UX**
- Responsive design (mobile-friendly)
- Intuitive navigation
- Keyboard shortcuts
- Real-time updates

## Project Structure

```
orcdb/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py              # Dashboard routes
│   │   ├── reports.py           # Report browsing/download
│   │   └── api.py               # REST API endpoints
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Main stylesheet
│   │   └── js/
│   │       └── main.js          # Frontend JavaScript
│   └── templates/
│       ├── base.html            # Base template
│       ├── index.html           # Dashboard
│       └── reports/
│           ├── index.html       # Reports listing
│           ├── category.html    # Category view
│           └── preview.html     # Report preview
├── configuration/
│   ├── config.py                # Configuration
│   ├── orcdb_logger.py          # Logging utilities
│   └── utils/
│       └── report_utility.py    # Report utilities
├── outputs/                     # Generated reports
│   ├── qa_daily_results/
│   ├── level10_dm_open/
│   └── ...
├── run_qa_daily_report.py       # QA report script
├── run_level10_dm_report.py     # Level 10 DM script
├── run_app.py                   # Flask app runner
└── requirements.txt             # Python dependencies
```

## Installation

### Prerequisites

- Python 3.8+
- Oracle Database access
- SQLcl (for SQL execution)

### Setup

1. **Clone/navigate to your project directory**
   ```bash
   cd /path/to/orcdb
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify directory structure**
   Ensure the following directories exist:
   ```bash
   mkdir -p outputs/{qa_daily_results,level10_dm_open}
   mkdir -p logs
   ```

## Running the Application

### Development Server

```bash
python run_app.py
```

The application will be available at: **http://localhost:5000**

### Production Deployment

For production, use a WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 'app:create_app()'
```

Or use the included systemd service file (create as needed).

## Usage

### Accessing the Dashboard

1. Open your browser to `http://localhost:5000`
2. View statistics and recent reports on the homepage

### Generating Reports

**Method 1: Via UI**
1. Click "Generate Report" in the navigation
2. Select the report type
3. Monitor progress in real-time

**Method 2: Keyboard Shortcut**
- Press `Ctrl+G` to open the generation modal

**Method 3: API**
```bash
curl -X POST http://localhost:5000/api/reports/run \
  -H "Content-Type: application/json" \
  -d '{"report_id": "qa_daily"}'
```

### Browsing Reports

1. Navigate to "Browse Reports"
2. Reports are organized by category
3. Click on any report to preview or download

### Downloading Reports

- Click the download icon on any report
- Or access directly: `http://localhost:5000/reports/download/<category>/<filename>`

## API Endpoints

### GET `/api/reports/available`
Get list of available report types

**Response:**
```json
[
  {
    "id": "qa_daily",
    "name": "QA Daily Results",
    "description": "QA results for the last 24 hours",
    "script": "run_qa_daily_report.py",
    "category": "qa_daily_results"
  }
]
```

### POST `/api/reports/run`
Execute a report generation

**Request:**
```json
{
  "report_id": "qa_daily"
}
```

**Response:**
```json
{
  "job_id": "qa_daily_1706633428",
  "status": "started",
  "message": "Report generation started: QA Daily Results"
}
```

### GET `/api/jobs/<job_id>`
Get status of a specific job

**Response:**
```json
{
  "id": "qa_daily_1706633428",
  "report_id": "qa_daily",
  "name": "QA Daily Results",
  "status": "completed",
  "started_at": "2026-01-30T14:30:28",
  "completed_at": "2026-01-30T14:30:45",
  "progress": 100
}
```

### GET `/api/jobs`
Get all jobs (active and recent)

### GET `/api/system/status`
Get system status

## Adding New Reports

To add a new report type to the system:

1. **Create the report script** (e.g., `run_new_report.py`)
   ```python
   from configuration.config import OUTPUT_BASE_DIR
   # ... your report logic
   ```

2. **Add output directory to `config.py`**
   ```python
   NEW_REPORT_DIR = OUTPUT_BASE_DIR / "new_report"
   ```

3. **Register in API** (`app/routes/api.py`)
   ```python
   {
       'id': 'new_report',
       'name': 'New Report Name',
       'description': 'Description of the report',
       'script': 'run_new_report.py',
       'category': 'new_report'
   }
   ```

4. The report will automatically appear in the UI

## Configuration

### Flask Configuration

Edit `app/__init__.py` to modify:
- `SECRET_KEY`: Change for production
- `MAX_CONTENT_LENGTH`: File upload size limit
- Other Flask settings

### Report Timeout

Adjust timeout in `app/routes/api.py`:
```python
result = subprocess.run(
    ...,
    timeout=300  # 5 minutes (adjust as needed)
)
```

## Keyboard Shortcuts

- `Ctrl+G` / `Cmd+G`: Open report generation modal
- `ESC`: Close any open modal

## Troubleshooting

### Reports not appearing
- Check that report scripts output to the correct directory
- Verify directory permissions
- Check logs in `logs/orcdb.log`

### Generation fails
- Verify Oracle database connection
- Check SQLcl is installed and accessible
- Review error messages in job status

### Port already in use
Change the port in `run_app.py`:
```python
app.run(port=5001)  # Use different port
```

## Security Considerations

⚠️ **Important for Production:**

1. **Change the SECRET_KEY** in `app/__init__.py`
2. **Use HTTPS** in production
3. **Add authentication** if exposing to network
4. **Validate file paths** to prevent directory traversal
5. **Use environment variables** for sensitive config
6. **Enable CORS** only for trusted domains
7. **Use a proper database** instead of in-memory job tracking

## License

Copyright © 2026 Oracle DB Reporting System

## Support

For issues or questions:
1. Check the logs: `logs/orcdb.log`
2. Review browser console for JavaScript errors
3. Verify all dependencies are installed
