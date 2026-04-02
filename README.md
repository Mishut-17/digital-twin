# Bearing Digital Twin — Remaining Useful Life Prediction

![CI](https://github.com/gautam2905/Digital-Twin/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11-blue)

A Digital Twin dashboard for industrial centrifugal pump bearings that predicts **Remaining Useful Life (RUL)** — when a bearing should be replaced — using vibration data analysis and machine learning.

Built for [Fabrik](https://fabrik.space) as part of IIIT Delhi's SDOS course.

## Architecture

```
Vibration Data (UODS-VAFDC + Multi-domain)
    ↓
Preprocessing: severity ordering → windowing → RUL labeling
    ↓
RUL Regression Model (PyTorch training)
    ↓
Export weights to .npz (lightweight NumPy-only inference)
    ↓
FastAPI Backend + WebSocket Real-Time Simulator
    ↓
Dark-Themed Dashboard (Chart.js)
```

## Features

- **RUL Prediction**: Predicts hours/days until bearing failure from vibration patterns
- **Real-Time Simulator**: Watch a bearing degrade in real-time with configurable speed (10x-1000x)
- **Interactive Dashboard**: Dark-themed UI with donut charts, trend analysis, raw data plots, and data table
- **Configurable Weights**: User-adjustable bearing life weight and slope weight (1-10 scale)
- **Lightweight Inference**: Pure NumPy forward pass — no PyTorch/TensorFlow needed at runtime
- **Actionable Output**: "Change bearing by April 15, 2026" — one line for operators

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the dashboard

```bash
python -m webapp.app
# or
bash run.sh
```

Open http://localhost:8000 in your browser.

### 3. Use the simulator

1. Click **Start** to begin the real-time bearing simulation
2. Watch the vibration RMS trend increase as the bearing degrades
3. The RUL countdown updates with each reading
4. Adjust speed with 10x/100x/500x/1000x buttons
5. Go to **Configuration** to adjust weight parameters

## Training (Optional)

If you want to retrain the model:

```bash
# Install training dependencies
pip install -r requirements-training.txt

# Build RUL dataset from vibration files
python -m data_generator.build_rul_dataset

# Train the model
python -m rul_model.train --epochs 200

# Evaluate
python -m rul_model.evaluate

# Export weights to NumPy format
python -m rul_model.export_weights
```

## Project Structure

```
├── data_generator/          # Vibration data → RUL dataset pipeline
├── rul_model/               # Model architecture, training, export
├── inference/               # Lightweight NumPy inference + scoring
├── webapp/                  # FastAPI dashboard + WebSocket simulator
├── tests/                   # Unit and integration tests
├── .github/                 # CI workflow, PR/issue templates
├── requirements.txt         # Runtime dependencies
└── requirements-training.txt # Training-only dependencies
```

## Weighting Formula

Per sponsor specifications:

| Factor | Breakpoints |
|--------|------------|
| **Bearing Life Weight** | 1x (new) → 3x (half-life) → 5x (end-of-life) |
| **Slope Weight** | 1x (stable) → 2x (+5) → 3x (+10) → 5x (+20) |
| **Combined** | Life × Slope (e.g., 4.6 × 3 = 13.8x) |

Both weights are adjustable via user sliders (1-10 scale) on the configuration page.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard UI |
| GET | `/config` | Weight configuration page |
| GET | `/api/health` | Current bearing health JSON |
| GET | `/api/history` | Recent readings JSON |
| GET | `/api/config` | Current config JSON |
| POST | `/api/config` | Update weight configuration |
| WS | `/ws/stream` | Real-time simulator WebSocket |

## Team

| Name | Role | Focus |
|------|------|-------|
| Gautam Gupta (2023220) | ML Engineer | Model training, backend integration |
| Yash Verma (2023610) | Full-Stack Dev | Inference engine, dashboard UI, tests |
| Utkarsh Mishra (2023571) | Data Engineer | Data pipeline, simulator, configuration |

## Data Sources

- [University of Ottawa Ball-bearing Vibration and Acoustic Fault Data (UODS-VAFDC)](https://data.mendeley.com/)
- [Multi-domain vibration dataset — deep groove ball bearing](https://data.mendeley.com/)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, branch naming, commit conventions, and PR process.

## License

This project is developed for academic purposes as part of IIIT Delhi's SDOS program.
