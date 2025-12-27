"""
Утилиты для выставления позы по фото - МЕТОД КОПИРОВАНИЯ ИЗ ВРЕМЕННОГО СКЕЛЕТА
"""

import os
import sys
import numpy as np
from mathutils import Vector, Quaternion, Euler

# Автоматическая настройка путей для Blender
user_site = os.path.expanduser("~\\AppData\\Roaming\\Python\\Python311\\site-packages")
if user_site not in sys.path:
    sys.path.insert(0, user_site)


def _save_pose_visualization(image_path, landmarks_2d, view_type):
    """Сохраняет фото с нарисованным поверх скелетом MediaPipe"""
    try:
        import cv2

        # Загружаем изображение
        image = cv2.imread(image_path)
        if image is None:
            print(f"⚠️ Не удалось загрузить изображение: {image_path}")
            return None

        h, w = image.shape[:2]

        # Создаем копию для рисования
        overlay = image.copy()

        # Определяем соединения между точками
        connections = [
            (0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 6),
            (1, 7), (2, 8), (7, 9), (8, 10), (9, 11), (10, 12), (7, 8)
        ]

        # Рисуем линии между точками
        for i, j in connections:
            if i < len(landmarks_2d) and j < len(landmarks_2d):
                x1, y1 = landmarks_2d[i]
                x2, y2 = landmarks_2d[j]

                pt1 = (int(x1), int(y1))
                pt2 = (int(x2), int(y2))

                cv2.line(overlay, pt1, pt2, (0, 255, 0), 3)

        # Рисуем точки
        for x, y in landmarks_2d:
            cv2.circle(overlay, (int(x), int(y)), 6, (0, 0, 255), -1)

        # Добавляем текст
        text = f"MediaPipe Pose - {view_type} View"
        cv2.putText(overlay, text, (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        # Смешиваем с оригиналом
        alpha = 0.6
        result = cv2.addWeighted(image, 1-alpha, overlay, alpha, 0)

        # Создаем путь для сохранения
        original_dir = os.path.dirname(image_path)
        original_name = os.path.basename(image_path)
        name_without_ext = os.path.splitext(original_name)[0]

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name_without_ext}_{view_type.lower()}_pose_{timestamp}.png"

        # Сохраняем в ту же папку
        output_path = os.path.join(original_dir, output_filename)

        cv2.imwrite(output_path, result)

        print(f"✅ Фото с скелетом сохранено: {output_path}")
        return output_path

    except Exception as e:
        print(f"⚠️ Ошибка при сохранении визуализации: {e}")
        return None


def _detect_pose_in_image(image_path):
    """Обнаруживает позу в изображении и возвращает 3D координаты MediaPipe"""
    if not os.path.exists(image_path):
        return None, None, f"Файл не существует: {image_path}"

    try:
        import cv2
        import mediapipe as mp

        # Находим путь к модели
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "models", "pose_landmarker.task")

        if not os.path.exists(model_path):
            return None, None, "Файл модели pose_landmarker.task не найден в папке models"

        image = cv2.imread(image_path)
        if image is None:
            return None, None, f"Не удалось загрузить изображение: {image_path}"

        h, w = image.shape[:2]

        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        # Создаем детектор
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False,
            num_poses=1,
            min_pose_detection_confidence=0.3,
            min_pose_presence_confidence=0.3,
            min_tracking_confidence=0.3
        )
        detector = vision.PoseLandmarker.create_from_options(options)

        # Обрабатываем изображение
        mp_image = mp.Image.create_from_file(image_path)
        detection_result = detector.detect(mp_image)

        if not detection_result.pose_landmarks:
            detector.close()
            return None, None, "Поза не обнаружена на изображении"

        # Извлекаем 2D и 3D координаты
        key_point_indices = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
        landmarks_2d = []  # 2D координаты в пикселях
        landmarks_3d = []  # 3D нормализованные координаты

        for landmark_idx in key_point_indices:
            if landmark_idx < len(detection_result.pose_landmarks[0]):
                landmark = detection_result.pose_landmarks[0][landmark_idx]
                # 2D координаты в пикселях
                x_px = landmark.x * w
                y_px = landmark.y * h
                landmarks_2d.append((x_px, y_px))
                # 3D координаты (нормализованные)
                landmarks_3d.append((landmark.x, landmark.y, landmark.z))
            else:
                landmarks_2d.append((0, 0))
                landmarks_3d.append((0, 0, 0))

        detector.close()

        return landmarks_2d, landmarks_3d, None

    except Exception as e:
        import traceback
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        return None, None, f"Ошибка обработки изображения: {error_details}"


