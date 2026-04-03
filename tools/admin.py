"""
CyberArmor – Admin Panel
Full admin dashboard with user management, scan history,
feedback viewer, activity log, and database tools.

Changes in this version:
- Feedback table: click any row to open full message in a popup dialog
- Removed broadcast section (it was just logging to activity, not useful)
- Activity log properly shows tool name + username from real scans
- Dashboard tool bars now pull real data from logged scans
- Port and link scan history pages show actual scan data from DB
- Click port scan row → see all open ports in a detail popup
- Click link scan row → see all security flags in a detail popup
- DB Tools page: export JSON + export summary TXT + clear logs
- Nicer row heights and font sizes throughout
"""

import json
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QTextEdit, QCheckBox, QMessageBox,
    QFileDialog, QProgressBar, QGraphicsDropShadowEffect, QDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor

import db


# ══════════════════════════════════════════════
# FEEDBACK DETAIL DIALOG
# ══════════════════════════════════════════════

class FeedbackDialog(QDialog):
    """Clean popup to read full feedback message when admin clicks a row."""

    def __init__(self, parent, username, rating, category, message, submitted_at):
        super().__init__(parent)
        self.setWindowTitle("Feedback Detail")
        self.setFixedSize(520, 360)
        self.setStyleSheet("QDialog { background: #0f172a; } QLabel { background: transparent; color: #e2e8f0; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Username + star rating row
        header_row = QHBoxLayout()
        user_lbl = QLabel("👤  " + str(username))
        user_lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
        user_lbl.setStyleSheet("color: #00BCD4; background: transparent;")
        header_row.addWidget(user_lbl)
        header_row.addStretch()

        # Show filled and empty stars
        try:
            filled = int(rating)
        except Exception:
            filled = 0
        stars = "★" * filled + "☆" * (5 - filled)
        star_lbl = QLabel(stars)
        star_lbl.setStyleSheet("color: #f59e0b; font-size: 18px; background: transparent;")
        header_row.addWidget(star_lbl)
        layout.addLayout(header_row)

        # Category badge + date
        meta_row = QHBoxLayout()
        cat_badge = QLabel("  " + str(category) + "  ")
        cat_badge.setStyleSheet(
            "background: rgba(0,188,212,0.15); color: #00BCD4; border-radius: 6px; "
            "padding: 4px 8px; font-size: 12px; font-weight: bold;"
        )
        meta_row.addWidget(cat_badge)
        meta_row.addStretch()
        date_lbl = QLabel(str(submitted_at))
        date_lbl.setStyleSheet("color: #475569; font-size: 12px; background: transparent;")
        meta_row.addWidget(date_lbl)
        layout.addLayout(meta_row)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #1e293b; border: none;")
        layout.addWidget(sep)

        # Full message in read-only text area
        msg_area = QTextEdit()
        msg_area.setReadOnly(True)
        msg_area.setPlainText(message)
        msg_area.setStyleSheet(
            "QTextEdit { background: #111827; border: 1px solid #1e293b; border-radius: 10px; "
            "padding: 12px; color: #cbd5e1; font-size: 14px; font-family: 'Segoe UI'; }"
        )
        layout.addWidget(msg_area)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(42)
        close_btn.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00BCD4, stop:1 #0097a7); "
            "border: none; border-radius: 10px; color: black; font-weight: bold; font-size: 14px; }"
            "QPushButton:hover { background: #26C6DA; }"
        )
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


# ══════════════════════════════════════════════
# STAT CARD
# ══════════════════════════════════════════════

