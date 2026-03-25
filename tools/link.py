import re
import math
import json
import socket
import ssl
import datetime
from urllib.parse import urlparse

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QHBoxLayout,
    QFrame, QProgressBar
)

from PyQt5.QtCore import QThread, pyqtSignal, Qt

from tools import theme
import db


# ----------------------------
# TRUSTED DOMAINS
# ----------------------------

TRUSTED_DOMAINS = {
    "google.com": "Google",
    "youtube.com": "YouTube",
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "github.com": "GitHub",
    "openai.com": "OpenAI",
    "tiktok.com": "TikTok",
    "twitter.com": "Twitter"
}


# ----------------------------
# ENTROPY
# ----------------------------

def url_entropy(url):

    prob = [url.count(c)/len(url) for c in set(url)]

    entropy = -sum([p*math.log2(p) for p in prob])

    return round(entropy,2)


# ----------------------------
# SAFE SSL CHECK
# ----------------------------

def ssl_check(domain):

    try:

        ctx = ssl.create_default_context()

        with socket.create_connection((domain,443),timeout=4) as sock:

            with ctx.wrap_socket(sock,server_hostname=domain) as ssock:

                cert = ssock.getpeercert()

                issuer = cert.get('issuer')

                return True,f"Valid SSL"

    except Exception as e:

        return False,"No SSL / Invalid SSL"


# ----------------------------
# WORKER THREAD
# ----------------------------

class LinkScanWorker(QThread):

    finished = pyqtSignal(dict)

    progress = pyqtSignal(int,str)


    def __init__(self,url):

        super().__init__()

        self.url=url


    def run(self):

        try:

            data={}

            flags=[]


            self.progress.emit(5,"Initializing scan...")


            url=self.url.strip()


            if not re.match(r'^https?://',url):

                url="http://"+url


            parsed=urlparse(url)


            domain=parsed.netloc.lower()


            if ":" in domain:
                domain=domain.split(":")[0]


            parts=domain.split(".")


            if len(parts)>=2:
                base_domain=".".join(parts[-2:])
            else:
                base_domain=domain


            data["url"]=url
            data["domain"]=domain
            data["base_domain"]=base_domain
            data["timestamp"]=str(datetime.datetime.now())


            # ---------------- DOMAIN CHECK

            self.progress.emit(20,"Analyzing domain...")


            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$",domain):

                flags.append("Raw IP address used")


            if len(parts)>3:

                flags.append("Too many subdomains")


            if domain.startswith("xn--"):

                flags.append("Punycode domain")


            suspicious_keywords=[
                "login","secure","verify","update","bank","account"
            ]


            for kw in suspicious_keywords:

                if kw in domain:

                    flags.append(f"Suspicious keyword: {kw}")


            # Fake domain check

            for trusted in TRUSTED_DOMAINS:

                if trusted in domain and not domain.endswith(trusted):

                    flags.append(f"Fake look-alike: {trusted}")


            # ---------------- SSL CHECK

            self.progress.emit(50,"Checking SSL certificate...")


            ssl_ok,ssl_info=ssl_check(base_domain)

            data["ssl"]=ssl_ok

            data["ssl_info"]=ssl_info


            # ---------------- ENTROPY

            self.progress.emit(75,"Calculating entropy...")


            entropy=url_entropy(url)

            data["entropy"]=entropy


            # ---------------- SCORE

            score=len(flags)*20+int(entropy)

            score=min(score,100)

            data["risk_score"]=score

            data["flags"]=flags


            self.progress.emit(100,"Scan completed")


            # DB save safely

            try:
                if hasattr(db,"save_link_scan"):
                    db.save_link_scan(data)
            except:
                pass


            self.finished.emit(data)


        except Exception as e:

            data={

                "url":self.url,
                "risk_score":100,
                "flags":[str(e)],
                "domain":"Error",
                "base_domain":"Error",
                "ssl":False,
                "ssl_info":"Error",
                "entropy":0

            }

            self.finished.emit(data)



# ----------------------------
# WIDGET
# ----------------------------

