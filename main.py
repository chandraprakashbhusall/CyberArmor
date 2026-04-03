"""
CyberArmor – Main Application Entry Point
Loads the login window, then routes to user dashboard or admin panel.

Changes:
- Theme is applied before any window is shown (fixes blank theme on startup)
- Global font size is set here so all widgets are readable at maximize
- Sidebar and navigation are unchanged in structure but styles are cleaned up
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame,
    QMenu, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import db
from tools import theme

from Form.login import AuthWindow
from tools.home       import HomeWidget
from tools.port       import PortScannerWidget
from tools.wifi       import WifiAdvancedWidget
from tools.link       import LinkScannerWidget
from tools.filescan   import FileScanWidget
from tools.system     import SystemSecurityWidget
from tools.ai         import AIWidget
from tools.setting    import SettingsWidget
from tools.password   import PasswordManagerWidget
from tools.email_spam import EmailSpamCheckerWidget
from tools.admin      import AdminPanelWidget

db.init_db()

# Admin credentials are checked in login.py too – kept here for clarity
ADMIN_EMAIL = "cyberarmor.np@gmail.com"
ADMIN_PASS  = "cyberarmor"


# ──────────────────────────────────────────────
# SIDEBAR NAVIGATION BUTTON
# ──────────────────────────────────────────────

class SidebarBtn(QPushButton):
    """A checkable sidebar button that changes style when active."""

    def __init__(self, text):
        super().__init__(text)
        self.setMinimumHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.set_active(False)

    def set_active(self, active):
        if active:
            self.setStyleSheet("""
            QPushButton {
                background: rgba(0,188,212,0.18);
                border: none;
                border-left: 3px solid #00BCD4;
                border-radius: 10px;
                text-align: left;
                padding-left: 18px;
                color: #00BCD4;
                font-weight: bold;
                font-size: 14px;
            }""")
        else:
            self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-left: 3px solid transparent;
                border-radius: 10px;
                text-align: left;
                padding-left: 18px;
                color: #64748b;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.04);
                color: #cbd5e1;
            }""")


# ──────────────────────────────────────────────
# MAIN APPLICATION WINDOW
# ──────────────────────────────────────────────

