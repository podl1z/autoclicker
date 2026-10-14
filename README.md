# AutoClicker

Простой автокликер для Windows с окном и глобальной горячей клавишей.

## Возможности

- Интервал между кликами: часы / минуты / секунды / миллисекунды (минимум 1 мс)
- Кнопка мыши: левая, правая, средняя
- Одинарный или двойной клик
- Клик в текущей позиции курсора
- Старт/стоп кнопками в окне или клавишей **F6** — работает, даже когда окно свёрнуто или не в фокусе
- Счётчик кликов

## Запуск готового exe

Скачайте `AutoClicker.exe` из [Releases](https://github.com/podl1z/autoclicker/releases) и запустите.
Python ставить не нужно.

## Запуск из исходников

Нужен Python 3.10+.

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python main.py
```

## Сборка exe

```powershell
.\build.ps1
```

Результат — `dist\AutoClicker.exe`.

## Тесты

```powershell
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest
```

## Известные ограничения

- Клики не доходят до окон, запущенных от имени администратора, если сам кликер запущен без прав администратора (так устроена защита Windows). В этом случае запустите AutoClicker тоже от администратора.
- Windows SmartScreen / Defender может предупреждать о неподписанном exe, собранном PyInstaller. Это ложное срабатывание; при сомнениях соберите exe сами из исходников.
