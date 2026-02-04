import os
import sys
import shutil
import re
from pathlib import Path


def get_saves_path():
    """Автоматически определяет путь к папке сохранений в зависимости от ОС"""
    system = sys.platform

    if system == "win32":
        # Windows: C:\Users\<username>\Documents\Prison Architect\saves
        docs = Path.home() / "Documents" / "Prison Architect" / "saves"
        if docs.exists():
            return docs
        # Альтернативный путь (Steam)
        steam = Path.home() / "AppData" / "Local" / "Introversion" / \
            "Prison Architect" / "saves"
        if steam.exists():
            return steam

    elif system == "darwin":
        # macOS
        mac = Path.home() / "Library" / "Application Support" / \
            "Prison Architect" / "saves"
        if mac.exists():
            return mac

    elif system.startswith("linux"):
        # Linux
        linux1 = Path.home() / ".local" / "share" / "Prison Architect" / "saves"
        if linux1.exists():
            return linux1
        linux2 = Path.home() / ".Prison Architect" / "saves"
        if linux2.exists():
            return linux2

    return None


def create_backup(filepath):
    """Создаёт резервную копию файла с суффиксом 'copy' перед расширением"""
    backup_path = filepath.with_stem(f"{filepath.stem}copy")
    shutil.copy2(filepath, backup_path)
    print(f"Создана резервная копия: {backup_path.name}")
    return backup_path


def find_construction_block(content):
    """
    Находит блок BEGIN Construction ... END с учётом вложенности.
    Возвращает (start_pos, end_pos) или None если не найден.
    """
    start_match = re.search(
        r'\nBEGIN\s+Construction\s*\n', content, re.IGNORECASE)
    if not start_match:
        return None

    start_pos = start_match.end()
    depth = 1
    i = start_pos

    while i < len(content) and depth > 0:
        begin_match = re.search(
            r'\nBEGIN\s+[^\n]*\n', content[i:], re.IGNORECASE)
        end_match = re.search(r'\nEND\s*\n', content[i:], re.IGNORECASE)

        next_begin = i + begin_match.start() if begin_match else None
        next_end = i + end_match.start() if end_match else None

        if next_begin is not None and (next_end is None or next_begin < next_end):
            depth += 1
            i = next_begin + 1
        elif next_end is not None:
            depth -= 1
            i = next_end + 1
        else:
            break

    if depth == 0:
        end_pos = i
        return (start_match.start(), end_pos)

    return None


def fix_construction_block(filepath):
    """Исправляет блок Construction в файле"""
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read()

        try:
            content = raw_data.decode('utf-8')
            encoding = 'utf-8'
        except UnicodeDecodeError:
            content = raw_data.decode('cp1251')
            encoding = 'cp1251'

        block_pos = find_construction_block(content)
        if not block_pos:
            print("✗ Блок 'Construction' не найден в файле!")
            return False

        start_pos, end_pos = block_pos

        fixed_block = (
            "\nBEGIN Construction\n"
            "BEGIN Jobs Size 0 END\n"
            "BEGIN PlanningJobs Size 16000 END\n"
            "BEGIN BlockedAreas END\n"
            "END\n"
        )

        new_content = content[:start_pos] + fixed_block + content[end_pos:]

        create_backup(filepath)

        with open(filepath, 'wb') as f:
            f.write(new_content.encode(encoding))

        print(f"Файл успешно исправлен: {filepath.name}")
        return True

    except Exception as e:
        print(f"✗ Ошибка при обработке файла: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Использование: python fix_prison.py <имя_файла.prison>")
        print("\nПримеры:")
        print("  python fix_prison.py 5.prison")
        print("  python fix_prison.py мой_тюряга.prison")
        sys.exit(1)

    filename = sys.argv[1]
    saves_path = get_saves_path()

    if not saves_path:
        print("✗ Не удалось автоматически определить путь к сохранениям!")
        print("Пожалуйста, укажите полный путь к файлу:")
        print("  python fix_prison.py /полный/путь/к/файлу.prison")
        sys.exit(1)

    if os.path.isabs(filename):
        filepath = Path(filename)
    else:
        filepath = saves_path / filename

    if not filepath.exists():
        print(f"✗ Файл не найден: {filepath}")
        print(f"Проверьте путь: {saves_path}")
        sys.exit(1)

    print(f"Обработка файла: {filepath}")
    print(f"Путь к сохранениям: {saves_path}")

    if fix_construction_block(filepath):
        print("\nИсправление завершено успешно!")
        print("Теперь можно загрузить сохранение в игре — зависшие строители должны исчезнуть.")
    else:
        print("\nНе удалось исправить файл. Проверьте его структуру.")


if __name__ == "__main__":
    main()
