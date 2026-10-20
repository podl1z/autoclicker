import ctypes

from autoclicker.gui import App


def enable_dpi_awareness():
    # Без этого при масштабе экрана 125–150% координаты снимка экрана и мыши расходятся.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    enable_dpi_awareness()
    App().mainloop()
