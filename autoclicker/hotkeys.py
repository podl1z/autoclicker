"""Глобальная горячая клавиша, работающая даже когда окно не в фокусе."""

from pynput import keyboard

DEFAULT_HOTKEY = keyboard.Key.f6


class HotkeyListener:
    """Вызывает callback при нажатии клавиши. Callback выполняется в потоке pynput."""

    def __init__(self, callback, key=DEFAULT_HOTKEY):
        self._callback = callback
        self._key = key
        self._listener = None

    def start(self):
        if self._listener is None:
            self._listener = keyboard.Listener(on_press=self._on_press, daemon=True)
            self._listener.start()

    def stop(self):
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key):
        if key == self._key:
            self._callback()
