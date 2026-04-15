/**
 * Simulator Controls - WebSocket client for real-time bearing data.
 */

let ws = null;
let currentSpeed = 100;

function getWsUrl() {
    const backendUrl = window.BACKEND_URL || '';
    if (backendUrl) {
        // Convert http:// → ws:// and https:// → wss://
        return backendUrl.replace(/^http/, 'ws') + '/ws/stream';
    }
    // Fallback: same-origin (works when backend serves frontend directly)
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${location.host}/ws/stream`;
}

function connectWs() {
    if (ws && ws.readyState === WebSocket.OPEN) return;

    ws = new WebSocket(getWsUrl());

    ws.onopen = () => {
        console.log('[ws] Connected');
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === 'reading') {
            updateDashboard(msg.data, msg.prediction);
        } else if (msg.type === 'reset') {
            clearDashboard();
            setStatus('stopped');
        } else if (msg.type === 'failure') {
            setStatus('failure');
            document.getElementById('rul-action').textContent =
                'BEARING FAILURE - Replace immediately!';
            document.getElementById('rul-value').textContent = '0.00';
            document.getElementById('rul-value').className = 'rul-value critical';
            if (typeof updateRiskChip === 'function') {
                updateRiskChip('critical');
            }
        } else if (msg.type === 'history') {
            // Load historical data into charts
            if (msg.data && msg.data.length > 0) {
                msg.data.forEach(reading => {
                    const prediction = {
                        rul_days: 0, health_percent: 100,
                        life_weight: 1, slope_weight: 1, combined_weight: 1,
                        risk_level: 'low', change_by: ''
                    };
                    updateDashboard(reading, prediction);
                });
            }
        }
    };

    ws.onclose = () => {
        console.log('[ws] Disconnected');
        setTimeout(connectWs, 2000);
    };

    ws.onerror = (err) => {
        console.error('[ws] Error', err);
    };
}

function sendWs(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
    } else {
        connectWs();
        setTimeout(() => sendWs(data), 500);
    }
}

function startSim() {
    connectWs();
    setTimeout(() => {
        sendWs({ action: 'start' });
        setStatus('running');
    }, 300);
}

function pauseSim() {
    sendWs({ action: 'pause' });
    setStatus('paused');
}

function resetSim() {
    sendWs({ action: 'reset' });
    clearDashboard();
    setStatus('stopped');
}

function setSpeed(speed) {
    currentSpeed = speed;
    sendWs({ action: 'speed', value: speed });

    document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.trim() === speed + 'x');
    });
}

function setStatus(status) {
    const light = document.getElementById('status-light');
    const text = document.getElementById('status-text');

    light.className = 'status-indicator';
    if (status === 'running') {
        light.classList.add('running');
        text.textContent = 'Running';
    } else if (status === 'paused') {
        light.classList.add('paused');
        text.textContent = 'Paused';
    } else if (status === 'failure') {
        light.style.background = '#e94560';
        text.textContent = 'BEARING FAILED';
        text.style.color = '#e94560';
    } else {
        text.textContent = 'Stopped';
    }
}

// Auto-connect on page load
connectWs();
