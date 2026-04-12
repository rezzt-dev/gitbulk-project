import os
import json
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, 
    QPushButton, QTreeView, QHeaderView, QAbstractItemView, QSizeGrip, 
    QFileDialog, QInputDialog, QMessageBox, QMenu, QSpacerItem, 
    QSizePolicy, QProgressBar, QDialog, QComboBox, QLineEdit, 
    QTextEdit, QCheckBox, QListWidget, QListWidgetItem, QTreeWidget, 
    QTreeWidgetItem
)
from PySide6.QtCore import Qt, QRect, QRectF, QPointF, QSize, QModelIndex, QTimer
from PySide6.QtGui import QIcon, QPainter, QPen, QColor, QStandardItemModel, QStandardItem, QFont, QFontDatabase
# Robust local imports for PyInstaller/Dev
try:
    from gui.translations import TR, set_language, get_current_language, LANGUAGES
except (ImportError, ModuleNotFoundError):
    try:
        from .translations import TR, set_language, get_current_language, LANGUAGES
    except (ImportError, ModuleNotFoundError):
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
    from model import calculate_optimal_workers, ensure_ssh_agent
except ImportError:
    from gui.icon_manager import get_icon
    from gui.workers import ScannerWorker, OperationWorker
    from model import calculate_optimal_workers, find_git_repos, archive_repository, clone_repo, ensure_ssh_agent


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
        
        # ── UI Performance Throttling
        self._log_queue = []
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(250) # Flush every 250ms
        self._ui_timer.timeout.connect(self._process_log_queue)
        self._found_repo_nodes = {} # Cache for UI updates

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

        # ── Initial diagnostic (SSH, etc)
        ssh_ok, ssh_info = ensure_ssh_agent()
        if not ssh_ok:
            self.append_log(f"[!] SSH: {ssh_info}", "#F0A033")
        elif "started" in ssh_info:
            self.append_log(f"[INFO] SSH: {ssh_info}", "#888888")

    def closeEvent(self, event):
        """
        Persists the active working directory and current virtual layout
        before the window closes so the next launch can restore the full
        session (directory + groups + repositories).
        """
        try:
            # 1. Global config (last_directory)
            _cfg = load_config()
            if self.target_dir:
                _cfg["last_directory"] = self.target_dir
                save_config(_cfg)
            
            # 2. Virtual layout (groups)
            if self.target_dir and (self.workspace_data or self.found_repos):
                self._save_virtual_layout()
        except Exception:
            pass
        super().closeEvent(event)

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
            ("btn_commit",  TR("btn_commit"),        "sync",    "#58A6FF", "commit"),
            ("btn_push",    TR("btn_push"),          "sync",    "#4CAF50", "push"),
            ("btn_sync",    TR("btn_sync"),          "sync",    "#888888", "sync"),
        ]
        for attr, label, icon, color, op in ops:
            btn = self._sidebar_btn(f"  {label}", icon, color)
            if op == "commit":
                btn.clicked.connect(self.open_commit_hub)
            else:
                btn.clicked.connect(lambda checked=False, o=op: self.start_operation(o))
            setattr(self, attr, btn)
            layout.addWidget(btn)

        layout.addSpacing(8)
        layout.addWidget(self._divider())

        # ── WORKSPACES section
        layout.addWidget(self._section_header("sidebar_workspaces"))
        
        self.workspace_list_layout = QVBoxLayout()
        self.workspace_list_layout.setSpacing(2)
        layout.addLayout(self.workspace_list_layout)
        
        self.btn_refresh_workspaces = self._sidebar_btn(f"  {TR('btn_refresh_workspaces')}", "sync", "#555555")
        self.btn_refresh_workspaces.clicked.connect(self.refresh_workspaces_ui)
        layout.addWidget(self.btn_refresh_workspaces)

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

        self.btn_group_inspector = self._sidebar_btn(f"  {TR('btn_group_inspector')}", "folder", "#888888")
        self.btn_group_inspector.clicked.connect(self.open_group_summary)
        layout.addWidget(self.btn_group_inspector)

        self.btn_sync_workspace = self._sidebar_btn(f"  {TR('btn_sync_workspace')}", "sync", "#F0A033")
        self.btn_sync_workspace.clicked.connect(self.open_workspace_sync)
        layout.addWidget(self.btn_sync_workspace)

        layout.addStretch()
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
        self.refresh_workspaces_ui()

    def refresh_workspaces_ui(self):
        """Clears and repopulates the workspace list in the sidebar."""
        # Clear existing
        while self.workspace_list_layout.count():
            item = self.workspace_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        config = load_config()
        workspaces = config.get("workspaces", {})
        
        if not workspaces:
            lbl = QLabel(f"  {TR('status_no_workspaces')}")
            lbl.setStyleSheet("color: #444444; font-family: 'JetBrains Mono'; font-size: 10px; padding: 4px 16px;")
            self.workspace_list_layout.addWidget(lbl)
        else:
            for name in workspaces:
                btn = QPushButton(f"  {name}")
                btn.setIcon(get_icon("repo", "#666666"))
                btn.setStyleSheet("""
                    QPushButton { 
                        font-family: 'JetBrains Mono'; text-align: left; padding: 6px 16px; 
                        color: #BBBBBB; border: none; font-size: 11px;
                    }
                    QPushButton:hover { background-color: #1A1A1A; color: #EEEEEE; }
                """)
                # Use default argument to capture the name in the lambda
                btn.clicked.connect(lambda checked=False, n=name: self.load_named_workspace(n))
                self.workspace_list_layout.addWidget(btn)

    def load_named_workspace(self, name):
        """Loads a workspace by name from the global config."""
        config = load_config()
        workspaces = config.get("workspaces", {})
        if name not in workspaces:
            return
            
        snapshot = workspaces[name]
        self.append_log(f"Loading workspace: {name}", "#3FB950")

        # Resolve the root directory: 
        # Named workspaces in config can be saved as a list of repos (CLI style)
        # or as a dict containing __root_dir__.
        root_dir = ""
        if isinstance(snapshot, dict):
             root_dir = snapshot.get("__root_dir__", "")
        
        # Fallback: if we don't have a recorded root, use the current active dir
        if not root_dir or not os.path.isdir(root_dir):
            root_dir = self.target_dir
            
        # Last fallback: if still no directory, ask the user
        if not root_dir or not os.path.isdir(root_dir):
            self.prompt_directory_selection()
            root_dir = self.target_dir

        if not root_dir:
            return

        # Prepare the layout for rendering
        layout = []
        if isinstance(snapshot, dict):
            # Strip metadata keys
            layout = {k: v for k, v in snapshot.items() if k != "__root_dir__"}
            # Actually, if it's a dict from GUI, it might be structured differently.
            # But based on current code, GUI snapshots are usually stored as lists of groups/repos.
        elif isinstance(snapshot, list):
            layout = snapshot

        self._pending_import_layout = layout
        # The scanner will pick it up after scan finishes
        self.load_directory(root_dir)

    def retranslate_ui(self):
        """Refreshes all UI strings without restarting."""
        self.setWindowTitle(TR("window_title"))
        self.title_bar.subtitle_label.setText(TR("status_no_workspace") if not self.target_dir else os.path.basename(self.target_dir))
        
        # Sidebar
        # Headers are recreated or updated if we keep refs, but let's update buttons
        self.btn_load_dir.setText(f"  {TR('btn_scan')}")
        self.btn_new_group.setText(f"  {TR('btn_group')}")
        self.btn_pull.setText(f"  {TR('btn_pull')}")
        self.btn_commit.setText(f"  {TR('btn_commit')}")
        self.btn_push.setText(f"  {TR('btn_push')}")
        self.btn_sync.setText(f"  {TR('btn_sync')}")
        self.btn_import.setText(f"  {TR('btn_import')}")
        self.btn_export.setText(f"  {TR('btn_export')}")
        self.btn_clean.setText(f"  {TR('btn_clean')}")
        self.btn_group_inspector.setText(f"  {TR('btn_group_inspector')}")
        self.btn_sync_workspace.setText(f"  {TR('btn_sync_workspace')}")
        
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
        lbl = QLabel(TR(text_key))
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

    def append_log(self, text, color="#484848"):
        """
        Updates the status bar detail text with a specific color.
        Provides a safe way to log information in the GUI.
        """
        self._set_status(self.lbl_status_op.text().strip(), detail=text, color=color)

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

        # ── Persist last working directory so it survives restarts
        try:
            _cfg = load_config()
            _cfg["last_directory"] = dir_path
            save_config(_cfg)
            # We also trigger a layout save if we switched directories
            self._save_virtual_layout()
        except Exception:
            pass

        self._set_status(TR("status_scanning"), dir_path, "", "#E2E2E2")
        self.repo_model.removeRows(0, self.repo_model.rowCount())

        self.scanner_worker = ScannerWorker(self.target_dir)
        self.scanner_worker.finished.connect(self.on_scan_finished)
        self.scanner_worker.start()

    def on_scan_finished(self, repos):
        # repos is now List[Dict] -> {"path": ..., "metadata": {"groups": [...]}}
        # We need to keep paths in self.found_repos for the OperationWorker
        self.raw_scan_results = repos
        self.found_repos = [r["path"] for r in repos]
        
        self.lbl_repo_count.setText(f"{len(repos)} {TR('lbl_repos')}")
        self.lbl_repo_count.show()

        # ── Synchronize with Data Model
        if self._pending_import_layout is not None:
            self.workspace_data = self._pending_import_layout
            self._pending_import_layout = None
        else:
            self.workspace_data = self._load_virtual_layout() or []

        # ── Auto-Group Logic (Integrate Repo Metadata)
        self._apply_metadata_to_layout()

        # ── Global Renderer
        open_state = self._get_expansion_state()
        self._rebuild_tree()
        self._apply_expansion_state(open_state)
        self._set_status(TR("status_loaded"), TR("status_repos_found", count=len(repos)), "", "#4CAF50")

    def _apply_metadata_to_layout(self):
        """
        Scans raw_scan_results and ensures any repository with 'groups' in its 
        metadata is placed in the corresponding folders within self.workspace_data,
        unless it's already explicitly mapped elsewhere.
        """
        # 1. Map current state to a flat set for fast lookup
        mapped_paths = self._get_mapped_paths(self.workspace_data)
        
        for item in self.raw_scan_results:
            repo_path = item["path"]
            groups = item["metadata"].get("groups", [])
            
            if not groups or repo_path in mapped_paths:
                continue
                
            # If repo is not mapped but has groups → Create/Find the group path
            # and append the repo there.
            container = self.workspace_data
            for g_name in groups:
                # Find or create group
                found_g = None
                for node in container:
                    if node.get("is_group") and node.get("name") == g_name:
                        found_g = node
                        break
                
                if not found_g:
                    found_g = {"name": g_name, "is_group": True, "children": []}
                    self._insert_sorted(container, found_g)
                
                container = found_g["children"]
            
            # Add repo to the last container
            container.append({"name": os.path.basename(repo_path), "path": repo_path})

    def _get_mapped_paths(self, data):
        """Recursively collects all repository paths already in the data model."""
        paths = set()
        for n in data:
            if n.get("is_group"):
                paths.update(self._get_mapped_paths(n.get("children", [])))
            else:
                paths.add(n.get("path"))
        return paths

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
        self._found_repo_nodes = {} # Reset cache

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
        
        # Cache row items for fast lookup
        row = parent_item.rowCount() - 1
        self._found_repo_nodes[repo_path] = [parent_item.child(row, col) for col in range(4)]

        # Async metadata update (branch name)
        meta = _safe_get_metadata(repo_path)
        if meta and meta.get("branch"):
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
        self._log_queue.clear()
        self._current_conflicts = [] # Track conflicts for resolution dialog
        self._ui_timer.start()

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
            "status": TR("op_status"), "fetch": TR("op_fetch"), "sync": TR("op_sync"), "pull": TR("op_pull"),
            "push": TR("op_push"), "clean": TR("op_clean"), "checkout": TR("op_checkout"), "ci": TR("op_ci")
        }
        self._set_status(
            f"{op_labels.get(operation, operation)}",
            f"0 / {total}",
            "",
            "#E2E2E2"
        )

        # Dynamic worker calculation (GUI currently defaults to auto-tuning)
        optimal = calculate_optimal_workers(self.target_dir, 0)
        
        self.operation_worker = OperationWorker(
            self.found_repos, operation, max_workers=optimal, kwargs=kwargs
        )
        
        # Log the auto-tuned worker count
        self.append_log(f"[INFO] Auto-tuning: using {optimal} concurrent threads.", "#888888")
        self.operation_worker.log_ready.connect(self.on_log_ready)
        self.operation_worker.finished.connect(self.on_operation_finished)
        self.operation_worker.start()
        self._set_buttons_enabled(False)

    def on_log_ready(self, status, detail, repo_path, output):
        # Buffer the log result instead of immediate UI reflow
        self._log_queue.append((status, detail, repo_path, output))
        if status == "CONFLICT" or "conflict" in detail.lower() or "conflict" in output.lower():
            self._current_conflicts.append((repo_path, detail, output))

    def _process_log_queue(self):
        """Flushes the log queue and updates the UI in a single batch."""
        if not self._log_queue:
            return
            
        batch = self._log_queue[:]
        self._log_queue.clear()
        
        # Color mapping (Pre-calculating to avoid re-lookup)
        color_map = {
            "OK": "#4CAF50", "CLEAN": "#4CAF50", "MODIFIED": "#F0DF5A",
            "CLEANED": "#4CAF50", "AHEAD": "#4CAF50", "BEHIND": "#F0DF5A",
            "DIVERGENT": "#BC8CFF", "CONFLICT": "#FF5252", "ERROR": "#FF5252",
            "FETCH_UPDATE": "#BC8CFF", "CHECKOUT": "#2196F3", "IGNORED": "#888888",
            "COMMITTED": "#58A6FF", "PUSHED": "#4CAF50", "SUCCESS": "#4CAF50",
            "FAILED": "#FF5252"
        }

        total = len(self.found_repos)
        
        for status, detail, repo_path, output in batch:
            row_items = self._found_repo_nodes.get(repo_path)
            if not row_items:
                # If cache missed (unlikely but safe fallback)
                leaf = self._find_repo_node(repo_path)
                if not leaf: continue
                parent = leaf.parent() or self.repo_model.invisibleRootItem()
                row = leaf.row()
                row_items = [parent.child(row, col) for col in range(4)]
                self._found_repo_nodes[repo_path] = row_items

            color = color_map.get(status.upper(), "#666666")
            
            # Status Column
            s_item = row_items[2]
            s_item.setText(TR(status.lower()))
            s_item.setForeground(QColor(color))
            
            # Detail Column
            d_item = row_items[3]
            display = detail if detail else (output.strip().split("\n")[0] if output else "")
            d_item.setText(display or "—")
            d_item.setForeground(QColor(color if display else "#444444"))
            if output:
                d_item.setToolTip(output.strip())
            
            self._processed_count += 1

        # Periodic status updates
        self.progress_bar.setValue(self._processed_count)
        self.lbl_status_detail.setText(f"{self._processed_count} / {total}")

    def on_operation_finished(self, count):
        self._ui_timer.stop()
        self._process_log_queue() # Final flush
        
        elapsed = time.time() - self._op_start_time if self._op_start_time else 0
        self.progress_bar.setValue(self.progress_bar.maximum())
        QTimer.singleShot(2000, self.progress_bar.hide)

        self._set_status(
            TR("status_done"),
            TR("status_processed", count=count),
            f"{elapsed:.1f}s",
            "#3FB950"
        )
        self._set_buttons_enabled(True)
        
        # Launch Conflict Hub if needed
        if self._current_conflicts:
            dialog = ConflictHubDialog(self._current_conflicts, self)
            dialog.exec()
            # Clear for next op
            self._current_conflicts = []

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
        text, ok = QInputDialog.getText(self, "GitBulk", TR("op_checkout") + ":")
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
            QMessageBox.warning(self, "GitBulk", f"{TR('btn_import')} error:\n{e}")
            return

        # Format: {"<workspace_dir>": [node, ...]}
        if not isinstance(raw, dict) or not raw:
            QMessageBox.warning(self, "GitBulk", f"{TR('btn_import')} error: invalid format")
            return

        workspace_dir = next(iter(raw))
        layout_data   = raw[workspace_dir]

        if not os.path.isdir(workspace_dir):
            # Ask user whether to use a new base dir
            msg = QMessageBox(self)
            msg.setWindowTitle("GitBulk")
            msg.setText(
                f"{TR('status_no_dir_selected')}:\n{workspace_dir}\n\n"
                "choose a different directory?"
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

    def open_group_summary(self):
        if not self.target_dir:
            self._set_status("Select a directory first", color="#F85149")
            return
            
        from model import get_groups_topology
        topology = get_groups_topology(self.target_dir)
        
        # Sort groups: Uncategorized last
        sorted_groups = sorted(topology.keys(), key=lambda x: (1 if x == "Uncategorized" else 0, x.lower()))
        
        dialog = GroupSummaryDialog(topology, self)
        dialog.exec()

    def open_commit_hub(self):
        if not self.target_dir or not self.found_repos:
            self._set_status("No repositories to commit", color="#F85149")
            return
            
        # Collect current state from tree
        repo_data = [] # List of (path, status_text)
        for leaf in self._all_leaves():
            path = leaf.data(Qt.UserRole + 1)
            parent = leaf.parent() or self.repo_model.invisibleRootItem()
            status_item = parent.child(leaf.row(), 2)
            status_text = status_item.text() if status_item else ""
            repo_data.append((path, status_text))
            
        dialog = CommitHubDialog(repo_data, self)
        if dialog.exec():
            msg, body, selected_paths = dialog.get_data()
            if not selected_paths:
                self._set_status("No repositories selected", color="#F85149")
                return
                
            # Temporarily filter found_repos to only selected ones for this operation
            original_found = self.found_repos
            self.found_repos = [r for r in original_found if r in selected_paths]
            
            try:
                self.start_operation("commit", kwargs={"message": msg, "body": body})
            finally:
                # Restore original list
                self.found_repos = original_found

    def open_workspace_sync(self):
        if not self.target_dir:
            self._set_status("Load a directory first", color="#F85149")
            return
            
        # 1. Select snapshot
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Reference Snapshot", "", "JSON files (*.json)")
        if not file_path:
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                snapshot = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load snapshot: {e}")
            return
            
        # 2. Compare
        raw_repos = find_git_repos(self.target_dir)
        expected_map = {os.path.normpath(r["path"]): r for r in snapshot}
        local_map = {os.path.normpath(os.path.relpath(r["path"], self.target_dir)): r["path"] for r in raw_repos}
        
        to_clone = [] # (abs_path, info)
        for rel_path, info in expected_map.items():
            if rel_path not in local_map:
                abs_path = os.path.normpath(os.path.join(self.target_dir, rel_path))
                to_clone.append((abs_path, info))
                
        to_archive = [] # abs_path
        for rel_path, abs_path in local_map.items():
            if rel_path not in expected_map:
                to_archive.append(abs_path)
                
        if not to_clone and not to_archive:
            QMessageBox.information(self, "Sync", "Workspace is already in sync with the reference.")
            return
            
        # 3. Preview Dialog
        dialog = SyncPreviewDialog(to_clone, to_archive, self)
        if dialog.exec():
            # 4. Execute Archive
            for path in to_archive:
                archive_repository(path, self.target_dir)
                
            # 5. Execute Clone
            if to_clone:
                # Reuse the existing loader logic
                # For simplicity, we trigger a refresh and then we'd normally clone.
                # In GUI, we will just show an info message for now or implement cloning here.
                # Actually, let's just use the OperationWorker if possible or the same clone_repo.
                for path, info in to_clone:
                    clone_repo(path, info)
            
            QMessageBox.information(self, "Success", "Sync complete. Repositories archived/cloned.")
            self.refresh_workspace()
        

    def focus_on_group(self, group_name):
        """Hides all repositories not part of the specified group."""
        if not self.found_repos or not self.repo_view: return
        
        from model import get_groups_topology
        topology = get_groups_topology(self.target_dir)
        
        if group_name not in topology:
            # Show all
            for i in range(self.repo_model.rowCount()):
                self.repo_view.setRowHidden(i, QModelIndex(), False)
            self._set_status(f"Showing all repositories", color="#58A6FF")
            return

        self._set_status(f"Focus: {group_name}", color="#F0DF5A")
        
        target_paths = {r["path"] for r in topology[group_name]}
        root = self.repo_model.invisibleRootItem()
        for i in range(root.rowCount()):
            item = root.child(i, 0)
            if not item: continue
            
            repo_path = item.data(Qt.UserRole + 1)
            is_match = repo_path in target_paths
            self.repo_view.setRowHidden(i, QModelIndex(), not is_match)


# ── Commit Hub Dialog ────────────────────────────────────────────────────────

class CommitHubDialog(QDialog):
    def __init__(self, repo_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(TR("commit_hub_title"))
        self.setMinimumWidth(950)
        self.setMinimumHeight(650)
        self.setStyleSheet("background-color: #0D1117; color: #C9D1D9; font-family: 'Inter', 'Segoe UI';")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30,30,30,30)
        main_layout.setSpacing(24)
        
        # Header with Statistics
        header_layout = QHBoxLayout()
        header_v = QVBoxLayout()
        title = QLabel(TR("commit_hub_title"))
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #F0F6FC;")
        header_v.addWidget(title)
        
        self.lbl_stats = QLabel(TR("commit_hub_stats", count=0))
        self.lbl_stats.setStyleSheet("color: #8B949E; font-size: 13px;")
        header_v.addWidget(self.lbl_stats)
        header_layout.addLayout(header_v)
        header_layout.addStretch()
        
        # Logo placeholder or Icon integration
        main_layout.addLayout(header_layout)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)
        
        # --- LEFT PANEL: Message Editor ---
        form_panel = QFrame()
        form_panel.setStyleSheet("background-color: #161B22; border-radius: 12px; border: 1px solid #30363D;")
        form_layout = QVBoxLayout(form_panel)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        form_layout.addWidget(QLabel(TR("commit_hub_label_title")))
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText(TR("commit_hub_placeholder_title"))
        self.edit_title.setStyleSheet("background-color: #0D1117; border: 1px solid #388BFD; padding: 12px; font-size: 14px; border-radius: 6px; color: #F0F6FC;")
        form_layout.addWidget(self.edit_title)
        
        form_layout.addWidget(QLabel(TR("commit_hub_label_body")))
        self.edit_body = QTextEdit()
        self.edit_body.setPlaceholderText(TR("commit_hub_placeholder_body"))
        self.edit_body.setStyleSheet("background-color: #0D1117; border: 1px solid #30363D; padding: 12px; font-size: 13px; border-radius: 6px;")
        form_layout.addWidget(self.edit_body)
        
        # Tips Box
        tips = QFrame()
        tips.setStyleSheet("background-color: #1F242B; border-radius: 8px;")
        tips_v = QVBoxLayout(tips)
        tips_text = QLabel(TR("commit_hub_tip"))
        tips_text.setStyleSheet("color: #8B949E; font-size: 12px; font-style: italic;")
        tips_v.addWidget(tips_text)
        form_layout.addWidget(tips)
        
        content_layout.addWidget(form_panel, 4)
        
        # --- RIGHT PANEL: Selection & Filtering ---
        repo_panel = QFrame()
        repo_layout = QVBoxLayout(repo_panel)
        repo_layout.setContentsMargins(0, 0, 0, 0)
        repo_layout.setSpacing(10)
        
        search_layout = QHBoxLayout()
        self.edit_filter = QLineEdit()
        self.edit_filter.setPlaceholderText(TR("commit_hub_placeholder_search"))
        self.edit_filter.setStyleSheet("background-color: #161B22; border: 1px solid #30363D; padding: 10px; border-radius: 6px;")
        self.edit_filter.textChanged.connect(self._on_filter_changed)
        search_layout.addWidget(self.edit_filter)
        
        self.btn_select_dirty = QPushButton(TR("commit_hub_btn_dirty"))
        self.btn_select_dirty.setFixedWidth(80)
        self.btn_select_dirty.setStyleSheet("background-color: #21262D; border: 1px solid #30363D; padding: 8px; font-size: 11px;")
        self.btn_select_dirty.clicked.connect(self._select_dirty)
        search_layout.addWidget(self.btn_select_dirty)
        repo_layout.addLayout(search_layout)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("background-color: #0D1117; border: 1px solid #30363D; border-radius: 10px; outline: none;")
        self.list_widget.setSpacing(4)
        
        self.checkboxes = {} # path -> QCheckBox
        self.all_items = []  # List of (item, path, basename)
        
        for path, status in repo_data:
            basename = os.path.basename(path)
            item = QListWidgetItem(self.list_widget)
            
            row_widget = QFrame()
            row_widget.setObjectName("repoCard")
            row_widget.setStyleSheet("""
                #repoCard { background-color: #161B22; border-radius: 8px; border: 1px solid transparent; }
                #repoCard:hover { border: 1px solid #388BFD; background-color: #1C2128; }
            """)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(12, 8, 12, 8)
            
            cb = QCheckBox(basename)
            cb.setStyleSheet("font-weight: 600; font-size: 13px; color: #C9D1D9;")
            cb.stateChanged.connect(self._update_stats)
            
            # Pre-select if modified
            if "MODIFIED" in status or "ahead" in status.lower():
                cb.setChecked(True)
                
            row_layout.addWidget(cb)
            row_layout.addStretch()
            
            status_lbl = QLabel(status)
            color = "#F0DF5A" if "MODIFIED" in status else "#8B949E"
            status_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
            row_layout.addWidget(status_lbl)
            
            item.setSizeHint(row_widget.sizeHint())
            self.list_widget.setItemWidget(item, row_widget)
            self.checkboxes[path] = cb
            self.all_items.append((item, path, basename.lower()))
            
        repo_layout.addWidget(self.list_widget)
        content_layout.addWidget(repo_panel, 5)
        
        main_layout.addLayout(content_layout)
        
        # Footer Actions
        footer = QHBoxLayout()
        self.btn_cancel = QPushButton(TR("commit_hub_btn_discard"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setStyleSheet("color: #8B949E; background: transparent; padding: 12px; font-weight: bold;")
        
        self.btn_commit = QPushButton(TR("commit_hub_btn_confirm"))
        self.btn_commit.setFixedWidth(260)
        self.btn_commit.clicked.connect(self.accept)
        self.btn_commit.setStyleSheet("""
            QPushButton { background-color: #238636; color: white; border-radius: 8px; padding: 15px; font-weight: 800; font-size: 14px; }
            QPushButton:hover { background-color: #2EA043; }
            QPushButton:pressed { background-color: #26a641; }
        """)
        
        footer.addStretch()
        footer.addWidget(self.btn_cancel)
        footer.addWidget(self.btn_commit)
        main_layout.addLayout(footer)
        
        self._update_stats()

    def _on_filter_changed(self, text):
        search = text.lower()
        for item, path, name in self.all_items:
            item.setHidden(search not in name)

    def _update_stats(self):
        count = sum(1 for cb in self.checkboxes.values() if cb.isChecked())
        self.lbl_stats.setText(TR("commit_hub_stats", count=count))
        self.btn_commit.setEnabled(count > 0)

    def _select_dirty(self):
        for item, path, name in self.all_items:
            # Re-check status from row widget if available or we can use another way.
            # For simplicity, we'll iterate the checkboxes.
            # If the status label in the row widget contains MODIFIED...
            row_widget = self.list_widget.itemWidget(item)
            if row_widget:
                status_lbl = row_widget.findChild(QLabel)
                if status_lbl and ("MODIFIED" in status_lbl.text() or "commits" in status_lbl.text()):
                    self.checkboxes[path].setChecked(True)

    def get_data(self):
        selected = [p for p, cb in self.checkboxes.items() if cb.isChecked()]
        return self.edit_title.text().strip(), self.edit_body.toPlainText().strip(), selected

# ── Conflict Resolution Dialog ───────────────────────────────────────────────

class ConflictHubDialog(QDialog):
    def __init__(self, conflict_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(TR("conflict_hub_title"))
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.setStyleSheet("background-color: #0D1117; color: #C9D1D9; font-family: 'JetBrains Mono';")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30,30,30,30)
        layout.setSpacing(20)
        
        header = QLabel(TR("conflict_hub_header"))
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #FF7B72;")
        layout.addWidget(header)
        
        desc = QLabel(TR("conflict_hub_desc"))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8B949E; font-size: 13px;")
        layout.addWidget(desc)
        
        from PySide6.QtWidgets import QListWidget, QListWidgetItem
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; outline: none;")
        
        for path, detail, output in conflict_data:
            item = QListWidgetItem(self.list_widget)
            
            card = QFrame()
            card.setStyleSheet("background-color: #0D1117; margin: 5px; border-radius: 6px; border: 1px solid #FF7B72;")
            item_ly = QHBoxLayout(card)
            
            info_v = QVBoxLayout()
            name_lbl = QLabel(os.path.basename(path))
            name_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #F0F6FC;")
            info_v.addWidget(name_lbl)
            
            err_lbl = QLabel(detail)
            err_lbl.setStyleSheet("color: #FF7B72; font-size: 11px;")
            info_v.addWidget(err_lbl)
            item_ly.addLayout(info_v)
            
            item_ly.addStretch()
            
            # Actions
            btn_folder = QPushButton(TR("conflict_hub_btn_explorer"))
            btn_folder.setFixedWidth(90)
            btn_folder.setStyleSheet("background-color: #21262D; border: 1px solid #30363D; padding: 6px;")
            btn_folder.clicked.connect(lambda checked=False, p=path: self._open_folder(p))
            item_ly.addWidget(btn_folder)
            
            btn_solve = QPushButton(TR("conflict_hub_btn_solve"))
            btn_solve.setFixedWidth(90)
            btn_solve.setStyleSheet("background-color: #388BFD; color: white; border: none; padding: 6px; font-weight: bold;")
            btn_solve.clicked.connect(lambda checked=False, p=path: self._solve_in_editor(p))
            item_ly.addWidget(btn_solve)
            
            btn_abort = QPushButton(TR("conflict_hub_btn_abort"))
            btn_abort.setFixedWidth(90)
            btn_abort.setStyleSheet("background-color: #BF4440; color: white; border: none; padding: 6px;")
            btn_abort.clicked.connect(lambda checked=False, p=path: self._abort_merge(p))
            item_ly.addWidget(btn_abort)
            
            item.setSizeHint(card.sizeHint())
            self.list_widget.setItemWidget(item, card)
            
        layout.addWidget(self.list_widget)
        
        btn_close = QPushButton(TR("conflict_hub_btn_close"))
        btn_close.setStyleSheet("background-color: #238636; color: white; padding: 12px; font-weight: bold; border-radius: 6px;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _open_folder(self, path):
        import os
        if os.name == 'nt':
            os.startfile(path)
        else:
            import subprocess
            subprocess.Popen(['xdg-open', path])

    def _solve_in_editor(self, path):
        # We launch the editor in a separate process so we don't block the UI
        try:
            from model import open_external_editor
            # Note: GUI version of open_external_editor shouldn't be blocking in a way that hangs UI.
            # But the 'subprocess.call' in my model is blocking.
            # For GUI, I should probably just launch the editor and not wait for content if we just want them to solve conflicts.
            editor = os.environ.get('EDITOR') or ('notepad.exe' if os.name == 'nt' else 'nano')
            import subprocess
            
            # ── Windows specific: Suppress console windows for silent GUI
            creationflags = 0
            if os.name == 'nt':
                creationflags = 0x08000000 # subprocess.CREATE_NO_WINDOW

            subprocess.Popen([editor, path], creationflags=creationflags) # Open the folder in editor or the conflicted path
        except Exception as e:
            QMessageBox.critical(self, "GitBulk", TR("conflict_hub_err_editor", e=e))

    def _abort_merge(self, path):
        try:
            from model import run_git_operation
            run_git_operation(path, "run_raw", cmd=["merge", "--abort"])
            QMessageBox.information(self, "GitBulk", TR("conflict_hub_msg_aborted", name=os.path.basename(path)))
        except Exception as e:
             QMessageBox.critical(self, "GitBulk", TR("conflict_hub_err_abort", e=e))

# ── Group Inspector Dialog ───────────────────────────────────────────────────

class GroupSummaryDialog(QDialog):
    def __init__(self, topology, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
        self.setWindowTitle(TR("dlg_group_inspector_title"))
        self.resize(500, 600)
        self.setStyleSheet("background-color: #0F0F0F; color: #EEEEEE; font-family: 'JetBrains Mono';")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel(TR("dlg_group_inspector_header"))
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #E2E2E2; margin-bottom: 10px;")
        layout.addWidget(header)
        
        tree = QTreeWidget()
        tree.setColumnCount(1)
        tree.setHeaderHidden(True)
        tree.setStyleSheet("""
            QTreeWidget { background-color: #161616; border: 1px solid #262626; padding: 10px; }
            QTreeWidget::item { padding: 4px; }
        """)
        
        # Sort groups: Uncategorized last
        sorted_groups = sorted(topology.keys(), key=lambda x: (1 if x == "Uncategorized" else 0, x.lower()))
        
        for group_name in sorted_groups:
            repos = topology[group_name]
            g_item = QTreeWidgetItem(tree)
            g_item.setText(0, f"{group_name} ({len(repos)})")
            g_item.setFont(0, QFont("JetBrains Mono", 11, QFont.Bold))

            for r in repos:
                r_name = os.path.basename(r["path"])
                r_item = QTreeWidgetItem(g_item)
                r_item.setText(0, r_name)
                r_item.setForeground(0, QColor("#E2E2E2"))
                r_item.setToolTip(0, r["path"])
                
                # Fetch live status from parent (MainWindow)
                if isinstance(parent, QMainWindow):
                    status_text = "—"
                    node = parent._find_repo_node(r["path"])
                    if node:
                        m = parent.repo_model
                        row = node.row()
                        p = node.parent() or m.invisibleRootItem()
                        st_item = p.child(row, 2)
                        status_text = st_item.text() if st_item else "—"
                    
                    # Status dot icon
                    dot_color = "#58A6FF" # Clean
                    if "MODIFIED" in status_text or "commits" in status_text:
                        dot_color = "#F0DF5A"
                    elif "ERROR" in status_text:
                        dot_color = "#F85149"
                    
                    r_item.setIcon(0, get_icon("dot", dot_color))
        
        layout.addWidget(tree)
        
        btn_close = QPushButton(TR("dlg_group_inspector_btn_close"))
        btn_close.setStyleSheet("""
            QPushButton { background-color: #21262D; border: 1px solid #30363D; padding: 8px; border-radius: 4px; color: white; }
            QPushButton:hover { background-color: #30363D; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.topology = topology

    def _on_item_double_clicked(self, item, column):
        # If it's a group (parent item)
        if item.childCount() > 0 or item.parent() is None:
            group_name = item.text(0).split(" (")[0]
            if isinstance(self.parent(), QMainWindow):
                self.parent().focus_on_group(group_name)
                self.accept()

# ── Sync Preview Dialog ──────────────────────────────────────────────────────

class SyncPreviewDialog(QDialog):
    def __init__(self, to_clone, to_archive, parent=None):
        super().__init__(parent)
        self.setWindowTitle(TR("sync_preview_title"))
        self.setMinimumWidth(700)
        self.setMinimumHeight(550)
        self.setStyleSheet("background-color: #0F0F0F; color: #EEEEEE; font-family: 'JetBrains Mono';")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Glassmorphism header style
        header_box = QFrame()
        header_box.setStyleSheet("background-color: #1A1A1A; border-radius: 8px; border: 1px solid #30363D;")
        header_layout = QVBoxLayout(header_box)
        
        title = QLabel(TR("sync_preview_header"))
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #58A6FF; border: none;")
        header_layout.addWidget(title)
        
        subtitle = QLabel(TR("sync_preview_subtitle", clone=len(to_clone), archive=len(to_archive)))
        subtitle.setStyleSheet("font-size: 11px; color: #888888; border: none;")
        header_layout.addWidget(subtitle)
        
        main_layout.addWidget(header_box)
        
        from PySide6.QtWidgets import QListWidget, QListWidgetItem
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: transparent; border: none; }
            QListWidget::item { background-color: #161616; border: 1px solid #30363D; border-radius: 6px; margin-bottom: 8px; padding: 10px; }
            QListWidget::item:hover { background-color: #1C1C1C; }
        """)
        self.list_widget.setSpacing(8)
        
        # Add Clone Items
        for path, info in to_clone:
            self._add_card(path, TR("sync_preview_clone"), "#4CAF50", info.get("url", "External source"))
            
        # Add Archive Items
        for path in to_archive:
            self._add_card(path, TR("sync_preview_archive"), "#FF5252", TR("sync_preview_archive_path"))
            
        main_layout.addWidget(self.list_widget)
        
        # Danger zone / warning
        if to_archive:
            warn_box = QFrame()
            warn_box.setStyleSheet("background-color: #211910; border-radius: 4px; padding: 8px;")
            warn_layout = QHBoxLayout(warn_box)
            warn_icon = QLabel()
            warn_icon.setPixmap(get_icon("info", "#F0A033").pixmap(16, 16))
            warn_layout.addWidget(warn_icon)
            warn_text = QLabel(TR("sync_preview_warn"))
            warn_text.setStyleSheet("color: #F0A033; font-size: 10px;")
            warn_layout.addWidget(warn_text)
            warn_layout.addStretch()
            main_layout.addWidget(warn_box)
            
        # Footer
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton(TR("sync_preview_btn_dismiss"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setStyleSheet("padding: 10px; color: #888888; background: transparent; border: 1px solid #30363D;")
        
        self.btn_confirm = QPushButton(TR("sync_preview_btn_confirm"))
        self.btn_confirm.clicked.connect(self.accept)
        self.btn_confirm.setStyleSheet("""
            QPushButton { background-color: #238636; color: white; border: none; padding: 12px; font-weight: bold; border-radius: 6px; }
            QPushButton:hover { background-color: #2EA043; }
        """)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        main_layout.addLayout(btn_layout)

    def _add_card(self, path, action_text, color_hex, detail_text):
        item = QListWidgetItem(self.list_widget)
        card = QWidget()
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)
        
        # Icon
        icon_lbl = QLabel()
        icon_name = "download" if action_text == "CLONE" else "archive"
        icon_lbl.setPixmap(get_icon(icon_name, color_hex).pixmap(24, 24))
        card_layout.addWidget(icon_lbl)
        
        # Text block
        text_layout = QVBoxLayout()
        name_lbl = QLabel(os.path.basename(path))
        name_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #E2E2E2;")
        text_layout.addWidget(name_lbl)
        
        detail_lbl = QLabel(detail_text)
        detail_lbl.setStyleSheet("font-size: 10px; color: #888888;")
        text_layout.addWidget(detail_lbl)
        card_layout.addLayout(text_layout)
        
        card_layout.addStretch()
        
        # Badge
        badge = QLabel(f" {action_text} ")
        badge.setStyleSheet(f"""
            background-color: transparent; border: 1px solid {color_hex}; 
            color: {color_hex}; border-radius: 10px; font-size: 9px; 
            font-weight: bold; padding: 2px 8px;
        """)
        card_layout.addWidget(badge)
        
        item.setSizeHint(card.sizeHint())
        self.list_widget.setItemWidget(item, card)
