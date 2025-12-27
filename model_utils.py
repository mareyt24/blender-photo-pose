"""
Утилиты для работы с моделью MediaPipe Pose
"""
import sys
import os

# Автоматическая настройка путей для Blender
user_site = os.path.expanduser("~\\AppData\\Roaming\\Python\\Python311\\site-packages")
if user_site not in sys.path:
    sys.path.insert(0, user_site)

import tempfile
import numpy as np

# Сначала устанавливаем значение по умолчания
SKELETON_UTILS_AVAILABLE = False

# Пытаемся импортировать остальные модули
try:
    from . import deps_utils
    from . import screenshot_utils
except ImportError as e:
    print(f"⚠️  Ошибка импорта модулей: {e}")
    deps_utils = None
    screenshot_utils = None

# Теперь пытаемся импортировать skeleton_utils
try:
    from . import skeleton_utils
    SKELETON_UTILS_AVAILABLE = True
    print("✅ skeleton_utils успешно импортирован")
except ImportError as e:
    SKELETON_UTILS_AVAILABLE = False
    print(f"⚠️  skeleton_utils не найден: {e}")

# Глобальная переменная для пути к модели
MODEL_PATH = None

# Настройки масштаба - УМЕНЬШАЕМ В 2 РАЗА
SCALE_FACTOR = 0.0015  # Было 0.003, теперь в 2 раза меньше
VERTICAL_OFFSET = 0.0
DEPTH_FACTOR = 0.3  # Коэффициент для уменьшения глубины


