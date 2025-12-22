import os
import re
import email
from email import policy
from urllib.parse import urlparse
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt

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

        # Extract links
        self.links = re.findall(r'https?://[^\s]+', self.body)

    def analyze(self):
        self.score = 0
        self.reasoning = []

        # ------------------ SENDER CHECK ------------------
        sender_domain = self.sender.split("@")[-1].lower() if "@" in self.sender else ""
        if any(domain in sender_domain for domain in SUSPICIOUS_DOMAINS):
            self.score += 20
            self.reasoning.append(f"Suspicious sender domain: {sender_domain}")

        # ------------------ SUBJECT CHECK ------------------
        for word in SPAM_KEYWORDS:
            if word.lower() in self.subject.lower():
                self.score += 5
                self.reasoning.append(f"Spam keyword in subject: '{word}'")

        # ------------------ BODY CHECK ------------------
        for word in SPAM_KEYWORDS:
            count = len(re.findall(word, self.body, re.IGNORECASE))
            if count > 0:
                self.score += count * 2
                self.reasoning.append(f"Spam keyword in body: '{word}' appears {count} times")

        # ------------------ LINKS CHECK ------------------
        for link in self.links:
            domain = urlparse(link).netloc.lower()
            if any(susp in domain for susp in SUSPICIOUS_DOMAINS):
                self.score += 10
                self.reasoning.append(f"Suspicious link domain: {domain}")
            if any(link.endswith(ext) for ext in SUSPICIOUS_EXTENSIONS):
                self.score += 10
                self.reasoning.append(f"Suspicious link extension: {link}")

        # Cap score at 100
        if self.score > 100:
            self.score = 100

        return self.score, self.reasoning

# -------------------- GUI WIDGET --------------------
class EmailSpamCheckerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background:#111; color:white; font-size:14px;")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("📧 Advanced Email Spam Checker")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:22px; font-weight:bold; color:cyan;")
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

        # Analyze Button
        self.analyze_btn = QPushButton("Analyze Email")
        self.analyze_btn.clicked.connect(self.analyze_email)
        layout.addWidget(self.analyze_btn)

        # Email Info
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setStyleSheet("background:#222; color:white;")
        layout.addWidget(self.info_text)

        # Result Table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Reason", "Points"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Spam Score
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

        analyzer = EmailSpamAnalyzer(self.email_path)
        analyzer.parse_email()
        score, reasons = analyzer.analyze()

        self.info_text.setPlainText(
            f"From: {analyzer.sender}\nSubject: {analyzer.subject}\n\nBody Preview:\n{analyzer.body[:500]}..."
        )

        self.table.setRowCount(0)
        for row, reason in enumerate(reasons):
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
