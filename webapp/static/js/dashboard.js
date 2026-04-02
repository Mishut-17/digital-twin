/**
 * Digital Twin Dashboard — Chart.js Visualizations
 * Donut charts, trend analysis, raw vibration, and data table.
 */

// Chart.js defaults for dark theme
Chart.defaults.color = '#8090a0';
Chart.defaults.borderColor = '#233554';

// --- Donut Charts ---
function createDonut(canvasId, healthPercent) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const healthy = Math.max(0, Math.min(100, healthPercent));
    const degraded = 100 - healthy;

    const color = healthy > 60 ? '#53d769' : healthy > 30 ? '#ffcc00' : '#e94560';

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Healthy', 'Degraded'],
            datasets: [{
                data: [healthy, degraded],
                backgroundColor: [color, '#233554'],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            cutout: '70%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: true },
            }
        }
    });
}

const donutOverall = createDonut('donut-overall', 100);
const donutDE = createDonut('donut-de', 100);
const donutNDE = createDonut('donut-nde', 100);

function updateDonuts(healthPercent) {
    const healthy = Math.max(0, Math.min(100, healthPercent));
    const degraded = 100 - healthy;
    const color = healthy > 60 ? '#53d769' : healthy > 30 ? '#ffcc00' : '#e94560';

    // Slight variation for DE and NDE
    const hDE = Math.min(100, healthy + (Math.random() * 6 - 3));
    const hNDE = Math.min(100, healthy + (Math.random() * 6 - 3));

    [donutOverall, donutDE, donutNDE].forEach((chart, i) => {
        const h = i === 0 ? healthy : i === 1 ? hDE : hNDE;
        chart.data.datasets[0].data = [h, 100 - h];
        chart.data.datasets[0].backgroundColor[0] = h > 60 ? '#53d769' : h > 30 ? '#ffcc00' : '#e94560';
        chart.update('none');
    });

    document.getElementById('health-overall').textContent = healthy.toFixed(1) + '%';
    document.getElementById('health-overall').style.color = color;
    document.getElementById('health-de').textContent = hDE.toFixed(1) + '%';
    document.getElementById('health-de').style.color = hDE > 60 ? '#53d769' : hDE > 30 ? '#ffcc00' : '#e94560';
    document.getElementById('health-nde').textContent = hNDE.toFixed(1) + '%';
    document.getElementById('health-nde').style.color = hNDE > 60 ? '#53d769' : hNDE > 30 ? '#ffcc00' : '#e94560';
}


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
                borderColor: '#4a9eff',
                backgroundColor: 'rgba(74, 158, 255, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
            },
            {
                label: 'Threshold',
                data: [],
                borderColor: '#e94560',
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
        plugins: {
            legend: { position: 'top' },
        },
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
            label: 'Temperature (°C)',
            data: [],
            backgroundColor: '#e94560',
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
                title: { display: true, text: 'Temperature (°C)' },
                min: 20,
                suggestedMax: 80,
            }
        },
        plugins: {
            legend: { position: 'top' },
        },
        animation: false,
    }
});


// --- Data Table ---
const MAX_TABLE_ROWS = 50;
const MAX_CHART_POINTS = 300;
let tableData = [];

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
    for (let i = tableData.length - 1; i >= Math.max(0, tableData.length - 30); i--) {
        const r = tableData[i].reading;
        const p = tableData[i].prediction;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${r.timestamp || '--'}</td>
            <td>${r.hours_running || '--'}</td>
            <td>${r.vibration_rms || '--'}</td>
            <td>${r.temperature || '--'}°C</td>
            <td>${r.rpm || '--'}</td>
            <td>${p.rul_days || '--'}</td>
            <td>${p.health_percent || '--'}%</td>
        `;
        tbody.appendChild(tr);
    }
}


// --- Update functions called by simulator.js ---
function updateDashboard(reading, prediction) {
    // RUL header
    const rulEl = document.getElementById('rul-value');
    const rulDays = prediction.rul_days;
    rulEl.textContent = rulDays.toFixed(2) + ' days';
    rulEl.className = 'rul-value';
    if (prediction.risk_level === 'critical') rulEl.classList.add('critical');
    else if (prediction.risk_level === 'high') rulEl.classList.add('high');
    else if (prediction.risk_level === 'medium') rulEl.classList.add('warning');

    document.getElementById('rul-action').textContent = prediction.change_by || '';

    // Donuts
    updateDonuts(prediction.health_percent);

    // Weight factors
    document.getElementById('weight-life').textContent = prediction.life_weight + 'x';
    document.getElementById('weight-slope').textContent = prediction.slope_weight + 'x';
    document.getElementById('weight-combined').textContent = prediction.combined_weight + 'x';

    const riskEl = document.getElementById('risk-level');
    riskEl.textContent = prediction.risk_level.toUpperCase();
    const riskColors = { low: '#53d769', medium: '#ffcc00', high: '#ff9500', critical: '#e94560' };
    riskEl.style.color = riskColors[prediction.risk_level] || '#e0e0e0';

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

    document.getElementById('rul-value').textContent = '--';
    document.getElementById('rul-action').textContent = 'Start the simulator to see predictions';
    updateDonuts(100);
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
