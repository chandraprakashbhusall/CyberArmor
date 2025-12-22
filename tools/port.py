import socket
import threading
from queue import Queue
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
import db


# ==========================================================
# PORT DEFINITIONS
# ==========================================================
DANGEROUS_PORTS = {
    21: "FTP (Vulnerable)",
    22: "SSH (Bruteforce Risk)",
    23: "TELNET (Very Dangerous)",
    25: "SMTP (Open Relay Risk)",
    53: "DNS (Resolver Exposure)",
    110: "POP3",
    139: "SMB",
    445: "SMB",
    3306: "MySQL",
    3389: "RDP",
    5900: "VNC"
}

SAFE_PORTS = {
    80: "HTTP",
    443: "HTTPS",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt"
}

IMPORTANT_PORTS = list(DANGEROUS_PORTS.keys()) + list(SAFE_PORTS.keys())


# ==========================================================
# OS Detection Improved
# ==========================================================
def detect_os(ip):
    try:
        cmd = ["ping", "-c", "1", ip]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
        ttl = int(output.lower().split("ttl=")[1].split()[0])

        if ttl > 100:
            return "Windows (TTL≈128)"
        elif ttl > 50:
            return "Linux (TTL≈64)"
        else:
            return "Unknown OS"

    except Exception:
        return "OS Undetected"


# ==========================================================
# Threat Level
# ==========================================================
def threat_level(port):
    if port in DANGEROUS_PORTS:
        return "HIGH", "🟥 HIGH RISK", DANGEROUS_PORTS[port]

    if port in SAFE_PORTS:
        return "SAFE", "🟩 SAFE", SAFE_PORTS[port]

    if port < 1024:
        return "MEDIUM", "🟧 MEDIUM", "System level port"

    return "LOW", "🟨 LOW", "User space port"


# ==========================================================
# Banner Grab
# ==========================================================
def identify_service(ip, port):
    try:
        s = socket.socket()
        s.settimeout(0.5)
        s.connect((ip, port))
        s.send(b"HEAD / HTTP/1.1\r\nHost: test\r\n\r\n")
        banner = s.recv(1024).decode(errors="ignore")
        s.close()

        if "HTTP" in banner:
            for line in banner.split("\n"):
                if "Server:" in line:
                    return f"HTTP ({line.strip()})"
            return "HTTP Service"

    except:
        return "Unknown"
    return "Unknown"


# ==========================================================
# PORT SCAN THREAD
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
            self.progress.emit("❌ Invalid Host")
            self.finished.emit([])
            return

        # OS detection
        os_guess = detect_os(ip)
        self.progress.emit(f"🖥 OS: {os_guess}")

        # Ports to scan
        if self.mode == "Quick Scan":
            ports = IMPORTANT_PORTS
        else:
            ports = range(1, 1025)

        for p in ports:
            self.queue.put(p)

        threads = []
        for _ in range(60):
            t = threading.Thread(target=self.scan_port, args=(ip,))
            t.daemon = True
            t.start()
            threads.append(t)

        self.queue.join()

        db.save_port_scan(self.target, self.mode, self.results, os_guess)
        self.finished.emit(self.results)

    def scan_port(self, ip):
        while not self.queue.empty():
            port = self.queue.get()
            try:
                s = socket.socket()
                s.settimeout(0.2)

                if s.connect_ex((ip, port)) == 0:
                    level, emoji, desc = threat_level(port)
                    service = identify_service(ip, port)

                    msg = f"{emoji} | Port {port} → {desc} | {service}"
                    self.progress.emit(msg)
                    self.results.append(msg)

                    self.table_update.emit(port, "OPEN", emoji)

                else:
                    self.table_update.emit(port, "CLOSED", "⬛")

                s.close()

            except:
                pass

            self.queue.task_done()


# ==========================================================
# MAIN UI WIDGET
# ==========================================================
class PortScannerWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Title
        title = QLabel("🛠 Advanced Port Scanner")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: cyan;")
        layout.addWidget(title)

        # Input Row
        row = QHBoxLayout()

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Enter IP or Domain (e.g., 192.168.1.1)")
        self.target_input.setStyleSheet("padding: 10px; font-size: 18px;")
        row.addWidget(self.target_input)

        self.mode = QComboBox()
        self.mode.addItems(["Quick Scan", "Full Scan"])
        self.mode.setStyleSheet("padding: 10px; font-size: 18px;")
        row.addWidget(self.mode)

        self.btn_start = QPushButton("Start Scan")
        self.btn_start.setStyleSheet(
            "padding: 10px; background:#007bff; color:white; font-weight:bold;"
        )
        self.btn_start.clicked.connect(self.start_scan)
        row.addWidget(self.btn_start)

        layout.addLayout(row)

        # Output Text
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background:#111; color:white; padding:10px;")
        layout.addWidget(self.output)

        # IMPORTANT PORTS TABLE
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Port", "Status", "Threat Level"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setRowCount(len(IMPORTANT_PORTS))
        layout.addWidget(self.table)

        # Fill table
        for i, p in enumerate(IMPORTANT_PORTS):
            self.table.setItem(i, 0, QTableWidgetItem(str(p)))
            self.table.setItem(i, 1, QTableWidgetItem("—"))
            self.table.setItem(i, 2, QTableWidgetItem("—"))

        self.setLayout(layout)

    # -----------------------------------------------------
    def start_scan(self):
        target = self.target_input.text().strip()
        if not target:
            self.output.append("❌ Please enter a target.")
            return

        self.output.append(f"\n🔍 Starting scan on {target}...\n")

        self.worker = PortScanWorker(target, self.mode.currentText())
        self.worker.progress.connect(self.output.append)
        self.worker.finished.connect(self.scan_finished)
        self.worker.table_update.connect(self.update_table)

        self.worker.start()

    # -----------------------------------------------------
    def update_table(self, port, status, emoji):
        try:
            row = IMPORTANT_PORTS.index(port)
            self.table.setItem(row, 1, QTableWidgetItem(status))
            self.table.setItem(row, 2, QTableWidgetItem(emoji))
        except:
            pass

    # -----------------------------------------------------
    def scan_finished(self, results):
        self.output.append("\n✔ Scan completed.\n")
