"""
Утилита для поиска файлов моделей
"""
import os
import bpy


def find_model_file(filename="pose_landmarker.task"):
    """Находит файл модели в системе"""

    # Список возможных путей
    possible_paths = []

    # 1. Относительно текущего файла
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths.append(os.path.join(current_dir, "models", filename))

    # 2. В папке аддона
    addon_name = "photo_tool_pro"
    for script_dir in bpy.utils.script_paths():
        # Проверяем разные варианты имен папок
        for folder_name in [addon_name, f"{addon_name}_3_3_5", "photo_tool"]:
            possible_paths.append(os.path.join(script_dir, "addons", folder_name, "models", filename))

    # 3. Проверяем существование файлов
    for path in possible_paths:
        normalized_path = os.path.normpath(path)
        if os.path.exists(normalized_path):
            return normalized_path

    return None


def get_model_path_with_fallback(filename="pose_landmarker.task"):
    """Получает путь к модели или возвращает путь для загрузки"""
    model_path = find_model_file(filename)

    if model_path:
        print(f"✅ Модель найдена: {model_path}")
        return model_path

    # Если модель не найдена, возвращаем путь по умолчанию
    current_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(current_dir, "models", filename)

    # Создаем папку models если ее нет
    os.makedirs(os.path.dirname(default_path), exist_ok=True)

    print(f"⚠️ Модель не найдена, будет использован путь: {default_path}")
    print("   Поместите файл модели в эту папку")

    return default_path