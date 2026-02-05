# Как использовать:

## 1 вариант

```bash
python fix_prison.py
```

## 2 вариант

Создание открытого .exe файла

## 3 вариант

Создание шифрованного .exe файла

# Ручное создание exe скрипта

## Установка PyInstaller

```bash
pip install pyinstaller
```

Если `pip` не найден — используйте полный путь к Python:

```cmd
C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python311\python.exe -m pip install pyinstaller
```

## Установка зависимостей (для шифрования)

```bash
pip install pycryptodome
```

## 1 вариант (без иконки)

```bash
pyinstaller --onefile --console --name "PrisonSaveEditor" fix_prison.py
```

## 2 вариант (с иконкой)

```bash
pyinstaller --onefile --console --icon=icon.ico --name "PrisonSaveEditor" fix_prison.py
```

## Пояснение флагов

- `--onefile` - создаёт один `.exe` файл (без кучи DLL в папке)
- `--console` - оставляет консольное окно (нужно для интерактивного ввода)
- `--name "PrisonSaveEditor"` - имя итогового файла (`PrisonSaveEditor.exe`)
- `-- icon=icon.ico` - выбор иконки для итогового файла

# Сборка exe с поддержкой плагинов

```bash
pyinstaller --onefile --console ^
  --add-data "plugins;plugins" ^
  --name "PrisonSaveEditor" ^
  main.py
```

Или в одну строку:

```bash
pyinstaller --onefile --console --add-data "plugins;plugins" --name "PrisonSaveEditor" main.py
```

> Важно: Папка plugins/ будет скопирована рядом с .exe. В неё можно класть файлы без перекомляции

# Создание шифрованного файла

## Ручное создание exe скрипта (с шифрованием с встроенными плагинами)

```bash
pyinstaller --onefile --console ^
  --add-data "plugins;plugins" ^
  --hidden-import Crypto.Cipher.AES ^
  --hidden-import Crypto.Random ^
  --name "PrisonSaveEditor" ^
  main.py
```

> Важно: При запуске .exe без pycryptodome плагины .enc будут пропущены, но .py (если есть) всё равно загрузятся. Для полной защиты нужно установить pycryptodome перед сборкой:

```bash
pip install pycryptodome
```

## Ручное создание exe скрипта (с шифрованием, без встроенных плагинов)

```bash
pyinstaller --onefile --console ^
  --hidden-import Crypto.Cipher.AES ^
  --hidden-import Crypto.Random ^
  --name "PrisonSaveEditor" ^
  main.py
```

## Пример шифрования дополнительных файлов (плагинов)

```bash
python encrypt_tool.py plugins/dead_zone.py plugins/dead_zone.enc
```
