"""Tests for the weighted scoring engine."""

from datetime import datetime
from inference.scoring import BearingScorer, interpolate_weight


def test_life_weight_at_start():
    scorer = BearingScorer(bearing_age_hours=0, bearing_total_life_hours=1500)
    w = scorer.compute_life_weight(0)
    assert abs(w - 1.0) < 0.01


def test_life_weight_at_half_life():
    scorer = BearingScorer(bearing_age_hours=750, bearing_total_life_hours=1500)
    w = scorer.compute_life_weight(750)
    assert abs(w - 3.0) < 0.01


def test_life_weight_at_end():
    scorer = BearingScorer(bearing_age_hours=1500, bearing_total_life_hours=1500)
    w = scorer.compute_life_weight(1500)
    assert abs(w - 5.0) < 0.01


def test_life_weight_scale():
    """Scale=10 should double the weight."""
    scorer_default = BearingScorer(life_weight_scale=5, bearing_age_hours=750,
                                    bearing_total_life_hours=1500)
    scorer_max = BearingScorer(life_weight_scale=10, bearing_age_hours=750,
                                bearing_total_life_hours=1500)
    w_default = scorer_default.compute_life_weight(750)
    w_max = scorer_max.compute_life_weight(750)
    assert abs(w_max - w_default * 2) < 0.01


def test_slope_weight_zero():
    scorer = BearingScorer()
    w = scorer.compute_slope_weight(0)
    assert abs(w - 1.0) < 0.01


def test_slope_weight_at_5():
    scorer = BearingScorer()
    w = scorer.compute_slope_weight(5.0)
    assert abs(w - 2.0) < 0.01


def test_predict_failure_date_returns_all_keys():
    scorer = BearingScorer(bearing_age_hours=500, bearing_total_life_hours=1500)
    result = scorer.predict_failure_date(
        model_rul_hours=500,
        rms_change=2.0,
        current_datetime=datetime(2026, 4, 1),
    )

    required_keys = [
        "rul_hours", "rul_days", "failure_date", "change_by",
        "health_percent", "risk_level", "life_weight", "slope_weight",
        "combined_weight",
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"

    assert result["rul_hours"] >= 0
    assert result["rul_days"] >= 0
    assert 0 <= result["health_percent"] <= 100
    assert result["risk_level"] in ("low", "medium", "high", "critical")


def test_higher_age_reduces_rul():
    """Older bearing should get lower adjusted RUL."""
    scorer_young = BearingScorer(bearing_age_hours=100, bearing_total_life_hours=1500)
    scorer_old = BearingScorer(bearing_age_hours=1400, bearing_total_life_hours=1500)

    r_young = scorer_young.predict_failure_date(500, current_datetime=datetime(2026, 4, 1))
    r_old = scorer_old.predict_failure_date(500, current_datetime=datetime(2026, 4, 1))

    assert r_old["rul_hours"] < r_young["rul_hours"]
