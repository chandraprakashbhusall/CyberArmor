import subprocess, re, math, socket, json, psutil
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QLineEdit, QFormLayout, QGroupBox, QHBoxLayout, QProgressBar
)
import db  # Your existing DB module for saving WiFi info

# ---------------- UTILS ----------------
def signal_bars(percent):
    if percent >= 80: return "📶📶📶📶"
    if percent >= 60: return "📶📶📶"
    if percent >= 40: return "📶📶"
    if percent >= 20: return "📶"
    return "•"

def wifi_security_rating(security):
    sec = security.lower()
    if "wpa3" in sec: return "🟢 Excellent (WPA3)"
    if "wpa2" in sec: return "🟡 Good (WPA2)"
    if "wep" in sec: return "🔴 Very Weak (WEP)"
    return "⚠️ Unknown Security"

def estimate_strength(password):
    length = len(password)
    charset = 0
    if re.search(r"[a-z]", password): charset += 26
    if re.search(r"[A-Z]", password): charset += 26
    if re.search(r"[0-9]", password): charset += 10
    if re.search(r"[^A-Za-z0-9]", password): charset += 32
    entropy = length * math.log2(charset) if charset else 0
    if entropy < 40: level = "🚨 Very Weak"
    elif entropy < 60: level = "⚠️ Weak"
    elif entropy < 80: level = "🙂 Medium"
    elif entropy < 100: level = "🔥 Strong"
    else: level = "🛡️ Ultra Secure"
    return level, round(entropy,2)

# ---------------- WIFI WORKER ----------------
class WifiDetailWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    def run(self):
        try:
            self.progress.emit("Scanning WiFi…")
            wifi_raw = subprocess.check_output(
                ["nmcli", "-t", "-f", "ACTIVE,SSID,SECURITY,SIGNAL", "dev", "wifi"]
            ).decode().splitlines()
            active = [x for x in wifi_raw if x.startswith("yes")]
            if not active:
                self.finished.emit({})
                return
            parts = active[0].split(":")
            ssid = parts[1]
            security = parts[2] if len(parts) > 2 else "Unknown"
            signal = int(parts[3]) if len(parts) > 3 else 0
            try:
                password = subprocess.check_output(
                    ["nmcli", "-s", "-g", "802-11-wireless-security.psk", "connection", "show", ssid]
                ).decode().strip()
            except:
                password = ""
            self.finished.emit({
                "ssid": ssid,
                "security": security,
                "signal": signal,
                "password": password
            })
        except:
            self.finished.emit({})

# ---------------- NETWORK INFO WORKER ----------------
class NetworkInfoWorker(QThread):
    finished = pyqtSignal(dict)
    def run(self):
        try:
            hostname = socket.gethostname()
            ip_addr = socket.gethostbyname(hostname)
            net_io = psutil.net_io_counters()
            upload_kb = round(net_io.bytes_sent / 1024,2)
            download_kb = round(net_io.bytes_recv / 1024,2)
            macs = {}
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family.name == "AF_LINK":
                        macs[iface] = addr.address
            self.finished.emit({
                "hostname": hostname,
                "ip": ip_addr,
                "upload_kb": upload_kb,
                "download_kb": download_kb,
                "macs": macs
            })
        except:
            self.finished.emit({})

# ---------------- SPEED WORKER ----------------
class SpeedWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    def run(self):
        try:
            self.progress.emit("Running speed test…")
            raw = subprocess.check_output(
                ["speedtest", "--accept-license", "--accept-gdpr", "-f", "json"]
            ).decode()
            data = json.loads(raw)
            self.finished.emit({
                "download": round(data["download"]["bandwidth"] * 8 / 1e6, 2),
                "upload": round(data["upload"]["bandwidth"] * 8 / 1e6, 2),
                "ping": round(data["ping"]["latency"], 2),
                "jitter": round(data["ping"]["jitter"], 2),
                "isp": data["isp"],
                "server": f"{data['server']['name']} ({data['server']['country']})"
            })
        except Exception as e:
            self.progress.emit(f"❌ Speed test failed: {str(e)}")
            self.finished.emit({})

