import threading
import time

import pytest
from pynput.mouse import Button

from autoclicker.clicker import ClickSettings, Clicker


class FakeMouse:
    def __init__(self):
        self.calls = []
        self.lock = threading.Lock()

    def click(self, button, count=1):
        with self.lock:
            self.calls.append((button, count))


def run_for(clicker, settings, seconds):
    clicker.start(settings)
    time.sleep(seconds)
    clicker.stop()


def test_clicks_until_stopped():
    mouse = FakeMouse()
    clicker = Clicker(mouse)
    run_for(clicker, ClickSettings(interval_ms=10), 0.2)
    assert not clicker.running
    assert len(mouse.calls) == clicker.count
    assert clicker.count >= 5
    stopped_at = len(mouse.calls)
    time.sleep(0.05)
    assert len(mouse.calls) == stopped_at


@pytest.mark.parametrize(
    "name, button", [("left", Button.left), ("right", Button.right), ("middle", Button.middle)]
)
def test_uses_selected_button(name, button):
    mouse = FakeMouse()
    run_for(Clicker(mouse), ClickSettings(interval_ms=10, button=name), 0.05)
    assert mouse.calls and all(b == button for b, _ in mouse.calls)


def test_double_click():
    mouse = FakeMouse()
    run_for(Clicker(mouse), ClickSettings(interval_ms=10, double=True), 0.05)
    assert mouse.calls and all(n == 2 for _, n in mouse.calls)


def test_stop_is_immediate_with_long_interval():
    mouse = FakeMouse()
    clicker = Clicker(mouse)
    clicker.start(ClickSettings(interval_ms=60_000))
    time.sleep(0.05)
    started = time.monotonic()
    clicker.stop()
    assert time.monotonic() - started < 0.5
    assert len(mouse.calls) == 1


def test_second_start_is_ignored():
    mouse = FakeMouse()
    clicker = Clicker(mouse)
    clicker.start(ClickSettings(interval_ms=10))
    first = clicker._thread
    clicker.start(ClickSettings(interval_ms=10))
    assert clicker._thread is first
    clicker.stop()


def test_can_restart_after_stop():
    mouse = FakeMouse()
    clicker = Clicker(mouse)
    run_for(clicker, ClickSettings(interval_ms=10), 0.05)
    run_for(clicker, ClickSettings(interval_ms=10), 0.05)
    assert clicker.count >= 1


@pytest.mark.parametrize("interval", [0, -5])
def test_rejects_bad_interval(interval):
    with pytest.raises(ValueError):
        ClickSettings(interval_ms=interval)


def test_rejects_unknown_button():
    with pytest.raises(ValueError):
        ClickSettings(button="side")
