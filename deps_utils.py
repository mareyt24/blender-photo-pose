"""
Утилиты для проверки зависимостей
"""
import sys
import os

# Автоматическая настройка путей для Blender
user_site = os.path.expanduser("~\\AppData\\Roaming\\Python\\Python311\\site-packages")
if user_site not in sys.path:
    sys.path.insert(0, user_site)


def check_deps_quick():
    """Быстрая проверка зависимостей - возвращает список отсутствующих пакетов"""
    missing = []

    try:
        import cv2
    except ImportError:
        missing.append('opencv-python')

    try:
        import mediapipe
    except ImportError:
        missing.append('mediapipe')

    return missing


def check_deps_detailed():
    """Детальная проверка зависимостей - возвращает (отчет, список_отсутствующих)"""
    missing = []
    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append("DEPENDENCY CHECK FOR PHOTO TOOL ADDON")
    report_lines.append("=" * 60)
    report_lines.append("")

    # Проверяем OpenCV
    try:
        import cv2
        report_lines.append("OpenCV (opencv-python): ✅ INSTALLED")
        # Некоторые версии OpenCV не имеют __version__
        if hasattr(cv2, '__version__'):
            report_lines.append(f"  Version: {cv2.__version__}")
        else:
            report_lines.append("  Version: available (no __version__ attribute)")
    except ImportError:
        report_lines.append("OpenCV (opencv-python): ❌ MISSING")
        missing.append('opencv-python')

    report_lines.append("")

    # Проверяем MediaPipe
    try:
        import mediapipe
        report_lines.append("MediaPipe: ✅ INSTALLED")
        report_lines.append(f"  Version: {mediapipe.__version__}")
    except ImportError:
        report_lines.append("MediaPipe: ❌ MISSING")
        missing.append('mediapipe')

    report_lines.append("")
    report_lines.append("=" * 60)

    if not missing:
        report_lines.append("✅ ALL DEPENDENCIES INSTALLED")
    else:
        report_lines.append(f"❌ MISSING: {', '.join(missing)}")
        report_lines.append("")
        report_lines.append("For installation, run in Command Prompt:")
        for package in missing:
            if package == 'opencv-python':
                report_lines.append(f"  pip install {package}")
            elif package == 'mediapipe':
                report_lines.append(f"  pip install {package}==0.10.13")

    report_lines.append("=" * 60)

    return "\n".join(report_lines), missing


def get_installation_guide():
    """Возвращает инструкцию по установке зависимостей"""
    python_exe = sys.executable

    guide = f"""
INSTALLATION GUIDE

Required for addon operation:
1. OpenCV (opencv-python)
2. MediaPipe (mediapipe==0.10.13)

INSTALLATION:

1. Open Command Prompt (CMD) or terminal.

2. Install packages with one of these commands:

   a) Install separately:
      pip install opencv-python
      pip install mediapipe==0.10.13

   b) Install with one command:
      pip install opencv-python mediapipe==0.10.13

3. Restart Blender.

NOTE:
Addon will automatically find libraries in your system.
If installation was successful but addon doesn't see libraries,
try restarting Blender.

CURRENT PYTHON PATH:
   {python_exe}
"""
    return guide


def get_simple_installation_steps():
    """Возвращает краткие шаги установки для UI"""
    return [
        "1. Open Command Prompt (CMD)",
        "2. Run commands:",
        "   pip install opencv-python",
        "   pip install mediapipe==0.10.13",
        "3. Restart Blender"
    ]