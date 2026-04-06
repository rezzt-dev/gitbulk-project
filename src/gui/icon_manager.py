import os
import sys
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray, Qt

def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    return os.path.join(base_path, relative_path)

def get_icon(icon_name: str, color: str = "#EEEEEE", size: int = 16) -> QIcon:
    """
    Loads an SVG from the icons folder, injects a color dynamically, and returns a QIcon.
    """
    icon_path = resource_path(os.path.join("src", "gui", "icons", f"{icon_name}.svg"))
    
    if not os.path.exists(icon_path):
        return QIcon()
        
    with open(icon_path, "r", encoding="utf-8") as f:
        svg_data = f.read()
        
    # Replace common octicon fills
    svg_data = svg_data.replace('fill="currentColor"', f'fill="{color}"')
    if f'fill="{color}"' not in svg_data:
        svg_data = svg_data.replace('<svg', f'<svg fill="{color}"', 1)
        
    renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return QIcon(pixmap)
