"""Движок автокликера: кликает в фоновом потоке, пока его не остановят."""

import threading
from dataclasses import dataclass

from pynput.mouse import Button, Controller

BUTTONS = {
    "left": Button.left,
    "right": Button.right,
    "middle": Button.middle,
}

MIN_INTERVAL_MS = 1


@dataclass(frozen=True)
class ClickSettings:
    interval_ms: int = 100
    button: str = "left"
    double: bool = False

    def __post_init__(self):
        if self.interval_ms < MIN_INTERVAL_MS:
            raise ValueError(f"Интервал должен быть не меньше {MIN_INTERVAL_MS} мс")
        if self.button not in BUTTONS:
            raise ValueError(f"Неизвестная кнопка мыши: {self.button!r}")


class Clicker:
    """Кликает в текущей позиции курсора с заданным интервалом."""

    def __init__(self, mouse=None):
        self._mouse = mouse if mouse is not None else Controller()
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._count = 0

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive()

    @property
    def count(self):
        return self._count

    def start(self, settings: ClickSettings):
        with self._lock:
            if self.running:
                return
            self._stop.clear()
            self._count = 0
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
        while not self._stop.is_set():
            self._mouse.click(button, clicks)
            self._count += 1
            if self._stop.wait(interval):
                break
