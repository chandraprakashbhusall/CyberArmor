"""
CyberArmor – Port Scanner
Fixed threading, proper DB save, export to JSON/TXT.
"""

import json
import socket
import subprocess
import threading
from datetime import datetime
from queue import Queue, Empty

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QFileDialog, QMessageBox
)

import db
from tools import theme


# ──────────────────────────────────────────────
# PORT DEFINITIONS
# ──────────────────────────────────────────────

DANGEROUS_PORTS = {21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
                   3306: "MySQL", 3389: "RDP", 4444: "Metasploit",
                   5900: "VNC", 6667: "IRC", 27017: "MongoDB"}

SAFE_PORTS = {80: "HTTP", 443: "HTTPS", 8080: "HTTP-Alt", 8443: "HTTPS-Alt"}

IMPORTANT_PORTS = sorted(set(list(DANGEROUS_PORTS.keys()) + list(SAFE_PORTS.keys())))


def detect_os(ip):
    try:
        out = subprocess.check_output(["ping", "-c", "1", "-W", "1", ip],
                                      stderr=subprocess.DEVNULL).decode()
        ttl = int(out.lower().split("ttl=")[1].split()[0])
        if ttl > 100:
            return "Windows"
        elif ttl > 50:
            return "Linux / macOS"
        return "Unknown"
    except Exception:
        return "Undetected"


# ──────────────────────────────────────────────
# WORKER
# ──────────────────────────────────────────────

class PortScanWorker(QThread):
    progress     = pyqtSignal(str)
    table_update = pyqtSignal(int, str, str, str)
    finished     = pyqtSignal(list, str)

    def __init__(self, target, mode):
        super().__init__()
        self.target  = target
        self.mode    = mode
        self.results = []
        self.queue   = Queue()
        self._lock   = threading.Lock()

    def run(self):
        try:
            ip = socket.gethostbyname(self.target)
        except Exception:
            self.progress.emit("❌ Cannot resolve host.")
            self.finished.emit([], "Unknown")
            return

        os_guess = detect_os(ip)
        self.progress.emit(f"🖥  OS Detected: {os_guess}")
        self.progress.emit(f"🔍  Scanning {ip} ({self.target}) — {self.mode}")

        if self.mode == "Quick Scan":
            ports = IMPORTANT_PORTS
        elif self.mode == "Full Scan (1-1024)":
            ports = range(1, 1025)
        else:
            ports = range(1, 65536)

        for p in ports:
            self.queue.put(p)

        threads = []
        for _ in range(min(100, self.queue.qsize())):
            t = threading.Thread(target=self._scan_port, args=(ip,), daemon=True)
            t.start()
            threads.append(t)

        self.queue.join()

        # Save to DB
        try:
            db.save_port_scan(self.target, self.mode, self.results, os_guess)
        except Exception:
            pass

        self.progress.emit(f"\n✅ Scan complete — {len(self.results)} open port(s) found.")
        self.finished.emit(self.results, os_guess)

    def _scan_port(self, ip):
        while True:
            try:
                port = self.queue.get_nowait()
            except Empty:
                break

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.4)
                result = s.connect_ex((ip, port))
                s.close()

                if result == 0:
                    if port in DANGEROUS_PORTS:
                        emoji   = "🔴"
                        service = DANGEROUS_PORTS[port]
                        risk    = "⚠ Dangerous"
                    elif port in SAFE_PORTS:
                        emoji   = "🟢"
                        service = SAFE_PORTS[port]
                        risk    = "Safe"
                    else:
                        emoji   = "🟡"
                        service = "Unknown"
                        risk    = "Review"

                    line = f"{emoji} Port {port} OPEN — {service}"
                    with self._lock:
                        self.results.append({"port": port, "service": service,
                                             "risk": risk, "status": "OPEN"})
                    self.progress.emit(line)
                    self.table_update.emit(port, "OPEN", service, risk)
                else:
                    self.table_update.emit(port, "CLOSED", "", "")

            except Exception:
                pass
            finally:
                self.queue.task_done()


# ──────────────────────────────────────────────
# WIDGET
# ──────────────────────────────────────────────

class PortScannerWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.scan_results = []
        self.scan_target  = ""
        self.scan_os      = ""

        main = QVBoxLayout(self)
        main.setContentsMargins(28, 22, 28, 22)
        main.setSpacing(18)

        # Title
        title = QLabel("🚀  Advanced Network Port Scanner")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Bold) if True else None)
        title.setStyleSheet("font-size: 20px; font-weight: bold; background: transparent;")
        main.addWidget(title)

        # Control row
        ctrl = QFrame()
        ctrl.setStyleSheet("QFrame { background: #111827; border-radius: 12px; border: 1px solid #1e293b; }")
        ctrl_layout = QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)
        ctrl_layout.setSpacing(12)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Target IP or domain (e.g. scanme.nmap.org)")
        self.target_input.setFixedHeight(42)
        ctrl_layout.addWidget(self.target_input, 3)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Quick Scan", "Full Scan (1-1024)", "Deep Scan (All Ports)"])
        self.mode_combo.setFixedHeight(42)
        self.mode_combo.setFixedWidth(200)
        ctrl_layout.addWidget(self.mode_combo)

        self.start_btn = QPushButton("▶  Start Scan")
        self.start_btn.setFixedHeight(42)
        self.start_btn.setFixedWidth(140)
        self.start_btn.clicked.connect(self._start_scan)
        self.start_btn.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4,stop:1 #0097a7);
            border: none; border-radius: 10px; color: black; font-weight: bold; font-size: 14px;
        }
        QPushButton:hover { background: #26C6DA; }
        QPushButton:disabled { background: #1e293b; color: #4b5563; }
        """)
        ctrl_layout.addWidget(self.start_btn)

        self.export_btn = QPushButton("💾  Export")
        self.export_btn.setFixedHeight(42)
        self.export_btn.setFixedWidth(110)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export)
        self.export_btn.setStyleSheet("""
        QPushButton {
            background: #1e293b; border: 1px solid #334155;
            border-radius: 10px; color: #94a3b8; font-weight: bold;
        }
        QPushButton:hover { background: #334155; color: #e2e8f0; }
        QPushButton:disabled { color: #4b5563; }
        """)
        ctrl_layout.addWidget(self.export_btn)

        main.addWidget(ctrl)

        # Output + Table split
        split = QHBoxLayout()
        split.setSpacing(16)

        # Log output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
        QTextEdit {
            background: #060c18;
            border: 1px solid #1e293b;
            border-radius: 10px;
            padding: 10px;
            font-family: "Courier New", monospace;
            font-size: 12px;
            color: #7dd3fc;
        }
        """)
        split.addWidget(self.output, 2)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Port", "Status", "Service", "Risk"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self._reset_table()
        split.addWidget(self.table, 3)

        main.addLayout(split)

        self.worker = None

    # ══════════════════════════════════════════
    # ACTIONS
    # ══════════════════════════════════════════

    def _start_scan(self):
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Input Required", "Please enter a target IP or domain.")
            return

        self.scan_target = target
        self.scan_results = []
        self.output.clear()
        self.export_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.start_btn.setText("Scanning...")
        self._reset_table()

        mode = self.mode_combo.currentText()
        self.worker = PortScanWorker(target, mode)
        self.worker.progress.connect(self.output.append)
        self.worker.table_update.connect(self._update_table)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _reset_table(self):
        self.table.setRowCount(len(IMPORTANT_PORTS))
        for i, port in enumerate(IMPORTANT_PORTS):
            self.table.setItem(i, 0, QTableWidgetItem(str(port)))
            self.table.setItem(i, 1, QTableWidgetItem("—"))
            svc = DANGEROUS_PORTS.get(port, SAFE_PORTS.get(port, ""))
            self.table.setItem(i, 2, QTableWidgetItem(svc))
            self.table.setItem(i, 3, QTableWidgetItem("—"))

    def _update_table(self, port, status, service, risk):
        if port not in IMPORTANT_PORTS:
            return
        row = IMPORTANT_PORTS.index(port)
        self.table.setItem(row, 1, QTableWidgetItem(status))
        if service:
            self.table.setItem(row, 2, QTableWidgetItem(service))
        if risk:
            self.table.setItem(row, 3, QTableWidgetItem(risk))

        # Colour open rows
        if status == "OPEN":
            color = "#1e1f0e" if "Safe" in risk else "#1f0e0e"
            for c in range(4):
                item = self.table.item(row, c)
                if item:
                    item.setBackground(__import__("PyQt5.QtGui", fromlist=["QColor"]).QColor(color))

    def _on_finished(self, results, os_guess):
        self.scan_results = results
        self.scan_os      = os_guess
        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶  Start Scan")
        self.export_btn.setEnabled(True)

    def _export(self):
        if not self.scan_results:
            QMessageBox.information(self, "No Data", "No scan results to export yet.")
            return

        path, fmt = QFileDialog.getSaveFileName(
            self, "Save Scan Report",
            f"port_scan_{self.scan_target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "JSON Report (*.json);;Text Report (*.txt)"
        )
        if not path:
            return

        if path.endswith(".txt"):
            with open(path, "w") as f:
                f.write(f"CyberArmor Port Scan Report\n")
                f.write(f"Target : {self.scan_target}\n")
                f.write(f"OS     : {self.scan_os}\n")
                f.write(f"Date   : {datetime.now()}\n")
                f.write("=" * 50 + "\n")
                for r in self.scan_results:
                    f.write(f"Port {r['port']} OPEN — {r['service']} — {r['risk']}\n")
        else:
            report = {
                "target": self.scan_target,
                "os_guess": self.scan_os,
                "scanned_at": str(datetime.now()),
                "open_ports": self.scan_results,
            }
            with open(path, "w") as f:
                json.dump(report, f, indent=4)

        QMessageBox.information(self, "Saved", f"✅ Report saved:\n{path}")

# Fix missing import
from PyQt5.QtGui import QFont