class LinkScannerWidget(QWidget):

    def __init__(self):

        super().__init__()

        self.resize(900,650)

        main_layout=QVBoxLayout(self)

        main_layout.setSpacing(20)


        title=QLabel("🔗 Advanced Link Security Scanner")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("font-size:24px;font-weight:bold;")

        main_layout.addWidget(title)


        card=QFrame()

        card_layout=QVBoxLayout(card)

        card_layout.setSpacing(15)


        row=QHBoxLayout()

        self.input=QLineEdit()

        self.input.setPlaceholderText("Enter URL example.com")

        row.addWidget(self.input)


        self.btn=QPushButton("Scan")

        row.addWidget(self.btn)

        card_layout.addLayout(row)


        self.progress=QProgressBar()

        card_layout.addWidget(self.progress)


        self.result_label=QLabel("Status: -")

        self.result_label.setAlignment(Qt.AlignCenter)

        self.result_label.setStyleSheet("font-size:18px;font-weight:bold;")

        card_layout.addWidget(self.result_label)


        self.output=QTextEdit()

        self.output.setReadOnly(True)

        card_layout.addWidget(self.output)


        self.export_btn=QPushButton("💾 Export Report")

        self.export_btn.setEnabled(False)

        card_layout.addWidget(self.export_btn)


        main_layout.addWidget(card)


        self.btn.clicked.connect(self.start_scan)

        self.export_btn.clicked.connect(self.export_result)


        self.worker=None
        self.scan_data=None


    # ---------------- START

    def start_scan(self):

        url=self.input.text().strip()

        if not url:

            self.output.append("Enter URL")

            return


        self.output.clear()

        self.progress.setValue(0)

        self.result_label.setText("Scanning...")


        self.worker=LinkScanWorker(url)

        self.worker.progress.connect(self.update_progress)

        self.worker.finished.connect(self.display_result)

        self.worker.start()


    # ---------------- PROGRESS

    def update_progress(self,value,message):

        self.progress.setValue(value)

        self.output.append(message)


    # ---------------- RESULT

    def display_result(self,data):

        self.scan_data=data

        score=data["risk_score"]


        if score>=70:

            status="🔴 Dangerous"
            color="red"

        elif score>=40:

            status="🟡 Warning"
            color="orange"

        else:

            status="🟢 Safe"
            color="green"


        self.result_label.setText(
            f"{status}  ({score}/100)"
        )

        self.result_label.setStyleSheet(
            f"color:{color};font-size:20px;font-weight:bold;"
        )


        self.output.append("\n=== REPORT ===")

        self.output.append(f"Domain: {data['domain']}")

        self.output.append(f"SSL: {data['ssl_info']}")

        self.output.append(f"Entropy: {data['entropy']}")

        self.output.append(f"Score: {score}")


        if data["flags"]:

            self.output.append("\nWarnings:")

            for f in data["flags"]:

                self.output.append("• "+f)

        else:

            self.output.append("\nNo threats found")


        self.export_btn.setEnabled(True)


    # ---------------- EXPORT

    def export_result(self):

        if not self.scan_data:
            return
import re
import math
import json
import socket
import ssl
import datetime
from urllib.parse import urlparse

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QHBoxLayout,
    QFrame, QProgressBar
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt

from tools import theme
import db


# ----------------------------
# Trusted domains
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
def url_entropy(url):
    prob = [url.count(c)/len(url) for c in set(url)]
    entropy = -sum([p*math.log2(p) for p in prob])
    return round(entropy, 2)


def ssl_check(domain):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(3)
            s.connect((domain, 443))
            cert = s.getpeercert()
            issuer = cert.get('issuer')
            return True, f"Valid SSL (Issuer: {issuer})"
    except:
        return False, "Invalid / No SSL certificate"


