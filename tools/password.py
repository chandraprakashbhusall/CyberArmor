import os
import json
import math
import random
import string
import hashlib

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QMessageBox, QGroupBox, QFormLayout, QFrame
)
from PyQt5.QtCore import Qt

# ===================== CONFIG =====================
DATA_FILE = "password_vault.json"
SYMBOLS = "!@#$%^&*()_+-="

# ===================== CORE LOGIC =====================
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

# ===================== PASSWORD MANAGER WIDGET =====================
class PasswordManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("color:white; font-size:14px; background:#1e1e1e;")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)

        # ---------------- TITLE ----------------
        title = QLabel("🔐 Advanced Password Manager")
        title.setStyleSheet("font-size:24px; font-weight:bold; color:cyan;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ---------------- GENERATE PASSWORD ----------------
        gen_group = QGroupBox("Generate Password")
        gen_group.setStyleSheet(
            "QGroupBox {color:cyan; font-weight:bold; border:1px solid cyan; border-radius:5px; padding:10px;}"
        )
        gen_layout = QVBoxLayout()
        input_layout = QHBoxLayout()
        self.gen_length = QLineEdit()
        self.gen_length.setPlaceholderText("Length (default 12)")
        self.gen_length.setFixedWidth(120)
        self.gen_pwd_display = QLineEdit()
        self.gen_pwd_display.setReadOnly(True)
        self.gen_pwd_display.setStyleSheet("background:#222; color:lightgreen; font-weight:bold;")
        input_layout.addWidget(QLabel("Password Length:"))
        input_layout.addWidget(self.gen_length)
        input_layout.addWidget(QLabel("Generated Password:"))
        input_layout.addWidget(self.gen_pwd_display)
        gen_layout.addLayout(input_layout)

        gen_btn = QPushButton("Generate Password")
        gen_btn.setStyleSheet("background:cyan; color:black; font-weight:bold;")
        gen_btn.clicked.connect(self.generate_ui)
        gen_layout.addWidget(gen_btn)
        gen_group.setLayout(gen_layout)
        main_layout.addWidget(gen_group)

        # ---------------- CHECK STRENGTH ----------------
        strength_group = QGroupBox("Password Strength Checker")
        strength_group.setStyleSheet(
            "QGroupBox {color:cyan; font-weight:bold; border:1px solid cyan; border-radius:5px; padding:10px;}"
        )
        strength_layout = QVBoxLayout()
        self.str_pwd_input = QLineEdit()
        self.str_pwd_input.setPlaceholderText("Enter password to check")
        self.str_pwd_input.setStyleSheet("background:#222; color:white; font-weight:bold;")
        strength_layout.addWidget(self.str_pwd_input)
        self.str_result = QLabel("Strength: - | Rating: -/5 | Entropy: - | Crack: -")
        self.str_result.setStyleSheet("font-weight:bold;")
        strength_layout.addWidget(self.str_result)
        check_btn = QPushButton("Check Strength")
        check_btn.setStyleSheet("background:orange; color:black; font-weight:bold;")
        check_btn.clicked.connect(self.check_ui)
        strength_layout.addWidget(check_btn)
        strength_group.setLayout(strength_layout)
        main_layout.addWidget(strength_group)

        # ---------------- SAVE PASSWORD ----------------
        save_group = QGroupBox("Save Password")
        save_group.setStyleSheet(
            "QGroupBox {color:cyan; font-weight:bold; border:1px solid cyan; border-radius:5px; padding:10px;}"
        )
        save_layout = QFormLayout()
        self.platform_input = QLineEdit()
        self.platform_input.setPlaceholderText("Platform (Facebook, Instagram)")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username / Email")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        save_btn = QPushButton("Save Password")
        save_btn.setStyleSheet("background:lightgreen; color:black; font-weight:bold;")
        save_btn.clicked.connect(self.save_ui)
        save_layout.addRow("Platform:", self.platform_input)
        save_layout.addRow("Username:", self.username_input)
        save_layout.addRow("Password:", self.password_input)
        save_layout.addRow(save_btn)
        save_group.setLayout(save_layout)
        main_layout.addWidget(save_group)

        # ---------------- RESULT ----------------
        self.result = QLabel("")
        self.result.setStyleSheet("color:lightgreen; font-weight:bold;")
        main_layout.addWidget(self.result)

        # ---------------- PASSWORD TABLE ----------------
        table_group = QGroupBox("Saved Passwords")
        table_group.setStyleSheet(
            "QGroupBox {color:cyan; font-weight:bold; border:1px solid cyan; border-radius:5px; padding:10px;}"
        )
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Platform", "Username", "Strength", "Rating", "Entropy", "Crack Time"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet(
            "QTableWidget {background:#222; color:white; gridline-color:cyan;} QHeaderView::section {background:cyan; color:black; font-weight:bold;}"
        )
        table_layout = QVBoxLayout()
        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)

        self.load_table()

    # ================= UI FUNCTIONS =================
    def generate_ui(self):
        length_text = self.gen_length.text()
        length = int(length_text) if length_text.isdigit() else 12
        pwd = generate_password(length)
        self.gen_pwd_display.setText(pwd)

    def check_ui(self):
        pwd = self.str_pwd_input.text()
        if not pwd: return
        strength, rating, color = check_strength(pwd)
        entropy = calculate_entropy(pwd)
        crack = estimate_crack_time(entropy)
        self.str_result.setText(
            f"Strength: {strength} | Rating: {rating}/5 | Entropy: {entropy} | Crack: {crack}"
        )
        self.str_result.setStyleSheet(f"color:{color}; font-weight:bold;")

    def save_ui(self):
        platform = self.platform_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not platform or not username or not password:
            QMessageBox.warning(self, "Error", "All fields must be filled")
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
        self.result.setText(f"✔ Password for {platform} saved securely")
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
