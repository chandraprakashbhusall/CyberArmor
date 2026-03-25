import os
import re
import magic

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QHBoxLayout,
    QFrame, QProgressBar
)
from PyQt5.QtCore import Qt

# ✅ Import your theme
from tools import theme


class FileScanWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setAcceptDrops(True)
        self.resize(900, 650)

        # ✅ Apply global theme
        self.setStyleSheet(theme.get_stylesheet())

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)

        # ================= TITLE =================
        title = QLabel("🛡️ Advanced File & Folder Scanner")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold;")
        main_layout.addWidget(title)

        # ================= CARD FRAME =================
        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        # Buttons Row
        btn_layout = QHBoxLayout()

        self.file_btn = QPushButton("📄 Scan Single File")
        self.file_btn.clicked.connect(self.select_file)

        self.folder_btn = QPushButton("📁 Scan Entire Folder")
        self.folder_btn.clicked.connect(self.select_folder)

        btn_layout.addWidget(self.file_btn)
        btn_layout.addWidget(self.folder_btn)

        card_layout.addLayout(btn_layout)

        # Output Area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        card_layout.addWidget(self.output)

        # Risk Progress
        self.progress = QProgressBar()
        self.progress.setMaximum(150)
        card_layout.addWidget(self.progress)

        # Risk Label
        self.result_label = QLabel("Scan Result: -")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size:18px; font-weight:bold;")
        card_layout.addWidget(self.result_label)

        main_layout.addWidget(card)

        # ================= Suspicious Patterns =================
        self.suspicious_patterns = [
            (r"base64_decode\(|base64.b64decode", "File is hiding encoded content", 70),
            (r"eval\(", "File can execute hidden code", 70),
            (r"exec\(", "File can run system-level commands", 70),
            (r"system\(|os.system", "Trying to run terminal commands", 40),
            (r"subprocess\.Popen", "May run external programs", 40),
            (r"chmod\s+777", "Making itself fully open", 20),
            (r"wget http|curl http", "Downloading files from internet", 40),
            (r"<script>", "Script injection detected", 70),
            (r"import pty|spawn", "Reverse shell behavior detected", 70),
            (r"nc -e|netcat", "Reverse shell signature detected", 70),
        ]

    # ================= FILE SELECT =================
    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select File to Scan")
        if file:
            self.output.clear()
            self.output.append(f"🔍 Scanning File:\n{file}\n")
            self.scan_file(file)

    # ================= FOLDER SELECT =================
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.output.clear()
            self.output.append(f"📁 Scanning Folder:\n{folder}\n")
            self.scan_folder(folder)

    # ================= SCAN FOLDER =================
    def scan_folder(self, folder_path):
        threats = 0
        scanned = 0

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                scanned += 1
                result = self.scan_file(full_path, show_ui=False)
                if result != "Safe":
                    threats += 1

        self.output.append("\n" + "=" * 50)
        self.output.append("📊 Folder Scan Summary")
        self.output.append(f"Total Files Scanned: {scanned}")
        self.output.append(f"Suspicious Files Found: {threats}")

        if threats == 0:
            self.result_label.setText("🟢 Folder Status: Fully Safe")
            self.result_label.setStyleSheet("color:green; font-weight:bold; font-size:18px;")
        else:
            self.result_label.setText("🔴 Folder Status: Attention Needed")
            self.result_label.setStyleSheet("color:red; font-weight:bold; font-size:18px;")

    # ================= SCAN FILE =================
    def scan_file(self, filepath, show_ui=True):
        risk_score = 0
        detected = []

        try:
            mime = magic.from_file(filepath, mime=True)

            if "executable" in mime:
                detected.append("Executable file detected")
                risk_score += 50

            if "script" in mime:
                detected.append("Script file detected")
                risk_score += 30

            with open(filepath, "r", errors="ignore") as f:
                content = f.read()

            for pattern, description, points in self.suspicious_patterns:
                if re.search(pattern, content):
                    detected.append(description)
                    risk_score += points

            if "\x00" in content:
                detected.append("Hidden binary data found")
                risk_score += 40

        except Exception:
            if show_ui:
                self.output.append("❌ Unable to scan this file.\n")
            return "Safe"

        # Cap score
        if risk_score > 150:
            risk_score = 150

        # Determine status
        if risk_score >= 120:
            status = "Dangerous"
            color = "red"
        elif risk_score >= 60:
            status = "Warning"
            color = "orange"
        else:
            status = "Safe"
            color = "green"

        # ===== UI Update =====
        if show_ui:
            self.progress.setValue(risk_score)

            self.output.append("📌 File Behavior Summary:")
            if detected:
                for d in detected:
                    self.output.append(f"   • {d}")
            else:
                self.output.append("   • No harmful behaviors detected")

            self.output.append(f"\n⭐ Risk Score: {risk_score}/150")
            self.output.append("-" * 50 + "\n")

            self.result_label.setText(f"{status}")
            self.result_label.setStyleSheet(
                f"color:{color}; font-weight:bold; font-size:20px;"
            )

        return status