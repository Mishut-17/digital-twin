"""
Configuration for bearing RUL dataset generation.

Defines severity ordering, bearing life parameters, and windowing
settings used to construct synthetic run-to-failure trajectories
from the UODS-VAFDC and Multi-domain vibration datasets.
"""

import os

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_HERE)

# ---------------------------------------------------------------------------
#  Dataset paths
# ---------------------------------------------------------------------------
UODS_ROOT = os.path.join(
    PROJECT_ROOT, "phase1", "data",
    "University of Ottawa Ball-bearing Vibration and Acoustic Fault Data "
    "under Constant Load and Speed Conditions (UODS-VAFDC)"
)

MULTIDOMAIN_ROOT = os.path.join(
    PROJECT_ROOT, "phase1", "data",
    "Multi-domain vibration dataset with various bearing types under "
    "compound machine fault scenarios subset 1 (deep groove ball bearing)",
    "BearingType_DeepGrooveBall"
)

# ---------------------------------------------------------------------------
#  Signal processing
# ---------------------------------------------------------------------------
TARGET_SR = 16_000          # All signals resampled to 16 kHz
WINDOW_SIZE = 8192          # samples per window  (0.512 s at 16 kHz)
STEP_SIZE = 4096            # 50 % overlap

# ---------------------------------------------------------------------------
#  Bearing life parameters (from sponsor: 1000-2000 h, safe 30-70 C)
# ---------------------------------------------------------------------------
BEARING_LIFE_HOURS = 1500   # assumed mean bearing life for RUL labels

# ---------------------------------------------------------------------------
#  UODS-VAFDC severity mapping
# ---------------------------------------------------------------------------
# Naming:  {FaultCode}_{ID}_{Sample}.mat
# FaultCode:  H = healthy,  I = inner race,  O = outer race,
#             B = ball,  C = cage
# The IDs themselves don't indicate severity gradients, so we treat
# all healthy files as "far from failure" and all faulty as "near failure".
UODS_FOLDERS = {
    "1_Healthy":          {"label": "H", "severity": 0.0},
    "2_Inner_Race_Faults": {"label": "I", "severity": 1.0},
    "3_Outer_Race_Faults": {"label": "O", "severity": 1.0},
    "4_Ball_Faults":       {"label": "B", "severity": 1.0},
    "5_Cage_Faults":       {"label": "C", "severity": 1.0},
}

# ---------------------------------------------------------------------------
#  Multi-domain severity mapping
# ---------------------------------------------------------------------------
# Filename:  {SeverityLevel}_{BearingCond}_{SampRate}_{Model}_{Speed}.mat
# SeverityLevel:  L = low,  M1/M2/M3 = medium 1-3,  H = high
# BearingCond:    H = healthy,  B = ball,  IR = inner race,  OR = outer race
# Severity ordering for degradation trajectory (0 = healthy, 1 = failure):
MULTIDOMAIN_SEVERITY_ORDER = {
    "H_H": 0.00,   # healthy bearing, high component → fully healthy
    "L_H": 0.00,   # healthy bearing, low component → fully healthy
    "M1_H": 0.00,  # healthy bearing
    "M2_H": 0.00,
    "M3_H": 0.00,
    "L":   0.20,   # low severity fault
    "M1":  0.40,   # medium-1 severity fault
    "M2":  0.55,   # medium-2
    "M3":  0.70,   # medium-3
    "H":   0.90,   # high severity fault (near failure)
}

# ---------------------------------------------------------------------------
#  Weight computation parameters (from sponsor's weighting formula)
# ---------------------------------------------------------------------------
# Bearing Life Weight: 1x at start → 3x at half-life → 5x at end
LIFE_WEIGHT_BREAKPOINTS = [(0.0, 1.0), (0.5, 3.0), (1.0, 5.0)]

# Slope Weight: based on RMS change in window
# 0 change → 1x,  +5 → 2x,  +10 → 3x,  +20 → 5x
SLOPE_WEIGHT_BREAKPOINTS = [(0.0, 1.0), (5.0, 2.0), (10.0, 3.0), (20.0, 5.0)]

# ---------------------------------------------------------------------------
#  Output
# ---------------------------------------------------------------------------
GENERATED_DIR = os.path.join(_HERE, "generated")