# ---------------- MAIN UI ----------------
class WifiAdvancedWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.theme())
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("🛡 CyberArmor – Advanced WiFi & Network Analyzer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:22px;font-weight:bold;")
        layout.addWidget(title)

        # --- WiFi Section ---
        wifi_box = QGroupBox("📶 Current WiFi")
        wifi_layout = QFormLayout()
        self.ssid_label = QLabel("—")
        self.security_label = QLabel("—")
        self.rating_label = QLabel("—")
        self.signal_label = QLabel("—")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        eye_btn = QPushButton("👁️")
        eye_btn.setFixedWidth(40)
        eye_btn.clicked.connect(self.toggle_password)
        pwd_box = QHBoxLayout()
        pwd_box.addWidget(self.password_input)
        pwd_box.addWidget(eye_btn)
        self.strength_label = QLabel("—")
        wifi_layout.addRow("SSID:", self.ssid_label)
        wifi_layout.addRow("Security:", self.security_label)
        wifi_layout.addRow("Rating:", self.rating_label)
        wifi_layout.addRow("Signal:", self.signal_label)
        wifi_layout.addRow("Password:", pwd_box)
        wifi_layout.addRow("Strength:", self.strength_label)
        wifi_box.setLayout(wifi_layout)
        layout.addWidget(wifi_box)

        # --- Speed Test ---
        sp_box = QGroupBox("🚀 Internet Speed Test")
        sp_layout = QVBoxLayout()
        self.speed_btn = QPushButton("Run Speed Test")
        self.speed_out = QTextEdit()
        self.speed_out.setReadOnly(True)
        self.speed_bar = QProgressBar()
        self.speed_bar.setRange(0,0)
        self.speed_bar.hide()
        sp_layout.addWidget(self.speed_btn)
        sp_layout.addWidget(self.speed_bar)
        sp_layout.addWidget(self.speed_out)
        sp_box.setLayout(sp_layout)
        layout.addWidget(sp_box)

        # --- Network Info ---
        net_box = QGroupBox("🌐 Network Info")
        net_layout = QFormLayout()
        self.hostname_label = QLabel("—")
        self.ip_label = QLabel("—")
        self.upload_label = QLabel("—")
        self.download_label = QLabel("—")
        self.mac_label = QLabel("—")
        net_layout.addRow("Hostname:", self.hostname_label)
        net_layout.addRow("IP Address:", self.ip_label)
        net_layout.addRow("Upload KB:", self.upload_label)
        net_layout.addRow("Download KB:", self.download_label)
        net_layout.addRow("MAC Addresses:", self.mac_label)
        net_box.setLayout(net_layout)
        layout.addWidget(net_box)

        # --- Save Report ---
        self.save_btn = QPushButton("💾 Export Full Report")
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)

        # --- Workers ---
        self.wifi_worker = WifiDetailWorker()
        self.speed_worker = None
        self.network_worker = NetworkInfoWorker()
        self.wifi_data = None
        self.speed_results = None
        self.net_results = None

        # --- Signals ---
        self.wifi_worker.finished.connect(self.display_wifi)
        self.wifi_worker.start()

        self.network_worker.finished.connect(self.display_network_info)
        self.network_worker.start()

        self.speed_btn.clicked.connect(self.start_speedtest)
        self.save_btn.clicked.connect(self.save_report)

    # -------- Display Functions --------
    def display_wifi(self, data):
        if not data:
            self.ssid_label.setText("Not Connected")
            return
        self.wifi_data = data
        self.ssid_label.setText(data["ssid"])
        self.security_label.setText(data["security"])
        self.rating_label.setText(wifi_security_rating(data["security"]))
        self.signal_label.setText(f"{data['signal']}% {signal_bars(data['signal'])}")
        self.password_input.setText(data["password"])
        lvl, ent = estimate_strength(data["password"])
        self.strength_label.setText(f"{lvl} (Entropy {ent})")
        db.save_wifi(data["ssid"], data["signal"], data["security"], data["password"], lvl, ent)

    def display_network_info(self, data):
        if not data: return
        self.net_results = data
        self.hostname_label.setText(data["hostname"])
        self.ip_label.setText(data["ip"])
        self.upload_label.setText(str(data["upload_kb"]))
        self.download_label.setText(str(data["download_kb"]))
        macs = "\n".join([f"{k}: {v}" for k,v in data.get("macs", {}).items()])
        self.mac_label.setText(macs)

    # -------- Speed Test --------
    def start_speedtest(self):
        self.speed_out.clear()
        self.speed_bar.show()
        self.save_btn.setEnabled(False)
        self.speed_worker = SpeedWorker()
        self.speed_worker.progress.connect(self.speed_out.append)
        self.speed_worker.finished.connect(self.speed_done)
        self.speed_worker.start()

    def speed_done(self,res):
        self.speed_bar.hide()
        if not res:
            self.speed_out.append("❌ Speed test failed.")
            return
        self.speed_results = res
        quality = "🟢 Excellent" if res["download"] > 50 else "🟡 Average" if res["download"] > 20 else "🔴 Poor"
        self.speed_out.append(f"""
📡 ISP: {res['isp']}
🌍 Server: {res['server']}

⬇ Download: {res['download']} Mbps
⬆ Upload: {res['upload']} Mbps
📶 Ping: {res['ping']} ms
📊 Jitter: {res['jitter']} ms

📈 Network Quality: {quality}
""")
        self.save_btn.setEnabled(True)

    # -------- Password Toggle --------
    def toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    # -------- Save Report --------
    def save_report(self):
        filename = "wifi_network_report.txt"
        with open(filename,"w") as f:
            if self.wifi_data:
                lvl, ent = estimate_strength(self.wifi_data["password"])
                f.write(f"SSID: {self.wifi_data['ssid']}\nSecurity: {self.wifi_data['security']}\nSignal: {self.wifi_data['signal']}%\nPassword: {self.wifi_data['password']}\nStrength: {lvl} (Entropy {ent})\n\n")
            if self.speed_results:
                f.write(f"ISP: {self.speed_results['isp']}\nServer: {self.speed_results['server']}\nDownload: {self.speed_results['download']} Mbps\nUpload: {self.speed_results['upload']} Mbps\nPing: {self.speed_results['ping']} ms\nJitter: {self.speed_results['jitter']} ms\n\n")
            if self.net_results:
                f.write(f"Hostname: {self.net_results['hostname']}\nIP: {self.net_results['ip']}\nUpload KB: {self.net_results['upload_kb']}\nDownload KB: {self.net_results['download_kb']}\nMACs:\n")
                for k,v in self.net_results.get("macs",{}).items():
                    f.write(f"  {k}: {v}\n")
        self.speed_out.append(f"\nSaved as {filename}")
        self.save_btn.setEnabled(True)

    # -------- Theme --------
    def theme(self):
        return """
        QWidget {
            background:#0b0f14;
            color:#e0e0e0;
            font-family: Consolas;
            font-size:14px;
        }
        QGroupBox {
            border:1px solid #2f3542;
            border-radius:10px;
            margin-top:15px;
            padding:10px;
        }
        QGroupBox:title {
            subcontrol-origin: margin;
            left:10px;
            padding:0 5px;
        }
        QPushButton {
            background:#1e90ff;
            border:none;
            padding:10px;
            border-radius:6px;
            font-weight:bold;
        }
        QPushButton:hover {
            background:#3aa0ff;
        }
        QTextEdit {
            background:#0f1722;
            border-radius:6px;
        }
        QLineEdit {
            background:#1c1c1c;
            border:1px solid #333;
            border-radius:5px;
            padding:5px;
            color:#fff;
        }
        QLabel {
            font-weight:bold;
        }
        QProgressBar {
            border:1px solid #555;
            border-radius:5px;
            text-align:center;
            background:#1c1c1c;
            color:#fff;
        }
        QProgressBar::chunk {
            background:#1e90ff;
            border-radius:5px;
        }
        """
