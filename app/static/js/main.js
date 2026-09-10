// ===========================
// Modal Management
// ===========================

class Modal {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.closeBtn = this.modal.querySelector('.close');
        
        // Close on X button
        this.closeBtn.addEventListener('click', () => this.close());
        
        // Close on outside click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }
    
    open() {
        this.modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
    
    close() {
        this.modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// ===========================
// Generate Report Modal
// ===========================

const generateModal = new Modal('generateModal');
const jobStatusModal = new Modal('jobStatusModal');
let reportCatalog = [];

// Open generate modal
document.getElementById('generateReportBtn').addEventListener('click', (e) => {
    e.preventDefault();
    loadAvailableReports();
    generateModal.open();
});

// Load available reports
async function loadAvailableReports() {
    const container = document.getElementById('reportTypesList');
    container.innerHTML = '<div class="loading">Loading available reports...</div>';
    
    try {
        const response = await fetch('/api/reports/available');
        const reports = await response.json();
        reportCatalog = reports;
        
        if (reports.length === 0) {
            container.innerHTML = '<p>No reports available</p>';
            return;
        }

        container.innerHTML = reports.map(report => `
            <div class="report-type-card" onclick="showReportOptions('${report.id}')">
                <h3><i class="fas fa-file-alt"></i> ${report.name}</h3>
                <p>${report.description}</p>
                ${report.arguments.length ? `<small>${report.arguments.length} configurable option(s)</small>` : ''}
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading reports:', error);
        container.innerHTML = '<p class="text-danger">Error loading reports</p>';
    }
}

// Show email options for report
async function showReportOptions(reportId) {
    const container = document.getElementById('reportTypesList');
    const report = reportCatalog.find(item => item.id === reportId);
    if (!report) return;
    const reportName = report.name;

    // Load groups for selection
    let groupOptions = '<option value="">Select a group (optional)</option>';
    try {
        const response = await fetch('/contacts/api/groups');
        const groups = await response.json();
        groupOptions += groups.map(group =>
            `<option value="${group.id}">${group.name} (${group.member_count} members)</option>`
        ).join('');
    } catch (error) {
        console.log('Groups not available');
    }

    container.innerHTML = `
        <div class="email-options-form">
            <h3><i class="fas fa-sliders-h"></i> Report Options</h3>
            <p style="margin-bottom: 1.5rem;">Report: <strong>${reportName}</strong></p>

            ${renderArgumentFields(report.arguments)}
            
            <div class="form-group">
                <label for="emailGroup">
                    <i class="fas fa-users"></i> Send to Group (optional):
                </label>
                <select id="emailGroup" class="form-input" onchange="handleGroupSelection()">
                    ${groupOptions}
                </select>
                <small>Select a group to auto-fill recipients</small>
            </div>
            
            <div class="form-group">
                <label for="emailTo">
                    <i class="fas fa-user"></i> Send To (optional):
                </label>
                <input 
                    type="text" 
                    id="emailTo" 
                    class="form-input" 
                    placeholder="recipient@example.com or multiple separated by commas"
                />
                <small>Leave blank to generate without email, or add more recipients</small>
            </div>
            
            <div class="form-group">
                <label for="emailCc">
                    <i class="fas fa-users"></i> CC (optional):
                </label>
                <input 
                    type="text" 
                    id="emailCc" 
                    class="form-input" 
                    placeholder="cc@example.com"
                />
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="generateReportWithEmail('${reportId}')">
                    <i class="fas fa-play-circle"></i> Generate Report
                </button>
                <button class="btn btn-secondary" onclick="loadAvailableReports()">
                    <i class="fas fa-arrow-left"></i> Back
                </button>
            </div>
        </div>
    `;

    // Pre-fill if there's a pending group email
    if (window.pendingGroupEmail) {
        document.getElementById('emailTo').value = window.pendingGroupEmail.emails;
        window.pendingGroupEmail = null;
    }
}

// Handle group selection
async function handleGroupSelection() {
    const groupId = document.getElementById('emailGroup').value;
    if (!groupId) {
        return;
    }

    try {
        const response = await fetch(`/contacts/api/groups/${groupId}/emails`);
        const data = await response.json();

        if (data.emails && data.emails.length > 0) {
            // Set the email field with group members
            document.getElementById('emailTo').value = data.emails.join(', ');
            showNotification(`Added ${data.count} recipients from group`, 'success');
        } else {
            showNotification('This group has no members', 'error');
        }
    } catch (error) {
        console.error('Error loading group emails:', error);
        showNotification('Error loading group members', 'error');
    }
}

// Generate report with email options
async function generateReportWithEmail(reportId) {
    const emailTo = document.getElementById('emailTo').value.trim();
    const emailCc = document.getElementById('emailCc').value.trim();
    const report = reportCatalog.find(item => item.id === reportId);
    const argumentsPayload = {};
    for (const argument of (report?.arguments || [])) {
        const input = document.getElementById(`reportArg_${argument.name}`);
        if (!input) continue;
        argumentsPayload[argument.name] = argument.type === 'bool' ? input.checked : input.value.trim();
    }

    try {
        const response = await fetch('/api/reports/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                report_id: reportId,
                email_to: emailTo || null,
                email_cc: emailCc || null,
                arguments: argumentsPayload
            })
        });

        const result = await response.json();

        if (response.ok) {
            generateModal.close();

            if (emailTo) {
                showNotification(`Report generation started! Email will be sent to ${emailTo}`, 'success');
            } else {
                showNotification('Report generation started!', 'success');
            }

            // Monitor job status
            monitorJob(result.job_id);
        } else {
            showNotification(result.error || 'Failed to start report', 'error');
        }

    } catch (error) {
        console.error('Error generating report:', error);
        showNotification('Error starting report generation', 'error');
    }
}

// Generate a report (backwards compatibility)
async function generateReport(reportId) {
    showReportOptions(reportId);
}

function renderArgumentFields(argumentsList) {
    if (!argumentsList.length) return '';
    return `<h4 style="margin-bottom: 1rem;">Query Parameters</h4>` + argumentsList.map(argument => {
        const required = argument.required ? 'required' : '';
        const defaultValue = argument.default ?? '';
        if (argument.type === 'bool') {
            return `<div class="form-group"><label><input id="reportArg_${argument.name}" type="checkbox" ${defaultValue ? 'checked' : ''}> ${argument.label}</label><small>${argument.help || ''}</small></div>`;
        }
        const inputType = argument.type === 'int' ? 'number' : 'text';
        return `<div class="form-group"><label for="reportArg_${argument.name}">${argument.label}${argument.required ? ' *' : ''}</label><input id="reportArg_${argument.name}" class="form-input" type="${inputType}" value="${escapeAttribute(defaultValue)}" ${required}><small>${argument.help || ''}</small></div>`;
    }).join('');
}

function escapeAttribute(value) {
    return String(value).replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

// ===========================
// Job Monitoring
// ===========================

let activeMonitors = new Set();

async function monitorJob(jobId) {
    if (activeMonitors.has(jobId)) return;
    activeMonitors.add(jobId);

    const checkStatus = async () => {
        try {
            const response = await fetch(`/api/jobs/${jobId}`);
            const job = await response.json();

            if (job.status === 'completed') {
                activeMonitors.delete(jobId);

                let message = `Report "${job.name}" completed successfully!`;
                if (job.email_sent) {
                    message += ' Email sent.';
                } else if (job.email_status) {
                    message += ` ${job.email_status}`;
                }

                showNotification(message, 'success');

                // Refresh page after short delay
                setTimeout(() => {
                    window.location.reload();
                }, 2000);

            } else if (job.status === 'failed') {
                activeMonitors.delete(jobId);
                showNotification(`Report "${job.name}" failed: ${job.error}`, 'error');

            } else {
                // Still running, check again
                setTimeout(checkStatus, 2000);
            }

        } catch (error) {
            console.error('Error checking job status:', error);
            activeMonitors.delete(jobId);
        }
    };

    checkStatus();
}

// ===========================
// View All Jobs
// ===========================

async function loadAllJobs() {
    const content = document.getElementById('jobStatusContent');
    content.innerHTML = '<div class="loading">Loading jobs...</div>';

    jobStatusModal.open();

    try {
        const response = await fetch('/api/jobs');
        const jobs = await response.json();

        if (jobs.length === 0) {
            content.innerHTML = '<p>No jobs found</p>';
            return;
        }

        content.innerHTML = `
            <div style="max-height: 400px; overflow-y: auto;">
                ${jobs.map(job => `
                    <div class="job-card" style="border: 1px solid #e5e7eb; border-radius: 0.375rem; padding: 1rem; margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                            <h3 style="margin: 0; font-size: 1rem;">${job.name}</h3>
                            <span class="badge badge-${getStatusColor(job.status)}">${job.status}</span>
                        </div>
                        <p style="font-size: 0.875rem; color: #6b7280; margin: 0;">
                            <i class="fas fa-clock"></i> Started: ${formatDateTime(job.started_at)}
                        </p>
                        ${job.completed_at ? `
                            <p style="font-size: 0.875rem; color: #6b7280; margin: 0;">
                                <i class="fas fa-check-circle"></i> Completed: ${formatDateTime(job.completed_at)}
                            </p>
                        ` : ''}
                        ${job.email_to ? `
                            <p style="font-size: 0.875rem; color: #059669; margin: 0.5rem 0 0 0;">
                                <i class="fas fa-envelope"></i> Email: ${job.email_to}
                                ${job.email_sent ? '✓' : ''}
                            </p>
                        ` : ''}
                        ${job.error ? `
                            <p style="color: #ef4444; font-size: 0.875rem; margin-top: 0.5rem;">
                                <i class="fas fa-exclamation-circle"></i> ${job.error}
                            </p>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;

    } catch (error) {
        console.error('Error loading jobs:', error);
        content.innerHTML = '<p class="text-danger">Error loading jobs</p>';
    }
}

function getStatusColor(status) {
    const colors = {
        'running': 'info',
        'completed': 'primary',
        'failed': 'danger'
    };
    return colors[status] || 'primary';
}

// ===========================
// Notifications
// ===========================

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.375rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 2000;
        animation: slideInRight 0.3s;
        max-width: 400px;
    `;

    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Add notification animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .form-group {
        margin-bottom: 1.5rem;
    }
    
    .form-group label {
        display: block;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #374151;
    }
    
    .form-input {
        width: 100%;
        padding: 0.625rem 0.875rem;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        font-size: 1rem;
        transition: border-color 0.2s;
    }
    
    .form-input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    .form-group small {
        display: block;
        margin-top: 0.25rem;
        color: #6b7280;
        font-size: 0.875rem;
    }
    
    .button-group {
        display: flex;
        gap: 0.75rem;
        margin-top: 1.5rem;
    }
    
    .email-options-form {
        padding: 1rem 0;
    }
`;
document.head.appendChild(style);

// ===========================
// Utility Functions
// ===========================

function formatDateTime(isoString) {
    if (!isoString) return 'N/A';

    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ===========================
// Auto-refresh for active jobs
// ===========================

// Check for active jobs on page load and set up auto-refresh
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/api/jobs');
        const jobs = await response.json();

        // Monitor any running jobs
        jobs.forEach(job => {
            if (job.status === 'running') {
                monitorJob(job.id);
            }
        });

    } catch (error) {
        console.error('Error checking for active jobs:', error);
    }
});

// ===========================
// Keyboard Shortcuts
// ===========================

document.addEventListener('keydown', (e) => {
    // Escape to close modals
    if (e.key === 'Escape') {
        generateModal.close();
        jobStatusModal.close();
    }

    // Ctrl/Cmd + G to open generate modal
    if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
        e.preventDefault();
        document.getElementById('generateReportBtn').click();
    }
});
// ===========================
// Email Existing Report Functions
// ===========================

let currentReportPath = null;

async function showEmailReportModal(reportPath, reportName) {
    // --------------------------------------------------
    // Normalize report path (defensive fix)
    // Ensures folder/file are separated by ONE slash
    // --------------------------------------------------
    if (reportPath && !reportPath.includes('/')) {
        console.warn(
            '⚠️ reportPath missing slash, attempting auto-fix:',
            reportPath
        );

        // Try to infer folder from filename prefix
        const match = reportPath.match(/^([a-zA-Z0-9_]+)_/);
        if (match) {
            reportPath = `${match[1]}/${reportPath}`;
        }
    }

    currentReportPath = reportPath;

    console.group('📧 showEmailReportModal');
    console.log('Report name:', reportName);
    console.log('Normalized report path:', currentReportPath);
    console.groupEnd();

    // --------------------------------------------------
    // Load groups
    // --------------------------------------------------
    let groupOptions = '<option value="">Select a group (optional)</option>';

    try {
        const response = await fetch('/contacts/api/groups');
        if (response.ok) {
            const groups = await response.json();
            groupOptions += groups.map(group =>
                `<option value="${group.id}">
                    ${group.name} (${group.member_count} members)
                 </option>`
            ).join('');
        }
    } catch (error) {
        console.warn('Groups not available', error);
    }

    // --------------------------------------------------
    // Create modal container
    // --------------------------------------------------
    let modal = document.getElementById('emailReportModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'emailReportModal';
        modal.className = 'modal';
        document.body.appendChild(modal);
    }

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>
                    <i class="fas fa-envelope"></i>
                    Email Report
                </h2>
                <span class="close" onclick="closeEmailReportModal()">&times;</span>
            </div>

            <div class="modal-body">
                <div class="email-options-form">

                    <p><strong>Report:</strong> ${reportName}</p>
                    <p style="font-size:0.85rem;color:#666">
                        <strong>Path:</strong> ${currentReportPath}
                    </p>

                    <div class="form-group">
                        <label>Send To *</label>
                        <input id="emailReportTo" class="form-input" />
                    </div>

                    <div class="form-group">
                        <label>CC</label>
                        <input id="emailReportCc" class="form-input" />
                    </div>

                    <div class="button-group">
                        <button type="button"
                                class="btn btn-primary"
                                onclick="sendExistingReport()">
                            <i class="fas fa-paper-plane"></i> Send Email
                        </button>

                        <button type="button"
                                class="btn btn-secondary"
                                onclick="closeEmailReportModal()">
                            Cancel
                        </button>
                    </div>

                </div>
            </div>
        </div>
    `;

    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}


function closeEmailReportModal() {
    const modal = document.getElementById('emailReportModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
    currentReportPath = null;
}

async function handleEmailReportGroupSelection() {
    const groupId = document.getElementById('emailReportGroup').value;
    if (!groupId) return;

    try {
        const response = await fetch(`/contacts/api/groups/${groupId}/emails`);
        const data = await response.json();

        if (data.emails && data.emails.length > 0) {
            document.getElementById('emailReportTo').value = data.emails.join(', ');
            showNotification(`Added ${data.count} recipients from group`, 'success');
        } else {
            showNotification('This group has no members', 'error');
        }
    } catch (error) {
        console.error('Error loading group emails:', error);
        showNotification('Error loading group members', 'error');
    }
}

async function sendExistingReport() {
    const emailTo = document.getElementById('emailReportTo')?.value;
    const emailCc = document.getElementById('emailReportCc')?.value || null;

    console.group('📨 Send Existing Report');
    console.log('currentReportPath:', currentReportPath);
    console.log('emailTo:', emailTo);
    console.log('emailCc:', emailCc);

    if (!currentReportPath) {
        console.error('❌ currentReportPath is EMPTY');
        console.groupEnd();
        alert('No report selected.');
        return;
    }

    if (!emailTo) {
        console.error('❌ emailTo is EMPTY');
        console.groupEnd();
        alert('Recipient email is required.');
        return;
    }

    const payload = {
        report_path: currentReportPath,
        email_to: emailTo,
        email_cc: emailCc
    };

    console.log('Payload being sent:', payload);

    try {
        const response = await fetch('/api/reports/email_existing_report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        console.log('Response status:', response.status);

        const responseText = await response.text();
        console.log('Raw response:', responseText);

        let result;
        try {
            result = JSON.parse(responseText);
        } catch {
            console.error('❌ Response is not JSON');
            console.groupEnd();
            return;
        }

        console.log('Parsed response:', result);

        if (!response.ok) {
            console.error('❌ Server returned error', result);
            alert(result.error || 'Failed to send email');
            console.groupEnd();
            return;
        }

        console.log('✅ Email request accepted');
        showNotification(`Email is being sent to ${emailTo}`, 'success');
        closeEmailReportModal();

    } catch (err) {
        console.error('❌ Fetch failed:', err);
        alert('Network error while sending email');
    }

    console.groupEnd();
}