# ----------------------------
# WORKER THREAD
# ----------------------------
class LinkScanWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int, str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        data = {"url": self.url, "timestamp": str(datetime.datetime.now())}
        flags = []

        self.progress.emit(10, "Initializing scan...")

        url = self.url
        if not re.match(r'^https?://', url):
            url = "http://" + url

        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        parts = domain.split(".")
        base_domain = ".".join(parts[-2:]) if len(parts) >= 2 else domain

        data["domain"] = domain
        data["base_domain"] = base_domain

        self.progress.emit(30, f"Checking domain: {domain}")

        # IP check
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
            flags.append("Raw IP address used")

        # Subdomain check
        if len(parts) > 3:
            flags.append("Too many subdomains")

        # Punycode
        if domain.startswith("xn--"):
            flags.append("Punycode domain detected")

        # Suspicious keywords
        suspicious_keywords = ["login","secure","verify","update","bank","account"]
        for kw in suspicious_keywords:
            if kw in domain:
                flags.append(f"Suspicious keyword: {kw}")

        # Look-alike check
        for trusted in TRUSTED_DOMAINS:
            if trusted in domain and not domain.endswith(trusted):
                flags.append(f"Fake look-alike of {trusted}")

        self.progress.emit(60, "Checking SSL certificate...")

        ssl_ok, ssl_info = ssl_check(base_domain)
        data["ssl"] = ssl_ok
        data["ssl_info"] = ssl_info

        entropy = url_entropy(url)
        data["entropy"] = entropy

        score = len(flags) * 20 + int(entropy)
        score = min(score, 100)

        data["risk_score"] = score
        data["flags"] = flags

        self.progress.emit(100, "Scan completed")

        self.finished.emit(data)
        db.save_link_scan(data)


# ----------------------------
# WIDGET
# ----------------------------
class LinkScannerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(900, 650)
        self.setStyleSheet(theme.get_stylesheet())

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)

        # ===== TITLE =====
        title = QLabel("🔗 Advanced Link Security Scanner")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:24px; font-weight:bold;")
        main_layout.addWidget(title)

        # ===== CARD =====
        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        # URL input row
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter URL (example.com)")
        row.addWidget(self.input)

        self.btn = QPushButton("Scan")
        row.addWidget(self.btn)

        card_layout.addLayout(row)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        card_layout.addWidget(self.progress)

        # Result badge
        self.result_label = QLabel("Status: -")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size:18px; font-weight:bold;")
        card_layout.addWidget(self.result_label)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        card_layout.addWidget(self.output)

        # Export button
        self.export_btn = QPushButton("💾 Export Report")
        self.export_btn.setEnabled(False)
        card_layout.addWidget(self.export_btn)

        main_layout.addWidget(card)

        self.worker = None
        self.scan_data = None

        self.btn.clicked.connect(self.start_scan)
        self.export_btn.clicked.connect(self.export_result)

    # ----------------------------
    def start_scan(self):
        url = self.input.text().strip()
        if not url:
            self.output.append("⚠️ Please enter a URL.")
            return

        self.output.clear()
        self.progress.setValue(0)
        self.result_label.setText("Scanning...")
        self.result_label.setStyleSheet("font-weight:bold;")

        self.worker = LinkScanWorker(url)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.display_result)
        self.worker.start()

    def update_progress(self, value, message):
        self.progress.setValue(value)
        self.output.append(message)

    def display_result(self, data):
        self.scan_data = data

        score = data["risk_score"]

        if score >= 70:
            status = "🔴 Dangerous"
            color = "red"
        elif score >= 40:
            status = "🟡 Warning"
            color = "orange"
        else:
            status = "🟢 Safe"
            color = "green"

        self.result_label.setText(f"Status: {status} ({score}/100)")
        self.result_label.setStyleSheet(
            f"color:{color}; font-size:20px; font-weight:bold;"
        )

        self.output.append("\n=== Detailed Report ===")
        self.output.append(f"Domain: {data['domain']}")
        self.output.append(f"Base Domain: {data['base_domain']}")
        self.output.append(f"SSL: {data['ssl_info']}")
        self.output.append(f"Entropy: {data['entropy']}")
        self.output.append(f"Risk Score: {score}/100")

        if data["flags"]:
            self.output.append("\n⚠️ Security Warnings:")
            for f in data["flags"]:
                self.output.append(f" • {f}")
        else:
            self.output.append("\nNo suspicious indicators found.")

        self.export_btn.setEnabled(True)

    def export_result(self):
        if not self.scan_data:
            return

        filename = "link_scan_result.json"
        with open(filename, "w") as f:
            json.dump(self.scan_data, f, indent=4)

        self.output.append(f"\n💾 Report saved to {filename}")

        with open("link_report.json","w") as f:

            json.dump(self.scan_data,f,indent=4)


        self.output.append("\nSaved link_report.json")