import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont
from .main_window import MainWindow

def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_path, relative_path)

try:
    from persistence import load_config
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from persistence import load_config


def _set_taskbar_icon():
    """
    On Windows, override the process AppUserModelID so the taskbar
    groups and shows OUR icon instead of the Python interpreter's icon.
    Must be called BEFORE QApplication is created.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("rezzt.GitBulk.1")
        except Exception:
            pass


def _resolve_resource(relative_path: str) -> str:
    """Returns the absolute path to a resource, works for dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    # dev: project root is two levels up from this file
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(base, relative_path)


def run_gui():
    """
    Initializes and starts the PySide6 Application.
    """
    _set_taskbar_icon()

<<<<<<< Updated upstream
def run_gui():
    """
    Initializes and starts the PySide6 Application.
    """
    _set_taskbar_icon()

    # ── DPI Handling (MUST be before QApplication)
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    if hasattr(QApplication, 'setHighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    
    # ── Master Font Setup (Clean, Non-Pixelated Strategy)
    font = QFont("JetBrains Mono")
    font.setPointSizeF(10.5) # Points scale better than pixels for high-quality rendering
    font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
    font.setHintingPreference(QFont.PreferNoHinting) # Allow OS ClearType to handle smoothing
    app.setFont(font)

    # ── App icon
    ico_path = _resolve_resource(os.path.join("assets", "gitbulk.ico"))
    svg_path = _resolve_resource(os.path.join("src", "gui", "icons", "gitbulk_icon.svg"))
    icon_path = ico_path if os.path.exists(ico_path) else svg_path
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # ── QSS Theme
    theme_path = _resolve_resource(os.path.join("src", "gui", "theme.qss"))

    if os.path.exists(theme_path):
        with open(theme_path, "r", encoding="utf-8") as f:
            qss_content = f.read()
            # Dynamically fix icon paths
            icons_abs = os.path.dirname(theme_path).replace("\\", "/")
            # Also handle if icons are in a subfolder relative to theme
            icons_dir = os.path.join(icons_abs, "icons").replace("\\", "/")
            qss_content = qss_content.replace("{ICONS_PATH}", icons_dir)
            app.setStyleSheet(qss_content)

    try:
        from .translations import TR, set_language
    except ImportError:
        from translations import TR, set_language

    # ── Load and Apply saved language
    config = load_config()
    saved_lang = config.get("language")
    if saved_lang:
        set_language(saved_lang)

    window = MainWindow()
    window.show()

    # Auto-load last directory
    config = load_config()
    default_dir = config.get("last_directory", os.getcwd())
    if default_dir and os.path.exists(default_dir):
        window.load_directory(default_dir)
    else:
        window.append_log(TR("status_idle_msg"), "#888888")

    return app.exec()
