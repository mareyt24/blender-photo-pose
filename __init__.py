bl_info = {
    "name": "Photo Tool Pro",
    "author": "Maria2442",
    "version": (3, 3, 5),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Tool",
    "description": "Pose detection and skeleton creation from viewport",
    "category": "3D View",
}

# Глобальные переменные
modules_loaded = False
import os

# Получаем путь к папке аддона
ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(ADDON_DIR, "models", "pose_landmarker.task")

def get_model_path():
    """Возвращает путь к файлу модели"""
    return MODEL_PATH

def register():
    """Регистрация аддона"""
    import bpy
    import traceback

    print("\n" + "=" * 60)
    print("📦 Photo Tool Pro: Начало регистрации...")
    print("=" * 60)

    # Список модулей для импорта
    modules_to_import = [
        "operators",
        "ui_panels",
        "model_utils",
        "skeleton_utils",
        "screenshot_utils",
        "deps_utils",
        "pose_from_photo"
    ]

    # Загружаем все модули
    loaded_modules = {}

    for module_name in modules_to_import:
        try:
            print(f"  🔄 Импорт модуля: {module_name}")
            module = __import__(f"{__name__}.{module_name}", fromlist=[module_name])
            loaded_modules[module_name] = module
            print(f"    ✅ {module_name} загружен")
        except ImportError as e:
            print(f"    ❌ Ошибка импорта {module_name}: {e}")
            continue

    # Регистрируем операторы
    if "operators" in loaded_modules:
        try:
            print("\n🔧 Регистрация операторов...")
            loaded_modules["operators"].register()
            print("✅ Операторы зарегистрированы")
        except Exception as e:
            print(f"❌ Ошибка регистрации операторов: {e}")

    # Регистрируем панель
    if "ui_panels" in loaded_modules:
        try:
            print("\n🎨 Регистрация панели...")
            loaded_modules["ui_panels"].register()
            print("✅ Панель зарегистрирована")
        except Exception as e:
            print(f"❌ Ошибка регистрации панели: {e}")

    print("\n" + "=" * 60)
    print("✅ Photo Tool Pro успешно зарегистрирован!")
    print("\n📍 Расположение панели:")
    print("   1. Откройте 3D Viewport")
    print("   2. Нажмите N для открытия боковой панели")
    print("   3. Перейдите на вкладку 'Tool'")
    print("\n📢 Проверьте консоль для подробных сообщений")
    print("=" * 60 + "\n")