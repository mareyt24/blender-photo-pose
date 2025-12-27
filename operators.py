"""
Операторы для аддона Photo Tool Pro
"""

import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty
from mathutils import Quaternion, Vector, Euler
import numpy as np


class VIEW3D_OT_edit_skeleton(Operator):
    """Select skeleton and enter edit mode"""
    bl_idname = "view3d.edit_skeleton"
    bl_label = "Редактировать скелет"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]
        return len(skeletons) > 0 and context.area and context.area.type == 'VIEW_3D'

    def execute(self, context):
        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]

        if not skeletons:
            self.report({'ERROR'}, "Скелет не найден")
            return {'CANCELLED'}

        skeleton = skeletons[0]

        if context.mode == 'EDIT_ARMATURE':
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'INFO'}, "Переключено в Object Mode")
        else:
            bpy.ops.object.select_all(action='DESELECT')
            skeleton.select_set(True)
            context.view_layer.objects.active = skeleton
            bpy.ops.object.mode_set(mode='EDIT')
            self.report({'INFO'}, "Режим редактирования костей")

        return {'FINISHED'}


class VIEW3D_OT_pose_skeleton(Operator):
    """Select skeleton and enter pose mode"""
    bl_idname = "view3d.pose_skeleton"
    bl_label = "Настроить позу"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]
        return len(skeletons) > 0 and context.area and context.area.type == 'VIEW_3D'

    def execute(self, context):
        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]

        if not skeletons:
            self.report({'ERROR'}, "Скелет не найден")
            return {'CANCELLED'}

        skeleton = skeletons[0]

        if context.mode == 'POSE':
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'INFO'}, "Переключено в Object Mode")
        else:
            bpy.ops.object.select_all(action='DESELECT')
            skeleton.select_set(True)
            context.view_layer.objects.active = skeleton
            bpy.ops.object.mode_set(mode='POSE')
            self.report({'INFO'}, "Режим настройки позы")

        return {'FINISHED'}


class VIEW3D_OT_create_skeleton(Operator):
    """Create skeleton from viewport"""
    bl_idname = "view3d.create_skeleton"
    bl_label = "Создать скелет"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == 'VIEW_3D'

    def execute(self, context):
        from . import model_utils

        print("\n" + "=" * 60)
        print("🎯 Photo Tool Pro: Создание скелета...")
        print("=" * 60)

        skeleton, debug_images, error = model_utils.create_skeleton_from_viewport(context, make_screenshot=False)

        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        self.report({'INFO'}, "✅ Скелет успешно создан!")
        return {'FINISHED'}


class VIEW3D_OT_create_skeleton_with_screenshot(Operator):
    """Create skeleton from viewport and save 2D debug screenshots"""
    bl_idname = "view3d.create_skeleton_with_screenshot"
    bl_label = "Создать скелет + 2D скриншоты"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == 'VIEW_3D'

    def execute(self, context):
        from . import model_utils

        print("\n" + "=" * 60)
        print("🎯 Photo Tool Pro: Создание скелета + 2D скриншоты...")
        print("=" * 60)

        skeleton, debug_images, error = model_utils.create_skeleton_from_viewport(context, make_screenshot=True)

        if error:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        if debug_images:
            paths_text = "\n".join([os.path.basename(p) for p in debug_images])
            self.report({'INFO'}, f"✅ Скелет создан! 2D скриншоты сохранены:\n{paths_text}")
        else:
            self.report({'INFO'}, "✅ Скелет создан! (2D скриншоты не удалось создать)")

        return {'FINISHED'}


class VIEW3D_OT_attach_skeleton(Operator):
    """Attach skeleton to mesh with automatic weights"""
    bl_idname = "view3d.attach_skeleton"
    bl_label = "Привязать скелет к модели"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]
        meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        return len(skeletons) > 0 and len(meshes) > 0 and context.area and context.area.type == 'VIEW_3D'

    def execute(self, context):
        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]

        if not skeletons:
            self.report({'ERROR'}, "Не найден скелет")
            return {'CANCELLED'}

        skeleton = skeletons[0]

        meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not meshes:
            self.report({'ERROR'}, "Не выбран меш. Сначала выберите объект меша.")
            return {'CANCELLED'}

        mesh = meshes[0]

        try:
            for obj in context.selected_objects:
                obj.select_set(False)

            mesh.select_set(True)
            skeleton.select_set(True)
            context.view_layer.objects.active = skeleton

            bpy.ops.object.parent_set(type='ARMATURE_AUTO')

            self.report({'INFO'}, f"Скелет привязан к {mesh.name} с автоматическими весами")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Ошибка при привязке скелета: {str(e)}")
            return {'CANCELLED'}


