import os
import json
import math
import random
import string
import hashlib

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QMessageBox, QGroupBox,
    QFormLayout, QProgressBar
)
from PyQt5.QtCore import Qt

from tools import theme

# ================= CONFIG =================
DATA_FILE = "password_vault.json"
SYMBOLS = "!@#$%^&*()_+-="


# ================= CORE =================
def generate_password(length=12):
    chars = string.ascii_letters + string.digits + SYMBOLS
    return "".join(random.choice(chars) for _ in range(length))


def check_strength(password):
    score = 0
    if len(password) >= 8: score += 1
    if any(c.islower() for c in password): score += 1
    if any(c.isupper() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    if any(c in SYMBOLS for c in password): score += 1

    if score <= 2: return "Weak", score, "red"
    elif score == 3: return "Medium", score, "orange"
    else: return "Strong", score, "green"


def calculate_entropy(password):
    charset = 0
    if any(c.islower() for c in password): charset += 26
    if any(c.isupper() for c in password): charset += 26
    if any(c.isdigit() for c in password): charset += 10
    if any(c in SYMBOLS for c in password): charset += len(SYMBOLS)
    if charset == 0: return 0
    return round(len(password) * math.log2(charset), 2)


def estimate_crack_time(entropy):
    guesses_per_sec = 1e9
    seconds = (2 ** entropy) / guesses_per_sec
    if seconds < 60: return "Instant"
    if seconds < 3600: return "Minutes"
    if seconds < 86400: return "Hours"
    if seconds < 31536000: return "Days"
    return "Years"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ================= WIDGET =================
class PasswordManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(theme.get_stylesheet())
        self.resize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        title = QLabel("🔐 Secure Password Manager")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:26px; font-weight:bold;")
        layout.addWidget(title)

        # ---------- Generate ----------
        gen_group = QGroupBox("Generate Password")
        gen_layout = QVBoxLayout()

        row = QHBoxLayout()
        self.length_input = QLineEdit()
        self.length_input.setPlaceholderText("Length (default 12)")
        self.generated_pwd = QLineEdit()
        self.generated_pwd.setReadOnly(True)

        row.addWidget(self.length_input)
        row.addWidget(self.generated_pwd)

        gen_btn = QPushButton("Generate")
        gen_btn.clicked.connect(self.generate_ui)

        gen_layout.addLayout(row)
        gen_layout.addWidget(gen_btn)
        gen_group.setLayout(gen_layout)
        layout.addWidget(gen_group)

        # ---------- Strength ----------
        strength_group = QGroupBox("Password Strength Analyzer")
        strength_layout = QVBoxLayout()

        self.str_input = QLineEdit()
        self.str_input.setPlaceholderText("Enter password to analyze")
        strength_layout.addWidget(self.str_input)

        self.str_progress = QProgressBar()
        self.str_progress.setMaximum(5)
        strength_layout.addWidget(self.str_progress)

        self.str_label = QLabel("Strength: -")
        strength_layout.addWidget(self.str_label)

        check_btn = QPushButton("Check Strength")
        check_btn.clicked.connect(self.check_ui)
        strength_layout.addWidget(check_btn)

        strength_group.setLayout(strength_layout)
        layout.addWidget(strength_group)

        # ---------- Save ----------
        save_group = QGroupBox("Save Password")
        save_layout = QFormLayout()

        self.platform_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        save_btn = QPushButton("Save Securely")
        save_btn.clicked.connect(self.save_ui)

        save_layout.addRow("Platform:", self.platform_input)
        save_layout.addRow("Username:", self.username_input)
        save_layout.addRow("Password:", self.password_input)
        save_layout.addRow(save_btn)

        save_group.setLayout(save_layout)
        layout.addWidget(save_group)

        # ---------- Table ----------
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Platform", "Username", "Strength", "Rating", "Entropy", "Crack Time"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.load_table()

    # ================= UI =================
    def generate_ui(self):
        length = int(self.length_input.text()) if self.length_input.text().isdigit() else 12
        pwd = generate_password(length)
        self.generated_pwd.setText(pwd)

    def check_ui(self):
        pwd = self.str_input.text()
        if not pwd:
            return

        strength, rating, color = check_strength(pwd)
        entropy = calculate_entropy(pwd)
        crack = estimate_crack_time(entropy)

        self.str_progress.setValue(rating)
        self.str_label.setText(
            f"{strength} ({rating}/5) | Entropy: {entropy} | Crack Time: {crack}"
        )
        self.str_label.setStyleSheet(f"color:{color}; font-weight:bold;")

    def save_ui(self):
        platform = self.platform_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not platform or not username or not password:
            QMessageBox.warning(self, "Error", "All fields required")
            return

        strength, rating, _ = check_strength(password)
        entropy = calculate_entropy(password)
        crack = estimate_crack_time(entropy)

        data = load_data()
        data.append({
            "platform": platform,
            "username": username,
            "password_hash": hash_password(password),
            "strength": strength,
            "rating": rating,
            "entropy": entropy,
            "crack_time": crack
        })

        save_data(data)

        self.platform_input.clear()
        self.username_input.clear()
        self.password_input.clear()

        self.load_table()

    def load_table(self):
        data = load_data()
        self.table.setRowCount(0)
        for row, item in enumerate(data):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item["platform"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["username"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["strength"]))
            self.table.setItem(row, 3, QTableWidgetItem(f'{item["rating"]}/5'))
            self.table.setItem(row, 4, QTableWidgetItem(str(item["entropy"])))
            self.table.setItem(row, 5, QTableWidgetItem(item["crack_time"]))