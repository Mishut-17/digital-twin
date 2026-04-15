"""
Digital Twin Dashboard — FastAPI Backend
=========================================
Serves the bearing Digital Twin dashboard, handles WebSocket
connections for real-time simulation, and provides API endpoints
for configuration and data access.
"""

import os
import sys
import json
import asyncio
import numpy as np
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from inference.numpy_inference import NumpyRULModel
from inference.scoring import BearingScorer
from webapp.simulator import BearingSimulator

# ---------------------------------------------------------------------------
#  App Setup
# ---------------------------------------------------------------------------
app = FastAPI(title="Fabrik Digital Twin Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(PROJECT_ROOT, "webapp", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ---------------------------------------------------------------------------
#  Global State
# ---------------------------------------------------------------------------
model = None
scorer = None
simulator = None
config_state = {
    "life_weight_scale": 5,
    "slope_weight_scale": 5,
    "bearing_age_hours": 0,
    "bearing_total_life_hours": 1500,
}
history = []  # stores recent readings for the data table


# ---------------------------------------------------------------------------
#  Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    global model, scorer, simulator

    weights_path = os.path.join(PROJECT_ROOT, "rul_model", "weights", "rul_model_weights.npz")
    if os.path.exists(weights_path):
        model = NumpyRULModel(weights_path)
        print(f"[startup] Model loaded from {weights_path}")
    else:
        print(f"[startup] WARNING: No model weights at {weights_path}")
        print(f"          Dashboard will use simulator-only mode")

    scorer = BearingScorer(**config_state)
    simulator = BearingSimulator(
        total_life_hours=config_state["bearing_total_life_hours"]
    )
    print("[startup] Dashboard ready")


# ---------------------------------------------------------------------------
#  API Endpoints
# ---------------------------------------------------------------------------
class ConfigUpdate(BaseModel):
    life_weight_scale: int = 5
    slope_weight_scale: int = 5
    bearing_age_hours: float = 0
    bearing_total_life_hours: float = 1500


@app.post("/api/config")
async def update_config(cfg: ConfigUpdate):
    global scorer, config_state
    config_state.update(cfg.dict())
    scorer = BearingScorer(**config_state)
    return {"status": "ok", "config": config_state}


@app.get("/api/config")
async def get_config():
    return config_state


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    dashboard_path = os.path.join(PROJECT_ROOT, "webapp", "templates", "dashboard.html")
    with open(dashboard_path, "r") as f:
        return f.read()


@app.get("/config", response_class=HTMLResponse)
async def get_config_page():
    config_path = os.path.join(PROJECT_ROOT, "webapp", "templates", "config.html")
    with open(config_path, "r") as f:
        return f.read()


@app.get("/api/health")
async def get_health():
    """Current bearing health based on simulator state."""
    if simulator is None:
        return {"error": "Simulator not initialized"}

    reading = simulator.generate_reading()
    prediction = _predict_from_reading(reading)

    return {
        "reading": reading,
        "prediction": prediction,
    }


@app.get("/api/history")
async def get_history():
    """Return recent readings."""
    return {"readings": history[-100:]}


# ---------------------------------------------------------------------------
#  Prediction Helper
# ---------------------------------------------------------------------------
def _predict_from_reading(reading):
    """Run inference + scoring on a reading."""
    rms = reading.get("vibration_rms", 0.5)

    if model is not None:
        # Create a synthetic window from RMS for inference
        # In production, this would come from raw vibration sensor
        window = np.random.default_rng(int(rms * 10000)).normal(0, rms, 8192).astype(np.float32)
        std = window.std()
        if std > 1e-8:
            window = (window - window.mean()) / std
        rul_hours = model.predict_hours(window)
    else:
        # Fallback: estimate RUL from simulator state
        frac = reading.get("life_fraction", 0.5)
        rul_hours = max(0, (1 - frac) * config_state["bearing_total_life_hours"])

    # Update scorer with current bearing age
    scorer.bearing_age_hours = reading.get("hours_running", 0)

    prediction = scorer.predict_failure_date(
        model_rul_hours=rul_hours,
        rms_change=rms * 10,  # scale RMS to match slope breakpoints
        current_datetime=datetime.now(),
    )

    return prediction


# ---------------------------------------------------------------------------
#  WebSocket — Real-time Simulator Stream
# ---------------------------------------------------------------------------
@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    global simulator, history

    try:
        while True:
            # Wait for control messages (non-blocking check)
            try:
                msg = await asyncio.wait_for(
                    websocket.receive_text(), timeout=0.01
                )
                data = json.loads(msg)
                action = data.get("action", "")

                if action == "start":
                    simulator.running = True
                elif action == "pause":
                    simulator.running = False
                elif action == "reset":
                    simulator.reset()
                    history.clear()
                    await websocket.send_json({"type": "reset"})
                elif action == "speed":
                    simulator.speed = int(data.get("value", 100))
                elif action == "get_history":
                    n = int(data.get("count", 100))
                    hist = simulator.generate_history(n)
                    await websocket.send_json({
                        "type": "history",
                        "data": hist,
                    })
            except asyncio.TimeoutError:
                pass

            # Send data if running
            if simulator.running:
                reading = simulator.advance()
                if reading is None:
                    await websocket.send_json({
                        "type": "failure",
                        "message": "Bearing has reached end of life!",
                    })
                    simulator.running = False
                    continue

                prediction = _predict_from_reading(reading)

                message = {
                    "type": "reading",
                    "data": reading,
                    "prediction": prediction,
                }

                history.append({**reading, **prediction})
                if len(history) > 500:
                    history = history[-500:]

                await websocket.send_json(message)

            # Sleep based on simulator speed
            interval = simulator.get_tick_interval()
            await asyncio.sleep(min(interval, 0.5))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[ws] Error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("webapp.app:app", host=host, port=port, reload=True)
