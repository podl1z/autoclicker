"""Поиск образца кнопки на экране по шаблону."""

import base64
import os
import tkinter as tk
from pathlib import Path

import cv2
import mss
import numpy as np

THRESHOLD = 0.8
TEMPLATE_PATH = Path(os.environ.get("APPDATA", Path.home())) / "AutoClicker" / "template.png"


def grab_screen():
    """Снимок всего виртуального экрана: (картинка BGR, left, top)."""
    with mss.MSS() as sct:
        monitor = sct.monitors[0]
        shot = np.asarray(sct.grab(monitor))
    return cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR), monitor["left"], monitor["top"]


def find(template, screen, threshold=THRESHOLD):
    """Центр лучшего совпадения шаблона на screen или None, если похожего нет."""
    th, tw = template.shape[:2]
    sh, sw = screen.shape[:2]
    if th > sh or tw > sw:
        return None
    result = cv2.matchTemplate(
        cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY),
        cv2.cvtColor(template, cv2.COLOR_BGR2GRAY),
        cv2.TM_CCOEFF_NORMED,
    )
    _, score, _, (x, y) = cv2.minMaxLoc(result)
    if score < threshold:
        return None
    return x + tw // 2, y + th // 2


def locate_on_screen(template):
    """Координаты центра кнопки на экране (для клика) или None."""
    screen, left, top = grab_screen()
    pos = find(template, screen)
    if pos is None:
        return None
    return pos[0] + left, pos[1] + top


def load_template(path=TEMPLATE_PATH):
    if not path.exists():
        return None
    # cv2.imread не понимает кириллицу в пути, поэтому читаем байты сами.
    data = np.frombuffer(path.read_bytes(), np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def save_template(img, path=TEMPLATE_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_png(img))


def to_photo(img, subsample=1):
    """numpy-картинка → tk.PhotoImage (нужен уже созданный корень Tk)."""
    photo = tk.PhotoImage(data=base64.b64encode(_png(img)))
    return photo.subsample(subsample) if subsample > 1 else photo


def _png(img):
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise ValueError("Не удалось закодировать картинку")
    return buf.tobytes()
