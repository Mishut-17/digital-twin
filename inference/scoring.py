"""
Weighted Scoring Engine
=======================
Combines model RUL prediction with sponsor-defined weighting logic:
  - Bearing Life Weight: older bearing → higher weight (1x→3x→5x)
  - Slope Weight: vibration RMS spikes → higher weight (1x→5x)
  - User-configurable scale (1-10) for each factor

Outputs actionable prediction: "Change bearing by April 15, 2026"
"""

from datetime import datetime, timedelta


def interpolate_weight(value, breakpoints):
    """Piecewise-linear interpolation from breakpoints list."""
    if value <= breakpoints[0][0]:
        return breakpoints[0][1]
    if value >= breakpoints[-1][0]:
        return breakpoints[-1][1]
    for i in range(len(breakpoints) - 1):
        x0, y0 = breakpoints[i]
        x1, y1 = breakpoints[i + 1]
        if value <= x1:
            frac = (value - x0) / (x1 - x0)
            return y0 + frac * (y1 - y0)
    return breakpoints[-1][1]


class BearingScorer:
    """
    Combines model prediction with sponsor-defined weighting logic.

    The 1-10 user scale works as:
      scale=5 → default multipliers (1x/3x/5x for life, 1x/2x/3x/5x for slope)
      scale=1 → all multipliers near 1x (factor almost ignored)
      scale=10 → all multipliers doubled
    """

    # Breakpoints from sponsor's formula
    LIFE_BREAKPOINTS = [(0.0, 1.0), (0.5, 3.0), (1.0, 5.0)]
    SLOPE_BREAKPOINTS = [(0.0, 1.0), (5.0, 2.0), (10.0, 3.0), (20.0, 5.0)]

    def __init__(
        self,
        life_weight_scale=5,
        slope_weight_scale=5,
        bearing_age_hours=0.0,
        bearing_total_life_hours=1500.0,
    ):
        self.life_weight_scale = life_weight_scale
        self.slope_weight_scale = slope_weight_scale
        self.bearing_age_hours = bearing_age_hours
        self.bearing_total_life_hours = bearing_total_life_hours

    def compute_life_weight(self, current_hours=None):
        """
        Map bearing age to weight multiplier.
        Breakpoints: 0%→1x, 50%→3x, 100%→5x
        """
        if current_hours is None:
            current_hours = self.bearing_age_hours
        fraction = min(current_hours / max(self.bearing_total_life_hours, 1), 1.0)
        base = interpolate_weight(fraction, self.LIFE_BREAKPOINTS)
        scale_factor = self.life_weight_scale / 5.0
        return base * scale_factor

    def compute_slope_weight(self, rms_change):
        """
        Map vibration RMS change to weight multiplier.
        Breakpoints: 0→1x, 5→2x, 10→3x, 20→5x
        """
        base = interpolate_weight(abs(rms_change), self.SLOPE_BREAKPOINTS)
        scale_factor = self.slope_weight_scale / 5.0
        return base * scale_factor

    def predict_failure_date(
        self,
        model_rul_hours,
        rms_change=0.0,
        current_datetime=None,
    ):
        """
        Apply weighting and produce actionable output.

        Parameters
        ----------
        model_rul_hours : float
            Raw RUL prediction from the model (hours).
        rms_change : float
            Recent vibration RMS change (used for slope weight).
        current_datetime : datetime, optional
            Current time. Defaults to now.

        Returns
        -------
        dict with: rul_hours, rul_days, failure_date, change_by,
                   health_percent, risk_level, life_weight, slope_weight,
                   combined_weight
        """
        if current_datetime is None:
            current_datetime = datetime.now()

        life_w = self.compute_life_weight()
        slope_w = self.compute_slope_weight(rms_change)
        combined_w = life_w * slope_w

        # Higher combined weight → reduce RUL (more aggressive prediction)
        # Normalize: at default weights (scale=5, mid-life, no slope), combined~=3
        # So we divide by 3 to keep base prediction reasonable, then multiply
        adjustment = combined_w / 3.0
        adjusted_rul = max(model_rul_hours / max(adjustment, 0.1), 0.0)

        rul_days = adjusted_rul / 24.0
        failure_date = current_datetime + timedelta(hours=adjusted_rul)

        # Health percentage: 0% = about to fail, 100% = brand new
        health = min(100.0, max(0.0, (adjusted_rul / self.bearing_total_life_hours) * 100))

        # Risk level
        if health > 60:
            risk = "low"
        elif health > 30:
            risk = "medium"
        elif health > 10:
            risk = "high"
        else:
            risk = "critical"

        return {
            "rul_hours": round(adjusted_rul, 2),
            "rul_days": round(rul_days, 2),
            "failure_date": failure_date.strftime("%Y-%m-%d"),
            "change_by": f"Change bearing by {failure_date.strftime('%B %d, %Y')}",
            "health_percent": round(health, 1),
            "risk_level": risk,
            "life_weight": round(life_w, 2),
            "slope_weight": round(slope_w, 2),
            "combined_weight": round(combined_w, 2),
        }
