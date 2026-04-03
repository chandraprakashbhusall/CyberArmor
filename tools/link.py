"""
CyberArmor – Link Inspector
Clean version with fixed duplicate code, proper export.
"""

import json
import math
import re
import socket
import ssl
import datetime
from urllib.parse import urlparse

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QHBoxLayout,
    QFrame, QProgressBar, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt

import db


# ──────────────────────────────────────────────
# TRUSTED DOMAINS
# ──────────────────────────────────────────────

TRUSTED_DOMAINS = {
    "google.com": "Google", "youtube.com": "YouTube",
    "facebook.com": "Facebook", "instagram.com": "Instagram",
    "github.com": "GitHub", "openai.com": "OpenAI",
    "tiktok.com": "TikTok", "twitter.com": "Twitter / X",
    "microsoft.com": "Microsoft", "apple.com": "Apple",
}


def url_entropy(url):
    if not url:
        return 0.0
    prob = [url.count(c) / len(url) for c in set(url)]
    return round(-sum(p * math.log2(p) for p in prob if p > 0), 2)


def ssl_check(domain):
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=4) as raw:
            with ctx.wrap_socket(raw, server_hostname=domain) as ssock:
                cert   = ssock.getpeercert()
                issuer = dict(x[0] for x in cert.get("issuer", []))
                org    = issuer.get("organizationName", "Unknown CA")
                return True, f"Valid SSL (Issued by: {org})"
    except Exception:
        return False, "No SSL / Invalid certificate"


# ──────────────────────────────────────────────
# WORKER
# ──────────────────────────────────────────────

class LinkScanWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int, str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        flags = []
        data  = {
            "url":       self.url,
            "timestamp": str(datetime.datetime.now()),
        }

        try:
            self.progress.emit(5, "Initializing scan...")

            url = self.url.strip()
            if not re.match(r"^https?://", url):
                url = "http://" + url

            parsed     = urlparse(url)
            domain     = parsed.netloc.lower().split(":")[0]
            parts      = domain.split(".")
            base_domain = ".".join(parts[-2:]) if len(parts) >= 2 else domain

            data.update({"domain": domain, "base_domain": base_domain})

            # ── Domain checks ──
            self.progress.emit(20, f"Analyzing domain: {domain}")

            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
                flags.append("Raw IP address — no domain name")

            if len(parts) > 4:
                flags.append(f"Too many subdomains ({len(parts)-2} levels)")

            if domain.startswith("xn--"):
                flags.append("Punycode (internationalized) domain")

            suspicious_kw = ["login", "secure", "verify", "update", "bank",
                             "account", "confirm", "paypal", "wallet"]
            for kw in suspicious_kw:
                if kw in domain:
                    flags.append(f"Suspicious keyword in domain: '{kw}'")

            for trusted, name in TRUSTED_DOMAINS.items():
                if trusted in domain and not domain.endswith(trusted):
                    flags.append(f"Possible fake look-alike of {name} ({trusted})")

            # ── SSL ──
            self.progress.emit(55, "Checking SSL certificate...")
            ssl_ok, ssl_info = ssl_check(base_domain)
            if not ssl_ok:
                flags.append("No valid SSL certificate")
            data.update({"ssl": ssl_ok, "ssl_info": ssl_info})

            # ── Entropy ──
            self.progress.emit(80, "Calculating URL entropy...")
            entropy = url_entropy(url)
            data["entropy"] = entropy
            if entropy > 4.5:
                flags.append(f"High URL entropy ({entropy}) — possible obfuscation")

            # ── Score ──
            score = min(len(flags) * 20 + max(0, int(entropy) - 3) * 5, 100)
            data.update({"risk_score": score, "flags": flags})

            self.progress.emit(100, "Scan complete.")

            # Save to DB
            try:
                db.save_link_scan(data)
            except Exception:
                pass

        except Exception as e:
            data.update({"risk_score": 100, "flags": [str(e)],
                         "domain": "Error", "base_domain": "Error",
                         "ssl": False, "ssl_info": "Error", "entropy": 0})

        self.finished.emit(data)


# ──────────────────────────────────────────────
# WIDGET
# ──────────────────────────────────────────────

class LinkScannerWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.scan_data = None

        main = QVBoxLayout(self)
        main.setContentsMargins(28, 22, 28, 22)
        main.setSpacing(18)

        title = QLabel("🔗  Advanced Link Security Scanner")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; background: transparent;")
        main.addWidget(title)

        # Control row
        ctrl = QFrame()
        ctrl.setStyleSheet("QFrame { background: #111827; border-radius: 12px; border: 1px solid #1e293b; }")
        ctrl_layout = QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)
        ctrl_layout.setSpacing(12)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL to inspect (e.g. example.com or https://site.com)")
        self.url_input.setFixedHeight(42)
        self.url_input.returnPressed.connect(self._start_scan)
        ctrl_layout.addWidget(self.url_input, 1)

        self.scan_btn = QPushButton("🔍  Scan")
        self.scan_btn.setFixedHeight(42)
        self.scan_btn.setFixedWidth(120)
        self.scan_btn.clicked.connect(self._start_scan)
        self.scan_btn.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4,stop:1 #0097a7);
            border: none; border-radius: 10px; color: black; font-weight: bold;
        }
        QPushButton:hover { background: #26C6DA; }
        """)
        ctrl_layout.addWidget(self.scan_btn)

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

        # Progress + status
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setFixedHeight(8)
        main.addWidget(self.progress)

        self.status_lbl = QLabel("Status: —")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent;")
        main.addWidget(self.status_lbl)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
        QTextEdit {
            background: #060c18;
            border: 1px solid #1e293b;
            border-radius: 10px;
            padding: 12px;
            font-family: "Courier New", monospace;
            font-size: 12px;
            color: #7dd3fc;
        }
        """)
        main.addWidget(self.output)

        self.worker = None

    # ══════════════════════════════════════════
    # ACTIONS
    # ══════════════════════════════════════════

    def _start_scan(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Required", "Please enter a URL.")
            return

        self.output.clear()
        self.progress.setValue(0)
        self.status_lbl.setText("Scanning...")
        self.status_lbl.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: #94a3b8;")
        self.scan_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        self.worker = LinkScanWorker(url)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_result)
        self.worker.start()

    def _on_progress(self, value, msg):
        self.progress.setValue(value)
        self.output.append(f"  {msg}")

    def _on_result(self, data):
        self.scan_data = data
        score = data.get("risk_score", 0)

        if score >= 70:
            status, color = "🔴  DANGEROUS", "#ef4444"
        elif score >= 40:
            status, color = "🟡  WARNING", "#f59e0b"
        else:
            status, color = "🟢  SAFE", "#10b981"

        self.status_lbl.setText(f"{status}  —  {score}/100")
        self.status_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; background: transparent; color: {color};")

        self.output.append(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗  LINK INSPECTION REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URL         : {data.get('url', '—')}
Domain      : {data.get('domain', '—')}
Base Domain : {data.get('base_domain', '—')}
SSL Status  : {data.get('ssl_info', '—')}
Entropy     : {data.get('entropy', 0)}
Risk Score  : {score} / 100
""")

        flags = data.get("flags", [])
        if flags:
            self.output.append("⚠  Security Flags:")
            for f in flags:
                self.output.append(f"  • {f}")
        else:
            self.output.append("✅  No suspicious indicators found.")

        self.scan_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

    def _export(self):
        if not self.scan_data:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Link Scan Report",
            f"link_scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "JSON Report (*.json);;Text Report (*.txt)"
        )
        if not path:
            return

        if path.endswith(".txt"):
            with open(path, "w") as f:
                f.write("CyberArmor Link Scan Report\n")
                f.write(f"URL: {self.scan_data.get('url')}\n")
                f.write(f"Risk Score: {self.scan_data.get('risk_score')}/100\n")
                f.write(f"SSL: {self.scan_data.get('ssl_info')}\n\n")
                f.write("Flags:\n")
                for flag in self.scan_data.get("flags", []):
                    f.write(f"  • {flag}\n")
        else:
            with open(path, "w") as f:
                json.dump(self.scan_data, f, indent=4)

        QMessageBox.information(self, "Saved", f"✅ Report saved:\n{path}")
