import platform, os, psutil, socket, subprocess
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class SystemScanThread(QThread):
    result_signal = pyqtSignal(str)

    def run(self):
        report = "🖥 SYSTEM SECURITY REPORT\n"
        report += "──────────────────────────\n\n"

        # ---------------- OS INFO ----------------
        report += f"🔹 Operating System: {platform.system()} {platform.release()}\n"
        report += f"🔹 Kernel Version: {platform.version()}\n\n"

        # ---------------- CPU & RAM ----------------
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        report += f"⚙ CPU Usage: {cpu}%\n"
        report += f"🧠 RAM Usage: {ram}%\n\n"

        # ---------------- DISK USAGE ----------------
        try:
            disk = psutil.disk_usage('/')
            disk_status = "🟢 Healthy" if disk.percent < 85 else "⚠️ High Usage"
            report += f"💾 Disk Usage: {disk.percent}% ({disk_status})\n\n"
        except:
            report += "💾 Disk Usage: Unable to determine\n\n"

        # ---------------- RUNNING PROCESSES ----------------
        report += f"📌 Running Processes: {len(psutil.pids())}\n\n"

        # ---------------- OPEN PORTS ----------------
        report += "🌐 Listening Network Ports:\n"
        try:
            ports = subprocess.getoutput("ss -tulpn | grep LISTEN")
            if ports:
                report += "⚠️ Some services are listening on network ports:\n"
                for line in ports.splitlines()[:10]:
                    report += f"   • {line}\n"
                report += "   (Listing limited to 10 entries)\n\n"
            else:
                report += "🟢 No unexpected open ports detected.\n\n"
        except:
            report += "❌ Could not check open ports.\n\n"

        # ---------------- FIREWALL STATUS ----------------
        report += "🔥 Firewall Status:\n"
        if platform.system() == "Linux":
            try:
                ufw = subprocess.getoutput("sudo ufw status")
                if "inactive" in ufw.lower():
                    report += "⚠️ Firewall is inactive. Your system is exposed!\n\n"
                else:
                    report += f"🟢 Firewall active:\n{ufw}\n\n"
            except:
                report += "❌ Unable to determine firewall status.\n\n"
        else:
            report += "ℹ️ Firewall check only available on Linux.\n\n"

        # ---------------- ROOT LOGIN ----------------
        if platform.system() == "Linux":
            try:
                sshd = subprocess.getoutput("grep -i 'PermitRootLogin' /etc/ssh/sshd_config")
                if "yes" in sshd.lower():
                    report += "⚠️ Root login via SSH is ENABLED — Very risky!\n\n"
                else:
                    report += "🟢 Root login via SSH is disabled — Good!\n\n"
            except:
                report += "❌ Unable to check root login setting.\n\n"

        # ---------------- WEAK FILE PERMISSIONS ----------------
        if platform.system() == "Linux":
            report += "🔍 World-writable Files (may pose security risk):\n"
            try:
                ww = subprocess.getoutput("find / -perm -0002 -type f 2>/dev/null | head -n 5")
                if ww:
                    report += f"⚠️ Found some world-writable files:\n{ww}\n   (Listing limited to 5)\n\n"
                else:
                    report += "🟢 No weak file permissions detected.\n\n"
            except:
                report += "❌ Could not scan for weak permissions.\n\n"

        # ---------------- INTERNET CONNECTIVITY ----------------
        report += "🌐 Internet Connectivity:\n"
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            report += "🟢 Internet is active\n"
        except:
            report += "⚠️ Internet is not reachable\n"

        # ---------------- FINAL SYSTEM STATUS ----------------
        report += "\n──────────────────────────\n"
        report += "📌 Summary:\n"
        report += " - Review open ports and world-writable files carefully.\n"
        report += " - Ensure firewall is active and root login is disabled.\n"
        report += " - Check CPU, RAM, and disk usage regularly.\n"
        report += "🛡 Stay Safe! \n"

        self.result_signal.emit(report)


class SystemSecurityWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color:#0c0c0c; color:white;")

        layout = QVBoxLayout()
        title = QLabel("🖥 System Security Scanner")
        title.setStyleSheet("font-size:22px; font-weight:bold; color:cyan;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background:#111; font-size:15px; padding:10px;")
        layout.addWidget(self.output)

        self.scan_btn = QPushButton("Run Full Scan 🔍")
        self.scan_btn.setStyleSheet(
            "padding:12px; background:#1a1a1a; border-radius:6px; font-size:16px;"
        )
        self.scan_btn.clicked.connect(self.start_scan)
        layout.addWidget(self.scan_btn)

        self.setLayout(layout)

    def start_scan(self):
        self.output.setText("⏳ Running system scan… please wait...\n")
        self.thread = SystemScanThread()
        self.thread.result_signal.connect(self.show_result)
        self.thread.start()

    def show_result(self, text):
        self.output.setText(text)