class StatCard(QFrame):
    """KPI card shown at the top of the dashboard."""

    def __init__(self, title, value, icon, accent="#00BCD4"):
        super().__init__()
        self.accent = accent
        self.setFixedHeight(118)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #111827, stop:1 #0f172a); "
            "border-radius: 14px; border: 1px solid #1e293b; }"
            "QFrame:hover { border: 1px solid " + accent + "; }"
        )

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(16)

        r, g, b = self._hex_rgb(accent)
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(52, 52)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 22))
        icon_lbl.setStyleSheet("QLabel { background: rgba(" + str(r) + "," + str(g) + "," + str(b) + ", 0.15); border-radius: 26px; }")
        layout.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.val_lbl.setStyleSheet("color: " + accent + "; background: transparent;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        text_col.addWidget(self.val_lbl)
        text_col.addWidget(title_lbl)
        layout.addLayout(text_col)
        layout.addStretch()

    def set_value(self, v):
        self.val_lbl.setText(str(v))

    def _hex_rgb(self, h):
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# ══════════════════════════════════════════════
# SIDEBAR BUTTON
# ══════════════════════════════════════════════

class SidebarBtn(QPushButton):
    def __init__(self, icon, label):
        super().__init__("  " + icon + "  " + label)
        self.setCheckable(True)
        self.setFixedHeight(46)
        self.setFont(QFont("Segoe UI", 13))
        self.setCursor(Qt.PointingHandCursor)
        self.setActive(False)

    def setActive(self, active):
        if active:
            self.setStyleSheet(
                "QPushButton { background: rgba(0,188,212,0.18); border: none; border-left: 3px solid #00BCD4; "
                "border-radius: 10px; text-align: left; padding-left: 16px; color: #00BCD4; font-weight: bold; font-size: 13px; }"
            )
        else:
            self.setStyleSheet(
                "QPushButton { background: transparent; border: none; border-left: 3px solid transparent; "
                "border-radius: 10px; text-align: left; padding-left: 16px; color: #64748b; font-size: 13px; }"
                "QPushButton:hover { background: rgba(255,255,255,0.05); color: #e2e8f0; }"
            )


# ══════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════

class AdminPanelWidget(QWidget):

    logoutSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setMinimumSize(1280, 780)
        self._feedback_data   = []
        self._port_scan_data  = []
        self._link_scan_data  = []

        # Pages must be built before sidebar
        self._build_ui()
        self._load_all_data()

        # Auto-refresh every 30 seconds
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_all_data)
        self.refresh_timer.start(30_000)

    # ──────────────────────────────────────────
    # BUILD UI
    # ──────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Build all content pages first
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #0a0f1e;")

        self.page_dashboard  = self._build_dashboard_page()
        self.page_users      = self._build_users_page()
        self.page_stats      = self._build_stats_page()
        self.page_port_hist  = self._build_port_history_page()
        self.page_link_hist  = self._build_link_history_page()
        self.page_feedback   = self._build_feedback_page()
        self.page_activity   = self._build_activity_page()
        self.page_tools      = self._build_tools_page()

        for p in [self.page_dashboard, self.page_users, self.page_stats,
                  self.page_port_hist, self.page_link_hist,
                  self.page_feedback, self.page_activity, self.page_tools]:
            self.stack.addWidget(p)

        # Build sidebar after pages so it can reference them
        root.addWidget(self._build_sidebar())
        root.addWidget(self.stack, 1)
        self._switch_page(self.page_dashboard, self.btn_dashboard)

    # ──────────────────────────────────────────
    # SIDEBAR
    # ──────────────────────────────────────────

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet(
            "QFrame { background: #070d1a; border-right: 1px solid #1e293b; border-radius: 0px; }"
        )
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 26, 14, 20)
        layout.setSpacing(4)

        # Logo
        logo_row = QHBoxLayout()
        logo_icon = QLabel("🛡")
        logo_icon.setFont(QFont("Segoe UI Emoji", 22))
        logo_icon.setStyleSheet("background: transparent;")
        logo_col = QVBoxLayout()
        name_lbl = QLabel("CyberArmor")
        name_lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
        name_lbl.setStyleSheet("color: #e2e8f0; background: transparent;")
        sub_lbl = QLabel("Admin Panel")
        sub_lbl.setStyleSheet("color: #00BCD4; font-size: 11px; background: transparent; font-weight: bold; letter-spacing: 2px;")
        logo_col.addWidget(name_lbl)
        logo_col.addWidget(sub_lbl)
        logo_row.addWidget(logo_icon)
        logo_row.addLayout(logo_col)
        logo_row.addStretch()
        layout.addLayout(logo_row)
        layout.addSpacing(22)
        layout.addWidget(self._line())
        layout.addSpacing(10)

        nav_lbl = QLabel("NAVIGATION")
        nav_lbl.setStyleSheet("color: #334155; font-size: 10px; font-weight: bold; letter-spacing: 2px; background: transparent;")
        layout.addWidget(nav_lbl)
        layout.addSpacing(4)

        self.btn_dashboard = SidebarBtn("📊", "Dashboard")
        self.btn_users     = SidebarBtn("👥", "Users")
        self.btn_stats     = SidebarBtn("📈", "Statistics")
        self.btn_port_hist = SidebarBtn("🚀", "Port Scan History")
        self.btn_link_hist = SidebarBtn("🔗", "Link Scan History")
        self.btn_feedback  = SidebarBtn("💬", "Feedback")
        self.btn_activity  = SidebarBtn("⚡", "Activity Log")
        self.btn_tools     = SidebarBtn("🛠", "DB & Tools")

        self.sidebar_btns = [
            self.btn_dashboard, self.btn_users, self.btn_stats,
            self.btn_port_hist, self.btn_link_hist,
            self.btn_feedback, self.btn_activity, self.btn_tools,
        ]

        pairs = [
            (self.btn_dashboard, self.page_dashboard),
            (self.btn_users,     self.page_users),
            (self.btn_stats,     self.page_stats),
            (self.btn_port_hist, self.page_port_hist),
            (self.btn_link_hist, self.page_link_hist),
            (self.btn_feedback,  self.page_feedback),
            (self.btn_activity,  self.page_activity),
            (self.btn_tools,     self.page_tools),
        ]
        for btn, page in pairs:
            btn.clicked.connect(lambda checked, b=btn, p=page: self._switch_page(p, b))
            layout.addWidget(btn)

        layout.addStretch()
        layout.addWidget(self._line())
        layout.addSpacing(10)

        logout_btn = QPushButton("  🚪  Logout")
        logout_btn.setFixedHeight(44)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(
            "QPushButton { background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.3); "
            "border-radius: 10px; color: #ef4444; font-weight: bold; font-size: 13px; "
            "text-align: left; padding-left: 16px; }"
            "QPushButton:hover { background: rgba(239,68,68,0.28); }"
        )
        logout_btn.clicked.connect(self.logoutSignal.emit)
        layout.addWidget(logout_btn)
        return sidebar

    def _line(self):
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #1e293b; border: none; border-radius: 0;")
        return line

    # ══════════════════════════════════════════
    # PAGE: DASHBOARD
    # ══════════════════════════════════════════

    def _build_dashboard_page(self):
        page = QWidget()
        page.setStyleSheet("background: #0a0f1e;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)

        hdr = QHBoxLayout()
        tcol = QVBoxLayout()
        t = QLabel("Dashboard Overview")
        t.setFont(QFont("Segoe UI", 22, QFont.Bold))
        t.setStyleSheet("color: #e2e8f0; background: transparent;")
        s = QLabel("Live statistics from CyberArmor usage")
        s.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        tcol.addWidget(t); tcol.addWidget(s)
        hdr.addLayout(tcol); hdr.addStretch()
        rb = self._small_btn("↺  Refresh")
        rb.clicked.connect(self._load_all_data)
        hdr.addWidget(rb)
        layout.addLayout(hdr)

        # KPI cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        self.card_users    = StatCard("Total Users",    0,   "👥", "#00BCD4")
        self.card_scans    = StatCard("Total Scans",    0,   "🔍", "#8b5cf6")
        self.card_tools    = StatCard("Tools Used",     0,   "🛠",  "#f59e0b")
        self.card_feedback = StatCard("Feedback Count", 0,   "💬", "#10b981")
        self.card_rating   = StatCard("Avg Rating",     "—", "⭐", "#f97316")
        for c in [self.card_users, self.card_scans, self.card_tools,
                  self.card_feedback, self.card_rating]:
            cards_row.addWidget(c)
        layout.addLayout(cards_row)

        # Tool bars + recent users
        bottom = QHBoxLayout()
        bottom.setSpacing(20)

        tool_panel = self._section("🛠  Tool Usage Breakdown")
        self.tool_bars_layout = QVBoxLayout()
        self.tool_bars_layout.setSpacing(10)
        tool_panel.layout().addLayout(self.tool_bars_layout)
        bottom.addWidget(tool_panel, 3)

        users_panel = self._section("👥  Recent Registrations")
        self.recent_users_table = self._make_table(["Username", "Email", "Joined"])
        self.recent_users_table.setFixedHeight(220)
        users_panel.layout().addWidget(self.recent_users_table)
        bottom.addWidget(users_panel, 4)

        layout.addLayout(bottom)
        layout.addStretch()
        return page

    # ══════════════════════════════════════════
    # PAGE: USERS
    # ══════════════════════════════════════════

    def _build_users_page(self):
        page = QWidget()
        page.setStyleSheet("background: #0a0f1e;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        t = QLabel("User Management")
        t.setFont(QFont("Segoe UI", 20, QFont.Bold))
        t.setStyleSheet("color: #e2e8f0; background: transparent;")
        layout.addWidget(t)

        bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by username or email...")
        self.search_input.setFixedHeight(44)
        self.search_input.setStyleSheet(
            "QLineEdit { background: #111827; border: 1px solid #1e293b; border-radius: 10px; "
            "padding: 0 14px; color: #e2e8f0; font-size: 14px; }"
            "QLineEdit:focus { border-color: #00BCD4; }"
        )
        self.search_input.textChanged.connect(self._search_users)
        bar.addWidget(self.search_input, 1)

        del_btn = QPushButton("🗑  Delete Selected")
        del_btn.setFixedHeight(44)
        del_btn.setStyleSheet(
            "QPushButton { background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.4); "
            "border-radius: 10px; color: #ef4444; font-weight: bold; padding: 0 20px; font-size: 13px; }"
            "QPushButton:hover { background: rgba(239,68,68,0.3); }"
        )
        del_btn.clicked.connect(self._delete_users)
        bar.addWidget(del_btn)
        layout.addLayout(bar)

        self.user_count_lbl = QLabel("")
        self.user_count_lbl.setStyleSheet("color: #64748b; font-size: 12px; background: transparent;")
        layout.addWidget(self.user_count_lbl)

        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["☐", "Username", "Email", "Joined"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.user_table.setColumnWidth(0, 48)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.setAlternatingRowColors(True)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.verticalHeader().setDefaultSectionSize(40)
        self._style_table(self.user_table)
        layout.addWidget(self.user_table)
        return page

    # ══════════════════════════════════════════
    # PAGE: STATISTICS
    # ══════════════════════════════════════════

    def _build_stats_page(self):
        page = QWidget()
        page.setStyleSheet("background: #0a0f1e;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        t = QLabel("Statistics & Analytics")
        t.setFont(QFont("Segoe UI", 20, QFont.Bold))
        t.setStyleSheet("color: #e2e8f0; background: transparent;")
        layout.addWidget(t)

        cols = QHBoxLayout()
        cols.setSpacing(20)

        tf = self._section("🛠  Tool Usage Stats")
        self.stats_tool_table = self._make_table(["Tool Name", "Times Used"])
        tf.layout().addWidget(self.stats_tool_table)
        cols.addWidget(tf)

        uf = self._section("🔍  Scans Per User")
        self.stats_user_table = self._make_table(["Username", "Total Scans"])
        uf.layout().addWidget(self.stats_user_table)
        cols.addWidget(uf)

        layout.addLayout(cols)
        return page

    # ══════════════════════════════════════════
    # PAGE: PORT SCAN HISTORY
    # ══════════════════════════════════════════

    def _build_port_history_page(self):
        page = QWidget()
        page.setStyleSheet("background: #0a0f1e;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        hdr = QHBoxLayout()
        tcol = QVBoxLayout()
        t = QLabel("Port Scan History")
        t.setFont(QFont("Segoe UI", 20, QFont.Bold))
        t.setStyleSheet("color: #e2e8f0; background: transparent;")
        s = QLabel("All port scans done by users — click a row to see open ports")
        s.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        tcol.addWidget(t); tcol.addWidget(s)
        hdr.addLayout(tcol); hdr.addStretch()
        eb = self._small_btn("💾  Export TXT")
        eb.clicked.connect(self._export_port_history)
        hdr.addWidget(eb)
        rb = self._small_btn("↺  Refresh")
        rb.clicked.connect(self._load_port_history)
        hdr.addWidget(rb)
        layout.addLayout(hdr)

        hint = QLabel("💡  Click any row to see the full list of open ports found in that scan")
        hint.setStyleSheet(
            "background: rgba(0,188,212,0.08); border: 1px solid rgba(0,188,212,0.2); "
            "border-radius: 8px; padding: 8px 14px; color: #00BCD4; font-size: 13px;"
        )
        layout.addWidget(hint)

        self.port_hist_table = self._make_table(["Target", "Mode", "Open Ports", "OS Guess", "Scanned At"])
        self.port_hist_table.setCursor(Qt.PointingHandCursor)
        self.port_hist_table.cellClicked.connect(self._show_port_detail)
        layout.addWidget(self.port_hist_table)
        return page

    # ══════════════════════════════════════════
    # PAGE: LINK SCAN HISTORY
    # ══════════════════════════════════════════

    def _build_link_history_page(self):
        page = QWidget()
        page.setStyleSheet("background: #0a0f1e;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        hdr = QHBoxLayout()
        tcol = QVBoxLayout()
        t = QLabel("Link Scan History")
        t.setFont(QFont("Segoe UI", 20, QFont.Bold))
        t.setStyleSheet("color: #e2e8f0; background: transparent;")
        s = QLabel("All URLs scanned by users — click a row to see all security flags")
        s.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        tcol.addWidget(t); tcol.addWidget(s)
        hdr.addLayout(tcol); hdr.addStretch()
        eb = self._small_btn("💾  Export TXT")
        eb.clicked.connect(self._export_link_history)
        hdr.addWidget(eb)
        rb = self._small_btn("↺  Refresh")
        rb.clicked.connect(self._load_link_history)
        hdr.addWidget(rb)
        layout.addLayout(hdr)

        hint = QLabel("💡  Click any row to see all security flags for that URL")
        hint.setStyleSheet(
            "background: rgba(0,188,212,0.08); border: 1px solid rgba(0,188,212,0.2); "
            "border-radius: 8px; padding: 8px 14px; color: #00BCD4; font-size: 13px;"
        )
        layout.addWidget(hint)

        self.link_hist_table = self._make_table(["URL", "Domain", "Risk Score", "SSL", "Scanned At"])
        self.link_hist_table.setCursor(Qt.PointingHandCursor)
        self.link_hist_table.cellClicked.connect(self._show_link_detail)
        layout.addWidget(self.link_hist_table)
        return page

    # ══════════════════════════════════════════
    # PAGE: FEEDBACK (click row = full message popup)
    # ══════════════════════════════════════════

    def _build_feedback_page(self):
        page = QWidget()
        page.setStyleSheet("background: #0a0f1e;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        hdr = QHBoxLayout()
        tcol = QVBoxLayout()
        t = QLabel("User Feedback")
        t.setFont(QFont("Segoe UI", 20, QFont.Bold))
        t.setStyleSheet("color: #e2e8f0; background: transparent;")
        s = QLabel("Click any row to read the full feedback message")
        s.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        tcol.addWidget(t); tcol.addWidget(s)
        hdr.addLayout(tcol)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Summary bar
        self.feedback_summary = QLabel("")
        self.feedback_summary.setStyleSheet(
            "QLabel { background: #111827; border: 1px solid #1e293b; border-radius: 10px; "
            "padding: 12px 18px; color: #00BCD4; font-size: 14px; font-weight: bold; }"
        )
        layout.addWidget(self.feedback_summary)

        hint = QLabel("💡  Click any row below to open the full feedback message in a popup")
        hint.setStyleSheet(
            "background: rgba(0,188,212,0.08); border: 1px solid rgba(0,188,212,0.2); "
            "border-radius: 8px; padding: 8px 14px; color: #00BCD4; font-size: 13px;"
        )
        layout.addWidget(hint)

        # Feedback table — message is truncated in cell, full view on click
        self.feedback_table = self._make_table(
            ["Username", "Rating", "Category", "Message (click to expand)", "Submitted At"]
        )
        self.feedback_table.setCursor(Qt.PointingHandCursor)
        self.feedback_table.cellClicked.connect(self._show_feedback_detail)
        layout.addWidget(self.feedback_table)
        return page

    # ══════════════════════════════════════════
    # PAGE: ACTIVITY LOG
    # ══════════════════════════════════════════

    def _build_activity_page(self):
        page = QWidget()
        page.setStyleSheet("background: #0a0f1e;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        hdr = QHBoxLayout()
        tcol = QVBoxLayout()
        t = QLabel("Activity Log")
        t.setFont(QFont("Segoe UI", 20, QFont.Bold))
        t.setStyleSheet("color: #e2e8f0; background: transparent;")
        s = QLabel("Every tool used by every user — newest first")
        s.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        tcol.addWidget(t); tcol.addWidget(s)
        hdr.addLayout(tcol); hdr.addStretch()
        eb = self._small_btn("💾  Export TXT")
        eb.clicked.connect(self._export_activity)
        hdr.addWidget(eb)
        rb = self._small_btn("↺  Refresh")
        rb.clicked.connect(self._load_activity)
        hdr.addWidget(rb)
        layout.addLayout(hdr)

        self.activity_table = self._make_table(["Username", "Tool Used", "Timestamp"])
        layout.addWidget(self.activity_table)
        return page

    # ══════════════════════════════════════════
    # PAGE: DB & TOOLS (no broadcast — removed)
    # ══════════════════════════════════════════

    def _build_tools_page(self):
        page = QWidget()
        page.setStyleSheet("background: #0a0f1e;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)

        t = QLabel("Database & Admin Tools")
        t.setFont(QFont("Segoe UI", 20, QFont.Bold))
        t.setStyleSheet("color: #e2e8f0; background: transparent;")
        layout.addWidget(t)

        # Export section
        exp_frame = self._section("💾  Full Database Export")
        exp_layout = exp_frame.layout()
        desc = QLabel(
            "Export the entire CyberArmor database.\n"
            "Includes all users, scan results, feedback, and activity logs."
        )
        desc.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent;")
        desc.setWordWrap(True)
        exp_layout.addWidget(desc)

        btn_row = QHBoxLayout()
        json_btn = QPushButton("💾  Export as JSON")
        json_btn.setFixedHeight(46)
        json_btn.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00BCD4, stop:1 #0097a7); "
            "border: none; border-radius: 10px; color: black; font-weight: bold; font-size: 14px; }"
            "QPushButton:hover { background: #26C6DA; }"
        )
        json_btn.clicked.connect(self._export_full_db)
        btn_row.addWidget(json_btn)

        txt_btn = QPushButton("📄  Export Summary as TXT")
        txt_btn.setFixedHeight(46)
        txt_btn.setStyleSheet(
            "QPushButton { background: #1e293b; border: 1px solid #334155; border-radius: 10px; "
            "color: #94a3b8; font-weight: bold; font-size: 14px; }"
            "QPushButton:hover { background: #334155; color: #e2e8f0; }"
        )
        txt_btn.clicked.connect(self._export_summary_txt)
        btn_row.addWidget(txt_btn)
        exp_layout.addLayout(btn_row)
        layout.addWidget(exp_frame)

        # Danger zone
        danger_frame = QFrame()
        danger_frame.setStyleSheet(
            "QFrame { background: rgba(239,68,68,0.06); border-radius: 14px; "
            "border: 1px solid rgba(239,68,68,0.2); }"
        )
        dl = QVBoxLayout(danger_frame)
        dl.setContentsMargins(24, 20, 24, 20)
        dl.setSpacing(12)

        dt = QLabel("⚠  Danger Zone")
        dt.setFont(QFont("Segoe UI", 14, QFont.Bold))
        dt.setStyleSheet("color: #ef4444; background: transparent;")
        dl.addWidget(dt)

        dd = QLabel("Clear all activity logs from the database. This cannot be undone.")
        dd.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")
        dl.addWidget(dd)

        clear_btn = QPushButton("🗑  Clear All Activity Logs")
        clear_btn.setFixedHeight(44)
        clear_btn.setStyleSheet(
            "QPushButton { background: rgba(239,68,68,0.18); border: 1px solid rgba(239,68,68,0.5); "
            "border-radius: 10px; color: #ef4444; font-weight: bold; font-size: 13px; }"
            "QPushButton:hover { background: rgba(239,68,68,0.35); }"
        )
        clear_btn.clicked.connect(self._clear_logs)
        dl.addWidget(clear_btn)
        layout.addWidget(danger_frame)

        layout.addStretch()
        return page

    # ══════════════════════════════════════════
    # DATA LOADERS
    # ══════════════════════════════════════════

    def _load_all_data(self):
        self._load_summary_cards()
        self._load_tool_bars()
        self._load_recent_users()
        self._load_users()
        self._load_stats()
        self._load_port_history()
        self._load_link_history()
        self._load_feedback()
        self._load_activity()

    def _load_summary_cards(self):
        self.card_users.set_value(db.total_users())
        self.card_scans.set_value(db.total_scans())
        self.card_tools.set_value(db.total_tools())
        self.card_feedback.set_value(db.total_feedback())
        rating = db.avg_rating()
        self.card_rating.set_value(str(rating) + " ★" if rating else "—")

    def _load_tool_bars(self):
        while self.tool_bars_layout.count():
            item = self.tool_bars_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        stats = db.tool_stats()
        if not stats:
            lbl = QLabel("No tool usage yet. Use tools as a regular user first.")
            lbl.setStyleSheet("color: #4b5563; font-style: italic; background: transparent;")
            self.tool_bars_layout.addWidget(lbl)
            return

        max_val = max(stats.values()) or 1
        colors  = ["#00BCD4", "#8b5cf6", "#f59e0b", "#10b981", "#f97316", "#ef4444"]

        for i, (tool, count) in enumerate(stats.items()):
            row = QHBoxLayout()
            row.setSpacing(10)
            name_lbl = QLabel(tool)
            name_lbl.setFixedWidth(175)
            name_lbl.setStyleSheet("color: #cbd5e1; font-size: 13px; background: transparent;")
            row.addWidget(name_lbl)

            accent = colors[i % len(colors)]
            bar = QProgressBar()
            bar.setMaximum(max_val)
            bar.setValue(count)
            bar.setFixedHeight(10)
            bar.setTextVisible(False)
            bar.setStyleSheet(
                "QProgressBar { background: #1e293b; border: none; border-radius: 5px; }"
                "QProgressBar::chunk { background: " + accent + "; border-radius: 5px; }"
            )
            row.addWidget(bar, 1)

            count_lbl = QLabel(str(count))
            count_lbl.setFixedWidth(40)
            count_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            count_lbl.setStyleSheet("color: " + accent + "; font-weight: bold; font-size: 13px; background: transparent;")
            row.addWidget(count_lbl)

            container = QWidget()
            container.setStyleSheet("background: transparent;")
            container.setLayout(row)
            self.tool_bars_layout.addWidget(container)

    def _load_recent_users(self):
        users = db.get_all_users()[:8]
        self.recent_users_table.setRowCount(len(users))
        for r, u in enumerate(users):
            for c, val in enumerate(u):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.recent_users_table.setItem(r, c, item)

    def _load_users(self):
        self._populate_user_table(db.get_all_users())

    def _populate_user_table(self, users):
        self.user_table.setRowCount(len(users))
        self.user_count_lbl.setText("  " + str(len(users)) + " user(s) found")
        for r, u in enumerate(users):
            chk = QCheckBox()
            chk.setStyleSheet("QCheckBox { margin-left: 12px; }")
            self.user_table.setCellWidget(r, 0, chk)
            for c, val in enumerate(u, start=1):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.user_table.setItem(r, c, item)

    def _search_users(self):
        kw = self.search_input.text().strip()
        users = db.search_users(kw) if kw else db.get_all_users()
        self._populate_user_table(users)

    def _delete_users(self):
        targets = []
        for r in range(self.user_table.rowCount()):
            chk = self.user_table.cellWidget(r, 0)
            if chk and chk.isChecked():
                item = self.user_table.item(r, 2)
                if item:
                    targets.append(item.text())
        if not targets:
            QMessageBox.information(self, "No Selection", "Select at least one user to delete.")
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Delete " + str(len(targets)) + " user(s)? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for email in targets:
                db.delete_user(email)
            QMessageBox.information(self, "Done", "✅ " + str(len(targets)) + " user(s) deleted.")
            self._load_all_data()

    def _load_stats(self):
        stats = db.tool_stats()
        self.stats_tool_table.setRowCount(len(stats))
        for r, (tool, count) in enumerate(stats.items()):
            self.stats_tool_table.setItem(r, 0, QTableWidgetItem(tool))
            item = QTableWidgetItem(str(count))
            item.setTextAlignment(Qt.AlignCenter)
            self.stats_tool_table.setItem(r, 1, item)

        scans = db.scans_per_user()
        self.stats_user_table.setRowCount(len(scans))
        for r, (user, count) in enumerate(scans):
            self.stats_user_table.setItem(r, 0, QTableWidgetItem(user or "—"))
            item = QTableWidgetItem(str(count))
            item.setTextAlignment(Qt.AlignCenter)
            self.stats_user_table.setItem(r, 1, item)

    def _load_port_history(self):
        scans = db.get_port_scans(limit=200)
        self._port_scan_data = scans
        self.port_hist_table.setRowCount(len(scans))
        for r, row in enumerate(scans):
            try:
                open_ports = json.loads(row.get("results", "[]"))
                port_count = str(len(open_ports)) + " open"
                has_open = len(open_ports) > 0
            except Exception:
                port_count = "—"
                has_open = False

            values = [
                row.get("target", "—"),
                row.get("mode", "—"),
                port_count,
                row.get("os_guess", "Unknown") or "Unknown",
                str(row.get("scanned_at", "—")),
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if has_open and c == 2:
                    item.setForeground(QColor("#f59e0b"))
                self.port_hist_table.setItem(r, c, item)

    def _load_link_history(self):
        scans = db.get_link_scans(limit=200)
        self._link_scan_data = scans
        self.link_hist_table.setRowCount(len(scans))
        for r, row in enumerate(scans):
            score = row.get("risk_score", 0)
            if score >= 70:
                score_str = "🔴  " + str(score) + "/100"
                fg = QColor("#ef4444")
            elif score >= 40:
                score_str = "🟡  " + str(score) + "/100"
                fg = QColor("#f59e0b")
            else:
                score_str = "🟢  " + str(score) + "/100"
                fg = QColor("#10b981")

            values = [
                row.get("url", "—"),
                row.get("domain", "—"),
                score_str,
                "✅ Yes" if row.get("ssl_ok") else "❌ No",
                str(row.get("scanned_at", "—")),
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.link_hist_table.setItem(r, c, item)
            risk_item = self.link_hist_table.item(r, 2)
            if risk_item:
                risk_item.setForeground(fg)

    def _load_feedback(self):
        feedbacks = db.get_all_feedback()
        self._feedback_data = feedbacks
        avg   = db.avg_rating()
        total = db.total_feedback()
        try:
            stars = "★" * int(round(avg)) + "☆" * (5 - int(round(avg)))
        except Exception:
            stars = "—"
        self.feedback_summary.setText(
            "  Total Feedback: " + str(total) +
            "   ·   Average Rating: " + str(avg) + "/5.0   " + stars
        )
        self.feedback_table.setRowCount(len(feedbacks))
        for r, row in enumerate(feedbacks):
            username, rating, category, message, submitted_at = row
            try:
                stars_disp = "★" * int(rating) + "☆" * (5 - int(rating))
            except Exception:
                stars_disp = str(rating)
            # Truncate message in table — full message shown in popup on click
            short_msg = message[:60] + "..." if len(message) > 60 else message
            values = [str(username), stars_disp, str(category), short_msg, str(submitted_at)]
            for c, val in enumerate(values):
                align = Qt.AlignCenter if c != 3 else (Qt.AlignLeft | Qt.AlignVCenter)
                item = QTableWidgetItem(val)
                item.setTextAlignment(align)
                self.feedback_table.setItem(r, c, item)
            star_item = self.feedback_table.item(r, 1)
            if star_item:
                star_item.setForeground(QColor("#f59e0b"))

    def _load_activity(self):
        activity = db.recent_activity(200)
        self.activity_table.setRowCount(len(activity))
        for r, (user, tool, date) in enumerate(activity):
            self.activity_table.setItem(r, 0, QTableWidgetItem(str(user or "—")))
            self.activity_table.setItem(r, 1, QTableWidgetItem(str(tool or "—")))
            date_item = QTableWidgetItem(str(date))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(r, 2, date_item)

    # ══════════════════════════════════════════
    # CLICK DETAIL HANDLERS
    # ══════════════════════════════════════════

    def _show_feedback_detail(self, row, col):
        """Open full feedback message popup when a row is clicked."""
        if row >= len(self._feedback_data):
            return
        username, rating, category, message, submitted_at = self._feedback_data[row]
        dlg = FeedbackDialog(self, username, rating, category, message, submitted_at)
        dlg.exec_()

    def _show_port_detail(self, row, col):
        """Show popup with all open ports for the clicked scan."""
        if row >= len(self._port_scan_data):
            return
        scan = self._port_scan_data[row]
        try:
            ports = json.loads(scan.get("results", "[]"))
        except Exception:
            ports = []
        target = scan.get("target", "—")
        lines = [
            "Target : " + target,
            "Mode   : " + str(scan.get("mode", "—")),
            "OS     : " + str(scan.get("os_guess", "Unknown") or "Unknown"),
            "Date   : " + str(scan.get("scanned_at", "—")),
            "",
        ]
        if ports:
            lines.append("Open Ports (" + str(len(ports)) + " found):")
            lines.append("─" * 36)
            for p in ports:
                lines.append("  Port " + str(p.get("port")) + "  –  " + str(p.get("service", "?")) + "  –  " + str(p.get("risk", "?")))
        else:
            lines.append("No open ports found in this scan.")
        QMessageBox.information(self, "Port Scan: " + target, "\n".join(lines))

    def _show_link_detail(self, row, col):
        """Show popup with all security flags for the clicked link scan."""
        if row >= len(self._link_scan_data):
            return
        scan = self._link_scan_data[row]
        url = scan.get("url", "—")
        try:
            flags = json.loads(scan.get("flags", "[]"))
        except Exception:
            flags = []
        lines = [
            "URL    : " + url,
            "Domain : " + str(scan.get("domain", "—")),
            "Score  : " + str(scan.get("risk_score", 0)) + "/100",
            "SSL    : " + ("Yes" if scan.get("ssl_ok") else "No"),
            "Date   : " + str(scan.get("scanned_at", "—")),
            "",
        ]
        if flags:
            lines.append("Security Flags (" + str(len(flags)) + " found):")
            lines.append("─" * 36)
            for f in flags:
                lines.append("  •  " + str(f))
        else:
            lines.append("No security flags — URL appears safe.")
        QMessageBox.information(self, "Link Scan: " + scan.get("domain", url), "\n".join(lines))

    # ══════════════════════════════════════════
    # EXPORT ACTIONS
    # ══════════════════════════════════════════

    def _export_port_history(self):
        scans = db.get_port_scans(limit=1000)
        if not scans:
            QMessageBox.information(self, "No Data", "No port scan history to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Port Scan History",
            "port_scan_history_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "Text File (*.txt)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("CyberArmor - Port Scan History\n" + "=" * 50 + "\n\n")
            for row in scans:
                f.write("Target   : " + str(row.get("target", "")) + "\n")
                f.write("Mode     : " + str(row.get("mode", "")) + "\n")
                f.write("OS Guess : " + str(row.get("os_guess", "")) + "\n")
                f.write("Date     : " + str(row.get("scanned_at", "")) + "\n")
                try:
                    ports = json.loads(row.get("results", "[]"))
                    f.write("Results  : " + str(len(ports)) + " open port(s)\n")
                    for p in ports:
                        f.write("  Port " + str(p["port"]) + " - " + str(p["service"]) + " - " + str(p["risk"]) + "\n")
                except Exception:
                    pass
                f.write("\n")
        QMessageBox.information(self, "Exported", "Saved to:\n" + path)

    def _export_link_history(self):
        scans = db.get_link_scans(limit=1000)
        if not scans:
            QMessageBox.information(self, "No Data", "No link scan history to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Link Scan History",
            "link_scan_history_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "Text File (*.txt)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("CyberArmor - Link Scan History\n" + "=" * 50 + "\n\n")
            for row in scans:
                f.write("URL    : " + str(row.get("url", "")) + "\n")
                f.write("Domain : " + str(row.get("domain", "")) + "\n")
                f.write("Score  : " + str(row.get("risk_score", "")) + "/100\n")
                f.write("SSL    : " + ("Yes" if row.get("ssl_ok") else "No") + "\n")
                f.write("Date   : " + str(row.get("scanned_at", "")) + "\n\n")
        QMessageBox.information(self, "Exported", "Saved to:\n" + path)

    def _export_activity(self):
        activity = db.recent_activity(1000)
        if not activity:
            QMessageBox.information(self, "No Data", "No activity to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Activity Log",
            "activity_log_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "Text File (*.txt)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("CyberArmor - Activity Log\n" + "=" * 50 + "\n\n")
            for user, tool, date in activity:
                f.write(str(date) + "  |  " + str(user or "unknown") + "  |  " + str(tool) + "\n")
        QMessageBox.information(self, "Exported", "Saved to:\n" + path)

    def _export_full_db(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Full Database",
            "cyberarmor_db_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "JSON File (*.json)"
        )
        if not path:
            return
        try:
            data = {
                "exported_at": str(datetime.now()),
                "users":       [{"username": u[0], "email": u[1], "joined": u[2]} for u in db.get_all_users()],
                "port_scans":  db.get_port_scans(limit=10000),
                "link_scans":  db.get_link_scans(limit=10000),
                "feedback":    [{"user": f[0], "rating": f[1], "category": f[2], "message": f[3], "submitted_at": f[4]} for f in db.get_all_feedback()],
                "activity":    [{"user": a[0], "tool": a[1], "date": str(a[2])} for a in db.recent_activity(10000)],
                "tool_stats":  db.tool_stats(),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, default=str)
            QMessageBox.information(self, "Exported", "Database exported to:\n" + path)
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", "Error: " + str(e))

    def _export_summary_txt(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Admin Summary",
            "cyberarmor_summary_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "Text File (*.txt)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("CyberArmor - Admin Summary Report\n")
                f.write("=" * 50 + "\n")
                f.write("Generated : " + str(datetime.now()) + "\n\n")
                f.write("OVERVIEW\n")
                f.write("  Total Users    : " + str(db.total_users()) + "\n")
                f.write("  Total Scans    : " + str(db.total_scans()) + "\n")
                f.write("  Total Feedback : " + str(db.total_feedback()) + "\n")
                f.write("  Avg Rating     : " + str(db.avg_rating()) + "/5.0\n\n")
                f.write("TOOL USAGE\n")
                for tool, count in db.tool_stats().items():
                    f.write("  " + str(tool) + " : " + str(count) + " uses\n")
                f.write("\nSCANS PER USER\n")
                for user, count in db.scans_per_user():
                    f.write("  " + str(user) + " : " + str(count) + " scans\n")
            QMessageBox.information(self, "Exported", "Summary saved to:\n" + path)
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", "Error: " + str(e))

    def _clear_logs(self):
        reply = QMessageBox.question(
            self, "Confirm",
            "This will permanently delete ALL activity log entries.\nAre you sure?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.clear_logs()
            QMessageBox.information(self, "Done", "All activity logs cleared.")
            self._load_activity()

    # ══════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════

    def _switch_page(self, page, active_btn):
        self.stack.setCurrentWidget(page)
        for btn in self.sidebar_btns:
            btn.setActive(btn is active_btn)

    def _section(self, title_text):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background: #111827; border-radius: 14px; border: 1px solid #1e293b; }"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #e2e8f0; background: transparent; border: none;")
        layout.addWidget(title)
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #1e293b; border: none; border-radius: 0;")
        layout.addWidget(sep)
        return frame

    def _make_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(42)  # taller rows = more readable
        self._style_table(table)
        return table

    def _style_table(self, table):
        table.setStyleSheet("""
        QTableWidget {
            background: transparent; border: none;
            alternate-background-color: rgba(255,255,255,0.02);
            gridline-color: #1e293b;
            selection-background-color: rgba(0,188,212,0.18);
            font-size: 13px;
        }
        QTableWidget::item { padding: 10px; color: #cbd5e1; border: none; }
        QTableWidget::item:selected { color: #00BCD4; }
        QHeaderView::section {
            background: #0a0f1e; color: #64748b;
            padding: 10px; border: none;
            border-bottom: 2px solid #00BCD4;
            font-weight: bold; font-size: 11px;
            text-transform: uppercase; letter-spacing: 1px;
        }
        QScrollBar:vertical { background: #0a0f1e; width: 6px; border-radius: 3px; }
        QScrollBar::handle:vertical { background: #334155; border-radius: 3px; min-height: 20px; }
        QScrollBar::handle:vertical:hover { background: #00BCD4; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        table.setFocusPolicy(Qt.NoFocus)

    def _small_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedSize(140, 38)
        btn.setStyleSheet(
            "QPushButton { background: #1e293b; border: 1px solid #334155; border-radius: 8px; "
            "color: #94a3b8; font-weight: bold; font-size: 12px; }"
            "QPushButton:hover { background: #00BCD4; color: black; border-color: #00BCD4; }"
        )
        return btn