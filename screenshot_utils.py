"""
Утилиты для создания скриншотов в Blender
"""
import os
import math
import time
from datetime import datetime


def get_screenshots_directory():
    """Возвращает путь к директории для скриншотов"""
    try:
        import bpy
    except ImportError:
        print("❌ Модуль bpy не доступен. Функция работает только в Blender.")
        return ""

    if bpy.data.filepath:
        base_path = os.path.dirname(bpy.data.filepath)
    else:
        base_path = os.path.expanduser("~/Desktop")

    screenshots_dir = os.path.join(base_path, "blender_screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    return screenshots_dir


def take_photos_to_files(context, front_path, side_path):
    """Делает скриншоты и сохраняет в указанные файлы"""
    try:
        import bpy
        from mathutils import Euler
    except ImportError:
        return "❌ Модуль bpy не доступен."

    try:
        area = context.area
        if not area or area.type != 'VIEW_3D':
            return "Нет активного 3D viewport"

        space = area.spaces.active
        if not space or not space.region_3d:
            return "Не найден 3D space"

        # Сохраняем исходные настройки
        original_rotation = space.region_3d.view_rotation.copy()

        # 1. FRONT вид
        space.region_3d.view_rotation = Euler((math.pi/2, 0.0, 0.0)).to_quaternion()
        area.tag_redraw()

        # Ждем обновления
        time.sleep(0.3)

        # Делаем скриншот
        bpy.ops.screen.screenshot(filepath=front_path)

        # 2. SIDE вид
        space.region_3d.view_rotation = Euler((math.pi/2, 0.0, math.pi/2)).to_quaternion()
        area.tag_redraw()

        # Ждем обновления
        time.sleep(0.3)

        # Делаем скриншот
        bpy.ops.screen.screenshot(filepath=side_path)

        # Восстанавливаем оригинальные настройки
        space.region_3d.view_rotation = original_rotation
        area.tag_redraw()

        return None

    except Exception as e:
        return f"Ошибка при создании скриншотов: {str(e)}"


def draw_2d_pose_on_image(image_path, coordinates_2d, view_type):
    """Рисует 2D скелет на изображении БЕЗ ПОДПИСЕЙ ТОЧЕК"""
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("❌ OpenCV не установлен")
        return None

    try:
        # Загружаем изображение
        image = cv2.imread(image_path)
        if image is None:
            print(f"⚠️ Не удалось загрузить изображение: {image_path}")
            return None

        h, w = image.shape[:2]

        # Создаем копию для рисования
        overlay = image.copy()

        # Определяем соединения между точками (MediaPipe pose connections)
        connections = [
            (0, 1),   # нос -> левое плечо
            (0, 2),   # нос -> правое плечо
            (1, 3),   # левое плечо -> левый локоть
            (2, 4),   # правое плечо -> правый локоть
            (3, 5),   # левый локоть -> левое запястье
            (4, 6),   # правый локоть -> правое запястье
            (1, 7),   # левое плечо -> левое бедро
            (2, 8),   # правое плечо -> правое бедро
            (7, 9),   # левое бедро -> левое колено
            (8, 10),  # правое бедро -> правое колено
            (9, 11),  # левое колено -> левая лодыжка
            (10, 12), # правое колено -> правая лодыжка
            (7, 8),   # левое бедро -> правое бедро (таз)
        ]

        # Рисуем линии между точками
        for i, j in connections:
            if i < len(coordinates_2d) and j < len(coordinates_2d):
                x1, y1 = coordinates_2d[i]
                x2, y2 = coordinates_2d[j]

                # Преобразуем в целые числа
                pt1 = (int(x1), int(y1))
                pt2 = (int(x2), int(y2))

                # Рисуем линию (зеленая, толщина 3)
                cv2.line(overlay, pt1, pt2, (0, 255, 0), 3)

        # Рисуем точки (красные, без подписей)
        for x, y in coordinates_2d:
            # Рисуем точку (красная, радиус 6)
            cv2.circle(overlay, (int(x), int(y)), 6, (0, 0, 255), -1)

        # Добавляем заголовок
        cv2.putText(overlay, f"MediaPipe 2D Pose Detection - {view_type} View",
                   (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        # Смешиваем с оригиналом
        alpha = 0.7
        result = cv2.addWeighted(image, 1-alpha, overlay, alpha, 0)

        # Сохраняем результат
        save_dir = get_screenshots_directory()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(save_dir, f"{view_type.lower()}_2d_skeleton_{timestamp}.png")

        cv2.imwrite(output_path, result)

        print(f"✅ 2D скелет сохранен: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Ошибка при рисовании 2D скелета: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def create_skeleton_3d_screenshot():
    """Создает скриншот 3D скелета в Blender"""
    try:
        import bpy

        # Ищем скелет
        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]

        if not skeletons:
            print("⚠️  Скелет не найден")
            return None

        skeleton = skeletons[0]

        # Выбираем скелет
        bpy.ops.object.select_all(action='DESELECT')
        skeleton.select_set(True)
        bpy.context.view_layer.objects.active = skeleton

        # Фокус на скелете
        bpy.ops.view3d.view_selected()

        # Ждем обновления
        time.sleep(0.5)

        save_dir = get_screenshots_directory()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(save_dir, f"skeleton_3d_{timestamp}.png")

        # Делаем скриншот
        bpy.ops.screen.screenshot(filepath=output_path)

        print(f"✅ 3D скриншот скелета сохранен: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Ошибка скриншота 3D скелета: {str(e)}")
        return None