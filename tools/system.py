"""
CyberArmor – System Security Scanner
Real scan with export to JSON/TXT.
"""
import json, platform, socket, subprocess
from datetime import datetime

import psutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QProgressBar, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

class SystemScanThread(QThread):
    result_signal = pyqtSignal(dict)
    def run(self):
        result={}; risk=0
        result["os"]=f"{platform.system()} {platform.release()} ({platform.machine()})"
        result["hostname"]=socket.gethostname()
        cpu=psutil.cpu_percent(interval=1); result["cpu"]=cpu
        if cpu>85: risk+=1
        ram=psutil.virtual_memory(); result["ram"]=ram.percent; result["ram_total"]=ram.total
        if ram.percent>85: risk+=1
        try:
            disk=psutil.disk_usage("/"); result["disk"]=disk.percent; result["disk_free"]=disk.free
            if disk.percent>90: risk+=2
        except: result["disk"]=None; result["disk_free"]=None
        try:
            socket.create_connection(("8.8.8.8",53),timeout=3); result["internet"]=True
        except: result["internet"]=False; risk+=1
        fw=None
        if platform.system()=="Linux":
            try:
                s=subprocess.getoutput("ufw status"); fw="inactive" not in s.lower()
                if not fw: risk+=2
            except: pass
        result["firewall"]=fw
        result["cpu_count"]=psutil.cpu_count()
        result["python"]=platform.python_version()
        # Open ports check
        open_ports=[]
        for p in [21,22,23,25,80,443,3306,3389,5900]:
            try:
                s=socket.socket(); s.settimeout(0.3)
                if s.connect_ex(("127.0.0.1",p))==0: open_ports.append(p)
                s.close()
            except: pass
        result["open_ports"]=open_ports
        if any(p in open_ports for p in [21,23,3389,5900]): risk+=2
        result["overall"]="SAFE" if risk==0 else ("WARNING" if risk<=3 else "CRITICAL")
        result["risk_score"]=min(risk*15,100)
        result["time"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.result_signal.emit(result)

def _fmt(n):
    if n is None: return "Unknown"
    if n<1024**2: return f"{n/1024:.0f} KB"
    if n<1024**3: return f"{n/1024**2:.1f} MB"
    return f"{n/1024**3:.2f} GB"

class SystemSecurityWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._last_result=None
        main=QVBoxLayout(self)
        main.setContentsMargins(28,22,28,22); main.setSpacing(18)
        title=QLabel("💻  System Health & Security Check")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px;font-weight:bold;background:transparent;")
        main.addWidget(title)
        # Status card
        sc=QFrame()
        sc.setStyleSheet("QFrame{background:#111827;border-radius:14px;border:1px solid #1e293b;}")
        sl=QVBoxLayout(sc); sl.setContentsMargins(24,18,24,18); sl.setSpacing(12)
        self.status_lbl=QLabel("Click 'Run Scan' to check your system.")
        self.status_lbl.setFont(QFont("Segoe UI",14,QFont.Bold)); self.status_lbl.setStyleSheet("background:transparent;")
        sl.addWidget(self.status_lbl)
        self.progress=QProgressBar(); self.progress.setMaximum(100); self.progress.setFixedHeight(10); self.progress.setTextVisible(False)
        sl.addWidget(self.progress); main.addWidget(sc)
        # Details card
        dc=QFrame()
        dc.setStyleSheet("QFrame{background:#111827;border-radius:14px;border:1px solid #1e293b;}")
        dl=QVBoxLayout(dc); dl.setContentsMargins(20,16,20,16)
        self.details=QTextEdit(); self.details.setReadOnly(True)
        self.details.setStyleSheet("QTextEdit{background:#060c18;border:1px solid #1e293b;border-radius:10px;padding:12px;font-family:'Courier New';font-size:12px;color:#7dd3fc;}")
        dl.addWidget(self.details); main.addWidget(dc)
        # Buttons
        br=QHBoxLayout()
        self.scan_btn=QPushButton("▶  Run System Scan"); self.scan_btn.setFixedHeight(46)
        self.scan_btn.clicked.connect(self._scan)
        self.scan_btn.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4,stop:1 #0097a7);border:none;border-radius:10px;color:black;font-weight:bold;font-size:14px;}QPushButton:hover{background:#26C6DA;}")
        br.addWidget(self.scan_btn)
        self.export_btn=QPushButton("💾  Export Report"); self.export_btn.setFixedHeight(46); self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export)
        self.export_btn.setStyleSheet("QPushButton{background:#1e293b;border:1px solid #334155;border-radius:10px;color:#94a3b8;font-weight:bold;}QPushButton:hover{background:#334155;color:#e2e8f0;}QPushButton:disabled{color:#4b5563;}")
        br.addWidget(self.export_btn); main.addLayout(br)

    def _scan(self):
        self.status_lbl.setText("⏳  Scanning system — please wait...")
        self.status_lbl.setStyleSheet("background:transparent;color:#64748b;")
        self.progress.setValue(30); self.details.clear()
        self.scan_btn.setEnabled(False); self.scan_btn.setText("Scanning...")
        self._thread=SystemScanThread()
        self._thread.result_signal.connect(self._show_result)
        self._thread.start()

    def _show_result(self, d):
        self._last_result=d
        self.scan_btn.setEnabled(True); self.scan_btn.setText("▶  Run System Scan")
        self.progress.setValue(d["risk_score"])
        ov=d["overall"]
        if ov=="SAFE":
            self.status_lbl.setText("🟢  System is SAFE and healthy")
            self.status_lbl.setStyleSheet("background:transparent;color:#10b981;font-size:14px;font-weight:bold;")
        elif ov=="WARNING":
            self.status_lbl.setText("🟡  Minor issues detected — review below")
            self.status_lbl.setStyleSheet("background:transparent;color:#f59e0b;font-size:14px;font-weight:bold;")
        else:
            self.status_lbl.setText("🔴  CRITICAL — Security risks found!")
            self.status_lbl.setStyleSheet("background:transparent;color:#ef4444;font-size:14px;font-weight:bold;")
        ports_str=", ".join(str(p) for p in d["open_ports"]) if d["open_ports"] else "None detected"
        fw_str=("✅ Active" if d["firewall"] else "❌ INACTIVE — exposing your system") if d["firewall"] is not None else "Not checked (non-Linux)"
        report=f"""
📅  Scan Time   : {d['time']}
🖥  Hostname    : {d['hostname']}
💻  OS          : {d['os']}
🐍  Python      : {d['python']}

⚙  CPU Usage   : {d['cpu']}%{'  ⚠ HIGH' if d['cpu']>85 else '  ✅ OK'}
🧠  RAM Usage   : {d['ram']}%  (Total: {_fmt(d['ram_total'])}){'  ⚠ HIGH' if d['ram']>85 else '  ✅ OK'}
💾  Disk Usage  : {d['disk']}%  (Free: {_fmt(d['disk_free'])}){'  ⚠ ALMOST FULL' if d['disk'] and d['disk']>90 else '  ✅ OK'}
🌐  Internet    : {'✅ Connected' if d['internet'] else '❌ No connection'}
🔥  Firewall    : {fw_str}
🔓  Open Ports  : {ports_str}

{'─'*50}
🛡  Recommendations:
   • Keep your OS and software updated
   • Use a firewall and keep it enabled
   • Avoid installing software from unknown sources
   • Close unnecessary open ports
   • Use strong passwords with 2FA
"""
        self.details.setText(report)
        self.export_btn.setEnabled(True)

    def _export(self):
        if not self._last_result: return
        path,_=QFileDialog.getSaveFileName(self,"Export System Report",
            f"system_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}","JSON (*.json);;Text (*.txt)")
        if not path: return
        if path.endswith(".txt"):
            with open(path,"w") as f: f.write(self.details.toPlainText())
        else:
            with open(path,"w") as f: json.dump(self._last_result,f,indent=4,default=str)
        QMessageBox.information(self,"Saved",f"✅ Report saved:\n{path}")
