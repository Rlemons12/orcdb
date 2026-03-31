// ===========================
// WIP Analytics Dashboard
// ===========================

let charts = {};
let currentReportPath = null;

// Load available reports on page load
document.addEventListener('DOMContentLoaded', () => {
    loadAvailableReports();
});

async function loadAvailableReports() {
    try {
        // Load all available Excel files from the reports directory
        const response = await fetch('/api/reports/list');

        if (!response.ok) {
            console.error('Failed to load reports');
            return;
        }

        const data = await response.json();
        const select = document.getElementById('reportSelect');
        select.innerHTML = '<option value="">Select a report...</option>';

        // Filter for Excel files and group by category
        if (data.reports && Array.isArray(data.reports)) {
            data.reports.forEach(report => {
                if (report.name.endsWith('.xlsx') || report.name.endsWith('.xls')) {
                    const option = document.createElement('option');
                    option.value = report.path;
                    option.textContent = `${report.category} - ${report.name}`;
                    select.appendChild(option);
                }
            });
        }

    } catch (error) {
        console.error('Error loading reports:', error);
        showNotification('Could not load reports list', 'error');
    }
}

async function loadAnalytics() {
    const select = document.getElementById('reportSelect');
    const reportPath = select.value;

    if (!reportPath) {
        hideAllSections();
        return;
    }

    currentReportPath = reportPath;

    // Show loading
    document.getElementById('loadingIndicator').style.display = 'block';
    hideAllSections();

    try {
        // Fetch analytics data - UPDATED PATH
        const response = await fetch(`/analytics/api/wip/${reportPath}`);
        const data = await response.json();

        if (response.ok) {
            displayAnalytics(data);
        } else {
            showNotification(data.error || 'Failed to load analytics', 'error');
        }

    } catch (error) {
        console.error('Error loading analytics:', error);
        showNotification('Error loading analytics', 'error');
    } finally {
        document.getElementById('loadingIndicator').style.display = 'none';
    }
}

function displayAnalytics(data) {
    // Check if we have data
    if (!data || !data.summary) {
        showNotification('No analytics data available', 'error');
        return;
    }

    // Display summary
    displaySummary(data.summary);

    // Display charts (only if data exists)
    if (data.daily_trend && Object.keys(data.daily_trend).length > 0) {
        displayDailyTrend(data.daily_trend);
    }

    if (data.activity_breakdown && Object.keys(data.activity_breakdown).length > 0) {
        displayActivityBreakdown(data.activity_breakdown);
    }

    if (data.top_locations && Object.keys(data.top_locations).length > 0) {
        displayTopLocations(data.top_locations);
    }

    if (data.top_assets && Object.keys(data.top_assets).length > 0) {
        displayTopAssets(data.top_assets);
    }

    if (data.user_activity && Object.keys(data.user_activity).length > 0) {
        displayUserActivity(data.user_activity);
    }

    if (data.reason_breakdown && Object.keys(data.reason_breakdown).length > 0) {
        displayReasonBreakdown(data.reason_breakdown);
    }

    // Show sections
    document.getElementById('summarySection').style.display = 'block';
    document.getElementById('chartsSection').style.display = 'block';
}

function displaySummary(summary) {
    document.getElementById('totalRecords').textContent = summary.total_records || 0;
    document.getElementById('uniqueEntities').textContent = summary.unique_entities || 0;
    document.getElementById('uniqueAssets').textContent = summary.unique_assets || 0;
    document.getElementById('uniqueLocations').textContent = summary.unique_locations || 0;
}

function displayDailyTrend(data) {
    destroyChart('dailyTrendChart');

    const ctx = document.getElementById('dailyTrendChart');
    const dates = Object.keys(data).sort();
    const counts = dates.map(date => data[date]);

    charts.dailyTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Entities Created',
                data: counts,
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

function displayActivityBreakdown(data) {
    destroyChart('activityChart');

    const ctx = document.getElementById('activityChart');
    const labels = Object.keys(data);
    const values = Object.values(data);

    charts.activityChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    'rgb(59, 130, 246)',
                    'rgb(16, 185, 129)',
                    'rgb(245, 158, 11)',
                    'rgb(239, 68, 68)',
                    'rgb(139, 92, 246)',
                    'rgb(236, 72, 153)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

function displayTopLocations(data) {
    destroyChart('locationsChart');

    const ctx = document.getElementById('locationsChart');
    const labels = Object.keys(data);
    const values = Object.values(data);

    charts.locationsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Count',
                data: values,
                backgroundColor: 'rgba(16, 185, 129, 0.8)',
                borderColor: 'rgb(16, 185, 129)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

function displayTopAssets(data) {
    destroyChart('assetsChart');

    const ctx = document.getElementById('assetsChart');
    const labels = Object.keys(data);
    const values = Object.values(data);

    charts.assetsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Activity Count',
                data: values,
                backgroundColor: 'rgba(59, 130, 246, 0.8)',
                borderColor: 'rgb(59, 130, 246)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

function displayUserActivity(data) {
    destroyChart('usersChart');

    const ctx = document.getElementById('usersChart');
    const labels = Object.keys(data);
    const values = Object.values(data);

    charts.usersChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Records Created',
                data: values,
                backgroundColor: 'rgba(139, 92, 246, 0.8)',
                borderColor: 'rgb(139, 92, 246)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

function displayReasonBreakdown(data) {
    destroyChart('reasonsChart');

    const ctx = document.getElementById('reasonsChart');
    const labels = Object.keys(data);
    const values = Object.values(data);

    charts.reasonsChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    'rgb(245, 158, 11)',
                    'rgb(236, 72, 153)',
                    'rgb(59, 130, 246)',
                    'rgb(16, 185, 129)',
                    'rgb(239, 68, 68)',
                    'rgb(139, 92, 246)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

function destroyChart(chartId) {
    if (charts[chartId]) {
        charts[chartId].destroy();
        delete charts[chartId];
    }
}

function hideAllSections() {
    document.getElementById('summarySection').style.display = 'none';
    document.getElementById('chartsSection').style.display = 'none';
}

function showNotification(message, type = 'info') {
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
    `;

    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}