def _create_temporary_skeleton_from_mediapipe(landmarks_3d, is_front_view=True):
    """Создает временный скелет из координат MediaPipe"""
    try:
        import bpy

        print("🦴 Создаем временный скелет из координат MediaPipe...")

        # Применяем масштаб к координатам (как в skeleton_utils.py)
        SCALE_MULTIPLIER = 5.0
        scaled_coords = []

        for x, y, z in landmarks_3d:
            # Нормализуем координаты MediaPipe (0-1) в диапазон -0.5 до 0.5
            norm_x = x - 0.5
            norm_y = y - 0.5
            norm_z = z * 0.1  # СИЛЬНО уменьшаем глубину

            # Применяем масштаб
            scaled_coords.append((
                norm_x * SCALE_MULTIPLIER,
                norm_z * SCALE_MULTIPLIER,  # Z в Blender - это вертикаль
                -norm_y * SCALE_MULTIPLIER  # Y инвертируем для Blender
            ))

        # Создаем арматуру
        bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(0, 0, 0))
        temp_armature = bpy.context.active_object
        temp_armature.name = "Temp_Pose_Skeleton"

        # Переходим в режим редактирования
        bpy.ops.object.mode_set(mode='EDIT')

        # Получаем данные арматуры
        armature_data = temp_armature.data

        # Удаляем стандартную кость
        for bone in armature_data.edit_bones:
            armature_data.edit_bones.remove(bone)

        # Создаем кости на основе координат
        # 0: нос, 1: левое плечо, 2: правое плечо, 3: левый локоть, 4: правый локоть,
        # 5: левое запястье, 6: правое запястье, 7: левое бедро, 8: правое бедро,
        # 9: левое колено, 10: правое колено, 11: левая лодыжка, 12: правая лодыжка

        # Создаем основные кости
        bones_data = [
            # Позвоночник: от таза к шее
            ('spine', 7, 8, 1, 2, 0),  # от центра таза к центру плеч, затем к носу
            # Левая рука
            ('upper_arm.L', 1, 3),
            ('forearm.L', 3, 5),
            # Правая рука
            ('upper_arm.R', 2, 4),
            ('forearm.R', 4, 6),
            # Левая нога
            ('thigh.L', 7, 9),
            ('shin.L', 9, 11),
            # Правая нога
            ('thigh.R', 8, 10),
            ('shin.R', 10, 12),
        ]

        # Создаем кости
        created_bones = {}

        for bone_info in bones_data:
            bone_name = bone_info[0]

            if len(bone_info) == 6:  # spine
                _, hip1_idx, hip2_idx, shoulder1_idx, shoulder2_idx, nose_idx = bone_info

                # Центр таза
                hip_center = (
                    (scaled_coords[hip1_idx][0] + scaled_coords[hip2_idx][0]) / 2,
                    (scaled_coords[hip1_idx][1] + scaled_coords[hip2_idx][1]) / 2,
                    (scaled_coords[hip1_idx][2] + scaled_coords[hip2_idx][2]) / 2
                )

                # Центр плеч
                shoulder_center = (
                    (scaled_coords[shoulder1_idx][0] + scaled_coords[shoulder2_idx][0]) / 2,
                    (scaled_coords[shoulder1_idx][1] + scaled_coords[shoulder2_idx][1]) / 2,
                    (scaled_coords[shoulder1_idx][2] + scaled_coords[shoulder2_idx][2]) / 2
                )

                bone = armature_data.edit_bones.new(bone_name)
                bone.head = hip_center
                bone.tail = shoulder_center

            else:  # обычные кости
                _, start_idx, end_idx = bone_info

                bone = armature_data.edit_bones.new(bone_name)
                bone.head = scaled_coords[start_idx]
                bone.tail = scaled_coords[end_idx]

            created_bones[bone_name] = bone

        # Настраиваем иерархию
        # Позвоночник - корневая кость
        if 'spine' in created_bones:
            spine_bone = created_bones['spine']

            # Прикрепляем руки к позвоночнику
            for bone_name in ['upper_arm.L', 'upper_arm.R']:
                if bone_name in created_bones:
                    created_bones[bone_name].parent = spine_bone

            # Прикрепляем ноги к позвоночнику
            for bone_name in ['thigh.L', 'thigh.R']:
                if bone_name in created_bones:
                    created_bones[bone_name].parent = spine_bone

        # Прикрепляем предплечья к плечам
        if 'upper_arm.L' in created_bones and 'forearm.L' in created_bones:
            created_bones['forearm.L'].parent = created_bones['upper_arm.L']
            created_bones['forearm.L'].use_connect = True

        if 'upper_arm.R' in created_bones and 'forearm.R' in created_bones:
            created_bones['forearm.R'].parent = created_bones['upper_arm.R']
            created_bones['forearm.R'].use_connect = True

        # Прикрепляем голени к бедрам
        if 'thigh.L' in created_bones and 'shin.L' in created_bones:
            created_bones['shin.L'].parent = created_bones['thigh.L']
            created_bones['shin.L'].use_connect = True

        if 'thigh.R' in created_bones and 'shin.R' in created_bones:
            created_bones['shin.R'].parent = created_bones['thigh.R']
            created_bones['shin.R'].use_connect = True

        # Возвращаемся в объектный режим
        bpy.ops.object.mode_set(mode='OBJECT')

        print(f"✅ Временный скелет создан с {len(created_bones)} костями")
        return temp_armature

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Ошибка при создании временного скелета: {error_details}")
        return None


