import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame,
    QMenu, QScrollArea, QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
import os
import re
import email
from email import policy
from urllib.parse import urlparse

import db

from Form.login import AuthWindow
from tools.home import HomeWidget
from tools.port import PortScannerWidget
from tools.wifi import WifiAdvancedWidget
from tools.link import LinkScannerWidget
from tools.filescan import FileScanWidget
from tools.system import SystemSecurityWidget
from tools.ai import AIWidget
from tools.setting import SettingsWidget
from tools.password import PasswordManagerWidget   # ✅ PASSWORD MANAGER

# ---------------- Initialize Database ----------------
db.init_db()

# ---------------- Email Spam Checker Widget ----------------
SPAM_KEYWORDS = [
    "urgent", "limited time", "winner", "prize", "free", "click here",
    "buy now", "act now", "lottery", "bank account", "credit card"
]

SUSPICIOUS_DOMAINS = [
    "xyz.com", "abc123.net", "mailinator.com", "tempmail.com"
]

SUSPICIOUS_EXTENSIONS = [".exe", ".scr", ".zip", ".js", ".bat", ".vbs"]

class EmailSpamCheckerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background:#111; color:white; font-size:14px;")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("📧 Email Spam Checker")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px; font-weight:bold; color:cyan;")
        layout.addWidget(title)

        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Select an email file (.eml/.txt)")
        self.file_label.setStyleSheet("color:lightblue;")
        self.select_btn = QPushButton("Select File")
        self.select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_btn)
        layout.addLayout(file_layout)

        # Analyze button
        self.analyze_btn = QPushButton("Analyze Email")
        self.analyze_btn.clicked.connect(self.analyze_email)
        layout.addWidget(self.analyze_btn)

        # Email info
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setStyleSheet("background:#222; color:white;")
        layout.addWidget(self.info_text)

        # Result table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Reason", "Points"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Spam score label
        self.score_label = QLabel("Spam Score: -")
        self.score_label.setStyleSheet("font-size:16px; font-weight:bold; color:lightgreen;")
        layout.addWidget(self.score_label)

        self.email_path = None

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Email File", "", "Email Files (*.eml *.txt)")
        if path:
            self.email_path = path
            self.file_label.setText(os.path.basename(path))

    def analyze_email(self):
        if not self.email_path:
            QMessageBox.warning(self, "Error", "Select a file first!")
            return

        with open(self.email_path, "r", encoding="utf-8", errors="ignore") as f:
            msg = email.message_from_file(f, policy=policy.default)

        sender = msg.get("From", "")
        subject = msg.get("Subject", "")
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_content() + "\n"
        else:
            body = msg.get_content()

        links = re.findall(r'https?://[^\s]+', body)

        score = 0
        reasoning = []

        # Sender check
        sender_domain = sender.split("@")[-1].lower() if "@" in sender else ""
        if any(domain in sender_domain for domain in SUSPICIOUS_DOMAINS):
            score += 20
            reasoning.append(f"Suspicious sender domain: {sender_domain}")

        # Subject check
        for word in SPAM_KEYWORDS:
            if word.lower() in subject.lower():
                score += 5
                reasoning.append(f"Spam keyword in subject: '{word}'")

        # Body check
        for word in SPAM_KEYWORDS:
            count = len(re.findall(word, body, re.IGNORECASE))
            if count > 0:
                score += count * 2
                reasoning.append(f"Spam keyword in body: '{word}' appears {count} times")

        # Links check
        for link in links:
            domain = urlparse(link).netloc.lower()
            if any(susp in domain for susp in SUSPICIOUS_DOMAINS):
                score += 10
                reasoning.append(f"Suspicious link domain: {domain}")
            if any(link.endswith(ext) for ext in SUSPICIOUS_EXTENSIONS):
                score += 10
                reasoning.append(f"Suspicious link extension: {link}")

        if score > 100: score = 100

        # Show info
        self.info_text.setPlainText(f"From: {sender}\nSubject: {subject}\n\nBody Preview:\n{body[:500]}...")
        self.table.setRowCount(0)
        for row, reason in enumerate(reasoning):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(reason))
            self.table.setItem(row, 1, QTableWidgetItem(str(score)))

        self.score_label.setText(f"Spam Score: {score}/100")
        if score >= 70:
            self.score_label.setStyleSheet("color:red; font-weight:bold;")
        elif score >= 40:
            self.score_label.setStyleSheet("color:orange; font-weight:bold;")
        else:
            self.score_label.setStyleSheet("color:lightgreen; font-weight:bold;")


