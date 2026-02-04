# Как использовать:

## 1 вариант

```bash
python fix_prison.py
```

## 2 вариант

Просто запустите .exe файл из папки dist

# Создание exe скрипта

## Установка PyInstaller

```bash
pip install pyinstaller
```

Если `pip` не найден — используйте полный путь к Python:

```cmd
C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python311\python.exe -m pip install pyinstaller
```

## 1 вариант (без иконки)

```bash
pyinstaller --onefile --console --name "PrisonSaveEditor" fix_prison.py
```

## 2 вариант (с иконкой)

```bash
pyinstaller --onefile --console --icon=icon.ico --name "PrisonFixer" fix_prison.py
```

## Пояснение флагов

- `--onefile` - создаёт один `.exe` файл (без кучи DLL в папке)
- `--console` - оставляет консольное окно (нужно для интерактивного ввода)
- `--name "PrisonSaveEditor"` - имя итогового файла (`PrisonSaveEditor.exe`)
- `-- icon=icon.ico` - выбор иконки для итогового файла
