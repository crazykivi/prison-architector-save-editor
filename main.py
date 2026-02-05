# -*- coding: utf-8 -*-
"""
Prison Architect Toolkit — главное приложение
"""
from ui import Color
from core import PrisonSaveFixer
from pathlib import Path
import sys
import os
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pkg_resources')
warnings.filterwarnings('ignore', message='pkg_resources is deprecated')


def auto_scan_mode(fixer: PrisonSaveFixer):
    """Режим автоматического сканирования папки сохранений"""
    print(f"\n{Color.BLUE}Поиск сейвов в: {fixer.saves_path}{Color.END}\n")

    saves = fixer.find_save_files()
    if not saves:
        print(f"{Color.RED}В папке не найдено ни одного файла .prison{Color.END}\n")
        return

    print(f"{Color.GREEN}Найдено {len(saves)} сейвов:{Color.END}\n")
    for idx, save in enumerate(saves, 1):
        mtime = save.stat().st_mtime
        from datetime import datetime
        dt = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        size_mb = save.stat().st_size / 1024 / 1024
        print(f"  {idx:2d}. {save.name:<30} [{dt}] ({size_mb:.1f} МБ)")

    print(f"\n{Color.YELLOW}Введите номер сейва для исправления (или 0 для возврата в меню):{Color.END}")
    try:
        choice = int(input(f"{Color.CYAN}> {Color.END}").strip())
        if choice == 0:
            return
        elif 1 <= choice <= len(saves):
            selected_file = saves[choice - 1]
            print(f"\n{Color.BLUE}Выбран сейв:{Color.END} {selected_file.name}")
            if fixer.fix_construction_block(selected_file):
                print(f"\n{Color.GREEN}Исправление завершено успешно!{Color.END}")
                print(
                    "Теперь можно загрузить сохранение в игре — зависшие строители должны исчезнуть.\n")
            else:
                print(
                    f"\n{Color.RED}Не удалось исправить файл. Проверьте его структуру.{Color.END}\n")
        else:
            print(f"{Color.RED}Неверный номер сейва.{Color.END}\n")
    except ValueError:
        print(f"{Color.RED}Пожалуйста, введите число.{Color.END}\n")
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
        return

    input(f"\n{Color.YELLOW}Нажмите Enter для возврата в меню...{Color.END}")


def manual_mode(fixer: PrisonSaveFixer):
    """Режим ручного ввода пути к файлу"""
    print(f"\n{Color.BLUE}Ручной режим ввода{Color.END}")
    print("Введите имя файла (без или с .prison) или полный путь к файлу:")
    print("Примеры:")
    print("  • 1                    → ищет 1.prison в папке сохранений")
    print("  • myprison             → ищет myprison.prison в папке сохранений")
    print("  • C:\\Saves\\1.prison      → использует указанный полный путь")
    print(f"\n{Color.YELLOW}Введите путь (или 0 для возврата в меню):{Color.END}")

    try:
        user_input = input(f"{Color.CYAN}> {Color.END}").strip()
        if user_input == '0':
            return

        filepath = fixer.resolve_filepath(user_input)
        if not filepath:
            print(
                f"{Color.RED}✗ Файл не найден по указанному пути:{Color.END} {user_input}")
            if fixer.saves_path:
                print(f"Проверьте папку: {fixer.saves_path}")
            input(
                f"\n{Color.YELLOW}Нажмите Enter для повторной попытки...{Color.END}")
            manual_mode(fixer)
            return

        print(f"\n{Color.BLUE}Найден файл:{Color.END} {filepath}")
        print(f"Размер: {filepath.stat().st_size / 1024:.1f} КБ")

        confirm = input(
            f"{Color.YELLOW}Исправить этот файл? (да/нет): {Color.END}").strip().lower()
        if confirm in ('да', 'д', 'yes', 'y'):
            if fixer.fix_construction_block(filepath):
                print(f"\n{Color.GREEN}Исправление завершено успешно!{Color.END}")
                print(
                    "Теперь можно загрузить сохранение в игре — зависшие строители должны исчезнуть.\n")
            else:
                print(
                    f"\n{Color.RED}Не удалось исправить файл. Проверьте его структуру.{Color.END}\n")
        else:
            print(f"{Color.YELLOW}Операция отменена.{Color.END}\n")

    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
        return

    input(f"\n{Color.YELLOW}Нажмите Enter для возврата в меню...{Color.END}")