class VIEW3D_OT_clear_skeletons(Operator):
    """Clear all created skeletons and debug objects"""
    bl_idname = "view3d.clear_skeletons"
    bl_label = "Очистить все скелеты"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            skeletons = [
                obj for obj in bpy.data.objects
                if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
            ]

            debug_objects = [
                obj for obj in bpy.data.objects
                if obj.name.startswith(("Debug_", "Target_", "Visual_", "Origin_Marker"))
            ]

            for skeleton in skeletons:
                bpy.data.objects.remove(skeleton, do_unlink=True)

            for obj in debug_objects:
                bpy.data.objects.remove(obj, do_unlink=True)

            count_skeletons = len(skeletons)
            count_objects = len(debug_objects)

            self.report({'INFO'}, f"Удалено {count_skeletons} скелетов и {count_objects} объектов")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка при очистке: {str(e)}")
            return {'CANCELLED'}


class VIEW3D_OT_check_dependencies(Operator):
    """Check if required dependencies are installed"""
    bl_idname = "view3d.check_dependencies"
    bl_label = "Проверить зависимости"

    def execute(self, context):
        from . import deps_utils
        report, missing = deps_utils.check_deps_detailed()

        def draw_menu(self, context):
            self.layout.label(text=report)

        context.window_manager.popup_menu(draw_menu, title="Проверка зависимостей", icon='INFO')
        return {'FINISHED'}


