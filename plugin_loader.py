import sys
from pathlib import Path
from plugin_interface import Plugin
from ui import Color


def get_plugins_dir() -> Path:
    """Возвращает путь к папке plugins рядом с точкой запуска (.exe или main.py)"""
    if getattr(sys, 'frozen', False):
        # Запуск .exe - папка рядом с .exe
        base_dir = Path(sys.executable).parent
    else:
        # Запуск скрипта - папка рядом с main.py
        base_dir = Path(sys.argv[0]).parent.resolve()

    return base_dir / "plugins"


def load_plugins():
    """Загружает плагины в зависимости от режима запуска:
       - .exe → только .enc файлы (без .py!)
       - python main.py → только .py файлы (для разработки)
    """
    plugin_dir = get_plugins_dir()
    is_frozen = getattr(sys, 'frozen', False)

    # Для .exe папка создаётся автоматом, для разработки - нет
    if is_frozen and not plugin_dir.exists():
        plugin_dir.mkdir(exist_ok=True)
        print(f"{Color.YELLOW}Создана папка для плагинов:{Color.END} {plugin_dir}")
        return []

    # Пропуск создания папки, если в режиме разработки
    if not plugin_dir.exists():
        return []

    plugins = []

    if is_frozen:
        # Режим .exe - только .enc
        enc_files = list(plugin_dir.glob("*.enc"))
        if enc_files:
            plugins.extend(_load_encrypted_plugins(enc_files))
        # Без предупреждения - просто пропуск
    else:
        # Режим разработки - только .py файлы
        py_files = [f for f in plugin_dir.glob(
            "*.py") if not f.name.startswith("__")]
        if py_files:
            plugins.extend(_load_plain_plugins(py_files))
        # Без предупреждения также

    return plugins


def _load_encrypted_plugins(enc_files):
    """Загружает зашифрованные плагины через AES (только для .exe)"""
    plugins = []
    # 32 байта = AES-256 (ДЛЯ ПРИМЕРА)
    DECRYPTION_KEY = b'PrisonToolkitKey1234567890ABCDEF'

    try:
        from Crypto.Cipher import AES

        for enc_file in enc_files:
            try:
                with open(enc_file, 'rb') as f:
                    nonce = f.read(16)
                    tag = f.read(16)
                    ciphertext = f.read()

                cipher = AES.new(DECRYPTION_KEY, AES.MODE_GCM, nonce=nonce)
                source_code = cipher.decrypt_and_verify(ciphertext, tag)

                plugin_namespace = {}
                exec(source_code, plugin_namespace)

                for obj in plugin_namespace.values():
                    if isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin:
                        plugins.append(obj())
                        print(
                            f"{Color.GREEN}✓ Загружен плагин:{Color.END} {obj().menu_text}")
                        break
            except Exception as e:
                print(
                    f"{Color.RED}✗ Ошибка загрузки {enc_file.name}: {type(e).__name__}{Color.END}")
                continue
    except ImportError:
        print(
            f"{Color.RED}✗ Критическая ошибка: pycryptodome не найден в .exe{Color.END}")
        print(
            f"{Color.YELLOW}Пересоберите .exe с 'pip install pycryptodome' перед сборкой{Color.END}")

    return plugins


def _load_plain_plugins(py_files):
    """Загружает обычные .py плагины (только для разработки)"""
    plugins = []
    import importlib.util

    for plugin_file in py_files:
        try:
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(
                module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr is not Plugin:
                    plugin_instance = attr()
                    plugins.append(plugin_instance)
                    print(
                        f"{Color.GREEN}✓ Загружен плагин:{Color.END} {plugin_instance.menu_text}")
                    break
        except Exception as e:
            print(f"{Color.RED}✗ Ошибка загрузки {plugin_file.name}: {e}{Color.END}")

    return plugins