def _copy_pose_between_armatures(source_armature, target_armature):
    """Копирует позу из исходной арматуры в целевую"""
    try:
        import bpy

        print(f"🔄 Копируем позу из {source_armature.name} в {target_armature.name}...")

        # Убедимся, что целевая арматура в режиме позы
        if bpy.context.mode != 'POSE':
            bpy.ops.object.select_all(action='DESELECT')
            target_armature.select_set(True)
            bpy.context.view_layer.objects.active = target_armature
            bpy.ops.object.mode_set(mode='POSE')

        # Копируем вращения для каждой кости
        bones_copied = 0

        for bone_name in source_armature.pose.bones.keys():
            if bone_name in target_armature.pose.bones:
                source_bone = source_armature.pose.bones[bone_name]
                target_bone = target_armature.pose.bones[bone_name]

                # Копируем вращение
                target_bone.rotation_mode = source_bone.rotation_mode

                if source_bone.rotation_mode == 'QUATERNION':
                    target_bone.rotation_quaternion = source_bone.rotation_quaternion.copy()
                else:
                    target_bone.rotation_euler = source_bone.rotation_euler.copy()

                bones_copied += 1

        print(f"✅ Скопировано {bones_copied} костей")
        return True

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Ошибка при копировании позы: {error_details}")
        return False


def _align_skeleton_to_pose(armature, landmarks_3d, is_front_view=True):
    """Выставляет позу скелета на основе координат MediaPipe"""
    try:
        import bpy

        print("🎯 Выставляем позу скелета...")

        # 1. Создаем временный скелет из координат MediaPipe
        temp_armature = _create_temporary_skeleton_from_mediapipe(landmarks_3d, is_front_view)
        if not temp_armature:
            return False, "Не удалось создать временный скелет"

        # 2. Копируем позу из временного скелета в основной
        success = _copy_pose_between_armatures(temp_armature, armature)

        # 3. Удаляем временный скелет
        bpy.data.objects.remove(temp_armature)

        if success:
            return True, "Поза успешно скопирована из временного скелета"
        else:
            return False, "Не удалось скопировать позу"

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Ошибка при выставлении позы: {error_details}")
        return False, f"Ошибка при выставлении позы: {str(e)}"


def apply_pose_from_photo(image_path, armature, is_front_view=True, save_visualization=True):
    """
    Выставление позы по фото - основной метод
    """
    try:
        print(f"\n📸 Анализируем фото: {os.path.basename(image_path)}")
        print(f"🔍 Тип вида: {'FRONT' if is_front_view else 'SIDE'}")
        print(f"🎯 Метод: Создание временного скелета и копирование позы")

        # 1. Проверяем файл
        if not os.path.exists(image_path):
            return False, f"Файл не существует: {image_path}"

        # 2. Проверяем зависимости
        try:
            import cv2
            import mediapipe
        except ImportError:
            return False, "Требуются библиотеки OpenCV и MediaPipe"

        # 3. Проверяем режим арматуры - должно быть POSE!
        import bpy
        if bpy.context.mode != 'POSE':
            return False, "Перейдите в режим позы скелета (Pose Mode)"

        # 4. Обнаруживаем позу на фото
        landmarks_2d, landmarks_3d, error = _detect_pose_in_image(image_path)
        if error:
            return False, error

        if not landmarks_3d or len(landmarks_3d) < 13:
            return False, "Не удалось получить достаточно ключевых точек"

        print(f"✅ Обнаружено {len(landmarks_3d)} ключевых точек")

        # 5. Сохраняем фото с нарисованным скелетом
        visualization_path = None
        if save_visualization and landmarks_2d:
            view_type = 'FRONT' if is_front_view else 'SIDE'
            visualization_path = _save_pose_visualization(
                image_path,
                landmarks_2d,
                view_type
            )

        # 6. Выставляем позу скелета
        success, message = _align_skeleton_to_pose(armature, landmarks_3d, is_front_view)

        if success:
            # Обновляем viewport
            bpy.context.view_layer.update()

            # Формируем итоговое сообщение
            final_message = "✅ Поза успешно применена (метод временного скелета)"
            if visualization_path:
                final_message += f"\n📸 Фото с скелетом сохранено: {visualization_path}"

            return True, final_message
        else:
            return False, message

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Ошибка при применении позы: {error_details}")
        return False, f"Ошибка при применении позы: {str(e)}"