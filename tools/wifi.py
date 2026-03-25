import subprocess
import json
import datetime
import csv
import os
import platform

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QLineEdit, QFormLayout, QGroupBox, QHBoxLayout,
    QProgressBar, QTableWidget, QTableWidgetItem,
    QMessageBox
)

HISTORY_FILE = "speed_history.json"
CSV_FILE = "speed_history.csv"


# ================= SPEED WORKER =================

class SpeedWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)

    def run(self):
        try:
            self.progress.emit("🔄 Testing internet speed...")

            result = subprocess.check_output(
                ["speedtest-cli", "--json"],
                timeout=120
            ).decode()

            data = json.loads(result)

            self.finished.emit({
                "download": round(data["download"] / 1_000_000, 2),
                "upload": round(data["upload"] / 1_000_000, 2),
                "ping": round(data["ping"], 2),
                "server": data["server"]["name"],
                "isp": data["client"]["isp"]
            })

        except Exception as e:
            self.progress.emit(str(e))
            self.finished.emit({})


# ================= MAIN UI =================

class WifiAdvancedWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.modern_css())

        self.speed_history = self.load_history()

        layout = QVBoxLayout(self)

        title = QLabel("🛡 CyberArmor – Advanced WiFi Analyzer")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("Title")
        layout.addWidget(title)

        # ---------------- WIFI SECTION ----------------

        wifi_box = QGroupBox("📶 Current WiFi")
        wifi_layout = QFormLayout()

        self.ssid_label = QLabel()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.eye_btn = QPushButton("👁")
        self.eye_btn.setFixedWidth(40)
        self.eye_btn.clicked.connect(self.toggle_password)

        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(self.password_input)
        pwd_layout.addWidget(self.eye_btn)

        wifi_layout.addRow("SSID:", self.ssid_label)
        wifi_layout.addRow("Password:", pwd_layout)

        wifi_box.setLayout(wifi_layout)
        layout.addWidget(wifi_box)

        self.load_wifi_details()

        # ---------------- SPEED SECTION ----------------

        speed_box = QGroupBox("🚀 Internet Speed Test")
        speed_layout = QVBoxLayout()

        self.speed_btn = QPushButton("Run Speed Test")
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()

        speed_layout.addWidget(self.speed_btn)
        speed_layout.addWidget(self.progress)
        speed_layout.addWidget(self.output)

        speed_box.setLayout(speed_layout)
        layout.addWidget(speed_box)

        # ---------------- HISTORY TABLE ----------------

        history_box = QGroupBox("📊 Speed Test History")
        history_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Date & Time", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)", "ISP"]
        )

        history_layout.addWidget(self.table)
        history_box.setLayout(history_layout)
        layout.addWidget(history_box)

        self.populate_table()

        self.speed_btn.clicked.connect(self.start_speed)

    # ================= WIFI DETAILS =================

    def load_wifi_details(self):
        try:
            system = platform.system()

            if system == "Windows":
                output = subprocess.check_output(
                    "netsh wlan show interfaces",
                    shell=True
                ).decode(errors="ignore")

                ssid = ""
                for line in output.splitlines():
                    if "SSID" in line and "BSSID" not in line:
                        ssid = line.split(":")[1].strip()
                        break

                self.ssid_label.setText(ssid if ssid else "Not Connected")

                if ssid:
                    profile = subprocess.check_output(
                        f'netsh wlan show profile name="{ssid}" key=clear',
                        shell=True
                    ).decode(errors="ignore")

                    for line in profile.splitlines():
                        if "Key Content" in line:
                            password = line.split(":")[1].strip()
                            self.password_input.setText(password)
                            return

                self.password_input.setText("Unavailable")

            else:
                # Linux basic SSID detection
                ssid = subprocess.getoutput("iwgetid -r")
                self.ssid_label.setText(ssid if ssid else "Not Connected")
                self.password_input.setText("Protected (Linux Restriction)")

        except:
            self.ssid_label.setText("Unknown")
            self.password_input.setText("Unavailable")

    # ================= PASSWORD TOGGLE =================

    def toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.eye_btn.setText("👁")

    # ================= SPEED =================

    def start_speed(self):
        self.output.clear()
        self.progress.show()
        self.speed_btn.setEnabled(False)

        self.worker = SpeedWorker()
        self.worker.progress.connect(self.output.append)
        self.worker.finished.connect(self.speed_done)
        self.worker.start()

    def speed_done(self, result):
        self.progress.hide()
        self.speed_btn.setEnabled(True)

        if not result:
            self.output.append("❌ Speed test failed.")
            return

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.output.append(f"""
📅 Date: {now}
⬇ Download: {result['download']} Mbps
⬆ Upload: {result['upload']} Mbps
📶 Ping: {result['ping']} ms
🌐 ISP: {result['isp']}
🖥 Server: {result['server']}
""")

        entry = {
            "date": now,
            "download": result["download"],
            "upload": result["upload"],
            "ping": result["ping"],
            "isp": result["isp"]
        }

        # Popup before saving
        reply = QMessageBox.question(
            self,
            "Save Result",
            "Do you want to save this speed test result?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.speed_history.append(entry)
            self.save_history()
            self.save_csv(entry)
            QMessageBox.information(self, "Saved", "Speed test result saved successfully.")
            self.populate_table()

    # ================= HISTORY =================

    def load_history(self):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []

    def save_history(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump(self.speed_history, f, indent=4)

    def save_csv(self, entry):
        file_exists = os.path.isfile(CSV_FILE)

        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow(["Date & Time", "Download", "Upload", "Ping", "ISP"])

            writer.writerow([
                entry["date"],
                entry["download"],
                entry["upload"],
                entry["ping"],
                entry["isp"]
            ])

    def populate_table(self):
        self.table.setRowCount(len(self.speed_history))

        for row, entry in enumerate(self.speed_history):
            self.table.setItem(row, 0, QTableWidgetItem(entry["date"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(entry["download"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(entry["upload"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(entry["ping"])))
            self.table.setItem(row, 4, QTableWidgetItem(entry["isp"]))

    # ================= CSS =================

    def modern_css(self):
        return """
        QWidget {
            background:#0f172a;
            color:#e2e8f0;
            font-family:Segoe UI;
            font-size:14px;
        }
        #Title {
            font-size:22px;
            font-weight:bold;
            color:#38bdf8;
        }
        QGroupBox {
            border:1px solid #1e293b;
            border-radius:12px;
            padding:15px;
            background:#111827;
        }
        QPushButton {
            background:#2563eb;
            border:none;
            padding:8px;
            border-radius:8px;
            font-weight:bold;
        }
        QPushButton:hover {
            background:#3b82f6;
        }
        QTextEdit {
            background:#0b1220;
            border-radius:8px;
            padding:8px;
        }
        QLineEdit {
            background:#1e293b;
            border:1px solid #334155;
            border-radius:6px;
            padding:5px;
        }
        QProgressBar {
            border:none;
            background:#1e293b;
            height:6px;
        }
        QProgressBar::chunk {
            background:#38bdf8;
        }
        QTableWidget {
            background:#0b1220;
            border-radius:8px;
            gridline-color:#1e293b;
        }
        """