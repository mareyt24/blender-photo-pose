"""
Утилиты для создания скелета из ключевых точек
"""

import bpy
import mathutils


def create_skeleton_from_coordinates(coordinates, bone_size=0.05):
    """
    Упрощенная функция создания скелета для лучшего совпадения с моделью
    """
    try:
        # ЕЩЕ БОЛЬШЕ УМЕНЬШАЕМ МАСШТАБ - скелет все еще слишком большой
        SCALE_MULTIPLIER = 5.0  # Было 15.0, теперь 5.0 - еще в 3 раза меньше

        print(f"\n🦴 Создаем упрощенный скелет из {len(coordinates)} точек...")
        print(f"📏 Масштабный коэффициент: {SCALE_MULTIPLIER} (еще в 3 раза меньше)")

        # Проверяем координаты
        if not coordinates or len(coordinates) < 13:
            print("❌ Недостаточно координат для создания скелета")
            return None

        # Применяем масштаб к координатам
        scaled_coords = []
        for coord in coordinates:
            if isinstance(coord, (tuple, list)) and len(coord) == 3:
                scaled_coords.append((
                    coord[0] * SCALE_MULTIPLIER,
                    coord[1] * SCALE_MULTIPLIER,
                    coord[2] * SCALE_MULTIPLIER
                ))
            else:
                scaled_coords.append((0, 0, 0))

        # Определяем точки по индексам MediaPipe
        points = {
            'nose': mathutils.Vector(scaled_coords[0]),           # 0
            'left_shoulder': mathutils.Vector(scaled_coords[1]),  # 11
            'right_shoulder': mathutils.Vector(scaled_coords[2]), # 12
            'left_elbow': mathutils.Vector(scaled_coords[3]),     # 13
            'right_elbow': mathutils.Vector(scaled_coords[4]),    # 14
            'left_wrist': mathutils.Vector(scaled_coords[5]),     # 15
            'right_wrist': mathutils.Vector(scaled_coords[6]),    # 16
            'left_hip': mathutils.Vector(scaled_coords[7]),       # 23
            'right_hip': mathutils.Vector(scaled_coords[8]),      # 24
            'left_knee': mathutils.Vector(scaled_coords[9]),      # 25
            'right_knee': mathutils.Vector(scaled_coords[10]),    # 26
            'left_ankle': mathutils.Vector(scaled_coords[11]),    # 27
            'right_ankle': mathutils.Vector(scaled_coords[12])    # 28
        }

        # 1. Вычисляем центр масс скелета
        # Используем ключевые точки таза и плеч для более точного центра
        pelvis_center = (points['left_hip'] + points['right_hip']) / 2
        shoulders_center = (points['left_shoulder'] + points['right_shoulder']) / 2
        skeleton_center = (pelvis_center + shoulders_center) / 2

        print(f"📍 Центр масс скелета: X={skeleton_center.x:.3f}, Y={skeleton_center.y:.3f}, Z={skeleton_center.z:.3f}")

        # 2. Создаем арматуру в мировом центре (0,0,0)
        bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(0, 0, 0))
        armature = bpy.context.active_object
        armature.name = "Pose_Skeleton"

        # Переходим в режим редактирования
        bpy.ops.object.mode_set(mode='EDIT')

        # Получаем данные арматуры
        armature_data = armature.data

        # Удаляем стандартную кость
        for bone in armature_data.edit_bones:
            armature_data.edit_bones.remove(bone)

        # 3. Смещаем все точки относительно центра масс
        offset_points = {}
        for key, point in points.items():
            offset_points[key] = point - skeleton_center

        # 4. Создаем правильную иерархию

        # Центр таза
        pelvis_center_offset = (offset_points['left_hip'] + offset_points['right_hip']) / 2
        # Центр плеч
        shoulders_center_offset = (offset_points['left_shoulder'] + offset_points['right_shoulder']) / 2

        # 4.1. СОЗДАЕМ КОСТЬ ТАЗА (вниз, к центру между ног)
        # Вычисляем точку между бедрами, но ниже (для направления вниз)
        pelvis_tail = pelvis_center_offset.copy()
        pelvis_tail.z = pelvis_tail.z - 0.05  # Опускаем немного вниз

        pelvis_bone = armature_data.edit_bones.new('pelvis')
        pelvis_bone.head = pelvis_center_offset
        pelvis_bone.tail = pelvis_tail
        pelvis_bone.roll = 0

        # 4.2. КОСТИ НОГ (прикреплены к тазу СНИЗУ)
        # Левое бедро
        thigh_left = armature_data.edit_bones.new('thigh.L')
        thigh_left.head = offset_points['left_hip']
        thigh_left.tail = offset_points['left_knee']
        thigh_left.parent = pelvis_bone
        thigh_left.roll = 0
        thigh_left.use_connect = False  # Не соединяем напрямую

        # Левая голень
        shin_left = armature_data.edit_bones.new('shin.L')
        shin_left.head = offset_points['left_knee']
        shin_left.tail = offset_points['left_ankle']
        shin_left.parent = thigh_left
        shin_left.roll = 0
        shin_left.use_connect = True

        # Правое бедро
        thigh_right = armature_data.edit_bones.new('thigh.R')
        thigh_right.head = offset_points['right_hip']
        thigh_right.tail = offset_points['right_knee']
        thigh_right.parent = pelvis_bone
        thigh_right.roll = 0
        thigh_right.use_connect = False

        # Правая голень
        shin_right = armature_data.edit_bones.new('shin.R')
        shin_right.head = offset_points['right_knee']
        shin_right.tail = offset_points['right_ankle']
        shin_right.parent = thigh_right
        shin_right.roll = 0
        shin_right.use_connect = True

        # 4.3. ПОЗВОНОЧНИК (от таза к плечам)
        spine = armature_data.edit_bones.new('spine')
        spine.head = pelvis_center_offset
        spine.tail = shoulders_center_offset
        spine.parent = pelvis_bone
        spine.roll = 0
        spine.use_connect = True

        # 4.4. КОСТИ РУК
        # Левое плечо
        shoulder_left = armature_data.edit_bones.new('shoulder.L')
        shoulder_left.head = shoulders_center_offset
        shoulder_left.tail = offset_points['left_shoulder']
        shoulder_left.parent = spine
        shoulder_left.roll = 0
        shoulder_left.use_connect = False

        # Левое предплечье
        upper_arm_left = armature_data.edit_bones.new('upper_arm.L')
        upper_arm_left.head = offset_points['left_shoulder']
        upper_arm_left.tail = offset_points['left_elbow']
        upper_arm_left.parent = shoulder_left
        upper_arm_left.roll = 0
        upper_arm_left.use_connect = True

        # Левая кисть
        forearm_left = armature_data.edit_bones.new('forearm.L')
        forearm_left.head = offset_points['left_elbow']
        forearm_left.tail = offset_points['left_wrist']
        forearm_left.parent = upper_arm_left
        forearm_left.roll = 0
        forearm_left.use_connect = True

        # Правое плечо
        shoulder_right = armature_data.edit_bones.new('shoulder.R')
        shoulder_right.head = shoulders_center_offset
        shoulder_right.tail = offset_points['right_shoulder']
        shoulder_right.parent = spine
        shoulder_right.roll = 0
        shoulder_right.use_connect = False

        # Правое предплечье
        upper_arm_right = armature_data.edit_bones.new('upper_arm.R')
        upper_arm_right.head = offset_points['right_shoulder']
        upper_arm_right.tail = offset_points['right_elbow']
        upper_arm_right.parent = shoulder_right
        upper_arm_right.roll = 0
        upper_arm_right.use_connect = True

        # Правая кисть
        forearm_right = armature_data.edit_bones.new('forearm.R')
        forearm_right.head = offset_points['right_elbow']
        forearm_right.tail = offset_points['right_wrist']
        forearm_right.parent = upper_arm_right
        forearm_right.roll = 0
        forearm_right.use_connect = True

        # 4.5. ШЕЯ И ГОЛОВА
        neck = armature_data.edit_bones.new('neck')
        neck.head = shoulders_center_offset
        neck.tail = offset_points['nose']
        neck.parent = spine
        neck.roll = 0
        neck.use_connect = True

        # Возвращаемся в объектный режим
        bpy.ops.object.mode_set(mode='OBJECT')

        # Настраиваем отображение
        armature.show_in_front = True
        armature.data.display_type = 'OCTAHEDRAL'

        # 5. Устанавливаем origin в центр масс
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        empty = bpy.context.active_object
        empty.name = "temp_center"

        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature

        empty.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        bpy.ops.object.select_all(action='DESELECT')
        empty.select_set(True)
        bpy.ops.object.delete()

        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature

        print(f"📍 Скелет установлен в мировом центре: X={armature.location.x:.3f}, Y={armature.location.y:.3f}, Z={armature.location.z:.3f}")

        # Создаем маркер origin для визуализации
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.01, location=(0, 0, 0))
        sphere = bpy.context.active_object
        sphere.name = "Origin_Marker"
        sphere.display_type = 'WIRE'
        sphere.hide_select = True
        sphere.hide_render = True

        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature

        print(f"✅ Создан упрощенный скелет с {len(armature.data.bones)} костями")
        print(f"📐 Иерархия скелета:")
        print(f"  pelvis (таз)")
        print(f"  ├── spine (позвоночник)")
        print(f"  │   ├── shoulder.L (левое плечо)")
        print(f"  │   │   └── upper_arm.L (левое плечо)")
        print(f"  │   │       └── forearm.L (левое предплечье)")
        print(f"  │   ├── shoulder.R (правое плечо)")
        print(f"  │   │   └── upper_arm.R (правое плечо)")
        print(f"  │   │       └── forearm.R (правое предплечье)")
        print(f"  │   └── neck (шея)")
        print(f"  ├── thigh.L (левое бедро)")
        print(f"  │   └── shin.L (левая голень)")
        print(f"  └── thigh.R (правое бедро)")
        print(f"      └── shin.R (правая голень)")

        return armature

    except Exception as e:
        print(f"❌ Ошибка при создании скелета: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def center_skeleton(armature):
    """Центрирует скелет в (0,0,0)"""
    try:
        armature.location = (0, 0, 0)
        print(f"📍 Скелет установлен в (0,0,0)")
    except Exception as e:
        print(f"⚠️ Ошибка центрирования: {e}")