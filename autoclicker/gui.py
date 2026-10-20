"""Окно автокликера на tkinter."""

import queue
import tkinter as tk
from tkinter import messagebox, ttk

from .clicker import ClickSettings, Clicker
from .hotkeys import HotkeyListener
from .picker import pick_region
from .vision import load_template, locate_on_screen, save_template, to_photo

BUTTON_LABELS = {"Левая": "left", "Правая": "right", "Средняя": "middle"}
CLICK_TYPES = {"Одинарный": False, "Двойной": True}
POLL_MS = 100
# Превью уменьшаем, чтобы поиск не нашёл кнопку в нашем же окне.
PREVIEW_SUBSAMPLE = 2


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoClicker")
        self.resizable(False, False)

        self.clicker = Clicker()
        # Хоткей приходит из потока pynput, поэтому передаём его в GUI через очередь.
        self._events = queue.Queue()
        self.hotkeys = HotkeyListener(lambda: self._events.put("toggle"))
        self.template = load_template()

        self._build()
        self._show_template()
        self.hotkeys.start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(POLL_MS, self._poll)

    def _build(self):
        root = ttk.Frame(self, padding=12)
        root.grid()

        interval = ttk.LabelFrame(root, text="Интервал между кликами", padding=8)
        interval.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.hours = tk.StringVar(value="0")
        self.minutes = tk.StringVar(value="0")
        self.seconds = tk.StringVar(value="0")
        self.millis = tk.StringVar(value="100")
        self._inputs = []
        for col, (var, label, limit) in enumerate(
            [
                (self.hours, "ч", 23),
                (self.minutes, "мин", 59),
                (self.seconds, "сек", 59),
                (self.millis, "мс", 999),
            ]
        ):
            spin = ttk.Spinbox(interval, from_=0, to=limit, textvariable=var, width=5)
            spin.grid(row=0, column=col * 2, padx=(0, 2))
            ttk.Label(interval, text=label).grid(row=0, column=col * 2 + 1, padx=(0, 8))
            self._inputs.append(spin)

        options = ttk.LabelFrame(root, text="Параметры клика", padding=8)
        options.grid(row=1, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(options, text="Кнопка мыши:").grid(row=0, column=0, sticky="w")
        self.button = ttk.Combobox(
            options, values=list(BUTTON_LABELS), state="readonly", width=12
        )
        self.button.current(0)
        self.button.grid(row=0, column=1, padx=8, pady=2)
        ttk.Label(options, text="Тип клика:").grid(row=1, column=0, sticky="w")
        self.click_type = ttk.Combobox(
            options, values=list(CLICK_TYPES), state="readonly", width=12
        )
        self.click_type.current(0)
        self.click_type.grid(row=1, column=1, padx=8, pady=2)
        self._inputs += [self.button, self.click_type]

        target = ttk.LabelFrame(root, text="Куда кликать", padding=8)
        target.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.by_image = tk.BooleanVar(value=False)
        for row, (text, value) in enumerate([("По курсору", False), ("По картинке", True)]):
            radio = ttk.Radiobutton(target, text=text, variable=self.by_image, value=value)
            radio.grid(row=row, column=0, columnspan=2, sticky="w")
            self._inputs.append(radio)
        pick_btn = ttk.Button(
            target, text="Выбрать кнопку на экране…", command=self.pick_template
        )
        pick_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 4))
        self.preview = ttk.Label(target, text="Кнопка не выбрана", anchor="center")
        self.preview.grid(row=3, column=0, columnspan=2, pady=(0, 6))
        ttk.Label(target, text="Стоп, если не видно, сек:").grid(row=4, column=0, sticky="w")
        self.missing_timeout = tk.StringVar(value="5")
        timeout_spin = ttk.Spinbox(
            target, from_=1, to=3600, textvariable=self.missing_timeout, width=5
        )
        timeout_spin.grid(row=4, column=1, sticky="e")
        self._inputs += [pick_btn, timeout_spin]

        self.start_btn = ttk.Button(root, text="Старт (F6)", command=self.start)
        self.start_btn.grid(row=3, column=0, sticky="ew", padx=(0, 4))
        self.stop_btn = ttk.Button(
            root, text="Стоп (F6)", command=self.stop, state="disabled"
        )
        self.stop_btn.grid(row=3, column=1, sticky="ew", padx=(4, 0))

        self.status = tk.StringVar(value="Остановлен")
        ttk.Label(root, textvariable=self.status).grid(
            row=4, column=0, columnspan=2, pady=(8, 0)
        )

    def pick_template(self):
        template = pick_region(self)
        if template is None:
            return
        self.template = template
        save_template(template)
        self.by_image.set(True)
        self._show_template()

    def _show_template(self):
        if self.template is None:
            return
        # Ссылку держим на виджете, иначе картинку соберёт сборщик мусора.
        self.preview.photo = to_photo(self.template, PREVIEW_SUBSAMPLE)
        self.preview.configure(image=self.preview.photo, text="")

    def _read_settings(self):
        try:
            h, m, s, ms = (
                int(v.get() or 0)
                for v in (self.hours, self.minutes, self.seconds, self.millis)
            )
        except ValueError:
            raise ValueError("Интервал должен состоять из целых чисел")
        if min(h, m, s, ms) < 0:
            raise ValueError("Интервал не может быть отрицательным")
        total_ms = ((h * 60 + m) * 60 + s) * 1000 + ms
        locate = None
        if self.by_image.get():
            if self.template is None:
                raise ValueError("Сначала выберите кнопку на экране")
            template = self.template
            locate = lambda: locate_on_screen(template)
        try:
            missing_timeout = float(self.missing_timeout.get())
        except ValueError:
            raise ValueError("Время ожидания кнопки должно быть числом")
        return ClickSettings(
            interval_ms=total_ms,
            button=BUTTON_LABELS[self.button.get()],
            double=CLICK_TYPES[self.click_type.get()],
            locate=locate,
            missing_timeout_s=missing_timeout,
        )

    def start(self):
        if self.clicker.running:
            return
        try:
            settings = self._read_settings()
        except ValueError as e:
            messagebox.showerror("AutoClicker", str(e))
            return
        self.clicker.start(settings)
        for widget in self._inputs:
            widget.state(["disabled"])
        self.start_btn.state(["disabled"])
        self.stop_btn.state(["!disabled"])

    def stop(self):
        self.clicker.stop()
        for widget in self._inputs:
            widget.state(["!disabled"])
        # Комбобоксы должны остаться только для выбора из списка.
        self.button.state(["readonly"])
        self.click_type.state(["readonly"])
        self.start_btn.state(["!disabled"])
        self.stop_btn.state(["disabled"])

    def toggle(self):
        if self.clicker.running:
            self.stop()
        else:
            self.start()

    def _poll(self):
        while True:
            try:
                self._events.get_nowait()
            except queue.Empty:
                break
            self.toggle()
        # Кликер может остановиться сам (кнопка пропала) — вернуть окно в исходное состояние.
        if not self.clicker.running and self.stop_btn.instate(["!disabled"]):
            self.stop()
        if self.clicker.running:
            self.status.set(f"Кликает… кликов: {self.clicker.count}")
        elif self.clicker.stop_reason == "missing":
            self.status.set(f"Кнопка пропала — остановлено. Кликов: {self.clicker.count}")
        else:
            self.status.set(f"Остановлен. Кликов: {self.clicker.count}")
        self.after(POLL_MS, self._poll)

    def _on_close(self):
        self.clicker.stop()
        self.hotkeys.stop()
        self.destroy()
