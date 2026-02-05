# -*- coding: utf-8 -*-
"""
Prison Architect Save Fixer — ядро приложения
Исправляет зависшие задачи строительства в сейвах игры, также помогает с переносом сейвов
"""
import os
import sys
import shutil
import re
from pathlib import Path
from typing import Optional, List, Tuple
from ui import Color


class PrisonSaveFixer:
    """Основной класс для работы с сейвами Prison Architect"""

    def __init__(self):
        self.saves_path = self.get_saves_path()
        self.encoding = 'cp1251'
        self.plugins = []

    def get_saves_path(self) -> Optional[Path]:
        """Автоматически определяет путь к папке сохранений в зависимости от ОС"""
        system = sys.platform

        if system == "win32":
            docs = Path.home() / "Documents" / "Prison Architect" / "saves"
            if docs.exists():
                return docs
            steam = Path.home() / "AppData" / "Local" / "Introversion" / \
                "Prison Architect" / "saves"
            if steam.exists():
                return steam

        elif system == "darwin":
            mac = Path.home() / "Library" / "Application Support" / \
                "Prison Architect" / "saves"
            if mac.exists():
                return mac

        elif system.startswith("linux"):
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

            print(f"{Color.GREEN}Файл успешно исправлен:{Color.END} {filepath.name}")
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

    def load_plugins(self):
        """Загружает плагины из внешней папки plugins (рядом с .exe или скриптом)"""
        from plugin_loader import load_plugins as loader
        self.plugins = loader()
