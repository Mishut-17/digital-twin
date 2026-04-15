/**
 * Digital Twin Dashboard - Chart.js Visualizations
 * Donut charts, trend analysis, raw vibration, and data table.
 */

// Chart.js defaults for light theme
Chart.defaults.color = '#4a4a4a';
Chart.defaults.borderColor = '#cfcfcf';
Chart.defaults.font.family = "'Source Sans 3', 'Segoe UI', sans-serif";

const RISK_COLORS = {
    low: '#2f6b4f',
    medium: '#b27b2a',
    high: '#b2512a',
    critical: '#a81212'
};


// --- Trend Analysis Chart ---
const trendCtx = document.getElementById('trend-chart').getContext('2d');
const trendChart = new Chart(trendCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Vibration RMS',
                data: [],
                borderColor: '#1f4e79',
                backgroundColor: 'rgba(31, 78, 121, 0.12)',
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
            },
            {
                label: 'Threshold',
                data: [],
                borderColor: '#a81212',
                borderDash: [5, 5],
                borderWidth: 1,
                pointRadius: 0,
                fill: false,
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        scales: {
            x: {
                title: { display: true, text: 'Hours Running' },
                ticks: { maxTicksLimit: 10 },
            },
            y: {
                title: { display: true, text: 'Vibration RMS' },
                min: 0,
                suggestedMax: 1.5,
            }
        },
        plugins: { legend: { display: false } },
        animation: false,
    }
});


// --- Raw Vibration Chart ---
const rawCtx = document.getElementById('raw-chart').getContext('2d');
const rawChart = new Chart(rawCtx, {
    type: 'bar',
    data: {
        labels: [],
        datasets: [{
            label: 'Temperature (C)',
            data: [],
            backgroundColor: '#8b0f0f',
            borderWidth: 0,
            barPercentage: 1.0,
            categoryPercentage: 1.0,
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                title: { display: true, text: 'Hours Running' },
                ticks: { maxTicksLimit: 10 },
            },
            y: {
                title: { display: true, text: 'Temperature (C)' },
                min: 20,
                suggestedMax: 80,
            }
        },
        plugins: { legend: { display: false } },
        animation: false,
    }
});


// --- Data Table ---
const MAX_TABLE_ROWS = 50;
const MAX_CHART_POINTS = 300;
const MAX_LOG_LINES = 8;
const MAX_TABLE_VIEW = 8;
let tableData = [];
let logLines = [];

function addTableRow(reading, prediction) {
    tableData.push({ reading, prediction });
    if (tableData.length > MAX_TABLE_ROWS) {
        tableData.shift();
    }
    renderTable();
}