def _get_model_path():
    """Находит путь к файлу модели в папке аддона"""
    global MODEL_PATH

    if MODEL_PATH and os.path.exists(MODEL_PATH):
        return MODEL_PATH

    current_dir = os.path.dirname(os.path.abspath(__file__))

    possible_paths = [
        os.path.join(current_dir, "models", "pose_landmarker.task"),
        os.path.join(current_dir, "pose_landmarker.task"),
        r'C:\Users\Maria\programming\project1\pose_landmarker.task',
        os.path.join(user_site, "models", "pose_landmarker.task"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Модель найдена: {path}")
            MODEL_PATH = path
            return path

    return None


def _pixels_to_blender_coords(x_px, y_px, z_norm, w, h, center_x, center_y, is_front_view, scale):
    """
    Преобразует координаты пикселей в координаты Blender.
    В Blender: X - вправо, Z - вверх, Y - глубина (вперед/назад)
    """
    # Нормализуем координаты относительно центра изображения
    norm_x = (x_px - center_x) / w
    norm_y = (y_px - center_y) / h

    if is_front_view:
        # Front вид: X - горизонталь, Z - вертикаль, Y - глубина из MediaPipe
        bx = norm_x * w * scale  # X: вправо/влево
        bz = -norm_y * h * scale  # Z: вверх/вниз (инвертируем Y)
        # Уменьшаем влияние глубины с помощью DEPTH_FACTOR
        by = -z_norm * w * scale * DEPTH_FACTOR  # Y: глубина (уменьшена)

    else:  # Side вид
        # Side вид: Z - вертикаль, Y - горизонталь, X - глубина из MediaPipe
        bz = -norm_y * h * scale  # Z: вверх/вниз
        by = norm_x * w * scale  # Y: вперед/назад
        # Уменьшаем влияние глубины с помощью DEPTH_FACTOR
        bx = -z_norm * w * scale * DEPTH_FACTOR  # X: вправо/влево (глубина уменьшена)

    # Применяем вертикальное смещение
    bz += VERTICAL_OFFSET

    return (bx, by, bz)


def _detect_pose_in_image(image_path):
    """Обнаруживает позу в изображении и возвращает 2D и 3D координаты"""
    if not os.path.exists(image_path):
        return None, None, f"Файл не существует: {image_path}"

    try:
        model_path = _get_model_path()
        if model_path is None:
            error_msg = "Файл модели pose_landmarker.task не найден!\n"
            error_msg += "Поместите файл модели в папку 'models' аддона.\n"
            return None, None, error_msg

        import cv2
        import mediapipe as mp

        image = cv2.imread(image_path)
        if image is None:
            return None, None, f"Не удалось загрузить изображение: {image_path}"

        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
        except ImportError as e:
            return None, None, f"Ошибка импорта MediaPipe tasks: {str(e)}"

        # Создаем детектор
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        detector = vision.PoseLandmarker.create_from_options(options)

        # Обрабатываем изображение
        mp_image = mp.Image.create_from_file(image_path)
        detection_result = detector.detect(mp_image)

        if not detection_result.pose_landmarks:
            detector.close()
            return None, None, "Поза не обнаружена на изображении"

        # Извлекаем только нужные 13 точек
        key_point_indices = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
        coordinates_2d = []  # 2D координаты в пикселях
        h, w, _ = image.shape

        # Собираем 2D координаты ключевых точек
        for idx, landmark_idx in enumerate(key_point_indices):
            if landmark_idx < len(detection_result.pose_landmarks[0]):
                landmark = detection_result.pose_landmarks[0][landmark_idx]

                # Координаты в пикселях
                x_px = landmark.x * w
                y_px = landmark.y * h

                coordinates_2d.append((x_px, y_px))

        detector.close()

        if not coordinates_2d:
            return None, None, "Не удалось получить ключевые точки"

        return detection_result, coordinates_2d, None

    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        return None, None, f"Ошибка обработки изображения: {error_details}"


def _extract_3d_coordinates(detection_result, image_shape, is_front_view=True):
    """Извлекает 3D координаты из результатов детекции"""
    key_point_indices = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
    coordinates_3d = []  # 3D координаты в Blender
    h, w = image_shape[:2]

    # Центр изображения
    center_x, center_y = w // 2, h // 2

    # Собираем координаты ключевых точек
    for landmark_idx in key_point_indices:
        if landmark_idx < len(detection_result.pose_landmarks[0]):
            landmark = detection_result.pose_landmarks[0][landmark_idx]

            # Координаты в пикселях и нормализованная глубина
            x_px = landmark.x * w
            y_px = landmark.y * h
            z_norm = landmark.z

            # Преобразуем в координаты Blender
            bx, by, bz = _pixels_to_blender_coords(
                x_px, y_px, z_norm, w, h,
                center_x, center_y, is_front_view, SCALE_FACTOR
            )

            coordinates_3d.append((bx, by, bz))

    return coordinates_3d


def process_images_and_create_skeleton(front_path, side_path, create_debug_images=False):
    """Обрабатывает оба изображения и создает скелет - УПРОЩЕННАЯ ВЕРСИЯ"""
    try:
        # Обрабатываем FRONT изображение
        print("🔍 Обрабатываем FRONT изображение...")
        front_detection, front_2d, front_error = _detect_pose_in_image(front_path)

        if front_error:
            print(f"⚠️ Ошибка front: {front_error}")
            # Пробуем только SIDE
            front_detection, front_2d = None, []

        # Обрабатываем SIDE изображение
        print("🔍 Обрабатываем SIDE изображение...")
        side_detection, side_2d, side_error = _detect_pose_in_image(side_path)

        if side_error:
            print(f"⚠️ Ошибка side: {side_error}")
            # Пробуем только FRONT
            side_detection, side_2d = None, []

        # Создаем 2D скриншоты если нужно
        debug_images = []
        if create_debug_images:
            if front_2d:
                print("🎨 Создаем 2D скриншот для FRONT...")
                front_debug = screenshot_utils.draw_2d_pose_on_image(front_path, front_2d, 'FRONT')
                if front_debug:
                    debug_images.append(front_debug)

            if side_2d:
                print("🎨 Создаем 2D скриншот для SIDE...")
                side_debug = screenshot_utils.draw_2d_pose_on_image(side_path, side_2d, 'SIDE')
                if side_debug:
                    debug_images.append(side_debug)

        # Определяем какие координаты использовать
        coordinates_3d = []

        if front_detection and side_detection:
            # Есть оба вида - комбинируем
            import cv2
            front_img = cv2.imread(front_path)
            side_img = cv2.imread(side_path)

            front_3d = _extract_3d_coordinates(front_detection, front_img.shape, is_front_view=True)
            side_3d = _extract_3d_coordinates(side_detection, side_img.shape, is_front_view=False)

            # Простое комбинирование: X из front, Y из side, Z усредняем
            for i in range(min(len(front_3d), len(side_3d))):
                combined_x = front_3d[i][0]  # X из front
                combined_y = side_3d[i][1]   # Y из side
                combined_z = (front_3d[i][2] + side_3d[i][2]) / 2
                coordinates_3d.append((combined_x, combined_y, combined_z))

            print("✅ Используем комбинированные координаты из FRONT и SIDE")

        elif front_detection:
            # Только FRONT
            import cv2
            front_img = cv2.imread(front_path)
            coordinates_3d = _extract_3d_coordinates(front_detection, front_img.shape, is_front_view=True)
            print("✅ Используем только FRONT координаты")

        elif side_detection:
            # Только SIDE
            import cv2
            side_img = cv2.imread(side_path)
            coordinates_3d = _extract_3d_coordinates(side_detection, side_img.shape, is_front_view=False)
            print("✅ Используем только SIDE координаты")

        else:
            return None, debug_images, "Не удалось обработать ни одно изображение"

        if not coordinates_3d or len(coordinates_3d) < 13:
            return None, debug_images, f"Недостаточно координат: {len(coordinates_3d)} из 13"

        print(f"✅ Получены {len(coordinates_3d)} ключевых точек")
        print(f"📊 Масштаб: SCALE_FACTOR = {SCALE_FACTOR} (в 2 раза меньше)")

        # Выводим координаты для отладки
        print("\n📐 Координаты ключевых точек:")
        point_names = ["Нос", "Левое плечо", "Правое плечо", "Левый локоть", "Правый локоть",
                      "Левое запястье", "Правое запястье", "Левое бедро", "Правое бедро",
                      "Левое колено", "Правое колено", "Левая лодыжка", "Правая лодыжка"]

        for i, (x, y, z) in enumerate(coordinates_3d[:13]):
            if i < len(point_names):
                print(f"  {point_names[i]}: X={x:.3f}, Y={y:.3f}, Z={z:.3f}")

        # Создаем 3D скелет
        print("\n🦴 Создаем 3D скелет...")
        skeleton = skeleton_utils.create_skeleton_from_coordinates(coordinates_3d)
        if not skeleton:
            return None, debug_images, "Не удалось создать скелет из полученных координат"

        return skeleton, debug_images, None

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Ошибка: {error_details}")
        return None, [], f"Ошибка при создании скелета: {str(e)}"


def create_skeleton_from_viewport(context, make_screenshot=False):
    """
    Основная функция: делает скриншоты, обрабатывает и создает скелет
    Если make_screenshot=True - также создает отладочные 2D скриншоты
    """
    print("\n" + "="*60)
    print("Photo Tool Pro: Создание скелета" + (" + 2D скриншоты" if make_screenshot else ""))
    print("="*60)

    # Проверяем, доступен ли skeleton_utils
    if not SKELETON_UTILS_AVAILABLE:
        return None, [], "Модуль skeleton_utils не найден."

    # Проверяем зависимости
    if deps_utils is None:
        return None, [], "Модуль deps_utils не доступен"

    missing = deps_utils.check_deps_quick()
    if missing:
        return None, [], f"Для работы необходимо установить зависимости: {', '.join(missing)}"

    print("✅ Все зависимости установлены")

    # Делаем скриншоты во временные файлы
    print("\n📸 Делаем скриншоты viewport...")
    front_temp = None
    side_temp = None

    try:
        # Создаем временные файлы
        temp_dir = tempfile.gettempdir()
        front_temp = os.path.join(temp_dir, f"front_temp_{os.getpid()}.png")
        side_temp = os.path.join(temp_dir, f"side_temp_{os.getpid()}.png")

        # Делаем скриншоты
        error = screenshot_utils.take_photos_to_files(context, front_temp, side_temp)
        if error:
            return None, [], error

        print("✅ Скриншоты сделаны")

        # Обрабатываем изображения и создаем скелет
        skeleton, debug_images, error = process_images_and_create_skeleton(
            front_temp, side_temp, create_debug_images=make_screenshot
        )

        if error:
            return None, debug_images, error

        print("✅ Скелет успешно создан!")
        return skeleton, debug_images, None

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Ошибка: {error_details}")
        return None, [], f"Ошибка при создании скелета: {str(e)}"

    finally:
        # Удаляем временные файлы
        try:
            if front_temp and os.path.exists(front_temp):
                os.remove(front_temp)
                print(f"🗑️ Удален временный файл: {front_temp}")
            if side_temp and os.path.exists(side_temp):
                os.remove(side_temp)
                print(f"🗑️ Удален временный файл: {side_temp}")
        except Exception as e:
            print(f"⚠️ Не удалось удалить временные файлы: {e}")