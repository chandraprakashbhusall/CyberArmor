"""
CyberArmor – WiFi Analyzer & Speed Test
With export to JSON/CSV and real-time speed display.
"""

import csv
import json
import os
import platform
import subprocess
import datetime

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QLineEdit, QFormLayout, QGroupBox, QHBoxLayout,
    QProgressBar, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QHeaderView
)

HISTORY_FILE = "speed_history.json"


# ──────────────────────────────────────────────
# SPEED WORKER
# ──────────────────────────────────────────────

class SpeedWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)

    def run(self):
        try:
            self.progress.emit("🔄 Running speed test — this may take up to 30 seconds...")
            result = subprocess.check_output(
                ["speedtest-cli", "--json"],
                timeout=120,
                stderr=subprocess.DEVNULL
            ).decode()
            data = json.loads(result)
            self.finished.emit({
                "download": round(data["download"] / 1_000_000, 2),
                "upload":   round(data["upload"]   / 1_000_000, 2),
                "ping":     round(data["ping"],    2),
                "server":   data["server"]["name"],
                "isp":      data["client"]["isp"]
            })
        except FileNotFoundError:
            self.progress.emit("❌ speedtest-cli not found. Install: pip install speedtest-cli")
            self.finished.emit({})
        except Exception as e:
            self.progress.emit(f"❌ Speed test failed: {e}")
            self.finished.emit({})


# ──────────────────────────────────────────────
# WIFI WIDGET
# ──────────────────────────────────────────────

class WifiAdvancedWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.speed_history = self._load_history()
        self._last_result  = None

        main = QVBoxLayout(self)
        main.setContentsMargins(28, 22, 28, 22)
        main.setSpacing(18)

        # Title
        title = QLabel("📶  Advanced WiFi & Speed Analyzer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; background: transparent;")
        main.addWidget(title)

        # ── WiFi Info ──
        wifi_box = self._group("📡  Current WiFi Connection")
        wifi_form = QFormLayout()
        self.ssid_lbl = QLabel("—")
        self.pwd_field = QLineEdit()
        self.pwd_field.setReadOnly(True)
        self.pwd_field.setEchoMode(QLineEdit.Password)
        self.pwd_field.setFixedHeight(36)

        eye_row = QHBoxLayout()
        eye_row.addWidget(self.pwd_field)
        eye_btn = QPushButton("👁")
        eye_btn.setFixedSize(36, 36)
        eye_btn.setStyleSheet("background: #1e293b; border: 1px solid #334155; border-radius: 8px;")
        eye_btn.clicked.connect(self._toggle_pwd)
        eye_row.addWidget(eye_btn)

        wifi_form.addRow("SSID:", self.ssid_lbl)
        wifi_form.addRow("Password:", eye_row)
        wifi_box.layout().addLayout(wifi_form)
        main.addWidget(wifi_box)

        self._load_wifi()

        # ── Speed Test ──
        speed_box = self._group("🚀  Internet Speed Test")
        speed_v = QVBoxLayout()

        btn_row = QHBoxLayout()
        self.speed_btn = QPushButton("▶  Run Speed Test")
        self.speed_btn.setFixedHeight(42)
        self.speed_btn.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4,stop:1 #0097a7);
            border: none; border-radius: 10px; color: black; font-weight: bold;
        }
        QPushButton:hover { background: #26C6DA; }
        """)
        self.speed_btn.clicked.connect(self._start_speed)
        btn_row.addWidget(self.speed_btn)

        self.export_btn = QPushButton("💾  Export History")
        self.export_btn.setFixedHeight(42)
        self.export_btn.setEnabled(len(self.speed_history) > 0)
        self.export_btn.clicked.connect(self._export_history)
        self.export_btn.setStyleSheet("""
        QPushButton {
            background: #1e293b; border: 1px solid #334155;
            border-radius: 10px; color: #94a3b8; font-weight: bold;
        }
        QPushButton:hover { background: #334155; color: #e2e8f0; }
        QPushButton:disabled { color: #4b5563; }
        """)
        btn_row.addWidget(self.export_btn)
        speed_v.addLayout(btn_row)

        self.prog = QProgressBar()
        self.prog.setRange(0, 0)
        self.prog.setFixedHeight(6)
        self.prog.hide()
        speed_v.addWidget(self.prog)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFixedHeight(130)
        self.output.setStyleSheet("font-family: 'Courier New'; font-size: 12px;")
        speed_v.addWidget(self.output)

        speed_box.layout().addLayout(speed_v)
        main.addWidget(speed_box)

        # ── History Table ──
        hist_box = self._group("📊  Speed Test History")
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Date & Time", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)", "ISP"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)   # results are read-only
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        hist_box.layout().addWidget(self.table)
        main.addWidget(hist_box)

        self._populate_table()

    # ── HELPERS ──────────────────────────────

    def _group(self, title):
        box = QGroupBox(title)
        box.setLayout(QVBoxLayout())
        return box

    def _load_wifi(self):
        try:
            system = platform.system()
            if system == "Windows":
                out  = subprocess.check_output("netsh wlan show interfaces",
                                               shell=True, stderr=subprocess.DEVNULL).decode(errors="ignore")
                ssid = ""
                for line in out.splitlines():
                    if "SSID" in line and "BSSID" not in line:
                        ssid = line.split(":", 1)[1].strip()
                        break
                self.ssid_lbl.setText(ssid or "Not Connected")
                if ssid:
                    profile = subprocess.check_output(
                        f'netsh wlan show profile name="{ssid}" key=clear',
                        shell=True, stderr=subprocess.DEVNULL).decode(errors="ignore")
                    for line in profile.splitlines():
                        if "Key Content" in line:
                            self.pwd_field.setText(line.split(":", 1)[1].strip())
                            return
                self.pwd_field.setText("Unavailable")
            else:
                ssid = subprocess.getoutput("iwgetid -r").strip()
                self.ssid_lbl.setText(ssid if ssid else "Not Connected")
                self.pwd_field.setText("Protected — root required")
        except Exception:
            self.ssid_lbl.setText("Unknown")
            self.pwd_field.setText("Unavailable")

    def _toggle_pwd(self):
        mode = QLineEdit.Normal if self.pwd_field.echoMode() == QLineEdit.Password else QLineEdit.Password
        self.pwd_field.setEchoMode(mode)

    def _start_speed(self):
        self.output.clear()
        self.prog.show()
        self.speed_btn.setEnabled(False)
        self.speed_btn.setText("Testing...")

        self.worker = SpeedWorker()
        self.worker.progress.connect(self.output.append)
        self.worker.finished.connect(self._on_speed_done)
        self.worker.start()

    def _on_speed_done(self, result):
        self.prog.hide()
        self.speed_btn.setEnabled(True)
        self.speed_btn.setText("▶  Run Speed Test")

        if not result:
            return

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.output.append(f"""
✅ Speed Test Complete  —  {now}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⬇  Download : {result['download']} Mbps
⬆  Upload   : {result['upload']} Mbps
📡  Ping     : {result['ping']} ms
🌐  ISP      : {result['isp']}
🖥  Server   : {result['server']}
""")

        self._last_result = result

        reply = QMessageBox.question(
            self, "Save Result",
            "Save this speed test result to history?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            entry = {
                "date":     now,
                "download": result["download"],
                "upload":   result["upload"],
                "ping":     result["ping"],
                "isp":      result["isp"]
            }
            self.speed_history.append(entry)
            self._save_history()
            self._populate_table()
            self.export_btn.setEnabled(True)

    def _populate_table(self):
        self.table.setRowCount(len(self.speed_history))
        for r, entry in enumerate(reversed(self.speed_history)):
            self.table.setItem(r, 0, QTableWidgetItem(entry["date"]))
            self.table.setItem(r, 1, QTableWidgetItem(str(entry["download"])))
            self.table.setItem(r, 2, QTableWidgetItem(str(entry["upload"])))
            self.table.setItem(r, 3, QTableWidgetItem(str(entry["ping"])))
            self.table.setItem(r, 4, QTableWidgetItem(entry["isp"]))

    def _load_history(self):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_history(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump(self.speed_history, f, indent=4)

    def _export_history(self):
        if not self.speed_history:
            QMessageBox.information(self, "No Data", "No history to export.")
            return

        path, fmt = QFileDialog.getSaveFileName(
            self, "Export Speed History",
            f"wifi_speed_history_{datetime.datetime.now().strftime('%Y%m%d')}",
            "Text (*.txt);;JSON (*.json);;CSV (*.csv)"
        )
        if not path:
            return

        if path.endswith(".csv"):
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)", "ISP"])
                for e in self.speed_history:
                    writer.writerow([e["date"], e["download"], e["upload"], e["ping"], e["isp"]])
        elif path.endswith(".txt"):
            with open(path, "w") as f:
                f.write("CyberArmor - WiFi Speed Test History\n")
                f.write("=" * 44 + "\n\n")
                for e in self.speed_history:
                    f.write("Date     : " + str(e["date"]) + "\n")
                    f.write("Download : " + str(e["download"]) + " Mbps\n")
                    f.write("Upload   : " + str(e["upload"]) + " Mbps\n")
                    f.write("Ping     : " + str(e["ping"]) + " ms\n")
                    f.write("ISP      : " + str(e["isp"]) + "\n\n")
        else:
            with open(path, "w") as f:
                json.dump(self.speed_history, f, indent=4)

        QMessageBox.information(self, "Exported", f"✅ History saved:\n{path}")