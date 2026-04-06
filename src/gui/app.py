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


def _resolve_base():
    """Returns the base path for bundled assets (works both dev and PyInstaller)."""
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe — PyInstaller extracts to _MEIPASS
        return sys._MEIPASS
    # Running as script — project root is two levels up from this file
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def run_gui():
    """
    Initializes and starts the PySide6 Application.
    """
    _set_taskbar_icon()

    # ── High Fidelity Typography & DPI Handling
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

    # ── App icon: prefer .ico (native Windows multi-size), fallback to .svg
    base    = _resolve_base()
    ico_path = os.path.join(base, "assets", "gitbulk.ico")
    svg_path = os.path.join(os.path.dirname(__file__), "icons", "gitbulk_icon.svg")
    icon_path = ico_path if os.path.exists(ico_path) else svg_path
    icon_path = resource_path(os.path.join("assets", "gitbulk.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # ── QSS Theme (also resolves for both dev and PyInstaller)
    theme_path = resource_path(os.path.join("gui", "theme.qss"))
    if os.path.exists(theme_path):
        with open(theme_path, "r", encoding="utf-8") as f:
            qss_content = f.read()
            # Dynamically fix icon paths based on whether we are in src/ or frozen
            icons_abs = os.path.join(os.path.dirname(theme_path), "icons").replace("\\", "/")
            qss_content = qss_content.replace("{ICONS_PATH}", icons_abs)
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
