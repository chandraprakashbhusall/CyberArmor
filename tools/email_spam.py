import os
import re
import email
from email import policy
from urllib.parse import urlparse

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt

# ✅ Import your theme
from tools import theme


# -------------------- SUSPICIOUS DATA --------------------
SPAM_KEYWORDS = [
    "urgent", "limited time", "winner", "prize", "free", "click here",
    "buy now", "act now", "lottery", "bank account", "credit card"
]

SUSPICIOUS_DOMAINS = [
    "xyz.com", "abc123.net", "mailinator.com", "tempmail.com"
]

SUSPICIOUS_EXTENSIONS = [".exe", ".scr", ".zip", ".js", ".bat", ".vbs"]


# -------------------- SPAM ANALYZER --------------------
class EmailSpamAnalyzer:
    def __init__(self, filepath):
        self.filepath = filepath
        self.headers = {}
        self.subject = ""
        self.sender = ""
        self.body = ""
        self.links = []
        self.score = 0
        self.reasoning = []

    def parse_email(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            msg = email.message_from_file(f, policy=policy.default)

        self.sender = msg.get("From", "")
        self.subject = msg.get("Subject", "")
        self.headers = dict(msg.items())

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    self.body += part.get_content() + "\n"
        else:
            self.body = msg.get_content()

        self.links = re.findall(r'https?://[^\s]+', self.body)

    def analyze(self):
        self.score = 0
        self.reasoning = []

        # Sender domain check
        sender_domain = self.sender.split("@")[-1].lower() if "@" in self.sender else ""
        if any(domain in sender_domain for domain in SUSPICIOUS_DOMAINS):
            self.score += 20
            self.reasoning.append(("Suspicious sender domain", 20))

        # Subject keywords
        for word in SPAM_KEYWORDS:
            if word.lower() in self.subject.lower():
                self.score += 5
                self.reasoning.append((f"Keyword in subject: {word}", 5))

        # Body keywords
        for word in SPAM_KEYWORDS:
            count = len(re.findall(word, self.body, re.IGNORECASE))
            if count > 0:
                pts = count * 2
                self.score += pts
                self.reasoning.append((f"Keyword '{word}' in body ({count} times)", pts))

        # Links
        for link in self.links:
            domain = urlparse(link).netloc.lower()
            if any(susp in domain for susp in SUSPICIOUS_DOMAINS):
                self.score += 10
                self.reasoning.append((f"Suspicious link domain: {domain}", 10))

            if any(link.endswith(ext) for ext in SUSPICIOUS_EXTENSIONS):
                self.score += 10
                self.reasoning.append((f"Dangerous file link: {link}", 10))

        if self.score > 100:
            self.score = 100

        return self.score, self.reasoning


# -------------------- GUI --------------------
class EmailSpamCheckerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.resize(900, 650)

        self.setStyleSheet(theme.get_stylesheet())  # ✅ Apply theme

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)

        # ===== TITLE =====
        title = QLabel("📧 Email Spam Analyzer")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:26px; font-weight:bold;")
        main_layout.addWidget(title)

        # ===== CARD FRAME =====
        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        # File Selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Drag & Drop email OR Click Select")
        self.select_btn = QPushButton("Select Email File")
        self.select_btn.clicked.connect(self.select_file)

        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_btn)
        card_layout.addLayout(file_layout)

        # Analyze Button
        self.analyze_btn = QPushButton("Analyze Email")
        self.analyze_btn.clicked.connect(self.analyze_email)
        card_layout.addWidget(self.analyze_btn)

        # Info Text
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        card_layout.addWidget(self.info_text)

        # Table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Reason", "Points"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        card_layout.addWidget(self.table)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        card_layout.addWidget(self.progress)

        # Score Label
        self.score_label = QLabel("Spam Score: -")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setStyleSheet("font-size:18px; font-weight:bold;")
        card_layout.addWidget(self.score_label)

        main_layout.addWidget(card)

        self.email_path = None

    # -------------------- Drag & Drop --------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        file_path = event.mimeData().urls()[0].toLocalFile()
        if file_path.endswith((".eml", ".txt")):
            self.email_path = file_path
            self.file_label.setText(os.path.basename(file_path))

    # -------------------- File Select --------------------
    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Email File", "", "Email Files (*.eml *.txt)"
        )
        if path:
            self.email_path = path
            self.file_label.setText(os.path.basename(path))

    # -------------------- Analyze --------------------
    def analyze_email(self):
        if not self.email_path:
            QMessageBox.warning(self, "Error", "Please select an email file first!")
            return

        analyzer = EmailSpamAnalyzer(self.email_path)
        analyzer.parse_email()
        score, reasons = analyzer.analyze()

        # Info Preview
        self.info_text.setPlainText(
            f"From: {analyzer.sender}\n"
            f"Subject: {analyzer.subject}\n\n"
            f"Body Preview:\n{analyzer.body[:600]}"
        )

        # Table Fill
        self.table.setRowCount(0)
        for row, (reason, points) in enumerate(reasons):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(reason))
            self.table.setItem(row, 1, QTableWidgetItem(str(points)))

        # Score Display
        self.progress.setValue(score)
        self.score_label.setText(f"Spam Score: {score}/100")

        if score >= 70:
            self.score_label.setStyleSheet("color:red; font-weight:bold; font-size:18px;")
        elif score >= 40:
            self.score_label.setStyleSheet("color:orange; font-weight:bold; font-size:18px;")
        else:
            self.score_label.setStyleSheet("color:green; font-weight:bold; font-size:18px;")