function renderTable() {
    const tbody = document.getElementById('data-table-body');
    tbody.innerHTML = '';
    for (let i = tableData.length - 1; i >= Math.max(0, tableData.length - MAX_TABLE_VIEW); i--) {
        const r = tableData[i].reading;
        const p = tableData[i].prediction;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${r.timestamp || '--'}</td>
            <td>${r.hours_running || '--'}</td>
            <td>${r.vibration_rms || '--'}</td>
            <td>${r.temperature || '--'}C</td>
            <td>${r.rpm || '--'}</td>
            <td>${p.rul_days || '--'}</td>
            <td>${p.health_percent || '--'}%</td>
        `;
        tbody.appendChild(tr);
    }
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function updateRiskChip(level) {
    const chip = document.getElementById('risk-level-chip');
    if (!chip) return;
    if (!level) {
        chip.textContent = '--';
        chip.style.background = '';
        chip.style.color = '';
        return;
    }
    const color = RISK_COLORS[level] || '#1b1b1d';
    chip.textContent = level.toUpperCase();
    chip.style.background = color;
    chip.style.color = '#ffffff';
}

function renderTelemetry() {
    const logEl = document.getElementById('telemetry-log');
    if (!logEl) return;
    logEl.innerHTML = logLines.map(line => `<div class="log-line">${line}</div>`).join('');
}

function pushTelemetry(reading, prediction) {
    const hoursLabel = Number.isFinite(Number(reading.hours_running))
        ? Number(reading.hours_running).toFixed(1)
        : '--';
    const timeLabel = reading.timestamp || ('t+' + hoursLabel + 'h');
    const vib = Number.isFinite(Number(reading.vibration_rms))
        ? Number(reading.vibration_rms).toFixed(3)
        : '--';
    const temp = Number.isFinite(Number(reading.temperature))
        ? Number(reading.temperature).toFixed(1)
        : '--';
    const rpm = Number.isFinite(Number(reading.rpm))
        ? Math.round(Number(reading.rpm))
        : '--';
    const rul = Number.isFinite(Number(prediction.rul_days))
        ? Number(prediction.rul_days).toFixed(2)
        : '--';

    logLines.push(`${timeLabel} | vib ${vib} | temp ${temp}C | rpm ${rpm} | RUL ${rul}d`);
    if (logLines.length > MAX_LOG_LINES) logLines.shift();
    renderTelemetry();
}

function updateBearingSpin(rpm) {
    const bearing = document.getElementById('bearing-anim');
    if (!bearing) return;
    const speed = Number(rpm);
    if (!Number.isFinite(speed) || speed <= 0) {
        bearing.style.setProperty('--spin-duration', '6s');
        return;
    }
    const duration = Math.max(1.5, Math.min(8, 600 / speed));
    bearing.style.setProperty('--spin-duration', `${duration.toFixed(2)}s`);
}

function updateLiveStats(reading) {
    const vib = Number.isFinite(Number(reading.vibration_rms))
        ? Number(reading.vibration_rms).toFixed(3)
        : '--';
    const temp = Number.isFinite(Number(reading.temperature))
        ? Number(reading.temperature).toFixed(1) + 'C'
        : '--';
    const rpm = Number.isFinite(Number(reading.rpm))
        ? Math.round(Number(reading.rpm))
        : '--';
    const hours = Number.isFinite(Number(reading.hours_running))
        ? Number(reading.hours_running).toFixed(1)
        : '--';

    setText('stat-vibration', vib);
    setText('stat-temperature', temp);
    setText('stat-rpm', rpm);
    setText('stat-hours', hours);
    setText('bearing-speed', rpm);
    setText('bearing-hours', hours);
    updateBearingSpin(reading.rpm);
}


// --- Update functions called by simulator.js ---
function updateDashboard(reading, prediction) {
    // RUL header
    const rulEl = document.getElementById('rul-value');
    const rulDays = Number(prediction.rul_days);
    rulEl.textContent = Number.isFinite(rulDays) ? rulDays.toFixed(2) : '--';
    rulEl.className = 'rul-value';
    if (prediction.risk_level === 'critical') rulEl.classList.add('critical');
    else if (prediction.risk_level === 'high') rulEl.classList.add('high');
    else if (prediction.risk_level === 'medium') rulEl.classList.add('warning');

    document.getElementById('rul-action').textContent = prediction.change_by || '';

    // Weight factors
    document.getElementById('weight-life').textContent = prediction.life_weight + 'x';
    document.getElementById('weight-slope').textContent = prediction.slope_weight + 'x';
    document.getElementById('weight-combined').textContent = prediction.combined_weight + 'x';

    const riskEl = document.getElementById('risk-level');
    riskEl.textContent = prediction.risk_level.toUpperCase();
    riskEl.style.color = RISK_COLORS[prediction.risk_level] || '#e0e0e0';

    const health = Number(prediction.health_percent);
    setText('stat-health', Number.isFinite(health) ? health.toFixed(1) + '%' : '--');
    updateRiskChip(prediction.risk_level);

    // Trend chart
    const hour = reading.hours_running;
    trendChart.data.labels.push(hour);
    trendChart.data.datasets[0].data.push(reading.vibration_rms);
    trendChart.data.datasets[1].data.push(1.0); // threshold line

    if (trendChart.data.labels.length > MAX_CHART_POINTS) {
        trendChart.data.labels.shift();
        trendChart.data.datasets[0].data.shift();
        trendChart.data.datasets[1].data.shift();
    }
    trendChart.update('none');

    // Raw chart
    rawChart.data.labels.push(hour);
    rawChart.data.datasets[0].data.push(reading.temperature);

    if (rawChart.data.labels.length > MAX_CHART_POINTS) {
        rawChart.data.labels.shift();
        rawChart.data.datasets[0].data.shift();
    }
    rawChart.update('none');

    // Table
    addTableRow(reading, prediction);

    // Live stats and telemetry
    updateLiveStats(reading);
    pushTelemetry(reading, prediction);
}

function clearDashboard() {
    trendChart.data.labels = [];
    trendChart.data.datasets.forEach(ds => ds.data = []);
    trendChart.update();

    rawChart.data.labels = [];
    rawChart.data.datasets.forEach(ds => ds.data = []);
    rawChart.update();

    tableData = [];
    document.getElementById('data-table-body').innerHTML =
        '<tr><td colspan="7" style="text-align:center;color:#555;">No data yet</td></tr>';

    const rulEl = document.getElementById('rul-value');
    rulEl.textContent = '--';
    rulEl.className = 'rul-value';
    document.getElementById('rul-action').textContent = 'Start the simulator to see predictions';
    updateRiskChip('');

    logLines = [];
    renderTelemetry();
    const logEl = document.getElementById('telemetry-log');
    if (logEl) {
        logEl.innerHTML = '<div class="log-line">Waiting for data...</div>';
    }
    ['stat-vibration', 'stat-temperature', 'stat-rpm', 'stat-hours', 'stat-health', 'bearing-speed', 'bearing-hours']
        .forEach(id => setText(id, '--'));
    ['weight-life', 'weight-slope', 'weight-combined', 'risk-level']
        .forEach(id => setText(id, '--'));
    const riskEl = document.getElementById('risk-level');
    if (riskEl) riskEl.style.color = '';
    updateBearingSpin(0);
}


// --- Error Handling ---
window.onerror = function(msg, url, line) {
    console.error('[Dashboard Error]', msg, 'at', url, ':', line);
    return false;
};

// --- Keyboard Shortcuts ---
document.addEventListener('keydown', function(e) {
    if (e.key === ' ' && e.target === document.body) {
        e.preventDefault();
        const status = document.getElementById('status-text').textContent;
        if (status === 'Running') pauseSim();
        else startSim();
    }
    if (e.key === 'r' && e.ctrlKey) {
        e.preventDefault();
        resetSim();
    }
});
