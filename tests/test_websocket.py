"""Tests for the WebSocket simulator."""

from webapp.simulator import BearingSimulator


def test_simulator_init():
    sim = BearingSimulator(total_life_hours=100)
    assert sim.current_hour == 0
    assert sim.total_life_hours == 100
    assert not sim.running


def test_simulator_advance():
    sim = BearingSimulator(total_life_hours=100)
    reading = sim.advance()
    assert reading is not None
    assert "timestamp" in reading
    assert "vibration_rms" in reading
    assert "hours_running" in reading
    assert reading["vibration_rms"] > 0


def test_simulator_degradation():
    """Later readings should have higher vibration RMS on average."""
    sim = BearingSimulator(total_life_hours=100)

    early_rms = []
    for _ in range(10):
        r = sim.advance()
        early_rms.append(r["vibration_rms"])

    # Skip to near end
    sim.current_hour = 90
    late_rms = []
    for _ in range(10):
        r = sim.advance()
        if r:
            late_rms.append(r["vibration_rms"])

    if early_rms and late_rms:
        avg_early = sum(early_rms) / len(early_rms)
        avg_late = sum(late_rms) / len(late_rms)
        assert avg_late > avg_early, \
            f"Late RMS ({avg_late:.3f}) should be higher than early ({avg_early:.3f})"


def test_simulator_failure():
    """Simulator returns None after end of life."""
    sim = BearingSimulator(total_life_hours=5)
    readings = []
    for _ in range(10):
        r = sim.advance()
        if r is None:
            break
        readings.append(r)

    assert len(readings) == 5


def test_simulator_reset():
    sim = BearingSimulator(total_life_hours=100)
    sim.advance()
    sim.advance()
    assert sim.current_hour == 2

    sim.reset()
    assert sim.current_hour == 0
    assert not sim.running


def test_simulator_generate_history():
    sim = BearingSimulator(total_life_hours=100)
    sim.current_hour = 50
    hist = sim.generate_history(20)
    assert len(hist) > 0
    assert hist[0]["hours_running"] < hist[-1]["hours_running"]
