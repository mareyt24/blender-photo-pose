"""
Операторы для аддона Photo Tool Pro
"""

import os
import bpy  # Импортируем bpy на верхнем уровне
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty


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

        # Если уже в режиме редактирования, выходим
        if context.mode == 'EDIT_ARMATURE':
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'INFO'}, "Переключено в Object Mode")
        else:
            # Выбираем скелет
            bpy.ops.object.select_all(action='DESELECT')
            skeleton.select_set(True)
            context.view_layer.objects.active = skeleton

            # Переходим в режим редактирования
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

        # Если уже в режиме позы, выходим
        if context.mode == 'POSE':
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'INFO'}, "Переключено в Object Mode")
        else:
            # Выбираем скелет
            bpy.ops.object.select_all(action='DESELECT')
            skeleton.select_set(True)
            context.view_layer.objects.active = skeleton

            # Переходим в режим позы
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

    # Свойство для пути к файлу
    filepath: StringProperty(
        name="Путь к файлу",
        description="Путь к файлу фотографии",
        maxlen=1024,
        default=""
    )

    # Свойство для выбора вида фото
    view_type: EnumProperty(
        name="Вид фото",
        description="Выберите вид фотографии",
        items=[
            ('FRONT', 'Фронтальный вид', 'Фронтальный вид позы'),
            ('SIDE', 'Боковой вид', 'Боковой вид позы'),
        ],
        default='FRONT'
    )

    # Фильтр файлов
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
        # Требуется скелет и быть в режиме POSE или OBJECT
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

        # Автоматически переключаемся в режим POSE если нужно
        if context.mode != 'POSE':
            # Выбираем скелет
            bpy.ops.object.select_all(action='DESELECT')
            skeleton.select_set(True)
            context.view_layer.objects.active = skeleton
            # Переходим в режим позы
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

        # Попробуем импортировать pose_fitting, если есть
        try:
            from . import pose_fitting
            # Используем новую функцию из pose_fitting.py
            is_front_view = (self.view_type == 'FRONT')
            success, message = pose_fitting.apply_pose_from_photo_simple(
                self.filepath,
                skeleton,
                is_front_view,
                save_visualization=True
            )
        except ImportError:
            # Если pose_fitting не найден, используем старую функцию
            print("⚠️  Модуль pose_fitting не найден, используем старую версию")
            try:
                from . import pose_from_photo
                is_front_view = (self.view_type == 'FRONT')
                success, message = pose_from_photo.apply_pose_from_photo(
                    self.filepath,
                    skeleton,
                    is_front_view
                )
            except ImportError as e:
                self.report({'ERROR'}, f"Модуль pose_from_photo не найден: {e}")
                return {'CANCELLED'}

        if success:
            self.report({'INFO'}, f"✅ {message}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"❌ {message}")
            return {'CANCELLED'}

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
        from mathutils import Quaternion

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


# Список всех операторов для регистрации
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
    """Регистрация всех операторов"""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ Зарегистрирован оператор: {cls.__name__}")
        except Exception as e:
            print(f"⚠️ Ошибка регистрации оператора {cls.__name__}: {e}")


def unregister():
    """Отмена регистрации всех операторов"""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass