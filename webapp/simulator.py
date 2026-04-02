"""
Real-Time Bearing Degradation Simulator
========================================
Streams progressive vibration readings simulating a bearing degrading
from healthy to failure. Each reading includes vibration RMS, computed
RUL prediction, and health indicators.
"""

import asyncio
import math
import random
import numpy as np
from datetime import datetime, timedelta


class BearingSimulator:
    """
    Simulates a bearing degrading in real-time.
    Generates one reading per tick, where each tick represents 1 hour
    of bearing life. Speed multiplier controls playback rate.
    """

    def __init__(
        self,
        total_life_hours=1500,
        base_rms=0.15,
        failure_rms=1.2,
        noise_std=0.02,
    ):
        self.total_life_hours = total_life_hours
        self.base_rms = base_rms
        self.failure_rms = failure_rms
        self.noise_std = noise_std
        self.reset()

    def reset(self):
        """Reset simulator to hour 0."""
        self.current_hour = 0.0
        self.start_time = datetime.now()
        self.running = False
        self.speed = 100  # default 100x real-time
        self._rng = random.Random(42)
        self._prev_rms = self.base_rms

    def _compute_rms(self, hour):
        """
        Generate realistic vibration RMS following 3-regime degradation:
          0-60% life: stable baseline with noise
          60-85% life: gradual increase with occasional spikes
          85-100% life: exponential rise toward failure
        """
        frac = hour / self.total_life_hours

        if frac < 0.6:
            # Normal operation
            base = self.base_rms
            noise = self._rng.gauss(0, self.noise_std)
            # Occasional minor spikes
            if self._rng.random() < 0.02:
                noise += self._rng.uniform(0.05, 0.15)
            rms = base + noise

        elif frac < 0.85:
            # Early degradation
            progress = (frac - 0.6) / 0.25
            base = self.base_rms + progress * 0.3
            noise = self._rng.gauss(0, self.noise_std * 1.5)
            # More frequent spikes
            if self._rng.random() < 0.08:
                noise += self._rng.uniform(0.1, 0.3)
            rms = base + noise

        else:
            # Rapid failure
            progress = (frac - 0.85) / 0.15
            base = self.base_rms + 0.3 + progress * (self.failure_rms - self.base_rms - 0.3)
            # Exponential component
            exp_factor = math.exp(progress * 2) / math.exp(2)
            base += exp_factor * 0.3
            noise = self._rng.gauss(0, self.noise_std * 2)
            rms = base + noise

        rms = max(0.01, rms)
        self._prev_rms = rms
        return round(rms, 4)

    def generate_reading(self):
        """
        Generate one data point for the current hour.
        Returns dict with all sensor values.
        """
        hour = self.current_hour
        rms = self._compute_rms(hour)

        sim_timestamp = self.start_time + timedelta(hours=hour)
        frac = hour / self.total_life_hours

        # Simulated temperature (correlated with vibration RMS)
        temp = 40 + (rms - self.base_rms) * 80 + self._rng.gauss(0, 1)
        temp = max(25, min(95, temp))

        reading = {
            "timestamp": sim_timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
            "hours_running": round(hour, 1),
            "vibration_rms": rms,
            "temperature": round(temp, 1),
            "rpm": 1800 + self._rng.randint(-10, 10),
            "load": 400 + self._rng.randint(-5, 5),
            "life_fraction": round(frac, 4),
        }

        return reading

    def advance(self):
        """Advance by 1 hour. Returns None if bearing has failed."""
        if self.current_hour >= self.total_life_hours:
            return None
        reading = self.generate_reading()
        self.current_hour += 1.0
        return reading

    def get_tick_interval(self):
        """Seconds between ticks at current speed."""
        # 1 hour of bearing life per tick
        # At speed=100, 1 tick every 0.036s (100 hours per 3.6 seconds)
        return 3600.0 / self.speed

    def generate_history(self, n_hours=100):
        """Generate n_hours of historical data (for initial chart loading)."""
        saved_hour = self.current_hour
        start = max(0, self.current_hour - n_hours)

        history = []
        self.current_hour = start
        while self.current_hour < saved_hour:
            reading = self.advance()
            if reading:
                history.append(reading)

        self.current_hour = saved_hour
        return history
