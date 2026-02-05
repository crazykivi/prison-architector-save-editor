# -*- coding: utf-8 -*-
"""Плагин: детектор мёртвых зон камер и охраны"""
import re
from plugin_interface import Plugin
from pathlib import Path
from ui import Color


class DeadZoneDetector(Plugin):
    @property
    def menu_text(self) -> str:
        return "Анализ мёртвых зон камер и охраны"

    def execute(self, saves_path: Path) -> None:
        print(f"\n{Color.BLUE}Запуск анализа мёртвых зон...{Color.END}")

        saves = sorted(
            [f for f in saves_path.glob("*.prison") if f.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not saves:
            print(f"{Color.RED}Не найдено сейвов для анализа{Color.END}")
            input("\nНажмите Enter...")
            return

        print(f"\n{Color.GREEN}Найдено {len(saves)} сейвов:{Color.END}")
        for i, save in enumerate(saves, 1):
            print(f"  {i}. {save.name}")

        try:
            choice = int(
                input(f"\n{Color.YELLOW}Выберите сейв для анализа (0 для отмены): {Color.END}"))
            if choice == 0:
                return
            if 1 <= choice <= len(saves):
                target = saves[choice - 1]
                self._analyze_save(target)
            else:
                print(f"{Color.RED}Неверный номер{Color.END}")
        except ValueError:
            print(f"{Color.RED}Введите число{Color.END}")

        input(f"\n{Color.YELLOW}Нажмите Enter для возврата в меню...{Color.END}")

    def _analyze_save(self, filepath: Path):
        """Анализ конкретного сейва с корректным парсингом структуры"""
        # Чтение файла в бинарном режиме (определеине кодировки)
        try:
            with open(filepath, 'rb') as f:
                raw_data = f.read()

            try:
                content = raw_data.decode('cp1251')
            except UnicodeDecodeError:
                content = raw_data.decode('utf-8')
        except Exception as e:
            print(f"{Color.RED}Ошибка чтения файла: {e}{Color.END}")
            return

        # ПАРСИНГ СТРУКТУРЫ СЕЙВА

        # 1. Камеры наблюдения: в сейвах Prison Architect тип = "Cctv"
        cameras = len(re.findall(r'^\s*Type\s+Cctv\s*$',
                      content, re.MULTILINE | re.IGNORECASE))

        # 2. Мониторы для просмотра камер (опционально)
        monitors = len(re.findall(r'^\s*Type\s+CctvMonitor\s*$',
                       content, re.MULTILINE | re.IGNORECASE))

        # 3. Патрули: парсинг секции Patrols (основной источник)
        patrols = 0
        patrol_match = re.search(
            r'BEGIN\s+Patrols\s*\n\s*Size\s+(\d+)', content, re.IGNORECASE)
        if patrol_match:
            patrols = int(patrol_match.group(1))

        # 4. Точки патрулирования (дополнительная проверка)
        patrol_points = len(re.findall(
            r'^\s*Type\s+PatrolPoint\s*$', content, re.MULTILINE | re.IGNORECASE))

        # 5. Охранники
        guards = len(re.findall(r'^\s*Type\s+Guard\s*$',
                     content, re.MULTILINE | re.IGNORECASE))

        # 6. Камеры заключения (комнаты типа "Cell")
        cells = len(re.findall(r'^\s*RoomType\s+Cell\s*$',
                    content, re.MULTILINE | re.IGNORECASE))

        # 7. Двери всех типов
        doors = len(re.findall(r'^\s*Type\s+(JailDoor|Door|StaffDoor|DoubleDoor|JailDoorLarge|DoubleStaffDoorBlue)\b',
                    content, re.MULTILINE | re.IGNORECASE))

        # 8. Зоны безопасности
        staff_zones = len(re.findall(
            r'Zone\s+StaffOnly', content, re.IGNORECASE))
        minsec_zones = len(re.findall(
            r'Zone\s+MinSecOnly', content, re.IGNORECASE))
        maxsec_zones = len(re.findall(
            r'Zone\s+MaxSecOnly', content, re.IGNORECASE))
        deathrow_zones = len(re.findall(
            r'Zone\s+DeathRow', content, re.IGNORECASE))

        # ВЫВОД РЕЗУЛЬТАТОВ
        print(f"\n{Color.CYAN}Результаты анализа: {filepath.name}{Color.END}")
        print(f"  • Камеры наблюдения: {cameras}")
        if monitors > 0:
            print(
                f"  • Мониторы: {monitors} {'✓' if monitors >= cameras else '⚠️ недостаточно'}")
        print(f"  • Зоны патрулирования: {patrols}")
        if patrol_points > 0:
            print(f"  • Точки патрулирования: {patrol_points}")
        print(f"  • Охранники: {guards}")
        print(f"  • Камеры заключения: {cells}")
        print(f"  • Двери (все типы): {doors}")
        print(f"\n  • Зоны безопасности:")
        print(f"    - Только для персонала: {staff_zones}")
        print(f"    - Мин. безопасность: {minsec_zones}")
        print(f"    - Макс. безопасность: {maxsec_zones}")
        print(f"    - Камера смертников: {deathrow_zones}")

        # АНАЛИЗ ПРОБЛЕМ
        issues = []
        recommendations = []

        # Проблема 1: отсутствие камер
        if cameras == 0:
            issues.append("Критически: отсутствуют камеры наблюдения")
            recommendations.append(
                "Установите камеры (Cctv) в коридорах, возле входов и в зонах общего пользования")
        elif cameras < max(1, (minsec_zones + maxsec_zones * 2) // 3):
            issues.append(
                f"Недостаточно камер (есть {cameras}, рекомендуется минимум {max(1, (minsec_zones + maxsec_zones * 2) // 3)})")
            recommendations.append(
                "Добавьте камеры в зоны максимальной безопасности (1 камера на 2 зоны мин.безопасности, 1:1 для макс.безопасности)")

        # Проблема 2: нет мониторов для просмотра
        if cameras > 0 and monitors == 0:
            issues.append(
                f"Есть {cameras} камер, но нет мониторов для просмотра")
            recommendations.append(
                "Установите мониторы (CctvMonitor) в комнате охраны для просмотра камер")
        elif monitors < cameras // 4:
            issues.append(
                f"Недостаточно мониторов ({monitors} на {cameras} камер)")
            recommendations.append(
                "Добавьте мониторы — рекомендуется 1 монитор на 4 камеры")

        # Проблема 3: патрули без охраны
        if patrols > 0 and guards < patrols * 2:
            issues.append(
                f"Недостаточно охраны для патрулей (патрулей: {patrols}, охранников: {guards}, нужно минимум {patrols * 2})")
            recommendations.append(
                "Наймите дополнительных охранников (минимум 2 на патруль) или упростите маршруты")
        elif patrols == 0 and guards > 5 and patrol_points > 0:
            issues.append(
                f"Есть {patrol_points} точек патрулирования, но не настроены маршруты")
            recommendations.append(
                "Настройте маршруты патрулирования через меню 'Охрана → Патрули'")
        elif patrols == 0 and guards > 10:
            issues.append(
                f"Много охранников ({guards}) без маршрутов патрулирования")
            recommendations.append(
                "Создайте хотя бы 1-2 патруля для эффективного патрулирования территории")

        # Проблема 4: зоны максимальной безопасности без камер
        high_risk_zones = maxsec_zones + deathrow_zones
        if high_risk_zones > 0 and cameras < high_risk_zones:
            issues.append(
                f"Зоны максимальной безопасности без камер ({high_risk_zones} зон, {cameras} камер)")
            recommendations.append(
                "Установите минимум по 1 камере в каждой зоне максимальной безопасности")

        # Проблема 5: двери без наблюдения
        critical_doors = doors // 3  # Примерно треть дверей должны быть под наблюдением
        if cameras > 0 and cameras < critical_doors:
            issues.append(
                f"Недостаточно камер для наблюдения за дверями ({cameras} камер на {doors} дверей)")
            recommendations.append(
                "Установите камеры напротив служебных дверей и выходов")

        # ВЫВОД РЕКОМЕНДАЦИЙ
        if issues:
            print(f"\n{Color.RED}Обнаружены проблемы:{Color.END}")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")

            print(f"\n{Color.YELLOW}Рекомендации:{Color.END}")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")

            # Практические советы
            print(f"\n{Color.BLUE}Советы по размещению:{Color.END}")
            print(
                "  • Камеры: размещайте на высоте 2-3 клетки, направляя вдоль коридоров")
            print("  • Перекрытие: ставьте камеры попарно для устранения слепых зон")
            print("  • Патрули: создавайте маршруты длиной 15-25 клеток с 2+ охранниками")
            if deathrow_zones > 0:
                print(
                    "  • Смертники: обязательно 2+ камеры на зону + постоянный патруль")
        else:
            print(f"\n{Color.GREEN}✓ Система безопасности в норме:{Color.END}")
            if cameras > 0:
                print(f"  • Камеры обеспечивают покрытие критических зон")
            if patrols > 0:
                print(
                    f"  • Настроены {patrols} патруль(ей) для {guards} охранников")
            if monitors > 0:
                print(f"  • Мониторы позволяют отслеживать все камеры")
