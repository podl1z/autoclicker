"""Движок автокликера: кликает в фоновом потоке, пока его не остановят."""

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from pynput.mouse import Button, Controller

BUTTONS = {
    "left": Button.left,
    "right": Button.right,
    "middle": Button.middle,
}

MIN_INTERVAL_MS = 1
# Как часто искать цель заново, пока её не видно.
RETRY_S = 0.25


@dataclass(frozen=True)
class ClickSettings:
    interval_ms: int = 100
    button: str = "left"
    double: bool = False
    # Возвращает точку для клика или None, если цели сейчас нет. None — кликать по курсору.
    locate: Optional[Callable[[], Optional[tuple]]] = field(default=None, compare=False)
    # Сколько секунд цель может отсутствовать, прежде чем кликер остановится сам.
    missing_timeout_s: float = 5.0

    def __post_init__(self):
        if self.interval_ms < MIN_INTERVAL_MS:
            raise ValueError(f"Интервал должен быть не меньше {MIN_INTERVAL_MS} мс")
        if self.button not in BUTTONS:
            raise ValueError(f"Неизвестная кнопка мыши: {self.button!r}")
        if self.missing_timeout_s <= 0:
            raise ValueError("Время ожидания кнопки должно быть больше нуля")


class Clicker:
    """Кликает с заданным интервалом: по курсору или по найденной цели."""

    def __init__(self, mouse=None):
        self._mouse = mouse if mouse is not None else Controller()
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._count = 0
        self._stop_reason = None

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    @property
    def count(self):
        return self._count

    @property
    def stop_reason(self):
        """None или "missing", если кликер остановился сам, потеряв цель."""
        return self._stop_reason

    def start(self, settings: ClickSettings):
        with self._lock:
            if self.running:
                return
            self._stop.clear()
            self._count = 0
            self._stop_reason = None
            self._thread = threading.Thread(
                target=self._run, args=(settings,), name="clicker", daemon=True
            )
            self._thread.start()

    def stop(self):
        with self._lock:
            self._stop.set()
            thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2)

    def _run(self, settings: ClickSettings):
        button = BUTTONS[settings.button]
        clicks = 2 if settings.double else 1
        interval = settings.interval_ms / 1000
        missing_since = None
        while not self._stop.is_set():
            if settings.locate is not None:
                pos = settings.locate()
                if pos is None:
                    now = time.monotonic()
                    if missing_since is None:
                        missing_since = now
                    elif now - missing_since >= settings.missing_timeout_s:
                        self._stop_reason = "missing"
                        break
                    if self._stop.wait(min(interval, RETRY_S)):
                        break
                    continue
                missing_since = None
                self._mouse.position = pos
            self._mouse.click(button, clicks)
            self._count += 1
            if self._stop.wait(interval):
                break