# ------------------ MAIN APP ------------------
class CyberArmor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberArmor – Advanced Security Suite")
        self.setStyleSheet("background-color:#0c0c0c; color:white;")
        self.user_row = None
        self.page_refs = {}

        # Main layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet("background:#121212; border-right:2px solid #222;")
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(20,20,20,20)
        side_layout.setSpacing(20)

        title = QLabel("🛡 CyberArmor")
        title.setStyleSheet("font-size:28px; font-weight:bold; color:cyan;")
        side_layout.addWidget(title)

        # Pages
        self.pages = QStackedWidget()

        # ---------------- Sidebar Pages ----------------
        self.add_sidebar_page("🏠 Home", HomeWidget())
        self.add_sidebar_page("🔐 Password Manager", PasswordManagerWidget())
        self.add_sidebar_page("📧 Email Spam Checker", EmailSpamCheckerWidget())  # ✅ Added page
        self.add_sidebar_page("🛠 Port Scanner", PortScannerWidget())
        self.add_sidebar_page("📶 WiFi Analyzer", WifiAdvancedWidget())
        self.add_sidebar_page("🔗 Link Inspector", LinkScannerWidget())
        self.add_sidebar_page("🤖 AI Chat", AIWidget())
        self.add_sidebar_page("🗂 File Scanner", FileScanWidget())
        self.add_sidebar_page("💻 System Scan", SystemSecurityWidget())
        self.add_sidebar_page("⚙ Settings", SettingsWidget())

        side_layout.addStretch()

        # Profile Button
        self.profile_btn = QPushButton("👤 Profile ▼")
        self.profile_btn.setMinimumHeight(50)
        self.profile_btn.setStyleSheet("""
            QPushButton { padding:12px; font-size:16px; border-radius:8px; background:#1a1a1a; }
            QPushButton:hover { background:#333; }
        """)
        self.profile_btn.clicked.connect(self.open_profile_menu)
        side_layout.addWidget(self.profile_btn)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages, 1)

        self.switch_page("🏠 Home")

    # Sidebar button style
    def sidebar_btn_style(self):
        return """
            QPushButton {
                text-align:left; padding-left:20px; font-size:16px;
                background:#1a1a1a; border:none; color:white; border-radius:6px;
            }
            QPushButton:hover {
                background:qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00bcd4, stop:1 #006064
                );
            }
        """

    def add_sidebar_page(self, text, widget):
        btn = QPushButton(text)
        btn.setMinimumHeight(50)
        btn.setStyleSheet(self.sidebar_btn_style())
        btn.clicked.connect(lambda: self.switch_page(text))
        self.sidebar.layout().addWidget(btn)

        container = QFrame()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;")
        scroll.setWidget(widget)
        layout.addWidget(scroll)
        self.pages.addWidget(container)
        self.page_refs[text] = container

    def switch_page(self, key):
        self.pages.setCurrentWidget(self.page_refs[key])

    def open_profile_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#111; color:white; font-size:15px; border:1px solid #444; }
            QMenu::item:selected { background:#333; }
        """)
        menu.addAction("⚙ Settings", lambda: self.switch_page("⚙ Settings"))
        menu.addSeparator()
        menu.addAction("🚪 Logout", self.logout)
        menu.exec_(self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomLeft()))

    def logout(self):
        self.close()
        self.login = AuthWindow()
        self.login.show()

    def set_user(self, user_row):
        self.user_row = user_row


# ================== APP START ==================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = AuthWindow()
    login.resize(420, 520)
    login.show()

    def start_main(user_row):
        main = CyberArmor()
        main.set_user(user_row)
        main.showMaximized()
        login.close()

    login.login_successful.connect(start_main)
    sys.exit(app.exec_())
