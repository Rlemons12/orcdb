let availableReports = [];
let workbookAnalytics = null;
let activeCharts = [];

document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('reportSelect').addEventListener('change', loadAnalytics);
    document.getElementById('reportSearch').addEventListener('input', renderReportOptions);
    document.getElementById('sheetSelect').addEventListener('change', renderSelectedSheet);
    await loadReports();
});

async function loadReports() {
    const response = await fetch('/analytics/api/reports');
    availableReports = await response.json();
    renderReportOptions();
}

function renderReportOptions() {
    const select = document.getElementById('reportSelect');
    const current = select.value;
    const search = document.getElementById('reportSearch').value.toLowerCase();
    const filtered = availableReports.filter(report =>
        `${report.category} ${report.name}`.toLowerCase().includes(search)
    );
    select.innerHTML = '<option value="">Select a report...</option>' + filtered.map(report =>
        `<option value="${escapeHtml(report.path)}">${escapeHtml(report.category)} / ${escapeHtml(report.name)}</option>`
    ).join('');
    if (filtered.some(report => report.path === current)) select.value = current;
}

async function loadAnalytics() {
    const filepath = document.getElementById('reportSelect').value;
    if (!filepath) return hideAnalytics();
    setLoading(true);
    try {
        const response = await fetch(`/analytics/api/workbook/${encodePath(filepath)}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || data.error || 'Analysis failed');
        workbookAnalytics = data;
        renderSummary(data.summary);
        const sheetSelect = document.getElementById('sheetSelect');
        sheetSelect.innerHTML = data.sheets.map((sheet, index) =>
            `<option value="${index}">${escapeHtml(sheet.name)} (${sheet.rows.toLocaleString()} rows)</option>`
        ).join('');
        document.getElementById('summarySection').hidden = false;
        document.getElementById('sheetSection').hidden = false;
        renderSelectedSheet();
    } catch (error) {
        hideAnalytics();
        const panel = document.getElementById('analyticsError');
        panel.textContent = error.message;
        panel.hidden = false;
    } finally {
        setLoading(false);
    }
}

function renderSummary(summary) {
    const cards = [
        ['Sheets', summary.sheet_count], ['Total Rows', summary.total_rows],
        ['Numeric Columns', summary.numeric_columns], ['Date Columns', summary.date_columns]
    ];
    document.getElementById('summaryCards').innerHTML = cards.map(([label, value]) => `
        <div class="stat-card"><div class="stat-details"><h3>${Number(value).toLocaleString()}</h3><p>${label}</p></div></div>
    `).join('');
}

function renderSelectedSheet() {
    if (!workbookAnalytics) return;
    destroyCharts();
    const sheet = workbookAnalytics.sheets[Number(document.getElementById('sheetSelect').value || 0)];
    document.getElementById('sheetOverview').innerHTML = `
        <h2>${escapeHtml(sheet.name)}</h2>
        <p><strong>${sheet.rows.toLocaleString()}</strong> rows and <strong>${sheet.columns.toLocaleString()}</strong> columns</p>
        <p class="column-list">${sheet.column_names.map(escapeHtml).join(', ')}</p>`;
    renderCharts(sheet);
    renderNumericSummary(sheet.numeric_summary);
    renderPreview(sheet);
}

function renderCharts(sheet) {
    const grid = document.getElementById('chartGrid');
    const charts = [];
    sheet.date_trends.forEach(item => charts.push({title: `${item.column} by Month`, type: 'line', values: item.values}));
    sheet.categorical_summary.slice(0, 8).forEach(item => charts.push({title: `Top ${item.column}`, type: 'bar', values: item.values}));
    grid.innerHTML = charts.length ? charts.map((chart, index) => `
        <div class="chart-container"><h2>${escapeHtml(chart.title)}</h2><canvas id="analyticsChart${index}"></canvas></div>
    `).join('') : '<div class="section"><p>No categorical or date charts are available for this sheet.</p></div>';
    charts.forEach((chart, index) => {
        activeCharts.push(new Chart(document.getElementById(`analyticsChart${index}`), {
            type: chart.type,
            data: {labels: chart.values.map(item => item.label), datasets: [{label: 'Records', data: chart.values.map(item => item.count), backgroundColor: 'rgba(59,130,246,.75)', borderColor: 'rgb(59,130,246)', borderWidth: 1}]},
            options: {responsive: true, indexAxis: chart.type === 'bar' ? 'y' : 'x', scales: {y: {beginAtZero: true}}, plugins: {legend: {display: chart.type === 'line'}}}
        }));
    });
}

function renderNumericSummary(items) {
    const section = document.getElementById('numericSection');
    if (!items.length) { section.innerHTML = '<h2>Numeric Summary</h2><p>No numeric columns.</p>'; return; }
    section.innerHTML = `<h2>Numeric Summary</h2><div class="table-responsive"><table class="analytics-table"><thead><tr><th>Column</th><th>Count</th><th>Sum</th><th>Average</th><th>Min</th><th>Max</th></tr></thead><tbody>${items.map(item => `<tr><td>${escapeHtml(item.column)}</td><td>${formatNumber(item.count)}</td><td>${formatNumber(item.sum)}</td><td>${formatNumber(item.average)}</td><td>${formatNumber(item.minimum)}</td><td>${formatNumber(item.maximum)}</td></tr>`).join('')}</tbody></table></div>`;
}

function renderPreview(sheet) {
    const section = document.getElementById('previewSection');
    if (!sheet.preview.length) { section.innerHTML = '<h2>Data Preview</h2><p>No rows.</p>'; return; }
    const columns = sheet.column_names.slice(0, 12);
    section.innerHTML = `<h2>Data Preview</h2><div class="table-responsive"><table class="analytics-table"><thead><tr>${columns.map(column => `<th>${escapeHtml(column)}</th>`).join('')}</tr></thead><tbody>${sheet.preview.map(row => `<tr>${columns.map(column => `<td>${escapeHtml(row[column] ?? '')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}

function destroyCharts() { activeCharts.forEach(chart => chart.destroy()); activeCharts = []; }
function setLoading(value) { document.getElementById('loadingIndicator').hidden = !value; document.getElementById('analyticsError').hidden = true; }
function hideAnalytics() { destroyCharts(); workbookAnalytics = null; document.getElementById('summarySection').hidden = true; document.getElementById('sheetSection').hidden = true; }
function encodePath(path) { return path.split('/').map(encodeURIComponent).join('/'); }
function formatNumber(value) { return value == null ? '' : Number(value).toLocaleString(undefined, {maximumFractionDigits: 2}); }
function escapeHtml(value) { const div = document.createElement('div'); div.textContent = String(value); return div.innerHTML; }
