import os
import json
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QLabel, QPushButton, QTreeView, QHeaderView,
    QAbstractItemView, QSizeGrip, QFileDialog, QInputDialog,
    QMessageBox, QMenu, QSpacerItem, QSizePolicy, QProgressBar,
    QDialog, QComboBox
)
from PySide6.QtCore import Qt, QRect, QRectF, QPointF, QSize, QModelIndex, QTimer
from PySide6.QtGui import QIcon, QPainter, QPen, QColor, QStandardItemModel, QStandardItem, QFont, QFontDatabase
try:
    from .translations import TR, set_language, get_current_language, LANGUAGES
except ImportError:
    # Fallback if not inside package
    from translations import TR, set_language, get_current_language, LANGUAGES

try:
    from persistence import load_config, save_config
except ImportError:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from persistence import load_config, save_config

try:
    from .icon_manager import get_icon
    from .workers import ScannerWorker, OperationWorker
except ImportError:
    from gui.icon_manager import get_icon
    from gui.workers import ScannerWorker, OperationWorker


def _safe_get_metadata(repo_path):
    try:
        from model.git_ops import get_repo_metadata
        return get_repo_metadata(repo_path)
    except ImportError:
        import sys
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from model.git_ops import get_repo_metadata
        return get_repo_metadata(repo_path)


# ── Traffic Light Button Group (macOS style) ──────────────────────────────────

class TrafficLightGroup(QWidget):
    """
    Draws the three macOS-style circles as a unified widget.
    On hover any button, ALL three show their icons simultaneously.
    """
    close_clicked    = __import__('PySide6.QtCore', fromlist=['Signal']).Signal()
    minimize_clicked = __import__('PySide6.QtCore', fromlist=['Signal']).Signal()
    maximize_clicked = __import__('PySide6.QtCore', fromlist=['Signal']).Signal()

    # Circle config: (base_color, hover_color, symbol)
    _CIRCLES = [
        ("#FEBC2E", "#BF8E22", "minimize"),  # Yellow — Minimize
        ("#28C840", "#1E9730", "maximize"),  # Green  — Maximize/Restore
        ("#FF5F57", "#BF4440", "close"),     # Red    — Close
    ]

    _D  = 12    # circle diameter
    _GAP = 8    # gap between circles
    _PAD_X = 16 # left padding

    def __init__(self, parent=None):
        super().__init__(parent)
        n = len(self._CIRCLES)
        total_w = self._PAD_X + n * self._D + (n - 1) * self._GAP + self._PAD_X
        self.setFixedSize(total_w, 36)
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)
        self._hovered_idx = -1   # which circle has the cursor (-1 = none)
        self._pressed_idx = -1   # which circle is being pressed

    # ── helpers ──────────────────────────────────────────────────────────────

    def _circle_rect(self, idx):
        """Returns the QRect of circle at index idx."""
        x = self._PAD_X + idx * (self._D + self._GAP)
        y = (self.height() - self._D) // 2
        return QRect(x, y, self._D, self._D)

    def _idx_at(self, pos):
        """Returns the index of the circle under pos, or -1."""
        for i in range(len(self._CIRCLES)):
            if self._circle_rect(i).contains(pos):
                return i
        return -1

    # ── events ────────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self._hovered_idx = -1
        self._pressed_idx = -1
        self.update()

    def mouseMoveEvent(self, event):
        idx = self._idx_at(event.pos())
        if idx != self._hovered_idx:
            self._hovered_idx = idx
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed_idx = self._idx_at(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            idx = self._idx_at(event.pos())
            if idx == self._pressed_idx:
                if idx == 0: self.minimize_clicked.emit()
                elif idx == 1: self.maximize_clicked.emit()
                elif idx == 2: self.close_clicked.emit()
            self._pressed_idx = -1
            self.update()

    # ── painting ─────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        for i, (base, pressed_color, symbol) in enumerate(self._CIRCLES):
            # Use QRectF for sub-pixel ellipse accuracy
            x = float(self._PAD_X + i * (self._D + self._GAP))
            y = (self.height() - self._D) / 2.0
            rect_f = QRectF(x, y, float(self._D), float(self._D))
            cx = x + self._D / 2.0
            cy = y + self._D / 2.0

            # Fill circle
            if self._pressed_idx == i:
                painter.setBrush(QColor(pressed_color))
            else:
                painter.setBrush(QColor(base))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect_f)

            # Symbols — only on the circle currently under cursor
            if self._hovered_idx == i:
                pen = QPen(QColor(0, 0, 0, 110))
                pen.setWidthF(1.3)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)

                # All symbols fit inside a ±3.2 radius from center (53% of circle)
                s = 3.2

                if symbol == "close":
                    # X: two diagonals through exact center
                    painter.drawLine(QPointF(cx - s, cy - s), QPointF(cx + s, cy + s))
                    painter.drawLine(QPointF(cx + s, cy - s), QPointF(cx - s, cy + s))

                elif symbol == "minimize":
                    # Horizontal dash through exact center
                    painter.drawLine(QPointF(cx - s, cy), QPointF(cx + s, cy))

                elif symbol == "maximize":
                    # macOS fullscreen arrows: two small diagonal arrows
                    # Top-right arrow: ↗
                    t = s * 0.85
                    painter.drawLine(QPointF(cx - t, cy + t), QPointF(cx + t, cy - t))
                    # Bottom-left corner marks
                    painter.drawLine(QPointF(cx - t, cy + t), QPointF(cx - t, cy))
                    painter.drawLine(QPointF(cx - t, cy + t), QPointF(cx, cy + t))

        painter.end()


# ── Title Bar ──────────────────────────────────────────────────────────────────

class TitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(36)
        self.setObjectName("titleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App icon
        self.icon_label = QLabel()
        self.icon_label.setStyleSheet("padding-left: 12px;")
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "gitbulk_icon.svg")
        if os.path.exists(icon_path):
            self.icon_label.setPixmap(QIcon(icon_path).pixmap(16, 16))
        layout.addWidget(self.icon_label)

        # App name
        self.title_label = QLabel("GitBulk")
        self.title_label.setObjectName("titleBarText")
        self.title_label.setStyleSheet("padding-left: 6px; font-family: 'JetBrains Mono';")
        layout.addWidget(self.title_label)

        # Separator dot
        sep_dot = QLabel("·")
        sep_dot.setObjectName("titleBarSubtext")
        sep_dot.setStyleSheet("padding: 0px 5px; color: #383838; font-family: 'JetBrains Mono';")
        layout.addWidget(sep_dot)

        # Workspace subtitle (updated dynamically)
        self.subtitle_label = QLabel(TR("status_no_workspace"))
        self.subtitle_label.setObjectName("titleBarSubtext")
        self.subtitle_label.setStyleSheet("font-family: 'JetBrains Mono';")
        layout.addWidget(self.subtitle_label)

        layout.addStretch()

        # ── Traffic lights (RIGHT side)
        self.traffic = TrafficLightGroup(self)
        self.traffic.close_clicked.connect(self.close_window)
        self.traffic.minimize_clicked.connect(self.minimize_window)
        self.traffic.maximize_clicked.connect(self.maximize_window)
        layout.addWidget(self.traffic)

        self.start_pos = None


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPos() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.start_pos:
            self.parent_window.move(event.globalPos() - self.start_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.maximize_window()

    def minimize_window(self):
        self.parent_window.showMinimized()

    def maximize_window(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

    def close_window(self):
        self.parent_window.close()


# ── Custom Tree Items ──────────────────────────────────────────────────────────

class RepoLeafItem(QStandardItem):
    def __init__(self, text):
        super().__init__(text)

    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class GroupFolderItem(QStandardItem):
    def __init__(self, text):
        super().__init__(text)

    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


# ── Move To Group Dialog ──────────────────────────────────────────────────

class MoveToDialog(QDialog):
    def __init__(self, current_groups, parent=None):
        super().__init__(parent)
        self.setWindowTitle(TR("dlg_move_title"))
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl = QLabel(TR("dlg_move_label"))
        lbl.setStyleSheet("color: #888888; font-family: 'JetBrains Mono'; font-weight: 500; font-size: 11px;")
        layout.addWidget(lbl)

        self.combo = QComboBox()
        self.combo.setStyleSheet("""
            QComboBox {
                background: #2D2D2D;
                color: #EEEEEE;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 8px;
                font-family: 'JetBrains Mono';
            }
            QComboBox::drop-down { border-left: 1px solid #444444; }
            QAbstractItemView { background: #1E1E1E; color: #EEEEEE; selection-background-color: #3D3D3D; font-family: 'JetBrains Mono'; }
        """)
        
        # Populate with groups
        self.combo.addItem(TR("dlg_move_root"), [])
        for label, path in current_groups:
            self.combo.addItem(label, path)
            
        layout.addWidget(self.combo)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton(TR("dlg_move_cancel"))
        btn_move = QPushButton(TR("dlg_move_btn"))
        btn_move.setStyleSheet("background: #4CAF50; color: white; font-family: 'JetBrains Mono'; font-weight: 500; padding: 8px 20px; border-radius: 0px;")
        
        btn_cancel.clicked.connect(self.reject)
        btn_move.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_move)
        layout.addLayout(btn_layout)

    def get_selected_path(self):
        return self.combo.currentData()

# ── Tree View Custom Components ───────────────────────────────────────────────

class WorkspaceTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(False)  # Disabled in favor of Move To menu
        self.setDragEnabled(False)
        self.setDropIndicatorShown(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setIndentation(24)
        self.setMouseTracking(True)
        self.setUniformRowHeights(True)
        
        # Style
        self.setStyleSheet("""
            QTreeView {
                background-color: #121212;
                border: none;
                color: #BBBBBB;
                font-family: 'JetBrains Mono';
                font-size: 12px;
                letter-spacing: 0.3px;
                outline: none;
            }
            QTreeView::item {
                padding: 5px 10px;
                border-bottom: 1px solid #1E1E1E;
            }
            QTreeView::item:hover {
                background-color: #1A1A1A;
            }
            QTreeView::item:selected {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border-left: 3px solid #4CAF50;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                image: none;
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                image: none;
            }
        """)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            # Handle group deletion from keyboard
            pass
        super().keyPressEvent(event)


# ── Sidebar Section Helper ────────────────────────────────────────────────────

def make_section_label(text_key):
    lbl = QLabel(TR(text_key).upper())
    lbl.setObjectName("sectionLabel")
    lbl.setStyleSheet("color: #555555; font-family: 'JetBrains Mono'; font-size: 10px; font-weight: 700; letter-spacing: 1.2px; padding: 0px 2px;")
    return lbl

def make_separator():
    sep = QFrame()
    sep.setObjectName("sidebarSeparator")
    sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet("background-color: #1E1E1E; max-height: 1px;")
    return sep

# ── Main Window ────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(TR("window_title"))
        self.resize(1400, 850)

        icon_path = os.path.join(os.path.dirname(__file__), "icons", "gitbulk_icon.svg")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.target_dir = ""
        self.found_repos = []
        self.workspace_data = []  # Single Source of Truth for hierarchy
        self.scanner_worker = None
        self.operation_worker = None
        self._op_start_time = None
        self._processed_count = 0
        self._pending_import_layout = None  # set by import_workspace(), consumed by on_scan_finished()

        # Master container
        self.master_widget = QWidget()
        self.master_widget.setObjectName("masterWidget")
        self.setCentralWidget(self.master_widget)

        root_layout = QVBoxLayout(self.master_widget)
        root_layout.setContentsMargins(1, 1, 1, 1)
        root_layout.setSpacing(0)

        # ── Title Bar
        self.title_bar = TitleBar(self)
        root_layout.addWidget(self.title_bar)

        # ── Body (Sidebar + Content)
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        root_layout.addWidget(body, 1)

        # ── Build sidebar
        self._build_sidebar(body_layout)

        # ── Build main content area
        self._build_content(body_layout)

        # ── Status Bar
        self._build_status_bar(root_layout)

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self, parent_layout):
        sidebar = QFrame()
        sidebar.setObjectName("sidePanel")
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("QFrame#sidePanel { font-family: 'JetBrains Mono'; }")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(0)

        # ── WORKSPACE section
        layout.addWidget(self._section_header("sidebar_actions"))

        self.btn_load_dir = QPushButton(f"  {TR('btn_scan')}")
        self.btn_load_dir.setIcon(get_icon("folder", "#111111"))
        self.btn_load_dir.setObjectName("primaryAction")
        self.btn_load_dir.setStyleSheet(
            "QPushButton#primaryAction { font-family: 'JetBrains Mono'; text-align: left; padding: 8px 16px; margin: 8px 12px 4px 12px; border-radius: 0px; font-weight: bold; }"
            "QPushButton#primaryAction:hover { background-color: #F0F0F0; }"
        )
        self.btn_load_dir.clicked.connect(self.prompt_directory_selection)
        layout.addWidget(self.btn_load_dir)

        self.lbl_workspace_path = QLabel(TR("status_no_dir_selected"))
        self.lbl_workspace_path.setObjectName("workspaceSubtitle")
        self.lbl_workspace_path.setStyleSheet("color: #555555; font-family: 'JetBrains Mono'; font-size: 11px; padding: 0px 16px 8px 16px;")
        self.lbl_workspace_path.setWordWrap(True)
        layout.addWidget(self.lbl_workspace_path)

        self.btn_new_group = QPushButton(f"  {TR('btn_group')}")
        self.btn_new_group.setIcon(get_icon("folder", "#888888"))
        self.btn_new_group.setStyleSheet("QPushButton { font-family: 'JetBrains Mono'; padding: 6px 16px; text-align: left; }")
        self.btn_new_group.clicked.connect(self.prompt_create_group)
        layout.addWidget(self.btn_new_group)

        layout.addSpacing(8)
        layout.addWidget(self._divider())

        # ── GIT OPERATIONS section
        layout.addWidget(self._section_header("sidebar_hierarchy"))

        ops = [
            ("btn_pull",    TR("btn_pull"),          "sync",    "#888888", "pull"),
            ("btn_push",    TR("btn_push"),          "sync",    "#888888", "push"),
            ("btn_sync",    TR("btn_sync"),          "sync",    "#888888", "sync"),
        ]
        for attr, label, icon, color, op in ops:
            btn = self._sidebar_btn(f"  {label}", icon, color)
            btn.clicked.connect(lambda checked=False, o=op: self.start_operation(o))
            setattr(self, attr, btn)
            layout.addWidget(btn)

        layout.addSpacing(8)
        layout.addWidget(self._divider())

        # ── ADVANCED TOOLS section
        layout.addWidget(self._section_header("sidebar_advanced"))

        self.btn_export = self._sidebar_btn(f"  {TR('btn_export')}", "export", "#888888")
        self.btn_export.clicked.connect(self.export_workspace)
        layout.addWidget(self.btn_export)

        self.btn_import = self._sidebar_btn(f"  {TR('btn_import')}", "restore", "#888888")
        self.btn_import.clicked.connect(self.import_workspace)
        layout.addWidget(self.btn_import)

        layout.addSpacing(8)
        layout.addWidget(self._divider())

        # ── DANGER section
        layout.addWidget(self._section_header("sidebar_danger"))

        self.btn_clean = QPushButton(f"  {TR('btn_clean')}")
        self.btn_clean.setIcon(get_icon("clean", "#F85149"))
        self.btn_clean.setObjectName("dangerAction")
        self.btn_clean.setStyleSheet(
            "QPushButton { font-family: 'JetBrains Mono'; text-align: left; padding: 7px 16px; color: #F85149; border: 1px solid transparent; }"
            "QPushButton:hover { background-color: #2D1414; border-color: #4A1818; color: #FF6B6B; }"
        )
        self.btn_clean.clicked.connect(lambda: self.start_operation("clean"))
        layout.addWidget(self.btn_clean)

        layout.addStretch()
        layout.addWidget(self._divider())

        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(16, 0, 16, 0)
        
        self.footer_lbl = QLabel(TR("footer_version"))
        self.footer_lbl.setStyleSheet("color: #383838; font-family: 'JetBrains Mono'; font-size: 10px;")
        footer_layout.addWidget(self.footer_lbl)
        
        footer_layout.addStretch()
        
        # ── Language Selector
        self.combo_lang = QComboBox()
        self.combo_lang.setFixedWidth(120)
        self.combo_lang.setStyleSheet("""
            QComboBox { 
                background: #1A1A1A; color: #888888; border: 1px solid #262626; 
                font-family: 'JetBrains Mono'; font-size: 10px; padding: 2px 5px;
            }
            QComboBox::drop-down { border: none; }
            QAbstractItemView { background: #161616; color: #888888; selection-background-color: #2D2D2D; }
        """)
        
        # Populate languages
        for lang_id, data in LANGUAGES.items():
            self.combo_lang.addItem(data["name"], lang_id)
            
        # Set current
        idx = self.combo_lang.findData(get_current_language())
        if idx >= 0: self.combo_lang.setCurrentIndex(idx)
        
        self.combo_lang.currentIndexChanged.connect(self._on_language_changed)
        footer_layout.addWidget(self.combo_lang)
        
        layout.addLayout(footer_layout)

        parent_layout.addWidget(sidebar)

    def _on_language_changed(self, index):
        lang_id = self.combo_lang.itemData(index)
        set_language(lang_id)
        
        # Save to config
        config = load_config()
        config["language"] = lang_id
        save_config(config)
        
        self.retranslate_ui()

    def retranslate_ui(self):
        """Refreshes all UI strings without restarting."""
        self.setWindowTitle(TR("window_title"))
        self.title_bar.subtitle_label.setText(TR("status_no_workspace") if not self.target_dir else os.path.basename(self.target_dir))
        
        # Sidebar
        # Headers are recreated or updated if we keep refs, but let's update buttons
        self.btn_load_dir.setText(f"  {TR('btn_scan')}")
        self.btn_new_group.setText(f"  {TR('btn_group')}")
        self.btn_pull.setText(f"  {TR('btn_pull')}")
        self.btn_push.setText(f"  {TR('btn_push')}")
        self.btn_sync.setText(f"  {TR('btn_sync')}")
        self.btn_import.setText(f"  {TR('btn_import')}")
        self.btn_export.setText(f"  {TR('btn_export')}")
        self.btn_clean.setText(f"  {TR('btn_clean')}")
        
        if not self.target_dir:
            self.lbl_workspace_path.setText(TR("status_no_dir_selected"))
        
        self.footer_lbl.setText(TR("footer_version"))
        
        # Hierarchy Headers
        self.repo_model.setHorizontalHeaderLabels([
            TR("col_name"), TR("col_branch"), TR("col_status"), TR("col_output")
        ])
        
        # Status Bar
        self.lbl_workspace_title.setText(TR("status_idle") if not self.target_dir else os.path.basename(self.target_dir))
        if self.found_repos:
             self.lbl_repo_count.setText(f"{len(self.found_repos)} {TR('lbl_repos')}")
        
        self.btn_collapse_all.setText(TR("btn_collapse"))
        self.btn_expand_all.setText(TR("btn_expand"))
        
        # Force a re-render of the tree for things like 'Awaiting operation'
        open_state = self._get_expansion_state()
        self._rebuild_tree()
        self._apply_expansion_state(open_state)

    def _sidebar_btn(self, label, icon_name, icon_color):
        btn = QPushButton(label)
        icon = get_icon(icon_name, icon_color)
        if not icon.isNull():
            btn.setIcon(icon)
        btn.setStyleSheet("QPushButton { font-family: 'JetBrains Mono'; text-align: left; padding: 7px 16px; }")
        return btn

    def _section_header(self, text_key):
        lbl = QLabel(TR(text_key).upper())
        lbl.setStyleSheet(
            "color: #484848; font-family: 'JetBrains Mono'; font-size: 9px; font-weight: 700; "
            "letter-spacing: 1.4px; padding: 10px 16px 4px 16px;"
        )
        return lbl

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #1E1E1E; max-height: 1px; margin: 0px 0px;")
        return line

    # ── Content Area ──────────────────────────────────────────────────────────

    def _build_content(self, parent_layout):
        center = QFrame()
        center.setObjectName("centerPanel")
        layout = QVBoxLayout(center)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Workspace header bar
        header_bar = QFrame()
        header_bar.setStyleSheet("background-color: #131313; border-bottom: 1px solid #1E1E1E;")
        header_bar.setFixedHeight(44)
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(8)

        self.lbl_workspace_title = QLabel(TR("status_idle"))
        self.lbl_workspace_title.setObjectName("workspaceTitle")
        self.lbl_workspace_title.setStyleSheet("font-family: 'JetBrains Mono'; font-size: 14px; font-weight: 500; color: #EEEEEE; letter-spacing: 0.5px;")
        header_layout.addWidget(self.lbl_workspace_title)

        self.lbl_repo_count = QLabel("")
        self.lbl_repo_count.setObjectName("repoBadge")
        self.lbl_repo_count.setStyleSheet(
            "color: #E2E2E2; font-size: 11px; font-weight: 600; "
            "background-color: #222222; padding: 2px 8px; margin-left: 4px;"
        )
        self.lbl_repo_count.hide()
        header_layout.addWidget(self.lbl_repo_count)

        header_layout.addStretch()

        # Collapse / Expand all
        self.btn_collapse_all = QPushButton(TR("btn_collapse"))
        self.btn_collapse_all.setStyleSheet(
            "QPushButton { color: #555555; font-family: 'JetBrains Mono'; font-size: 11px; padding: 4px 10px; border: 1px solid #1E1E1E; }"
            "QPushButton:hover { color: #EEEEEE; border-color: #262626; background: #181818; }"
        )
        self.btn_collapse_all.clicked.connect(lambda: self.tree.collapseAll())
        header_layout.addWidget(self.btn_collapse_all)

        self.btn_expand_all = QPushButton(TR("btn_expand"))
        self.btn_expand_all.setStyleSheet(
            "QPushButton { color: #555555; font-family: 'JetBrains Mono'; font-size: 11px; padding: 4px 10px; border: 1px solid #1E1E1E; }"
            "QPushButton:hover { color: #EEEEEE; border-color: #262626; background: #181818; }"
        )
        self.btn_expand_all.clicked.connect(lambda: self.tree.expandAll())
        header_layout.addWidget(self.btn_expand_all)

        layout.addWidget(header_bar)

        # ── Tree View
        self.repo_model = QStandardItemModel()
        self.repo_model.setHorizontalHeaderLabels([
            TR("col_name"), TR("col_branch"), TR("col_status"), TR("col_output")
        ])

        self.tree = WorkspaceTreeView()
        self.tree.setObjectName("workspaceTree")
        self.tree.setModel(self.repo_model)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tree.setAlternatingRowColors(False)
        self.tree.setFocusPolicy(Qt.StrongFocus)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.setItemsExpandable(True)
        self.tree.setAnimated(True)
        self.tree.setRootIsDecorated(True)  # Enable expansion handles for hierarchy
        self.tree.setIndentation(24)         # Clear hierarchy differentiation
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setUniformRowHeights(True)

        # Drag & Drop — DISABLED intentionally.
        # All reordering is done exclusively via the context-menu Move To action
        # + _rebuild_tree(), which is the only safe atomic renderer.
        # Qt's native D&D on QStandardItemModel is destructive: it copies only
        # column-0 items and loses all sibling columns (branch/status/output)
        # as well as Qt.UserRole data (REPO/GROUP type and path).
        self.tree.setDragEnabled(False)
        self.tree.setAcceptDrops(False)
        self.tree.setDropIndicatorShown(False)
        self.tree.setDragDropMode(QAbstractItemView.NoDragDrop)

        # Column sizing
        header = self.tree.header()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setMinimumSectionSize(80)

        layout.addWidget(self.tree)

        parent_layout.addWidget(center, 1)

        # Signals
        self.repo_model.rowsMoved.connect(self._schedule_save)
        self.repo_model.rowsInserted.connect(self._schedule_save)
        self.repo_model.rowsRemoved.connect(self._schedule_save)
        self.tree.expanded.connect(self._on_item_expanded)
        self.tree.collapsed.connect(self._on_item_collapsed)
        self.tree.clicked.connect(self._on_tree_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)

    # ── Status Bar ────────────────────────────────────────────────────────────

    def _build_status_bar(self, parent_layout):
        # Outer wrapper stacks the progress bar ON TOP of the status content
        wrapper = QFrame()
        wrapper.setObjectName("statusBar")
        wrapper.setFixedHeight(28)
        wrapper.setStyleSheet(
            "QFrame#statusBar { background-color: #0F0F0F; border-top: 1px solid #1E1E1E; }"
        )
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)

        # ── Progress strip (2px, at the very top of the bar)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #181818;
                border-radius: 0px;
            }
            QProgressBar::chunk {
                background-color: #E2E2E2;
                border-radius: 0px;
            }
        """)
        self.progress_bar.hide()
        wrapper_layout.addWidget(self.progress_bar)

        # ── Content row
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        bar_layout = QHBoxLayout(content)
        bar_layout.setContentsMargins(0, 0, 12, 0)
        bar_layout.setSpacing(0)

        # Accent left border
        accent = QFrame()
        accent.setFixedWidth(3)
        accent.setFixedHeight(28)
        accent.setStyleSheet("background-color: #E2E2E2;")
        bar_layout.addWidget(accent)

        self.lbl_status_op = QLabel(f"  {TR('status_idle')}")
        self.lbl_status_op.setStyleSheet("color: #484848; font-family: 'JetBrains Mono'; font-size: 11px; padding: 0px 12px;")
        bar_layout.addWidget(self.lbl_status_op)

        self.lbl_status_dot = QLabel("·")
        self.lbl_status_dot.setStyleSheet("color: #1E1E1E; font-size: 11px;")
        self.lbl_status_dot.hide()
        bar_layout.addWidget(self.lbl_status_dot)

        self.lbl_status_detail = QLabel("")
        self.lbl_status_detail.setStyleSheet("color: #484848; font-family: 'JetBrains Mono'; font-size: 11px; padding: 0px 6px;")
        bar_layout.addWidget(self.lbl_status_detail)

        bar_layout.addStretch()

        self.lbl_status_time = QLabel("")
        self.lbl_status_time.setStyleSheet("color: #383838; font-family: 'JetBrains Mono'; font-size: 11px;")
        bar_layout.addWidget(self.lbl_status_time)

        wrapper_layout.addWidget(content, 1)
        parent_layout.addWidget(wrapper)

    def _set_status(self, op_text, detail="", time_str="", color="#484848"):
        self.lbl_status_op.setText(f"  {op_text}")
        self.lbl_status_op.setStyleSheet(
            f"color: {color}; font-family: 'JetBrains Mono'; font-size: 11px; padding: 0px 12px; "
            + ("font-weight: 600;" if color != "#484848" else "")
        )
        if detail:
            self.lbl_status_detail.setText(detail)
            self.lbl_status_dot.show()
        else:
            self.lbl_status_detail.setText("")
            self.lbl_status_dot.hide()
        self.lbl_status_time.setText(time_str)

    # ── Directory and Scanning ────────────────────────────────────────────────

    def prompt_directory_selection(self):
        dir_path = QFileDialog.getExistingDirectory(self, TR("dlg_move_title"))
        if dir_path:
            self.load_directory(dir_path)

    def load_directory(self, dir_path):
        self.target_dir = dir_path
        base = os.path.basename(dir_path)

        self.title_bar.subtitle_label.setText(base)
        self.lbl_workspace_title.setText(base)
        self.lbl_workspace_path.setText(dir_path)
        self.lbl_repo_count.hide()

        self._set_status(TR("status_scanning"), dir_path, "", "#E2E2E2")
        self.repo_model.removeRows(0, self.repo_model.rowCount())

        self.scanner_worker = ScannerWorker(self.target_dir)
        self.scanner_worker.finished.connect(self.on_scan_finished)
        self.scanner_worker.start()

    def on_scan_finished(self, repos):
        self.found_repos = repos
        self.lbl_repo_count.setText(f"{len(repos)} {TR('lbl_repos')}")
        self.lbl_repo_count.show()

        # ── Synchronize with Data Model
        # Case A: Imported layout exists
        if self._pending_import_layout is not None:
            self.workspace_data = self._pending_import_layout
            self._pending_import_layout = None
        # Case B: Load from local persistent cache
        else:
            self.workspace_data = self._load_virtual_layout() or []

        # ── Global Renderer
        open_state = self._get_expansion_state()
        self._rebuild_tree()
        self._apply_expansion_state(open_state)
        self._set_status(TR("status_loaded"), TR("status_repos_found", count=len(repos)), "", "#4CAF50")

    # ── Ordering Helpers (Invariant: groups before loose repos) ──────────────

    def _sort_nodes(self, nodes):
        """
        Sorts a node list IN-PLACE so that group nodes always come before
        repo nodes. Within each category the original relative order is kept
        (stable sort). Returns the same list for convenience.
        """
        nodes.sort(key=lambda n: (0 if n.get("is_group") else 1))
        return nodes

    def _sort_workspace_data(self, data):
        """
        Recursively sorts every level of the workspace data so that the
        invariant (groups before repos) holds throughout the full hierarchy.
        Operates in-place.
        """
        self._sort_nodes(data)
        for node in data:
            if node.get("is_group") and "children" in node:
                self._sort_workspace_data(node["children"])

    def _insert_sorted(self, container, node):
        """
        Inserts `node` into `container` while keeping the groups-first
        invariant: groups go after the last existing group (or at index 0
        when there are none), repos go at the very end.
        """
        if node.get("is_group"):
            # Find the insertion point: right after the last group
            insert_at = 0
            for i, n in enumerate(container):
                if n.get("is_group"):
                    insert_at = i + 1
            container.insert(insert_at, node)
        else:
            # Repos always go at the end
            container.append(node)

    # ── Master Renderer ───────────────────────────────────────────────────────

    def _rebuild_tree(self):
        """
        MASTER RENDERER: Sorts workspace_data to enforce the groups-first
        invariant, then rebuilds the QStandardItemModel from scratch.
        All visual state (colours, fonts, icons, column data) is re-created
        here so that no stale Qt items can leak from previous renders.
        """
        # 1. Enforce groups-first at every level of the data model before
        #    translating it to QStandardItems.
        self._sort_workspace_data(self.workspace_data)

        self.repo_model.removeRows(0, self.repo_model.rowCount())
        root = self.repo_model.invisibleRootItem()

        def build_recursive(data_list, parent_item):
            # data_list is already sorted (groups first) by _sort_workspace_data
            for node in data_list:
                if node.get("is_group"):
                    group = GroupFolderItem(node["name"])
                    group.setData("GROUP", Qt.UserRole)
                    group.setForeground(QColor("#EEEEEE"))
                    group.setIcon(get_icon("folder", "#888888"))

                    # All 4 columns must be created together so that sibling
                    # accessors (parent.child(row, col)) always work correctly.
                    col_branch = QStandardItem("")
                    col_branch.setFlags(Qt.ItemIsEnabled)
                    col_status = QStandardItem("")
                    col_status.setFlags(Qt.ItemIsEnabled)
                    col_output = QStandardItem("")
                    col_output.setFlags(Qt.ItemIsEnabled)

                    parent_item.appendRow([group, col_branch, col_status, col_output])

                    if "children" in node:
                        build_recursive(node["children"], group)
                else:
                    path = node.get("path")
                    if path in self.found_repos:
                        self._create_repo_row(parent_item, path)

        build_recursive(self.workspace_data, root)

        # 2. Auto-add repos that exist on disk but are not yet in the data
        #    model.  They are loose repos → always go at the end (after all
        #    groups that are already at root level).
        mapped = self._get_mapped_paths(self.workspace_data)
        for r_path in self.found_repos:
            if r_path not in mapped:
                new_node = {
                    "name": os.path.basename(r_path),
                    "is_group": False,
                    "path": r_path,
                }
                # Keep data model consistent: append to end (repos go last)
                self.workspace_data.append(new_node)
                self._create_repo_row(root, r_path)

    def _get_mapped_paths(self, data):
        """Recursively collects all repository paths already in the data model."""
        paths = set()
        for n in data:
            if n.get("is_group"):
                paths.update(self._get_mapped_paths(n.get("children", [])))
            else:
                paths.add(n.get("path"))
        return paths

    # ── Visual State Helpers ──────────────────────────────────────────────────

    def _get_expansion_state(self):
        expanded_paths = set()
        model = self.repo_model
        def recurse(parent_idx, current_path):
            for i in range(model.rowCount(parent_idx)):
                idx = model.index(i, 0, parent_idx)
                item = model.itemFromIndex(idx)
                if item and item.data(Qt.UserRole) == "GROUP":
                    new_path = current_path + (item.text(),)
                    if self.tree.isExpanded(idx):
                        expanded_paths.add(new_path)
                    recurse(idx, new_path)
        recurse(QModelIndex(), ())
        return expanded_paths

    def _apply_expansion_state(self, expanded_paths):
        if not expanded_paths: return
        model = self.repo_model
        def recurse(parent_idx, current_path):
            for i in range(model.rowCount(parent_idx)):
                idx = model.index(i, 0, parent_idx)
                item = model.itemFromIndex(idx)
                if item and item.data(Qt.UserRole) == "GROUP":
                    new_path = current_path + (item.text(),)
                    if new_path in expanded_paths:
                        self.tree.expand(idx)
                    recurse(idx, new_path)
        recurse(QModelIndex(), ())

    # ── Data Model Path Navigation (CRITICAL) ─────────────────────────────────

    def _get_data_path(self, index):
        """Converts QModelIndex to a coordinate list [root_idx, child_idx, ...]"""
        path = []
        curr = index
        while curr.isValid():
            path.insert(0, curr.row())
            curr = curr.parent()
        return path

    def _get_data_container(self, path):
        """Returns the actual 'children' list reference at the specified path."""
        curr_list = self.workspace_data
        for seg in path:
            if seg < len(curr_list):
                node = curr_list[seg]
                if "children" not in node:
                    node["children"] = []
                curr_list = node["children"]
            else:
                # Synchronization Error: Rebuild tree or return root?
                return self.workspace_data 
        return curr_list

    def _get_data_container_and_index(self, node_path):
        """Returns (container_list, index_in_container) for a node path."""
        if not node_path:
            return self.workspace_data, -1
        container = self._get_data_container(node_path[:-1])
        return container, node_path[-1]

    def _get_mapped_paths(self, data):
        """Recursively collects all repository paths already in the data model."""
        paths = set()
        for n in data:
            if n.get("is_group"):
                paths.update(self._get_mapped_paths(n.get("children", [])))
            else:
                paths.add(n.get("path"))
        return paths

    def _create_repo_row(self, parent_item, repo_path):
        repo_name = os.path.basename(repo_path)

        item_repo = RepoLeafItem(repo_name)
        item_repo.setToolTip(repo_path)
        item_repo.setData("REPO", Qt.UserRole)
        item_repo.setData(repo_path, Qt.UserRole + 1)
        item_repo.setForeground(QColor("#BBBBBB"))
        item_repo.setIcon(get_icon("repo", "#666666"))

        item_branch = QStandardItem("—")
        item_branch.setForeground(QColor("#555555"))
        item_branch.setFlags(item_branch.flags() & ~Qt.ItemIsEditable)

        item_status = QStandardItem(TR("status_idle_repo"))
        item_status.setForeground(QColor("#444444"))
        item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)

        item_output = QStandardItem(TR("status_awaiting"))
        item_output.setForeground(QColor("#444444"))
        item_output.setFlags(item_output.flags() & ~Qt.ItemIsEditable)

        parent_item.appendRow([item_repo, item_branch, item_status, item_output])

        # Async metadata update (branch name)
        meta = _safe_get_metadata(repo_path)
        if meta and meta.get("branch"):
            row = parent_item.rowCount() - 1
            bi = parent_item.child(row, 1)
            if bi:
                bi.setText(meta["branch"])
                bi.setForeground(QColor("#666666"))

    # ── Tree Events ───────────────────────────────────────────────────────────

    def _on_tree_clicked(self, index):
        if not index.isValid(): return
        col0 = index.sibling(index.row(), 0)
        item = self.repo_model.itemFromIndex(col0)
        if item and item.data(Qt.UserRole) == "GROUP":
            if self.tree.isExpanded(col0):
                self.tree.collapse(col0)
            else:
                self.tree.expand(col0)

    def _on_item_expanded(self, index):
        pass

    def _on_item_collapsed(self, index):
        pass

    def _on_context_menu(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid(): return
        col0 = index.sibling(index.row(), 0)
        item = self.repo_model.itemFromIndex(col0)
        node_path = self._get_data_path(col0)

        # ── Dynamic Context Menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #252525; color: #EEEEEE; border: 1px solid #444444; }
            QMenu::item:selected { background-color: #3D3D3D; }
        """)

        if item and item.data(Qt.UserRole) == "GROUP":
            action_move = menu.addAction(TR("menu_move_to_group"))
            menu.addSeparator()
            action_rename = menu.addAction(TR("menu_rename_group"))
            action_delete = menu.addAction(TR("menu_delete_group"))
        else:
            action_move = menu.addAction(TR("menu_move_repo"))

        action = menu.exec(self.tree.viewport().mapToGlobal(position))
        if not action: return

        if action == action_move:
            all_groups = []
            self._get_all_group_labels(self.workspace_data, "", [], all_groups)
            
            dlg = MoveToDialog(all_groups, self)
            if dlg.exec():
                tgt_container_path = dlg.get_selected_path()
                
                # Guard: Moving group into itself or child
                if item and item.data(Qt.UserRole) == "GROUP":
                    if len(node_path) <= len(tgt_container_path):
                        if node_path == tgt_container_path[:len(node_path)]:
                            QMessageBox.warning(self, TR("err_invalid_move_title"), TR("err_invalid_move"))
                            return

                try:
                    open_state = self._get_expansion_state()

                    # Resolve the target container reference BEFORE the pop.
                    # We use the Python object identity so even if the pop
                    # shifts positional indices inside the list, the reference
                    # to the list object itself stays valid.
                    tgt_container = self._get_data_container(tgt_container_path)

                    # Pop from source.  If the source and target are the SAME
                    # list (same container, just reordering inside it) the pop
                    # does not invalidate the reference — we still hold it.
                    src_container, src_idx = self._get_data_container_and_index(node_path)
                    node_data = src_container.pop(src_idx)

                    # Insert into target maintaining the groups-first invariant.
                    self._insert_sorted(tgt_container, node_data)

                    # Full atomic rebuild then restore which groups were open.
                    self._rebuild_tree()
                    self._apply_expansion_state(open_state)
                    self._save_virtual_layout()
                except Exception as e:
                    QMessageBox.critical(self, "Error", TR("err_move_failed", error=str(e)))
                    self._rebuild_tree()

        elif 'action_rename' in locals() and action == action_rename:
            text, ok = QInputDialog.getText(self, TR("dlg_rename_title"), TR("dlg_rename_label"), text=item.text())
            if ok and text:
                container, idx = self._get_data_container_and_index(node_path)
                if idx < len(container):
                    open_state = self._get_expansion_state()
                    container[idx]["name"] = text
                    self._rebuild_tree()
                    self._apply_expansion_state(open_state)
                    self._save_virtual_layout()
        elif 'action_delete' in locals() and action == action_delete:
            reply = QMessageBox.question(self, TR("dlg_delete_title"), TR("dlg_delete_msg"), QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                container, idx = self._get_data_container_and_index(node_path)
                if idx < len(container):
                    open_state = self._get_expansion_state()
                    container.pop(idx)
                    self._rebuild_tree()
                    self._apply_expansion_state(open_state)
                    self._save_virtual_layout()

    def _get_all_group_labels(self, data, prefix, path_acc, results):
        """Recursively builds list of (BreadcrumbLabel, DataPath) for all groups."""
        for i, node in enumerate(data):
            if node.get("is_group"):
                current_label = f"{prefix} > {node['name']}" if prefix else node["name"]
                current_path = path_acc + [i]
                results.append((current_label, current_path))
                if "children" in node:
                    self._get_all_group_labels(node["children"], current_label, current_path, results)

    # ── Group Management ──────────────────────────────────────────────────────

    def prompt_create_group(self):
        text, ok = QInputDialog.getText(self, TR("dlg_create_group_title"), TR("dlg_create_group_label"))
        if not (ok and text): return

        new_node = {"name": text, "is_group": True, "children": []}
        sel = self.tree.selectedIndexes()

        if sel:
            idx = sel[0].sibling(sel[0].row(), 0)
            target_path = self._get_data_path(idx)
            item = self.repo_model.itemFromIndex(idx)

            if item and item.data(Qt.UserRole) == "GROUP":
                # Selection is a group → add the new group inside it
                container = self._get_data_container(target_path)
            else:
                # Selection is a repo → add the new group in the same
                # container as that repo (sibling level), not inside the repo
                container = self._get_data_container(target_path[:-1])
        else:
            container = self.workspace_data

        # Use _insert_sorted so the new group lands before any loose repos
        # that may already exist in the container.
        open_state = self._get_expansion_state()
        self._insert_sorted(container, new_node)

        self._rebuild_tree()
        self._apply_expansion_state(open_state)
        self._save_virtual_layout()

    # ── Virtual Layout Persistence ────────────────────────────────────────────

    def _schedule_save(self, *args):
        self._save_virtual_layout()

    def _save_virtual_layout(self):
        if not self.target_dir: return
        layout_path = os.path.join(os.path.expanduser("~"), ".gitbulk_virtual_groups.json")
        full = {}
        if os.path.exists(layout_path):
            try:
                with open(layout_path, "r") as f:
                    full = json.load(f)
            except Exception: pass

        full[self.target_dir] = self.workspace_data
        with open(layout_path, "w") as f:
            json.dump(full, f, indent=4)

    def _load_virtual_layout(self):
        layout_path = os.path.join(os.path.expanduser("~"), ".gitbulk_virtual_groups.json")
        if os.path.exists(layout_path):
            try:
                with open(layout_path, "r") as f:
                    return json.load(f).get(self.target_dir, [])
            except Exception:
                pass
        return []

    # ── Git Operations ────────────────────────────────────────────────────────

    def _all_leaves(self):
        leaves = []
        self._traverse_leaves(self.repo_model.invisibleRootItem(), leaves)
        return leaves

    def _traverse_leaves(self, parent, result):
        for i in range(parent.rowCount()):
            child = parent.child(i, 0)
            if child:
                if child.data(Qt.UserRole) == "REPO":
                    result.append(child)
                else:
                    self._traverse_leaves(child, result)

    def _find_repo_node(self, repo_path):
        for leaf in self._all_leaves():
            if leaf.data(Qt.UserRole + 1) == repo_path:
                return leaf
        return None

    def start_operation(self, operation, kwargs=None):
        if not self.found_repos:
            self._set_status("No workspace loaded", "", "", "#F85149")
            return
        if self.operation_worker and self.operation_worker.isRunning():
            return

        self._op_start_time = time.time()
        self._processed_count = 0
        total = len(self.found_repos)

        # Progress bar
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        for leaf in self._all_leaves():
            row = leaf.row()
            parent = leaf.parent() or self.repo_model.invisibleRootItem()
            s = parent.child(row, 2)
            d = parent.child(row, 3)
            if s:
                s.setText("—")
                s.setForeground(QColor("#444444"))
            if d:
                d.setText("Processing...")
                d.setForeground(QColor("#444444"))

        op_labels = {
            "status": "Status", "fetch": "Fetch", "sync": "Sync", "pull": "Pull",
            "push": "Push", "clean": "Clean", "checkout": "Checkout", "ci": "CI Pipelines"
        }
        self._set_status(
            f"{op_labels.get(operation, operation)}",
            f"0 / {total}",
            "",
            "#E2E2E2"
        )

        self.operation_worker = OperationWorker(
            self.found_repos, operation, max_workers=10, kwargs=kwargs
        )
        self.operation_worker.log_ready.connect(self.on_log_ready)
        self.operation_worker.finished.connect(self.on_operation_finished)
        self.operation_worker.start()
        self._set_buttons_enabled(False)

    def on_log_ready(self, status, detail, repo_path, output):
        self._processed_count += 1
        total = len(self.found_repos)

        # Advance progress bar
        self.progress_bar.setValue(self._processed_count)
        self.lbl_status_detail.setText(f"{self._processed_count} / {total}")

        leaf = self._find_repo_node(repo_path)
        if not leaf:
            return

        row = leaf.row()
        parent = leaf.parent() or self.repo_model.invisibleRootItem()

        # Color mapping
        color_map = {
            "OK": "#3FB950",
            "CLEAN": "#3FB950",
            "MODIFIED": "#F0A033",
            "CLEANED": "#3FB950",
            "AHEAD": "#3FB950",           # Green: You are ahead, ready to push
            "BEHIND": "#BC8CFF",          # Purple: Remote has changes
            "DIVERGENT": "#BC8CFF",       # Purple: Both ahead and behind
            "CONFLICT": "#F85149",
            "ERROR": "#F85149",
            "FETCH_UPDATE": "#BC8CFF",
            "CHECKOUT": "#3FB950",
            "IGNORED": "#555555",
            "SUCCESS": "#3FB950",
            "FAILED": "#F85149",
        }
        color = color_map.get(status.upper(), "#666666")

        s_item = parent.child(row, 2)
        d_item = parent.child(row, 3)

        if s_item:
            s_item.setText(status)
            s_item.setForeground(QColor(color))

        if d_item:
            display = detail if detail else (output.strip().split("\n")[0] if output else "")
            d_item.setText(display or "—")
            d_item.setForeground(QColor(color if display else "#444444"))
            if output:
                d_item.setToolTip(output.strip())

    def on_operation_finished(self, count):
        elapsed = time.time() - self._op_start_time if self._op_start_time else 0

        # Complete the bar then fade it out after 2s
        self.progress_bar.setValue(self.progress_bar.maximum())
        QTimer.singleShot(2000, self.progress_bar.hide)

        self._set_status(
            "Done",
            f"{count} repositories processed",
            f"{elapsed:.1f}s",
            "#3FB950"
        )
        self._set_buttons_enabled(True)

    def start_ci_operation(self):
        token = ""
        try:
            import sys
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from persistence.config_repo import load_config
            config = load_config()
            token = config.get("github_token", "")
        except Exception:
            pass
        self.start_operation("ci", kwargs={"token": token})

    def prompt_checkout(self):
        if not self.target_dir:
            return
        text, ok = QInputDialog.getText(self, "Checkout Branch", "Target branch name:")
        if ok and text:
            self.start_operation("checkout", kwargs={"target_branch": text.strip()})

    def export_workspace(self):
        if not self.target_dir:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Workspace", "", "JSON Files (*.json)"
        )
        if path:
            def recurse(item):
                if not item:
                    return None
                node = {"name": item.text(), "is_group": item.data(Qt.UserRole) == "GROUP"}
                if not node["is_group"]:
                    node["path"] = item.data(Qt.UserRole + 1)
                children = []
                for i in range(item.rowCount()):
                    c = item.child(i, 0)
                    if c:
                        r = recurse(c)
                        if r:
                            children.append(r)
                if children or node["is_group"]:
                    node["children"] = children
                return node

            data = []
            root = self.repo_model.invisibleRootItem()
            for i in range(root.rowCount()):
                c = root.child(i, 0)
                if c:
                    r = recurse(c)
                    if r:
                        data.append(r)

            with open(path, "w") as f:
                json.dump({self.target_dir: data}, f, indent=4)
            self._set_status("Export complete", os.path.basename(path), "", "#3FB950")

    def import_workspace(self):
        """Load a previously exported workspace JSON and restore the tree layout."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Workspace", "", "JSON Files (*.json)"
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            QMessageBox.warning(self, "Import Error", f"Could not read the file:\n{e}")
            return

        # Format: {"<workspace_dir>": [node, ...]}
        if not isinstance(raw, dict) or not raw:
            QMessageBox.warning(self, "Import Error", "Invalid workspace file format.")
            return

        workspace_dir = next(iter(raw))
        layout_data   = raw[workspace_dir]

        if not os.path.isdir(workspace_dir):
            # Ask user whether to use a new base dir
            msg = QMessageBox(self)
            msg.setWindowTitle("Directory Not Found")
            msg.setText(
                f"The original workspace directory was not found:\n{workspace_dir}\n\n"
                "Would you like to choose a different root directory?"
            )
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            if msg.exec() != QMessageBox.Yes:
                return
            workspace_dir = QFileDialog.getExistingDirectory(self, "Select Workspace Directory")
            if not workspace_dir:
                return

        # Load the directory first so the scanner fills found_repos
        self.load_directory(workspace_dir)
        # Wait for scanner to finish, then apply the imported layout
        # We hook into on_scan_finished via a one-shot flag
        self._pending_import_layout = layout_data

    def _apply_imported_layout(self, layout_data):
        """Called after scan completes when an import is pending."""
        self.repo_model.removeRows(0, self.repo_model.rowCount())
        root   = self.repo_model.invisibleRootItem()
        mapped = set()
        self._build_tree_from_data(layout_data, root, self.found_repos, mapped)
        # Any repo not in the exported layout appears ungrouped at root
        for r in self.found_repos:
            if r not in mapped:
                self._create_repo_row(root, r)
        self._set_status("Import complete", f"{len(self.found_repos)} repos loaded", "", "#3FB950")

    def _set_buttons_enabled(self, enabled):
        for btn in (
            self.btn_load_dir, self.btn_new_group,
            self.btn_pull, self.btn_push, self.btn_sync,
            self.btn_clean, self.btn_export, self.btn_import
        ):
            if hasattr(self, btn.objectName()) or btn is not None:
                btn.setEnabled(enabled)
