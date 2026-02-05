# -*- coding: utf-8 -*-
"""Интерфейс для плагинов"""
from abc import ABC, abstractmethod
from pathlib import Path


class Plugin(ABC):
    """Базовый класс для всех плагинов"""

    @property
    @abstractmethod
    def menu_text(self) -> str:
        """Текст пункта меню (например: '4. Анализ мёртвых зон')"""
        pass

    @abstractmethod
    def execute(self, saves_path: Path) -> None:
        """Основная логика плагина"""
        pass
