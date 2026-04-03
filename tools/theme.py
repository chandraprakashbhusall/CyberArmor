"""
CyberArmor – Global Theme Manager
Handles dark/light themes and accent colors.
This is the single source of truth for all colors in the app.
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

# ── Theme state (module-level so all files can import it) ──
current_theme  = "dark"
primary_color  = "#00BCD4"

# ── Base font size – increase this to make everything bigger ──
BASE_FONT_SIZE = 18


# =====================================================
# DARK THEME STYLESHEET
# =====================================================

DARK_THEME = """
QWidget {
    background-color: #0a0f1e;
    color: #e2e8f0;
    font-family: "Segoe UI", "SF Pro Display", sans-serif;
    font-size: BASE_SIZEpx;
}
QMainWindow, QDialog {
    background-color: #0a0f1e;
}
QFrame {
    background-color: #111827;
    border-radius: 12px;
}
QGroupBox {
    border: 1px solid #1e293b;
    border-radius: 10px;
    margin-top: 16px;
    padding: 16px 12px 12px 12px;
    background-color: #111827;
    font-size: BASE_SIZEpx;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    top: -8px;
    color: PRIMARY;
    font-weight: bold;
    font-size: BASE_SIZEpx;
}
QPushButton {
    background-color: #1e293b;
    border: 1px solid #334155;
    color: #e2e8f0;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 600;
    font-size: BASE_SIZEpx;
    min-height: 18px;
}
QPushButton:hover {
    background-color: PRIMARY;
    border: 1px solid PRIMARY;
    color: #000000;
}
QPushButton:pressed {
    background-color: #0097a7;
}
QPushButton:disabled {
    background-color: #1a2233;
    color: #4b5563;
    border-color: #1e293b;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: #0f1929;
    border: 1px solid #1e293b;
    color: #e2e8f0;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: BASE_SIZEpx;
    selection-background-color: PRIMARY;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1.5px solid PRIMARY;
}
QComboBox {
    background-color: #0f1929;
    border: 1px solid #1e293b;
    color: #e2e8f0;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: BASE_SIZEpx;
    min-height: 18px;
}
QComboBox::drop-down {
    border: none;
    width: 26px;
}
QComboBox QAbstractItemView {
    background-color: #111827;
    border: 1px solid #1e293b;
    selection-background-color: PRIMARY;
    color: #e2e8f0;
    font-size: BASE_SIZEpx;
}
QTableWidget {
    background-color: #0a0f1e;
    alternate-background-color: #0f1929;
    gridline-color: #1e293b;
    border: 1px solid #1e293b;
    border-radius: 8px;
    selection-background-color: rgba(0,188,212,0.25);
    font-size: BASE_SIZEpx;
}
QTableWidget::item {
    padding: 8px 12px;
    color: #e2e8f0;
}
QTableWidget::item:selected {
    color: PRIMARY;
    background-color: rgba(0,188,212,0.2);
}
QHeaderView::section {
    background-color: #111827;
    color: #94a3b8;
    padding: 10px;
    border: none;
    border-bottom: 2px solid PRIMARY;
    font-weight: bold;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QScrollBar:vertical {
    background: #0a0f1e;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: PRIMARY;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #0a0f1e;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #334155;
    border-radius: 4px;
    min-width: 30px;
}
QProgressBar {
    background-color: #1e293b;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 PRIMARY, stop:1 #0097a7);
    border-radius: 6px;
}
QLabel {
    background: transparent;
    color: #e2e8f0;
    font-size: BASE_SIZEpx;
}
QCheckBox {
    spacing: 8px;
    color: #e2e8f0;
    font-size: BASE_SIZEpx;
}
QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 2px solid #334155;
    background: #0f1929;
}
QCheckBox::indicator:checked {
    background: PRIMARY;
    border-color: PRIMARY;
}
QMenu {
    background-color: #111827;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 4px;
    font-size: BASE_SIZEpx;
}
QMenu::item {
    padding: 10px 22px;
    border-radius: 6px;
    color: #e2e8f0;
}
QMenu::item:selected {
    background-color: PRIMARY;
    color: black;
}
QSplitter::handle {
    background: #1e293b;
    width: 2px;
}
QListWidget {
    background-color: #0f1929;
    border: 1px solid #1e293b;
    border-radius: 8px;
    outline: none;
    font-size: BASE_SIZEpx;
}
QListWidget::item {
    padding: 10px 14px;
    border-radius: 6px;
    color: #cbd5e1;
}
QListWidget::item:selected {
    background-color: rgba(0,188,212,0.2);
    color: PRIMARY;
}
QListWidget::item:hover {
    background-color: #1e293b;
}
QTabWidget::pane {
    border: 1px solid #1e293b;
    border-radius: 8px;
    background: #111827;
}
QTabBar::tab {
    background: #0a0f1e;
    color: #64748b;
    padding: 10px 22px;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
    font-weight: 600;
    font-size: BASE_SIZEpx;
}
QTabBar::tab:selected {
    background: PRIMARY;
    color: black;
}
QTabBar::tab:hover:!selected {
    background: #1e293b;
    color: #e2e8f0;
}
QToolTip {
    background: #111827;
    border: 1px solid PRIMARY;
    color: #e2e8f0;
    padding: 6px;
    border-radius: 6px;
    font-size: 12px;
}
QScrollArea {
    background: #0a0f1e;
    border: none;
}
"""


# =====================================================
# LIGHT THEME STYLESHEET
# =====================================================

LIGHT_THEME = """
QWidget {
    background-color: #f1f5f9;
    color: #0f172a;
    font-family: "Segoe UI", "SF Pro Display", sans-serif;
    font-size: BASE_SIZEpx;
}
QMainWindow, QDialog {
    background-color: #f1f5f9;
}
QFrame {
    background-color: #ffffff;
    border-radius: 12px;
}
QGroupBox {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    margin-top: 16px;
    padding: 16px 12px 12px 12px;
    background-color: #ffffff;
    font-size: BASE_SIZEpx;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    top: -8px;
    color: PRIMARY;
    font-weight: bold;
    font-size: BASE_SIZEpx;
}
QPushButton {
    background-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    color: #0f172a;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 600;
    font-size: BASE_SIZEpx;
    min-height: 18px;
}
QPushButton:hover {
    background-color: PRIMARY;
    border: 1px solid PRIMARY;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #0097a7;
}
QPushButton:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0f172a;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: BASE_SIZEpx;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid PRIMARY;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    color: #0f172a;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: BASE_SIZEpx;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    selection-background-color: PRIMARY;
    color: #0f172a;
    font-size: BASE_SIZEpx;
}
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    gridline-color: #e2e8f0;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    selection-background-color: rgba(0,188,212,0.15);
    font-size: BASE_SIZEpx;
}
QTableWidget::item {
    padding: 8px 12px;
    color: #0f172a;
}
QTableWidget::item:selected {
    color: PRIMARY;
    background-color: rgba(0,188,212,0.15);
}
QHeaderView::section {
    background-color: #f1f5f9;
    color: #64748b;
    padding: 10px;
    border: none;
    border-bottom: 2px solid PRIMARY;
    font-weight: bold;
    font-size: 12px;
}
QScrollBar:vertical {
    background: #f1f5f9;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: PRIMARY; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QProgressBar {
    background-color: #e2e8f0;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 PRIMARY, stop:1 #0097a7);
    border-radius: 6px;
}
QLabel {
    background: transparent;
    color: #0f172a;
    font-size: BASE_SIZEpx;
}
QCheckBox {
    spacing: 8px;
    color: #0f172a;
    font-size: BASE_SIZEpx;
}
QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 2px solid #cbd5e1;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: PRIMARY;
    border-color: PRIMARY;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
    font-size: BASE_SIZEpx;
}
QMenu::item { padding: 10px 22px; border-radius: 6px; color: #0f172a; }
QMenu::item:selected { background-color: PRIMARY; color: white; }
QListWidget {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    outline: none;
    font-size: BASE_SIZEpx;
}
QListWidget::item { padding: 10px 14px; border-radius: 6px; color: #334155; }
QListWidget::item:selected { background-color: rgba(0,188,212,0.15); color: PRIMARY; }
QListWidget::item:hover { background-color: #f1f5f9; }
QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 8px; background: #ffffff; }
QTabBar::tab {
    background: #f1f5f9; color: #64748b;
    padding: 10px 22px; border-radius: 6px 6px 0 0;
    margin-right: 2px; font-weight: 600; font-size: BASE_SIZEpx;
}
QTabBar::tab:selected { background: PRIMARY; color: white; }
QTabBar::tab:hover:!selected { background: #e2e8f0; color: #0f172a; }
QGroupBox { background-color: #ffffff; }
QToolTip { background: #ffffff; border: 1px solid PRIMARY; color: #0f172a; padding: 6px; border-radius: 6px; }
QScrollArea { background: #f1f5f9; border: none; }
QTextEdit { color: #0f172a; background: #ffffff; }
"""


# =====================================================
# PUBLIC API
# =====================================================

def get_stylesheet():
    """Build and return the current stylesheet with color/size substitutions."""
    base = DARK_THEME if current_theme == "dark" else LIGHT_THEME
    return (base
            .replace("PRIMARY", primary_color)
            .replace("BASE_SIZE", str(BASE_FONT_SIZE)))


def set_theme(mode):
    """Switch between 'dark' and 'light'."""
    global current_theme
    current_theme = mode
    apply_theme()


def set_primary_color(color):
    """Change the accent/primary color and re-apply."""
    global primary_color
    primary_color = color
    apply_theme()


def apply_theme():
    """
    Apply the stylesheet to the whole QApplication.
    Also sets the global font size so widgets not using stylesheets
    still get a readable size.
    """
    app = QApplication.instance()
    if not app:
        return

    # Apply global QSS
    app.setStyleSheet(get_stylesheet())

    # Set app-wide default font size (helps widgets that ignore QSS)
    font = app.font()
    font.setPointSize(BASE_FONT_SIZE)
    app.setFont(font)

    # Force every top-level widget to re-polish so the new sheet takes effect
    for widget in app.topLevelWidgets():
        widget.setStyleSheet(widget.styleSheet())   # nudge Qt
        widget.update()


def is_dark():
    return current_theme == "dark"


def get_primary():
    return primary_color


# ── Helper: returns text color for current theme ──
def text_color():
    return "#e2e8f0" if is_dark() else "#0f172a"


# ── Helper: card background for current theme ──
def card_bg():
    return "#111827" if is_dark() else "#ffffff"


# ── Helper: window background ──
def window_bg():
    return "#0a0f1e" if is_dark() else "#f1f5f9"


# ── Helper: border color ──
def border_color():
    return "#1e293b" if is_dark() else "#e2e8f0"


# ── Helper: muted text ──
def muted_color():
    return "#64748b"
