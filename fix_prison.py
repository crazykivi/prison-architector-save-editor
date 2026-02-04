# -*- coding: utf-8 -*-
"""
Prison Architect Save Editor
Исправляет зависшие задачи строительства в сейвах игры, также помогает с переносом сейвов нужную папку
"""
import os
import sys
import shutil
import re
from pathlib import Path
from typing import Optional, List, Tuple


class Color:
    """Цвета для терминала (работает в большинстве современных терминалов)"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class PrisonSaveFixer:
    """Основной класс для исправления сейвов Prison Architect"""

    def __init__(self):
        self.saves_path = self.get_saves_path()
        self.encoding = 'cp1251'

    def get_saves_path(self) -> Optional[Path]:
        """Автоматически определяет путь к папке сохранений в зависимости от ОС"""
        system = sys.platform

        if system == "win32":
            # Windows: Documents/Prison Architect/saves
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

    def find_save_files(self) -> List[Path]:
        """Находит все файлы .prison в папке сохранений"""
        if not self.saves_path or not self.saves_path.exists():
            return []

        return sorted(
            [f for f in self.saves_path.glob("*.prison") if f.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

    def normalize_filename(self, filename: str) -> str:
        """Добавляет расширение .prison если его нет"""
        if not filename.lower().endswith('.prison'):
            return filename + '.prison'
        return filename

    def resolve_filepath(self, input_path: str) -> Optional[Path]:
        """Определяет полный путь к файлу: абсолютный путь или относительный в папке сохранений"""
        if os.path.isabs(input_path) or (':' in input_path[:2] and sys.platform == 'win32'):
            filepath = Path(input_path)
        else:
            if not self.saves_path:
                return None

            filepath = self.saves_path / input_path

            if not filepath.exists():
                normalized = self.normalize_filename(input_path)
                filepath = self.saves_path / normalized

        return filepath if filepath.exists() else None

    def resolve_transfer_path(self, user_input: str) -> Optional[Path]:
        """Обрабатывает ввод для переноса: полный путь к файлу, папке или ключевые слова (Загрузки/Документы)"""
        # Обработка ключевых слов (пока только загрузка и документы)
        if user_input.lower() in ('загрузки', 'загрузка', 'downloads'):
            if sys.platform == 'win32':
                path = Path.home() / "Downloads"
            elif sys.platform == 'darwin':
                path = Path.home() / "Downloads"
            else:
                path = Path.home() / "Downloads"
            return path if path.exists() else None

        if user_input.lower() in ('документы', 'документ', 'documents'):
            if sys.platform == 'win32':
                path = Path.home() / "Documents"
            elif sys.platform == 'darwin':
                path = Path.home() / "Documents"
            else:
                path = Path.home() / "Documents"
            return path if path.exists() else None

        # обработка как абсолютного пути
        path = Path(user_input)
        if path.exists():
            return path
        return None

    def find_prison_files_in_folder(self, folder: Path) -> List[Path]:
        """Находит все .prison файлы в указанной папке"""
        if not folder or not folder.exists() or not folder.is_dir():
            return []
        return sorted(
            [f for f in folder.glob("*.prison") if f.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

    def create_backup(self, filepath: Path) -> Optional[Path]:
        """Создаёт резервную копию файла с суффиксом 'copy' перед расширением"""
        try:
            backup_path = filepath.with_stem(f"{filepath.stem}copy")
            shutil.copy2(filepath, backup_path)
            print(
                f"{Color.GREEN}✓ Создана резервная копия:{Color.END} {backup_path.name}")
            return backup_path
        except Exception as e:
            print(f"{Color.RED}✗ Ошибка создания резервной копии: {e}{Color.END}")
            return None

    def find_construction_block(self, content: str) -> Optional[Tuple[int, int]]:
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
        content_len = len(content)

        while i < content_len and depth > 0:
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

    def fix_construction_block(self, filepath: Path) -> bool:
        """Исправляет блок Construction в файле"""
        try:
            with open(filepath, 'rb') as f:
                raw_data = f.read()

            try:
                content = raw_data.decode('utf-8')
                self.encoding = 'utf-8'
            except UnicodeDecodeError:
                try:
                    content = raw_data.decode('cp1251')
                    self.encoding = 'cp1251'
                except UnicodeDecodeError:
                    print(
                        f"{Color.RED}✗ Не удалось определить кодировку файла{Color.END}")
                    return False

            block_pos = self.find_construction_block(content)
            if not block_pos:
                print(
                    f"{Color.RED}✗ Блок 'Construction' не найден в файле!{Color.END}")
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

            if not self.create_backup(filepath):
                return False

            with open(filepath, 'wb') as f:
                f.write(new_content.encode(self.encoding))

            print(
                f"{Color.GREEN}Файл успешно исправлен:{Color.END} {filepath.name}")
            return True

        except Exception as e:
            print(f"{Color.RED}Ошибка при обработке файла: {e}{Color.END}")
            import traceback
            traceback.print_exc()
            return False

    def transfer_save(self, source_file: Path) -> bool:
        """Переносит сейв и скриншот в папку сохранений игры"""
        if not self.saves_path:
            print(f"{Color.RED}✗ Не найдена папка сохранений игры{Color.END}")
            return False

        try:
            dest_file = self.saves_path / source_file.name
            screenshot_src = source_file.with_suffix('.png')
            screenshot_dest = self.saves_path / screenshot_src.name

            print(f"\n{Color.BLUE}Копирование файла:{Color.END} {source_file.name}")
            shutil.copy2(source_file, dest_file)
            print(f"{Color.GREEN}Сейв скопирован:{Color.END} {dest_file}")

            if screenshot_src.exists():
                print(
                    f"{Color.BLUE}Копирование скриншота:{Color.END} {screenshot_src.name}")
                shutil.copy2(screenshot_src, screenshot_dest)
                print(
                    f"{Color.GREEN}Скриншот скопирован:{Color.END} {screenshot_dest}")
            else:
                print(
                    f"{Color.YELLOW}Скриншот не найден:{Color.END} {screenshot_src.name}")

            return True
        except Exception as e:
            print(f"{Color.RED}Ошибка копирования: {e}{Color.END}")
            return False

    def transfer_mode(self):
        """Режим переноса сейва из произвольной папки или файла"""
        print(
            f"\n{Color.BOLD}{Color.CYAN}╔════════════════════════════════════╗")
        print(f"║        Перенос сейва в игру        ║")
        print(f"╚════════════════════════════════════╝{Color.END}")
        print(f"\n{Color.BLUE}Папка сохранений игры:{Color.END} {self.saves_path}")
        print(f"\n{Color.YELLOW}Введите путь к файлу .prison или папке:{Color.END}")
        print("  • Полный путь к файлу: C:\\Users\\Имя\\Downloads\\101.prison")
        print("  • Путь к папке:        C:\\Users\\Имя\\Downloads")
        print("  • Ключевые слова:      Загрузки, Документы")
        print(f"\n{Color.YELLOW}Путь (или 0 для отмены):{Color.END}")

        try:
            user_input = input(f"{Color.CYAN}> {Color.END}").strip()
            if user_input == '0':
                self.show_menu()
                return

            path = self.resolve_transfer_path(user_input)
            if not path:
                print(f"{Color.RED}Путь не найден: {user_input}{Color.END}")
                input(
                    f"\n{Color.YELLOW}Нажмите Enter для возврата в меню...{Color.END}")
                self.transfer_mode()
                return

            # Если это файл .prison — используем его напрямую
            if path.is_file() and path.suffix.lower() == '.prison':
                source_file = path
            # Если это папка — показываем список файлов для выбора
            elif path.is_dir():
                saves = self.find_prison_files_in_folder(path)
                if not saves:
                    print(
                        f"{Color.RED}✗ В папке не найдено файлов .prison{Color.END}")
                    input(
                        f"\n{Color.YELLOW}Нажмите Enter для повторной попытки...{Color.END}")
                    self.transfer_mode()
                    return

                print(
                    f"\n{Color.GREEN}Найдено {len(saves)} сейвов в папке {path}:{Color.END}\n")
                for idx, save in enumerate(saves, 1):
                    mtime = save.stat().st_mtime
                    from datetime import datetime
                    dt = datetime.fromtimestamp(
                        mtime).strftime('%Y-%m-%d %H:%M')
                    size_mb = save.stat().st_size / 1024 / 1024
                    print(
                        f"  {idx:2d}. {save.name:<30} [{dt}] ({size_mb:.1f} МБ)")

                print(
                    f"\n{Color.YELLOW}Выберите номер сейва (или 0 для отмены):{Color.END}")
                try:
                    choice = int(input(f"{Color.CYAN}> {Color.END}").strip())
                    if choice == 0:
                        self.transfer_mode()
                        return
                    if 1 <= choice <= len(saves):
                        source_file = saves[choice - 1]
                    else:
                        print(f"{Color.RED}Неверный номер{Color.END}")
                        input(
                            f"\n{Color.YELLOW}Нажмите Enter для повторной попытки...{Color.END}")
                        self.transfer_mode()
                        return
                except ValueError:
                    print(f"{Color.RED}Введите число{Color.END}")
                    input(
                        f"\n{Color.YELLOW}Нажмите Enter для повторной попытки...{Color.END}")
                    self.transfer_mode()
                    return
            else:
                print(
                    f"{Color.RED}Указанный путь не является файлом .prison или папкой{Color.END}")
                input(
                    f"\n{Color.YELLOW}Нажмите Enter для повторной попытки...{Color.END}")
                self.transfer_mode()
                return

            print(f"\n{Color.BLUE}Выбран файл:{Color.END} {source_file}")
            confirm = input(
                f"{Color.YELLOW}Перенести этот сейв в игру? (да/нет): {Color.END}").strip().lower()
            if confirm in ('да', 'д', 'yes', 'y'):
                if self.transfer_save(source_file):
                    print(
                        f"\n{Color.GREEN}Перенос завершён успешно!{Color.END}")
                    dest_file = self.saves_path / source_file.name
                    fix_choice = input(
                        f"{Color.YELLOW}Исправить зависшие задачи в этом сейве? (да/нет): {Color.END}").strip().lower()
                    if fix_choice in ('да', 'д', 'yes', 'y'):
                        self.fix_construction_block(dest_file)
                else:
                    print(f"\n{Color.RED}Не удалось перенести сейв{Color.END}")
            else:
                print(f"{Color.YELLOW}Операция отменена{Color.END}")

        except KeyboardInterrupt:
            print("\n\nПрервано пользователем.")
            return

        input(f"\n{Color.YELLOW}Нажмите Enter для возврата в меню...{Color.END}")
        self.show_menu()

    def show_menu(self):
        """Отображает главное меню и обрабатывает выбор пользователя"""
        print(
            f"\n{Color.BOLD}{Color.CYAN}╔══════════════════════════════════════════════╗")
        print(f"║   Prison Architect Construction Fixer v1.0   ║")
        print(f"╚══════════════════════════════════════════════╝{Color.END}\n")

        if not self.saves_path or not self.saves_path.exists():
            print(f"{Color.RED}✗ Не удалось найти папку сохранений игры!{Color.END}")
            print(f"Попробуйте указать полный путь к файлу вручную.\n")
            self.manual_mode()
            return

        print(f"{Color.BLUE}Путь к сохранениям:{Color.END} {self.saves_path}\n")

        while True:
            print(f"{Color.YELLOW}Выберите режим работы:{Color.END}")
            print(
                "  1. Исправление: Автоматическое сканирование (показать список сейвов)")
            print("  2. Исправление: Ручной ввод (имя файла или полный путь)")
            print("  3. Перенос сейва из другой папки")
            print("  0. Выход\n")

            choice = input(f"{Color.CYAN}Ваш выбор (0-3): {Color.END}").strip()

            if choice == '1':
                self.auto_scan_mode()
                break
            elif choice == '2':
                self.manual_mode()
                break
            elif choice == '3':
                self.transfer_mode()
                break
            elif choice == '0':
                print("\nДо свидания!")
                break
            else:
                print(
                    f"{Color.RED}Неверный выбор. Пожалуйста, введите 0, 1, 2 или 3.{Color.END}\n")

    def auto_scan_mode(self):
        """Режим автоматического сканирования папки сохранений"""
        print(f"\n{Color.BLUE}Поиск сейвов в: {self.saves_path}{Color.END}\n")

        saves = self.find_save_files()
        if not saves:
            print(
                f"{Color.RED}В папке не найдено ни одного файла .prison{Color.END}\n")
            self.show_menu()
            return

        print(f"{Color.GREEN}Найдено {len(saves)} сейвов:{Color.END}\n")
        for idx, save in enumerate(saves, 1):
            mtime = save.stat().st_mtime
            from datetime import datetime
            dt = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            size_mb = save.stat().st_size / 1024 / 1024
            print(f"  {idx:2d}. {save.name:<30} [{dt}] ({size_mb:.1f} МБ)")

        print(
            f"\n{Color.YELLOW}Введите номер сейва для исправления (или 0 для возврата в меню):{Color.END}")
        try:
            choice = int(input(f"{Color.CYAN}> {Color.END}").strip())
            if choice == 0:
                self.show_menu()
                return
            elif 1 <= choice <= len(saves):
                selected_file = saves[choice - 1]
                print(
                    f"\n{Color.BLUE}Выбран сейв:{Color.END} {selected_file.name}")
                if self.fix_construction_block(selected_file):
                    print(
                        f"\n{Color.GREEN}✅ Исправление завершено успешно!{Color.END}")
                    print(
                        "Теперь можно загрузить сохранение в игре — зависшие строители должны исчезнуть.\n")
                else:
                    print(
                        f"\n{Color.RED}❌ Не удалось исправить файл. Проверьте его структуру.{Color.END}\n")
            else:
                print(f"{Color.RED}Неверный номер сейва.{Color.END}\n")
        except ValueError:
            print(f"{Color.RED}Пожалуйста, введите число.{Color.END}\n")
        except KeyboardInterrupt:
            print("\n\nПрервано пользователем.")
            return

        input(f"\n{Color.YELLOW}Нажмите Enter для возврата в меню...{Color.END}")
        self.show_menu()

    def manual_mode(self):
        """Режим ручного ввода пути к файлу"""
        print(f"\n{Color.BLUE}Ручной режим ввода{Color.END}")
        print("Введите имя файла (без или с .prison) или полный путь к файлу:")
        print("Примеры:")
        print("  • 1                    → ищет 1.prison в папке сохранений")
        print("  • myprison             → ищет myprison.prison в папке сохранений")
        print("  • C:\\Saves\\1.prison      → использует указанный полный путь")
        print(
            f"\n{Color.YELLOW}Введите путь (или 0 для возврата в меню):{Color.END}")

        try:
            user_input = input(f"{Color.CYAN}> {Color.END}").strip()
            if user_input == '0':
                self.show_menu()
                return

            filepath = self.resolve_filepath(user_input)
            if not filepath:
                print(
                    f"{Color.RED}✗ Файл не найден по указанному пути:{Color.END} {user_input}")
                if self.saves_path:
                    print(f"Проверьте папку: {self.saves_path}")
                input(
                    f"\n{Color.YELLOW}Нажмите Enter для повторной попытки...{Color.END}")
                self.manual_mode()
                return

            print(f"\n{Color.BLUE}Найден файл:{Color.END} {filepath}")
            print(f"Размер: {filepath.stat().st_size / 1024:.1f} КБ")

            confirm = input(
                f"{Color.YELLOW}Исправить этот файл? (да/нет): {Color.END}").strip().lower()
            if confirm in ('да', 'д', 'yes', 'y'):
                if self.fix_construction_block(filepath):
                    print(
                        f"\n{Color.GREEN}✅ Исправление завершено успешно!{Color.END}")
                    print(
                        "Теперь можно загрузить сохранение в игре — зависшие строители должны исчезнуть.\n")
                else:
                    print(
                        f"\n{Color.RED}❌ Не удалось исправить файл. Проверьте его структуру.{Color.END}\n")
            else:
                print(f"{Color.YELLOW}Операция отменена.{Color.END}\n")

        except KeyboardInterrupt:
            print("\n\nПрервано пользователем.")
            return

        input(f"\n{Color.YELLOW}Нажмите Enter для возврата в меню...{Color.END}")
        self.show_menu()


def main():
    """Точка входа в программу"""
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            Color.GREEN = Color.YELLOW = Color.RED = Color.BLUE = Color.CYAN = Color.BOLD = Color.END = ''

    fixer = PrisonSaveFixer()
    try:
        fixer.show_menu()
    except KeyboardInterrupt:
        print("\n\nВыход по запросу пользователя. До свидания!")
    except Exception as e:
        print(f"\n{Color.RED}Критическая ошибка: {e}{Color.END}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")


if __name__ == "__main__":
    main()