def transfer_mode(fixer: PrisonSaveFixer):
    """Режим переноса сейва из произвольной папки или файла"""
    print(f"\n{Color.BOLD}{Color.CYAN}╔════════════════════════════════════╗")
    print(f"║        Перенос сейва в игру        ║")
    print(f"╚════════════════════════════════════╝{Color.END}")
    print(f"\n{Color.BLUE}Папка сохранений игры:{Color.END} {fixer.saves_path}")
    print(f"\n{Color.YELLOW}Введите путь к файлу .prison или папке:{Color.END}")
    print("  • Полный путь к файлу: C:\\Users\\Имя\\Downloads\\101.prison")
    print("  • Путь к папке:        C:\\Users\\Имя\\Downloads")
    print("  • Ключевые слова:      Загрузки, Документы")
    print(f"\n{Color.YELLOW}Путь (или 0 для отмены):{Color.END}")

    try:
        user_input = input(f"{Color.CYAN}> {Color.END}").strip()
        if user_input == '0':
            return

        path = fixer.resolve_transfer_path(user_input)
        if not path:
            print(f"{Color.RED}Путь не найден: {user_input}{Color.END}")
            input(
                f"\n{Color.YELLOW}Нажмите Enter для возврата в меню...{Color.END}")
            return

        if path.is_file() and path.suffix.lower() == '.prison':
            source_file = path
        elif path.is_dir():
            saves = fixer.find_prison_files_in_folder(path)
            if not saves:
                print(f"{Color.RED}✗ В папке не найдено файлов .prison{Color.END}")
                input(
                    f"\n{Color.YELLOW}Нажмите Enter для повторной попытки...{Color.END}")
                return

            print(
                f"\n{Color.GREEN}Найдено {len(saves)} сейвов в папке {path}:{Color.END}\n")
            for idx, save in enumerate(saves, 1):
                mtime = save.stat().st_mtime
                from datetime import datetime
                dt = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                size_mb = save.stat().st_size / 1024 / 1024
                print(f"  {idx:2d}. {save.name:<30} [{dt}] ({size_mb:.1f} МБ)")

            print(
                f"\n{Color.YELLOW}Выберите номер сейва (или 0 для отмены):{Color.END}")
            try:
                choice = int(input(f"{Color.CYAN}> {Color.END}").strip())
                if choice == 0:
                    return
                if 1 <= choice <= len(saves):
                    source_file = saves[choice - 1]
                else:
                    print(f"{Color.RED}Неверный номер{Color.END}")
                    input(
                        f"\n{Color.YELLOW}Нажмите Enter для повторной попытки...{Color.END}")
                    return
            except ValueError:
                print(f"{Color.RED}Введите число{Color.END}")
                input(
                    f"\n{Color.YELLOW}Нажмите Enter для повторной попытки...{Color.END}")
                return
        else:
            print(
                f"{Color.RED}Указанный путь не является файлом .prison или папкой{Color.END}")
            input(
                f"\n{Color.YELLOW}Нажмите Enter для повторной попытки...{Color.END}")
            return

        print(f"\n{Color.BLUE}Выбран файл:{Color.END} {source_file}")
        confirm = input(
            f"{Color.YELLOW}Перенести этот сейв в игру? (да/нет): {Color.END}").strip().lower()
        if confirm in ('да', 'д', 'yes', 'y'):
            if fixer.transfer_save(source_file):
                print(f"\n{Color.GREEN}Перенос завершён успешно!{Color.END}")
                dest_file = fixer.saves_path / source_file.name
                fix_choice = input(
                    f"{Color.YELLOW}Исправить зависшие задачи в этом сейве? (да/нет): {Color.END}").strip().lower()
                if fix_choice in ('да', 'д', 'yes', 'y'):
                    fixer.fix_construction_block(dest_file)
            else:
                print(f"\n{Color.RED}Не удалось перенести сейв{Color.END}")
        else:
            print(f"{Color.YELLOW}Операция отменена{Color.END}")

    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
        return

    input(f"\n{Color.YELLOW}Нажмите Enter для возврата в меню...{Color.END}")


def show_menu(fixer: PrisonSaveFixer):
    """Главное меню с поддержкой плагинов"""
    print(
        f"\n{Color.BOLD}{Color.CYAN}╔══════════════════════════════════════════════╗")
    print(f"║   Prison Architect Save Editor v1.1   ║")
    print(f"╚══════════════════════════════════════════════╝{Color.END}\n")

    if not fixer.saves_path or not fixer.saves_path.exists():
        print(f"{Color.RED}✗ Не удалось найти папку сохранений игры!{Color.END}")
        print(f"Попробуйте указать полный путь к файлу вручную.\n")
        manual_mode(fixer)
        return

    print(f"{Color.BLUE}Путь к сохранениям:{Color.END} {fixer.saves_path}\n")

    # Базовые пункты меню
    options = [
        ("1", "Исправление: Автоматическое сканирование (показать список сейвов)", auto_scan_mode),
        ("2", "Исправление: Ручной ввод (имя файла или полный путь)", manual_mode),
        ("3", "Перенос сейва из другой папки", transfer_mode),
    ]

    # Добавление плагинов
    for idx, plugin in enumerate(fixer.plugins, start=len(options) + 1):
        options.append((str(idx), plugin.menu_text, lambda f=fixer,
                       p=plugin: p.execute(f.saves_path)))

    options.append(("0", "Выход", None))

    # Вывод меню
    for key, text, _ in options:
        print(f"  {key}. {text}")

    print()
    choice = input(
        f"{Color.CYAN}Ваш выбор (0-{len(options)-1}): {Color.END}").strip()

    for key, _, action in options:
        if choice == key:
            if action:
                action(fixer)
            return choice == "0"

    print(f"{Color.RED}Неверный выбор. Пожалуйста, введите число от 0 до {len(options)-1}.{Color.END}\n")
    return False


def main():
    """Точка входа в программу"""
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass

    fixer = PrisonSaveFixer()
    fixer.load_plugins()

    while True:
        if show_menu(fixer):
            break

    print("\nДо свидания!")


if __name__ == "__main__":
    main()
