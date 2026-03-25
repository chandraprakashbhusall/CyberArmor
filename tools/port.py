import socket
import threading
from queue import Queue
import subprocess

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QHBoxLayout, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame
)

import db
from tools import theme


# ==========================================================
# PORT DEFINITIONS
# ==========================================================
DANGEROUS_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "TELNET",
    25: "SMTP",
    3306: "MySQL",
    3389: "RDP"
}

SAFE_PORTS = {
    80: "HTTP",
    443: "HTTPS"
}

IMPORTANT_PORTS = list(DANGEROUS_PORTS.keys()) + list(SAFE_PORTS.keys())


# ==========================================================
# OS Detection
# ==========================================================
def detect_os(ip):
    try:
        cmd = ["ping", "-c", "1", ip]
        output = subprocess.check_output(cmd).decode()
        ttl = int(output.lower().split("ttl=")[1].split()[0])

        if ttl > 100:
            return "Windows"
        elif ttl > 50:
            return "Linux"
        return "Unknown"
    except:
        return "Undetected"


# ==========================================================
# Worker Thread
# ==========================================================
class PortScanWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    table_update = pyqtSignal(int, str, str)

    def __init__(self, target, mode):
        super().__init__()
        self.target = target
        self.mode = mode
        self.results = []
        self.queue = Queue()

    def run(self):
        try:
            ip = socket.gethostbyname(self.target)
        except:
            self.progress.emit("❌ Invalid Target")
            self.finished.emit([])
            return

        os_guess = detect_os(ip)
        self.progress.emit(f"🖥 Detected OS: {os_guess}")

        ports = IMPORTANT_PORTS if self.mode == "Quick Scan" else range(1, 1025)

        for p in ports:
            self.queue.put(p)

        for _ in range(50):
            t = threading.Thread(target=self.scan_port, args=(ip,))
            t.daemon = True
            t.start()

        self.queue.join()

        db.save_port_scan(self.target, self.mode, self.results, os_guess)
        self.finished.emit(self.results)

    def scan_port(self, ip):
        while not self.queue.empty():
            port = self.queue.get()

            try:
                s = socket.socket()
                s.settimeout(0.3)

                if s.connect_ex((ip, port)) == 0:
                    emoji = "🟥" if port in DANGEROUS_PORTS else "🟢"
                    msg = f"{emoji} Port {port} OPEN"
                    self.progress.emit(msg)
                    self.results.append(msg)
                    self.table_update.emit(port, "OPEN", emoji)
                else:
                    self.table_update.emit(port, "CLOSED", "⚫")

                s.close()
            except:
                pass

            self.queue.task_done()


# ==========================================================
# MAIN WIDGET
# ==========================================================
class PortScannerWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(theme.DARK_THEME)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # ================= TITLE =================
        title = QLabel("🚀 Advanced Network Port Scanner")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:26px; font-weight:bold;")
        layout.addWidget(title)

        # ================= TOP CONTROLS =================
        control_frame = QFrame()
        control_layout = QHBoxLayout()

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Enter IP or Domain")

        self.mode = QComboBox()
        self.mode.addItems(["Quick Scan", "Full Scan"])

        self.theme_toggle = QPushButton("🌙 Dark")
        self.theme_toggle.clicked.connect(self.toggle_theme)

        self.start_btn = QPushButton("Start Scan")
        self.start_btn.clicked.connect(self.start_scan)

        control_layout.addWidget(self.target_input)
        control_layout.addWidget(self.mode)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.theme_toggle)

        control_frame.setLayout(control_layout)
        layout.addWidget(control_frame)

        # ================= OUTPUT =================
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # ================= TABLE =================
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Port", "Status", "Risk"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setRowCount(len(IMPORTANT_PORTS))

        for i, p in enumerate(IMPORTANT_PORTS):
            self.table.setItem(i, 0, QTableWidgetItem(str(p)))
            self.table.setItem(i, 1, QTableWidgetItem("—"))
            self.table.setItem(i, 2, QTableWidgetItem("—"))

        layout.addWidget(self.table)

        self.setLayout(layout)
        self.dark_mode = True

    # ==================================================
    def toggle_theme(self):
        if self.dark_mode:
            self.setStyleSheet(theme.LIGHT_THEME)
            self.theme_toggle.setText("☀ Light")
            self.dark_mode = False
        else:
            self.setStyleSheet(theme.DARK_THEME)
            self.theme_toggle.setText("🌙 Dark")
            self.dark_mode = True

    # ==================================================
    def start_scan(self):
        target = self.target_input.text().strip()

        if not target:
            self.output.append("❌ Please enter target")
            return

        self.output.append(f"\n🔍 Scanning {target}...\n")

        self.worker = PortScanWorker(target, self.mode.currentText())
        self.worker.progress.connect(self.output.append)
        self.worker.finished.connect(self.scan_finished)
        self.worker.table_update.connect(self.update_table)
        self.worker.start()

    # ==================================================
    def update_table(self, port, status, emoji):
        if port in IMPORTANT_PORTS:
            row = IMPORTANT_PORTS.index(port)
            self.table.setItem(row, 1, QTableWidgetItem(status))
            self.table.setItem(row, 2, QTableWidgetItem(emoji))

    # ==================================================
    def scan_finished(self, results):
        self.output.append("\n✔ Scan Completed\n")