class VIEW3D_OT_apply_pose_from_photo(Operator):
    """Apply pose from selected photo to active skeleton"""
    bl_idname = "view3d.apply_pose_from_photo"
    bl_label = "Выставить позу по фото"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="Путь к файлу",
        description="Путь к файлу фотографии",
        maxlen=1024,
        default=""
    )

    view_type: EnumProperty(
        name="Вид фото",
        description="Выберите вид фотографии",
        items=[
            ('FRONT', 'Фронтальный вид', 'Фронтальный вид позы'),
            ('SIDE', 'Боковой вид', 'Боковой вид позы'),
        ],
        default='FRONT'
    )

    filter_glob: StringProperty(
        default="*.jpg;*.jpeg;*.png;*.bmp",
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]
        return len(skeletons) > 0 and context.area and context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        print("\n" + "=" * 60)
        print("📸 Photo Tool Pro: Выставление позы по фото...")
        print("=" * 60)

        if not self.filepath:
            self.report({'ERROR'}, "Файл не выбран")
            return {'CANCELLED'}

        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]

        if not skeletons:
            self.report({'ERROR'}, "Не найден скелет Pose_Skeleton")
            return {'CANCELLED'}

        skeleton = skeletons[0]

        if context.mode != 'POSE':
            bpy.ops.object.select_all(action='DESELECT')
            skeleton.select_set(True)
            context.view_layer.objects.active = skeleton
            bpy.ops.object.mode_set(mode='POSE')
            print("✅ Автоматически переключились в Pose Mode")

        try:
            from . import deps_utils
            missing = deps_utils.check_deps_quick()
            if missing:
                self.report({'ERROR'}, f"Установите зависимости: {', '.join(missing)}")
                return {'CANCELLED'}
        except ImportError:
            self.report({'ERROR'}, "Не удалось проверить зависимости")
            return {'CANCELLED'}

        is_front_view = (self.view_type == 'FRONT')
        success, message = self._apply_pose_with_relative_rotation(image_path=self.filepath,
                                                                   armature=skeleton,
                                                                   is_front_view=is_front_view)

        if success:
            self.report({'INFO'}, f"✅ {message}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"❌ {message}")
            return {'CANCELLED'}

    def _apply_pose_with_relative_rotation(self, image_path, armature, is_front_view=True):
        """Метод, использующий только 2D координаты MediaPipe для вычисления позы."""
        try:
            import cv2
            import mediapipe as mp
            import numpy as np
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            print("🔄 Используем 2D метод (без учета глубины)...")

            image = cv2.imread(image_path)
            if image is None:
                return False, f"Не удалось загрузить изображение: {image_path}"

            h, w = image.shape[:2]

            # Поиск модели
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "models", "pose_landmarker.task")

            if not os.path.exists(model_path):
                model_path = os.path.join(current_dir, "..", "models", "pose_landmarker.task")
                if not os.path.exists(model_path):
                    return False, "Файл модели pose_landmarker.task не найден"

            print(f"✅ Используем модель: {model_path}")

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

            mp_image = mp.Image.create_from_file(image_path)
            detection_result = detector.detect(mp_image)

            if not detection_result.pose_landmarks:
                detector.close()
                return False, "Поза не обнаружена на изображении"

            # Сохраняем визуализацию
            self._save_pose_visualization(image_path, detection_result, is_front_view)

            # Получаем 2D координаты (используем только x, y, z игнорируем)
            # MediaPipe индексы: 0=нос, 11=левое плечо, 12=правое плечо, 13=левый локоть,
            # 14=правый локоть, 15=левое запястье, 16=правое запястье,
            # 23=левое бедро, 24=правое бедро, 25=левое колено, 26=правое колено,
            # 27=левая лодыжка, 28=правая лодыжка
            key_point_indices = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
            points_2d = []

            for landmark_idx in key_point_indices:
                if landmark_idx < len(detection_result.pose_landmarks[0]):
                    landmark = detection_result.pose_landmarks[0][landmark_idx]
                    # Берем только x, y. Игнорируем z.
                    x, y = landmark.x, landmark.y
                    # Нормализуем 2D координаты (X, Y) в диапазон [-1, 1]
                    norm_x = (x - 0.5) * 2.0  # -1.0 до 1.0
                    norm_y = (0.5 - y) * 2.0  # -1.0 до 1.0 (инвертируем Y)

                    if is_front_view:
                        # Для фронтального вида:
                        # - X фото -> X Blender (влево/вправо)
                        # - Y фото -> Z Blender (вверх/вниз)
                        # - Y Blender = 0 (нет глубины)
                        point = Vector((norm_x * 0.5, 0.0, norm_y * 0.5))
                    else:
                        # Для бокового вида:
                        # - X фото -> Y Blender (глубина вперед/назад)
                        # - Y фото -> Z Blender (вверх/вниз)
                        # - X Blender = 0 (нет бокового смещения)
                        point = Vector((0.0, norm_x * 0.5, norm_y * 0.5))

                    points_2d.append(point)
                else:
                    points_2d.append(Vector((0, 0, 0)))

            detector.close()

            print(f"\n=== ОТЛАДКА: Координаты точек ({'Фронтальный' if is_front_view else 'Боковой'} вид) ===")
            point_names = ['Нос', 'Левое_плечо', 'Правое_плечо', 'Левый_локоть', 'Правый_локоть',
                           'Левое_запястье', 'Правое_запястье', 'Левое_бедро', 'Правое_бедро',
                           'Левое_колено', 'Правое_колено', 'Левая_лодыжка', 'Правая_лодыжка']
            for i, (point, name) in enumerate(zip(points_2d, point_names)):
                print(f"  {i:2d} {name:15s}: X={point.x:6.3f}, Y={point.y:6.3f}, Z={point.z:6.3f}")
            print("=" * 60)

            # Вычисляем и применяем позу на основе 2D точек
            success = self._calculate_2d_pose_angles(armature, points_2d, is_front_view)

            if not success:
                return False, "Не удалось вычислить позу по 2D точкам"

            return True, "Поза успешно применена (2D метод, глубина игнорируется)"

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Ошибка в 2D методе: {error_details}")
            return False, f"Ошибка: {str(e)}"

    def _calculate_2d_pose_angles(self, armature, points_2d, is_front_view):
        """Вычисляет углы для костей на основе 2D точек."""
        try:
            # Словарь для сопоставления индексов points_2d с именами костей
            # Индексы points_2d: 0=нос, 1=левое плечо, 2=правое плечо, 3=левый локоть,
            # 4=правый локоть, 5=левое запястье, 6=правое запястье,
            # 7=левое бедро, 8=правое бедро, 9=левое колено, 10=правое колено,
            # 11=левая лодыжка, 12=правая лодыжка

            bone_mapping = {
                (1, 3): 'upper_arm.L',  # Левое плечо -> локоть
                (3, 5): 'forearm.L',  # Левый локоть -> запястье
                (2, 4): 'upper_arm.R',  # Правое плечо -> локоть
                (4, 6): 'forearm.R',  # Правый локоть -> запястье
                (7, 9): 'thigh.L',  # Левое бедро -> колено
                (9, 11): 'shin.L',  # Левое колено -> лодыжка
                (8, 10): 'thigh.R',  # Правое бедро -> колено
                (10, 12): 'shin.R',  # Правое колено -> лодыжка
            }

            # Для позвоночника используем среднюю точку между плечами и бедрами
            if len(points_2d) > 8:
                # Средняя точка плеч (индексы 1 и 2)
                shoulder_center = (points_2d[1] + points_2d[2]) * 0.5
                # Средняя точка бедер (индексы 7 и 8)
                hip_center = (points_2d[7] + points_2d[8]) * 0.5

                # Направление позвоночника (от бедер к плечам)
                spine_dir = (shoulder_center - hip_center)
                if spine_dir.length > 0.001:
                    spine_dir = spine_dir.normalized()

                if 'spine' in armature.pose.bones:
                    spine_bone = armature.pose.bones['spine']
                    spine_bone.rotation_mode = 'XYZ'

                    if is_front_view:
                        # Для фронтального вида: наклон вперед/назад (ось X)
                        angle_x = np.arctan2(spine_dir.z, abs(spine_dir.x)) * 0.5
                        spine_bone.rotation_euler.x = angle_x
                    else:
                        # Для бокового вида: наклон вбок (ось Z)
                        angle_z = np.arctan2(spine_dir.z, abs(spine_dir.y)) * 0.5
                        spine_bone.rotation_euler.z = angle_z

            # Применяем углы для конечностей
            for (start_idx, end_idx), bone_name in bone_mapping.items():
                if bone_name not in armature.pose.bones:
                    print(f"⚠️ Кость {bone_name} не найдена в скелете")
                    continue
                if start_idx >= len(points_2d) or end_idx >= len(points_2d):
                    print(f"⚠️ Индексы {start_idx} или {end_idx} вне диапазона (0-{len(points_2d) - 1})")
                    continue

                start_point = points_2d[start_idx]
                end_point = points_2d[end_idx]

                # Вычисляем вектор направления конечности
                direction = (end_point - start_point)
                if direction.length < 0.001:
                    continue
                direction = direction.normalized()

                bone = armature.pose.bones[bone_name]
                bone.rotation_mode = 'XYZ'

                if is_front_view:
                    # Для фронтального вида
                    if 'arm' in bone_name:
                        # Руки: вращение по оси Z для подъема/опускания
                        # Используем arctan2(Z, X) для угла в плоскости XZ
                        angle_z = np.arctan2(direction.z, direction.x) * 1.0
                        # Для правой руки инвертируем угол
                        if 'R' in bone_name:
                            angle_z = -angle_z
                        bone.rotation_euler.z = angle_z
                    elif 'thigh' in bone_name or 'shin' in bone_name:
                        # Ноги: вращение по оси X для движения вперед/назад
                        # Используем arctan2(Z, X) для угла в плоскости XZ
                        angle_x = np.arctan2(direction.z, direction.x) * 1.0
                        bone.rotation_euler.x = angle_x
                else:
                    # Для бокового вида
                    if 'arm' in bone_name:
                        # Руки: вращение по оси Y для движения вперед/назад
                        # Используем arctan2(Z, Y) для угла в плоскости YZ
                        angle_y = np.arctan2(direction.z, direction.y) * 1.0
                        bone.rotation_euler.y = angle_y
                    elif 'thigh' in bone_name or 'shin' in bone_name:
                        # Ноги: вращение по оси X для сгибания
                        # Используем arctan2(Z, Y) для угла в плоскости YZ
                        angle_x = np.arctan2(direction.z, direction.y) * 1.0
                        bone.rotation_euler.x = angle_x

            bpy.context.view_layer.update()
            return True

        except Exception as e:
            print(f"❌ Ошибка при вычислении 2D позы: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _save_pose_visualization(self, image_path, detection_result, is_front_view):
        """Сохраняет фото с отмеченными точками"""
        try:
            import cv2
            from datetime import datetime

            image = cv2.imread(image_path)
            if image is None:
                print("⚠️ Не удалось загрузить изображение для визуализации")
                return

            h, w = image.shape[:2]
            overlay = image.copy()

            # Рисуем точки
            key_point_indices = [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
            for idx in key_point_indices:
                if idx < len(detection_result.pose_landmarks[0]):
                    landmark = detection_result.pose_landmarks[0][idx]
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(overlay, (x, y), 6, (0, 0, 255), -1)

            # Рисуем линии между точками
            connections = [
                (0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 6),
                (1, 7), (2, 8), (7, 9), (8, 10), (9, 11), (10, 12), (7, 8)
            ]

            for i, j in connections:
                if i < len(key_point_indices) and j < len(key_point_indices):
                    idx1 = key_point_indices[i]
                    idx2 = key_point_indices[j]
                    if idx1 < len(detection_result.pose_landmarks[0]) and idx2 < len(
                            detection_result.pose_landmarks[0]):
                        x1 = int(detection_result.pose_landmarks[0][idx1].x * w)
                        y1 = int(detection_result.pose_landmarks[0][idx1].y * h)
                        x2 = int(detection_result.pose_landmarks[0][idx2].x * w)
                        y2 = int(detection_result.pose_landmarks[0][idx2].y * h)
                        cv2.line(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Добавляем текст
            view_type = "FRONT" if is_front_view else "SIDE"
            text = f"MediaPipe Pose - {view_type} View"
            cv2.putText(overlay, text, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

            # Смешиваем
            alpha = 0.6
            result = cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0)

            # Сохраняем
            original_dir = os.path.dirname(image_path)
            original_name = os.path.basename(image_path)
            name_without_ext = os.path.splitext(original_name)[0]

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{name_without_ext}_pose_{timestamp}.png"
            output_path = os.path.join(original_dir, output_filename)

            cv2.imwrite(output_path, result)
            print(f"✅ Фото с скелетом сохранено: {output_path}")

        except Exception as e:
            print(f"⚠️ Ошибка при сохранении визуализации: {e}")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "view_type")

class VIEW3D_OT_reset_skeleton_pose(Operator):
    """Reset skeleton pose to default T-pose"""
    bl_idname = "view3d.reset_skeleton_pose"
    bl_label = "Сбросить позу скелета"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]
        return len(skeletons) > 0 and context.area and context.area.type == 'VIEW_3D'

    def execute(self, context):
        print("\n" + "=" * 60)
        print("🔄 Photo Tool Pro: Сброс позы скелета...")
        print("=" * 60)

        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]

        if not skeletons:
            self.report({'ERROR'}, "Не найден скелет Pose_Skeleton")
            return {'CANCELLED'}

        skeleton = skeletons[0]

        if bpy.context.mode != 'POSE':
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            skeleton.select_set(True)
            bpy.context.view_layer.objects.active = skeleton
            bpy.ops.object.mode_set(mode='POSE')

        try:
            for bone in skeleton.pose.bones:
                bone.rotation_quaternion = Quaternion()
                bone.location = (0, 0, 0)
                bone.scale = (1, 1, 1)

            self.report({'INFO'}, "✅ Поза скелета сброшена")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"❌ Ошибка сброса позы: {str(e)}")
            return {'CANCELLED'}


classes = [
    VIEW3D_OT_create_skeleton,
    VIEW3D_OT_create_skeleton_with_screenshot,
    VIEW3D_OT_edit_skeleton,
    VIEW3D_OT_pose_skeleton,
    VIEW3D_OT_attach_skeleton,
    VIEW3D_OT_clear_skeletons,
    VIEW3D_OT_check_dependencies,
    VIEW3D_OT_apply_pose_from_photo,
    VIEW3D_OT_reset_skeleton_pose
]


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ Зарегистрирован оператор: {cls.__name__}")
        except Exception as e:
            print(f"⚠️ Ошибка регистрации оператора {cls.__name__}: {e}")


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass