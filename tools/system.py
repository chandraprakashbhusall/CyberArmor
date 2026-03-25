import platform
import psutil
import socket
import subprocess
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QHBoxLayout, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from tools import theme


# ==========================================================
# SYSTEM SCAN THREAD
# ==========================================================
class SystemScanThread(QThread):
    result_signal = pyqtSignal(dict)

    def run(self):
        result = {}
        risk_score = 0

        # ---------------- OS INFO ----------------
        result["os"] = f"{platform.system()} {platform.release()}"

        # ---------------- CPU ----------------
        cpu = psutil.cpu_percent(interval=1)
        result["cpu"] = cpu
        if cpu > 85:
            risk_score += 1

        # ---------------- RAM ----------------
        ram = psutil.virtual_memory().percent
        result["ram"] = ram
        if ram > 85:
            risk_score += 1

        # ---------------- DISK ----------------
        try:
            disk = psutil.disk_usage('/')
            result["disk"] = disk.percent
            if disk.percent > 90:
                risk_score += 2
        except:
            result["disk"] = None

        # ---------------- INTERNET ----------------
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            result["internet"] = True
        except:
            result["internet"] = False
            risk_score += 1

        # ---------------- FIREWALL (Linux Only) ----------------
        firewall_active = None
        if platform.system() == "Linux":
            try:
                status = subprocess.getoutput("ufw status")
                firewall_active = "inactive" not in status.lower()
                if not firewall_active:
                    risk_score += 2
            except:
                firewall_active = None

        result["firewall"] = firewall_active

        # ---------------- FINAL STATUS ----------------
        if risk_score == 0:
            overall = "SAFE"
        elif risk_score <= 2:
            overall = "WARNING"
        else:
            overall = "CRITICAL"

        result["overall"] = overall
        result["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.result_signal.emit(result)


# ==========================================================
# MAIN WIDGET
# ==========================================================
class SystemSecurityWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(theme.get_stylesheet())

        main = QVBoxLayout(self)
        main.setContentsMargins(40, 30, 40, 30)
        main.setSpacing(25)

        # ================= TITLE =================
        title = QLabel("🛡 System Health & Security Check")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:26px; font-weight:700;")
        main.addWidget(title)

        # ================= STATUS CARD =================
        self.status_card = self.create_card("System Status")
        self.status_label = QLabel("Click scan to check your system health.")
        self.status_label.setStyleSheet("font-size:16px; font-weight:600;")
        self.status_card.layout().addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.status_card.layout().addWidget(self.progress)

        main.addWidget(self.status_card)

        # ================= DETAILS CARD =================
        self.details_card = self.create_card("Scan Details")
        self.details_output = QTextEdit()
        self.details_output.setReadOnly(True)
        self.details_card.layout().addWidget(self.details_output)

        main.addWidget(self.details_card)

        # ================= BUTTON =================
        self.scan_btn = QPushButton("Run System Scan")
        self.scan_btn.setFixedHeight(45)
        self.scan_btn.clicked.connect(self.start_scan)
        main.addWidget(self.scan_btn)

        main.addStretch()

    # ==================================================
    # CARD CONTAINER
    # ==================================================
    def create_card(self, title_text):
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet("""
            QFrame#card {
                border-radius: 12px;
                padding: 20px;
                background-color: rgba(255,255,255,0.04);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(15)

        title = QLabel(title_text)
        title.setStyleSheet("font-size:18px; font-weight:600;")
        layout.addWidget(title)

        return card

    # ==================================================
    # START SCAN
    # ==================================================
    def start_scan(self):
        self.status_label.setText("Scanning system... please wait")
        self.progress.setValue(30)
        self.details_output.clear()

        self.thread = SystemScanThread()
        self.thread.result_signal.connect(self.show_result)
        self.thread.start()

    # ==================================================
    # SHOW RESULT
    # ==================================================
    def show_result(self, data):
        self.progress.setValue(100)

        overall = data["overall"]

        if overall == "SAFE":
            self.status_label.setText("🟢 Your system looks safe and healthy.")
        elif overall == "WARNING":
            self.status_label.setText("🟡 Minor issues detected. Review details below.")
        else:
            self.status_label.setText("🔴 Security risk detected! Attention required.")

        # ================= USER FRIENDLY REPORT =================
        report = f"""
📅 Scan Time: {data['time']}

💻 Operating System:
   {data['os']}

⚙ CPU Usage:
   {data['cpu']}%
   {"High usage — close heavy apps." if data['cpu'] > 85 else "Normal usage."}

🧠 RAM Usage:
   {data['ram']}%
   {"Memory almost full — consider restarting." if data['ram'] > 85 else "Memory usage is healthy."}

💾 Disk Usage:
   {data['disk']}%
   {"Disk nearly full — clean unnecessary files." if data['disk'] and data['disk'] > 90 else "Storage space is fine."}

🌐 Internet Connection:
   {"Connected and working." if data['internet'] else "No internet connection detected."}
"""

        if data["firewall"] is not None:
            report += f"""
🔥 Firewall Protection:
   {"Active and protecting your system." if data['firewall'] else "Firewall is OFF — your system may be exposed."}
"""

        report += "\n\n🛡 Recommendation:\n"
        report += " - Keep your system updated.\n"
        report += " - Avoid installing unknown software.\n"
        report += " - Use antivirus for extra protection.\n"

        self.details_output.setText(report)