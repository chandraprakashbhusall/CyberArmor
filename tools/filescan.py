from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit
from PyQt5.QtCore import Qt
import os
import re
import magic

class FileScanWidget(QWidget):
    def __init__(self):
        super().__init__()

        # --- UI STYLE ---
        self.setStyleSheet("""
            QWidget { background-color: #0c0c0c; color: #e5e5e5; font-size: 16px; }
            QPushButton {
                background-color: #151515; border: 1px solid #444;
                padding: 10px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #222; }
            QTextEdit {
                background-color: #0f0f0f; border: 1px solid #333;
                padding: 12px; border-radius: 6px; color: #dcdcdc; font-size: 15px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        self.setLayout(layout)

        title = QLabel("🛡️ Advanced File & Folder Scanner")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: cyan;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Buttons
        self.file_btn = QPushButton("📄 Scan Single File")
        self.file_btn.clicked.connect(self.select_file)
        layout.addWidget(self.file_btn)

        self.folder_btn = QPushButton("📁 Scan Entire Folder")
        self.folder_btn.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_btn)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # Suspicious patterns with friendly descriptions
        self.suspicious_patterns = [
            (r"base64_decode\(|base64.b64decode", "File is hiding encoded content", "High"),
            (r"eval\(", "File can execute hidden code", "High"),
            (r"exec\(", "File can run system-level commands", "High"),
            (r"system\(|os.system", "File is trying to run terminal commands", "Medium"),
            (r"subprocess\.Popen", "File may run external programs", "Medium"),
            (r"chmod\s+777", "File is making itself fully open", "Low"),
            (r"wget http|curl http", "File is downloading files from the internet", "Medium"),
            (r"<script>", "Script injection detected", "High"),
            (r"import pty|spawn", "Reverse shell behavior detected", "High"),
            (r"nc -e|netcat", "Reverse shell signature detected", "High"),
        ]

    # File selection
    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select File to Scan")
        if file:
            self.output.append("\n" + "-" * 60)
            self.output.append(f"🔍 Scanning: {file}\n")
            self.scan_file(file)

    # Folder selection
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.output.append("\n" + "-" * 60)
            self.output.append(f"📁 Scanning Folder: {folder}\n")
            self.scan_folder(folder)

    # Scan whole folder
    def scan_folder(self, folder_path):
        threats = 0
        scanned = 0

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                scanned += 1
                result = self.scan_file(full_path, show_header=True)
                if result != "Safe":
                    threats += 1

        # Final result for folder
        self.output.append("\n" + "=" * 60)
        self.output.append("📊 Folder Scan Summary\n")

        self.output.append(f"   • Total Files Scanned: {scanned}")
        self.output.append(f"   • Suspicious Files Found: {threats}")

        if threats == 0:
            self.output.append("   🟢 Folder Status: Fully Safe\n")
        else:
            self.output.append("   🔴 Folder Status: Attention Needed\n")

        self.output.append("=" * 60 + "\n")

    # Scan a single file
    def scan_file(self, filepath, show_header=False):
        risk_score = 0
        detected_things = []

        try:
            if show_header:
                self.output.append(f"\n📄 File: {filepath}")

            # Detect file type
            mime = magic.from_file(filepath, mime=True)

            if "executable" in mime:
                detected_things.append("This file can run programs")
                risk_score += 50

            if "script" in mime:
                detected_things.append("This file contains executable script code")
                risk_score += 30

            with open(filepath, "r", errors="ignore") as f:
                content = f.read()

            # Pattern matching
            for pattern, description, level in self.suspicious_patterns:
                if re.search(pattern, content):
                    detected_things.append(description)
                    if level == "High": risk_score += 70
                    elif level == "Medium": risk_score += 40
                    else: risk_score += 20

            if "\x00" in content:
                detected_things.append("Contains hidden binary data")
                risk_score += 40

        except Exception:
            self.output.append("❌ Unable to scan this file.\n")
            return "Safe"

        # Determine friendly risk level
        if risk_score >= 120:
            final_status = "🔴 Dangerous"
            color = "red"
        elif risk_score >= 60:
            final_status = "🟡 Warning"
            color = "yellow"
        else:
            final_status = "🟢 Safe"
            color = "green"

        # OUTPUT
        self.output.append(f"\n📌 File Behavior Summary:")
        if detected_things:
            for d in detected_things:
                self.output.append(f"   • {d}")
        else:
            self.output.append("   • No harmful behaviors detected")

        self.output.append(f"\n⭐ Final Result: {final_status}")
        self.output.append("-" * 60 + "\n")

        return final_status