class CyberArmor(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberArmor – Advanced Security Suite")
        self.resize(1400, 860)

        self.user_row        = None
        self.page_refs       = {}
        self.sidebar_btns    = {}
        self.settings_widget = None

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Build sidebar and page area
        self.sidebar = self._build_sidebar()
        root.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)

        # Build all tool pages
        self.settings_widget = SettingsWidget()

        pages_def = [
            ("🏠  Home",              HomeWidget()),
            ("🔐  Password Manager",  PasswordManagerWidget()),
            ("🛠  Port Scanner",       PortScannerWidget()),
            ("📶  WiFi Analyzer",      WifiAdvancedWidget()),
            ("🔗  Link Inspector",     LinkScannerWidget()),
            ("📧  Email Spam Checker", EmailSpamCheckerWidget()),
            ("🤖  AI Chat",            AIWidget()),
            ("🗂  File Scanner",       FileScanWidget()),
            ("💻  System Scan",        SystemSecurityWidget()),
            ("⚙  Settings",           self.settings_widget),
        ]
        for text, widget in pages_def:
            self._add_page(text, widget)

        self._switch_page("🏠  Home")

    # ── SIDEBAR ──────────────────────────────

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(275)
        sidebar.setStyleSheet("""
        QFrame {
            background: #070d1a;
            border-right: 1px solid #1e293b;
            border-radius: 0;
        }""")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 26, 16, 22)
        layout.setSpacing(4)

        # Logo row
        logo_row = QHBoxLayout()
        logo_icon = QLabel("🛡")
        logo_icon.setFont(QFont("Segoe UI Emoji", 24))
        logo_icon.setStyleSheet("background: transparent;")

        logo_col = QVBoxLayout()
        logo_col.setSpacing(2)
        name_lbl = QLabel("CyberArmor")
        name_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        name_lbl.setStyleSheet("color: #e2e8f0; background: transparent;")
        ver_lbl  = QLabel("Security Suite v2.0")
        ver_lbl.setStyleSheet(
            "color: #00BCD4; font-size: 11px; font-weight: bold; "
            "letter-spacing: 1px; background: transparent;"
        )
        logo_col.addWidget(name_lbl)
        logo_col.addWidget(ver_lbl)

        logo_row.addWidget(logo_icon)
        logo_row.addLayout(logo_col)
        logo_row.addStretch()
        layout.addLayout(logo_row)
        layout.addSpacing(22)
        layout.addWidget(self._divider())
        layout.addSpacing(14)

        # Section label
        tools_lbl = QLabel("TOOLS")
        tools_lbl.setStyleSheet(
            "color: #334155; font-size: 10px; font-weight: bold; "
            "letter-spacing: 2px; background: transparent;"
        )
        layout.addWidget(tools_lbl)
        layout.addSpacing(6)

        # Navigation items
        nav_items = [
            "🏠  Home",
            "🔐  Password Manager",
            "🛠  Port Scanner",
            "📶  WiFi Analyzer",
            "🔗  Link Inspector",
            "📧  Email Spam Checker",
            "🤖  AI Chat",
            "🗂  File Scanner",
            "💻  System Scan",
            "⚙  Settings",
        ]
        for text in nav_items:
            btn = SidebarBtn(text)
            btn.clicked.connect(lambda checked, t=text: self._switch_page(t))
            self.sidebar_btns[text] = btn
            layout.addWidget(btn)

        layout.addStretch()
        layout.addWidget(self._divider())
        layout.addSpacing(12)

        # Profile button at the bottom
        self.profile_btn = QPushButton("👤  My Profile")
        self.profile_btn.setFixedHeight(48)
        self.profile_btn.setCursor(Qt.PointingHandCursor)
        self.profile_btn.clicked.connect(self._open_profile_menu)
        self.profile_btn.setStyleSheet("""
        QPushButton {
            background: #111827;
            border: 1px solid #1e293b;
            border-radius: 10px;
            text-align: left;
            padding-left: 16px;
            color: #cbd5e1;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: #1e293b;
            border-color: #00BCD4;
            color: #00BCD4;
        }""")
        layout.addWidget(self.profile_btn)

        return sidebar

    def _divider(self):
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #1e293b; border: none; border-radius: 0;")
        return line

    # ── PAGE MANAGEMENT ──────────────────────

    def _add_page(self, text, widget):
        """Wrap each tool widget in a scroll area and add to the stack."""
        container = QWidget()
        layout    = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(widget)

        layout.addWidget(scroll)
        self.pages.addWidget(container)
        self.page_refs[text] = container

    def _switch_page(self, key):
        if key not in self.page_refs:
            return
        self.pages.setCurrentWidget(self.page_refs[key])
        for text, btn in self.sidebar_btns.items():
            btn.set_active(text == key)

    # ── PROFILE MENU ─────────────────────────

    def _open_profile_menu(self):
        menu = QMenu(self)
        menu.addAction("⚙  Settings", lambda: self._switch_page("⚙  Settings"))
        menu.addSeparator()
        if self.user_row:
            menu.addAction(f"👤  {self.user_row[1]}")
        menu.addSeparator()
        menu.addAction("🚪  Logout", self.logout)
        menu.exec_(
            self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomLeft())
        )

    # ── USER SESSION ─────────────────────────

    def set_user(self, user_row):
        if not user_row:
            return
        full_user = db.get_user_by_username(user_row[1])
        self.user_row = full_user
        if self.settings_widget:
            self.settings_widget.set_user(full_user)
        if self.profile_btn and full_user:
            self.profile_btn.setText(f"👤  {full_user[1]}")

    def logout(self):
        self.close()
        self.login_window = AuthWindow()
        self.login_window.login_successful.connect(_start_main)
        self.login_window.show()


# ──────────────────────────────────────────────
# ADMIN WINDOW
# ──────────────────────────────────────────────

class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberArmor – Admin Panel")
        self.resize(1440, 880)

        panel = AdminPanelWidget()
        panel.logoutSignal.connect(self._logout)
        self.setCentralWidget(panel)

    def _logout(self):
        self.close()
        login = AuthWindow()
        login.login_successful.connect(_start_main)
        login.show()
        global _login_window
        _login_window = login


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────

_main_window  = None
_admin_window = None
_login_window = None


def _start_main(user_row):
    global _main_window, _admin_window, _login_window

    if _login_window:
        _login_window.close()

    if user_row == "ADMIN":
        _admin_window = AdminWindow()
        _admin_window.showMaximized()
        return

    _main_window = CyberArmor()
    _main_window.set_user(user_row)
    _main_window.showMaximized()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("CyberArmor")

    # Apply theme BEFORE creating any windows so all styles are set from start
    theme.apply_theme()

    _login_window = AuthWindow()
    _login_window.login_successful.connect(_start_main)
    _login_window.show()

    sys.exit(app.exec_())
