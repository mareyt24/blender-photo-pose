"""
UI панели для аддона Photo Tool Pro
"""

import bpy
from bpy.types import Panel


class VIEW3D_PT_photo_tool_main(Panel):
    """Основная панель Photo Tool Pro"""
    bl_label = "Photo Tool Pro"
    bl_idname = "VIEW3D_PT_photo_tool_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == 'VIEW_3D'

    def draw(self, context):
        layout = self.layout

        # 📊 Заголовок
        box = layout.box()
        box.label(text="🎯 Photo Tool Pro", icon='CAMERA_DATA')
        box.label(text="Версия 3.3.5", icon='INFO')

        # Разделитель
        layout.separator()

        # 🎯 БЛОК 1: Создание скелета
        box = layout.box()
        box.label(text="1. Создание скелета", icon='ARMATURE_DATA')
        box.label(text="Поместите модель в центр", icon='INFO')

        col = box.column(align=True)
        row = col.row(align=True)
        row.operator(
            "view3d.create_skeleton",
            text="Создать скелет",
            icon='BONE_DATA'
        )
        row = col.row(align=True)
        row.operator(
            "view3d.create_skeleton_with_screenshot",
            text="Скелет + скриншоты",
            icon='RENDER_STILL'
        )

        # Разделитель
        layout.separator()

        # ⚙️ БЛОК 2: Режимы редактирования (только если есть скелет)
        skeletons = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj.name.startswith("Pose_Skeleton")
        ]

        if skeletons:
            box = layout.box()
            box.label(text="2. Режимы редактирования", icon='EDITMODE_HLT')

            col = box.column(align=True)
            row = col.row(align=True)
            row.operator(
                "view3d.edit_skeleton",
                text="Редактировать кости (Edit Mode)",
                icon='EDITMODE_HLT'
            )
            row = col.row(align=True)
            row.operator(
                "view3d.pose_skeleton",
                text="Настроить позу (Pose Mode)",
                icon='POSE_HLT'
            )

            # Разделитель
            layout.separator()

            # 🤖 БЛОК 3: Привязка к модели
            box = layout.box()
            box.label(text="3. Привязка к модели", icon='LINKED')
            box.label(text="Выберите меш и скелет", icon='INFO')

            col = box.column(align=True)
            row = col.row(align=True)
            row.operator(
                "view3d.attach_skeleton",
                text="Привязать скелет",
                icon='LINKED'
            )

            # Разделитель
            layout.separator()

            # 📸 БЛОК 4: Выставление позы по фото
            box = layout.box()
            box.label(text="4. Выставление позы", icon='IMAGE_DATA')
            box.label(text="Требуется режим Pose", icon='INFO')

            col = box.column(align=True)
            row = col.row(align=True)
            row.operator(
                "view3d.apply_pose_from_photo",
                text="Загрузить позу из фото",
                icon='IMAGE_DATA'
            )

            row = col.row(align=True)
            row.operator(
                "view3d.reset_skeleton_pose",
                text="Сбросить позу",
                icon='LOOP_BACK'
            )

        # Разделитель
        layout.separator()

        # 🛠️ БЛОК 5: Утилиты (всегда видно)
        box = layout.box()
        box.label(text="🛠️ Утилиты", icon='TOOL_SETTINGS')

        col = box.column(align=True)
        row = col.row(align=True)
        row.operator(
            "view3d.check_dependencies",
            text="Проверить зависимости",
            icon='PREFERENCES'
        )

        row = col.row(align=True)
        row.operator(
            "view3d.clear_skeletons",
            text="Очистить все скелеты",
            icon='TRASH'
        )


# Добавьте эти функции регистрации в конец файла
def register():
    bpy.utils.register_class(VIEW3D_PT_photo_tool_main)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_photo_tool_main)