"""Выделение образца кнопки мышкой прямо на экране."""

import time
import tkinter as tk

from .vision import grab_screen, to_photo

MIN_SIZE = 5
HINT = "Обведите кнопку мышкой. Esc — отмена"


def pick_region(root):
    """Прячет окно, даёт обвести область на снимке экрана и возвращает её (или None)."""
    root.withdraw()
    root.update()
    time.sleep(0.25)  # дать окну исчезнуть до снимка
    try:
        screen, left, top = grab_screen()
        return _Selector(root, screen, left, top).run()
    finally:
        root.deiconify()


class _Selector:
    def __init__(self, root, screen, left, top):
        self._screen = screen
        self._start = None
        self._rect = None
        self._result = None

        h, w = screen.shape[:2]
        self._win = tk.Toplevel(root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.geometry(f"{w}x{h}+{left}+{top}")

        self._canvas = tk.Canvas(
            self._win, width=w, height=h, highlightthickness=0, cursor="crosshair"
        )
        self._canvas.pack()
        # Держим ссылку, иначе картинку соберёт сборщик мусора.
        self._photo = to_photo(screen)
        self._canvas.create_image(0, 0, image=self._photo, anchor="nw")
        hint = self._canvas.create_text(
            w // 2, 40, text=HINT, fill="white", font=("Segoe UI", 16, "bold")
        )
        bg = self._canvas.create_rectangle(
            self._canvas.bbox(hint), fill="black", outline=""
        )
        self._canvas.tag_lower(bg, hint)

        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._win.bind("<Escape>", lambda e: self._win.destroy())

    def run(self):
        self._win.focus_force()
        self._win.grab_set()
        self._win.wait_window()
        return self._result

    def _on_press(self, event):
        self._start = (event.x, event.y)
        if self._rect is not None:
            self._canvas.delete(self._rect)
        self._rect = self._canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red", width=2
        )

    def _on_drag(self, event):
        if self._start is not None:
            self._canvas.coords(self._rect, *self._start, event.x, event.y)

    def _on_release(self, event):
        if self._start is None:
            return
        h, w = self._screen.shape[:2]
        x1, x2 = sorted((self._start[0], event.x))
        y1, y2 = sorted((self._start[1], event.y))
        x1, y1 = max(x1, 0), max(y1, 0)
        x2, y2 = min(x2, w), min(y2, h)
        if x2 - x1 >= MIN_SIZE and y2 - y1 >= MIN_SIZE:
            self._result = self._screen[y1:y2, x1:x2].copy()
        self._win.destroy()
