# Form/login.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QGraphicsDropShadowEffect, QFrame, QMessageBox
)
from PyQt5.QtGui import QFont, QCursor, QColor
from PyQt5.QtCore import Qt, pyqtSignal
import db

class AuthWindow(QWidget):
    login_successful = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛡️ CyberArmor – Modern Access")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 720)
        self.setStyleSheet("background:#0b0b0b; color:white;")
        self.init_ui()

    def init_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        # ---------------- LEFT SPLASH ----------------
        left_panel = QFrame()
        left_panel.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0b6fd6, stop:1 #3a87f8);"
        )
        left_panel.setMinimumWidth(450)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(50,50,50,50)
        left_layout.setSpacing(20)

        title = QLabel("🛡️ CyberArmor")
        title.setFont(QFont("Segoe UI", 32, QFont.Bold))
        title.setStyleSheet("color:white; letter-spacing:2px;")
        left_layout.addWidget(title)

        tagline = QLabel("AI‑Powered Cybersecurity Platform\nProtecting your digital world.")
        tagline.setFont(QFont("Segoe UI", 14))
        tagline.setStyleSheet("color:white;")
        tagline.setWordWrap(True)
        left_layout.addWidget(tagline)

        # Illustration placeholder
        illustration = QLabel()
        illustration.setStyleSheet(
            "background: rgba(255,255,255,0.1); border-radius:15px;"
        )
        illustration.setMinimumHeight(300)
        illustration.setAlignment(Qt.AlignCenter)
        illustration.setText("📡\nNetwork & Security Dashboard")
        illustration.setFont(QFont("Segoe UI", 18))
        left_layout.addWidget(illustration)
        left_layout.addStretch()

        root.addWidget(left_panel)

        # ---------------- RIGHT CARD ----------------
        right_panel = QFrame()
        right_panel.setStyleSheet("background:#111214;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(50,50,50,50)
        right_layout.setSpacing(20)

        # Card Frame
        card = QFrame()
        card.setStyleSheet(
            "background:#1c1c1c; border-radius:20px;"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40,40,40,40)
        card_layout.setSpacing(20)

        # Tab buttons
        tab_wrap = QHBoxLayout()
        self.btn_login_tab = QPushButton("Login")
        self.btn_register_tab = QPushButton("Register")
        for b in (self.btn_login_tab, self.btn_register_tab):
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setCheckable(True)
            b.setMinimumHeight(40)
            b.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_login_tab.setChecked(True)
        self.btn_login_tab.clicked.connect(lambda: self.switch_tab(0))
        self.btn_register_tab.clicked.connect(lambda: self.switch_tab(1))
        tab_wrap.addWidget(self.btn_login_tab)
        tab_wrap.addWidget(self.btn_register_tab)
        card_layout.addLayout(tab_wrap)

        # Stacked Widget
        self.stack = QStackedWidget()
        self.login_page = self.build_login_page()
        self.register_page = self.build_register_page()
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.register_page)
        card_layout.addWidget(self.stack)

        right_layout.addWidget(card)
        right_layout.addStretch()
        root.addWidget(right_panel)

        self.update_tabs()

    # ---------------- LOGIN / REGISTER PAGES ----------------
    def build_login_page(self):
        w = QFrame()
        layout = QVBoxLayout(w)
        layout.setSpacing(15)

        lbl = QLabel("Welcome Back")
        lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))
        layout.addWidget(lbl)

        sub = QLabel("Access your cybersecurity dashboard")
        sub.setStyleSheet("color:#a0a0a0;")
        layout.addWidget(sub)

        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email")
        self.login_email.setStyleSheet(self.input_box())
        layout.addWidget(self.login_email)

        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setStyleSheet(self.input_box())
        layout.addWidget(self.login_password)

        btn = QPushButton("Secure Login")
        btn.setStyleSheet(self.action_btn())
        btn.clicked.connect(self.login)
        layout.addWidget(btn)

        return w

    def build_register_page(self):
        w = QFrame()
        layout = QVBoxLayout(w)
        layout.setSpacing(15)

        lbl = QLabel("Create Account")
        lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))
        layout.addWidget(lbl)

        sub = QLabel("Protect your digital identity")
        sub.setStyleSheet("color:#a0a0a0;")
        layout.addWidget(sub)

        self.reg_user = QLineEdit()
        self.reg_user.setPlaceholderText("Username")
        self.reg_user.setStyleSheet(self.input_box())
        layout.addWidget(self.reg_user)

        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Email")
        self.reg_email.setStyleSheet(self.input_box())
        layout.addWidget(self.reg_email)

        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("Password")
        self.reg_pass.setEchoMode(QLineEdit.Password)
        self.reg_pass.setStyleSheet(self.input_box())
        layout.addWidget(self.reg_pass)

        self.reg_confirm = QLineEdit()
        self.reg_confirm.setPlaceholderText("Confirm Password")
        self.reg_confirm.setEchoMode(QLineEdit.Password)
        self.reg_confirm.setStyleSheet(self.input_box())
        layout.addWidget(self.reg_confirm)

        btn = QPushButton("Create & Login")
        btn.setStyleSheet(self.action_btn("#28a745"))
        btn.clicked.connect(self.register_and_login)
        layout.addWidget(btn)

        return w

    # ---------------- TAB LOGIC ----------------
    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        self.update_tabs()

    def update_tabs(self):
        active = self.stack.currentIndex()
        self.btn_login_tab.setChecked(active == 0)
        self.btn_register_tab.setChecked(active == 1)

        self.btn_login_tab.setStyleSheet(
            self.tab_btn(active == 0)
        )
        self.btn_register_tab.setStyleSheet(
            self.tab_btn(active == 1)
        )

    # ---------------- LOGIC ----------------
    def login(self):
        email = self.login_email.text().strip()
        pw = self.login_password.text().strip()
        row = db.check_user(email, pw)
        if row:
            QMessageBox.information(self, "Success", f"Welcome {row[1]} ❤️")
            self.login_successful.emit(row)
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials")

    def register_and_login(self):
        u = self.reg_user.text().strip()
        e = self.reg_email.text().strip()
        p = self.reg_pass.text().strip()
        c = self.reg_confirm.text().strip()
        if not u or not e or not p or p != c:
            QMessageBox.warning(self, "Error", "Invalid details")
            return
        if not db.add_user(u, e, p):
            QMessageBox.warning(self, "Error", "User exists")
            return
        row = db.check_user(e, p)
        self.login_successful.emit(row)
        self.close()

    # ---------------- STYLES ----------------
    def input_box(self):
        return (
            "padding:12px;font-size:14px;border-radius:8px;"
            "background:#222227;color:white;border:1px solid #333337;"
        )

    def action_btn(self, color="#0b84d6"):
        return (
            f"QPushButton{{padding:12px;font-size:15px;border-radius:10px;"
            f"background:{color};color:white;font-weight:600;}}"
            "QPushButton:hover{background:#0a75c2;}"
        )

    def tab_btn(self, active):
        if active:
            return (
                "QPushButton{background:#0b84d6;color:white;font-weight:600;"
                "border:none;border-radius:22px;padding:8px 28px;}"
            )
        return (
            "QPushButton{background:transparent;color:#cbd5d9;"
            "border:none;padding:8px 28px;}"
        )
