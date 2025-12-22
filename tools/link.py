import re
import math
import json
import socket
import ssl
from urllib.parse import urlparse
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QHBoxLayout
)
from PyQt5.QtCore import QThread, pyqtSignal
import db
import datetime

# ----------------------------
# Trusted domains DB
# ----------------------------
TRUSTED_DOMAINS = {
    "google.com": "Google",
    "youtube.com": "YouTube",
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "github.com": "GitHub",
    "openai.com": "OpenAI",
    "tiktok.com": "TikTok",
    "twitter.com": "Twitter / X"
}

# ----------------------------
# UTILS
# ----------------------------
def signal_bars(percent):
    if percent >= 80: return "🟩🟩🟩🟩"
    if percent >= 60: return "🟩🟩🟩"
    if percent >= 40: return "🟧🟧"
    if percent >= 20: return "🟥"
    return "•"

def url_entropy(url):
    """Calculate entropy of URL string for randomness / phishing"""
    prob = [url.count(c)/len(url) for c in set(url)]
    entropy = -sum([p*math.log2(p) for p in prob])
    return round(entropy,2)

def ssl_check(domain):
    """Return SSL info: valid / expired / self-signed"""
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(2)
            s.connect((domain, 443))
            cert = s.getpeercert()
            issuer = cert.get('issuer')
            return True, f"Issuer: {issuer}"
    except:
        return False, "No SSL / invalid certificate"


# ----------------------------
# WORKER THREAD
# ----------------------------
class LinkScanWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        self.progress.emit("🔍 Starting scan…")
        data = {"url": self.url, "timestamp": str(datetime.datetime.now())}

        # Ensure URL scheme
        url = self.url
        if not re.match(r'^https?://', url):
            url = "http://" + url
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        data["domain"] = domain
        self.progress.emit(f"🌐 Domain: {domain}")

        # Base domain
        parts = domain.split(".")
        base_domain = ".".join(parts[-2:]) if len(parts) >=2 else domain
        data["base_domain"] = base_domain
        self.progress.emit(f"Base domain: {base_domain}")

        # URL risk flags
        flags = []

        # IP-based domain
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
            flags.append("⚠️ Raw IP address")

        # Too many subdomains
        if len(parts) > 3:
            flags.append("⚠️ Excessive subdomains")

        # Homoglyph / punycode
        if domain.startswith("xn--"):
            flags.append("⚠️ Punycode domain (possible impersonation)")

        # Suspicious symbols
        if "@" in url:
            flags.append("⚠️ '@' in URL (redirect trick)")

        # Keyword analysis
        suspicious_keywords = ["login","secure","verify","update","bank","account"]
        for kw in suspicious_keywords:
            if kw in domain:
                flags.append(f"⚠️ Suspicious keyword: {kw}")

        # Look-alike domains
        for t in TRUSTED_DOMAINS:
            if t in domain and not domain.endswith(t):
                flags.append(f"⚠️ Looks similar to {t} but is fake")

        data["flags"] = flags

        # SSL check
        ssl_ok, ssl_info = ssl_check(base_domain)
        data["ssl"] = ssl_ok
        data["ssl_info"] = ssl_info
        self.progress.emit(f"🔒 SSL: {ssl_info}")

        # URL entropy
        entropy = url_entropy(url)
        data["entropy"] = entropy
        self.progress.emit(f"📈 URL entropy: {entropy}")

        # Risk score
        score = len(flags) * 20 + int(entropy)
        data["risk_score"] = min(score, 100)
        self.progress.emit(f"⚠️ Risk score: {data['risk_score']} / 100")
        self.finished.emit(data)

        # Save to DB
        db.save_link_scan(data)


# ----------------------------
# WIDGET
# ----------------------------
class LinkScannerWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("🔗 Advanced Link Scanner")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Paste URL here…")
        layout.addWidget(self.input)

        self.btn = QPushButton("Scan Link")
        layout.addWidget(self.btn)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.export_btn = QPushButton("💾 Export Result")
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)

        self.worker = None
        self.scan_data = None

        self.btn.clicked.connect(self.start_scan)
        self.export_btn.clicked.connect(self.export_result)

    def start_scan(self):
        url = self.input.text().strip()
        if not url:
            self.output.append("❗ Enter a URL!")
            return

        self.output.clear()
        self.worker = LinkScanWorker(url)
        self.worker.progress.connect(self.output.append)
        self.worker.finished.connect(self.display_result)
        self.worker.start()

    def display_result(self, data):
        self.scan_data = data
        self.output.append("\n=== Detailed Report ===")
        for k,v in data.items():
            if k != "flags":
                self.output.append(f"{k}: {v}")
        if data["flags"]:
            self.output.append("\n⚠️ Flags / warnings:")
            for f in data["flags"]:
                self.output.append(f" - {f}")

        self.export_btn.setEnabled(True)

    def export_result(self):
        if not self.scan_data:
            return
        filename = "link_scan_result.json"
        with open(filename,"w") as f:
            json.dump(self.scan_data, f, indent=4)
        self.output.append(f"\n💾 Results saved to {filename}")
