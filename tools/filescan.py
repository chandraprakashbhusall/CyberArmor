"""
CyberArmor – File & Folder Scanner
Detects malicious patterns. Export results to JSON or TXT.
"""
import os, re, json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QFrame, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

SUSPICIOUS_PATTERNS = [
    (r"base64_decode\(|base64\.b64decode", "Hidden encoded content (base64)", 70),
    (r"\beval\s*\(", "Dynamic code execution (eval)", 70),
    (r"\bexec\s*\(", "Runtime command execution (exec)", 70),
    (r"os\.system\s*\(|subprocess\.Popen", "System command execution", 40),
    (r"chmod\s+777", "Permissive file permission (777)", 20),
    (r"wget\s+http|curl\s+http", "Downloads from internet", 40),
    (r"<script\b", "Embedded script tag", 70),
    (r"import\s+pty|\.spawn\(", "Reverse shell behavior", 80),
    (r"\bnc\s+-e\b|netcat\b", "Netcat reverse shell signature", 80),
    (r"\\x[0-9a-fA-F]{2}{4,}", "Long hex escape sequence (obfuscation)", 30),
    (r"socket\.connect\(|socket\.bind\(", "Raw socket connection", 30),
    (r"rm\s+-rf\s+/", "Destructive file deletion command", 90),
]

class FileScanWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self._scan_log = []; self._summary = {}
        main = QVBoxLayout(self)
        main.setContentsMargins(28,22,28,22); main.setSpacing(18)
        title=QLabel("🗂  Advanced File & Folder Scanner")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px;font-weight:bold;background:transparent;")
        main.addWidget(title)
        # Button row
        ctrl=QFrame()
        ctrl.setStyleSheet("QFrame{background:#111827;border-radius:12px;border:1px solid #1e293b;}")
        cl=QHBoxLayout(ctrl); cl.setContentsMargins(16,12,16,12); cl.setSpacing(12)
        fb=QPushButton("📄  Scan File"); fb.setFixedHeight(42); fb.clicked.connect(self._select_file)
        fb.setStyleSheet("QPushButton{background:#1e293b;border:1px solid #334155;border-radius:10px;color:#94a3b8;font-weight:bold;}QPushButton:hover{background:#334155;color:#e2e8f0;}")
        cl.addWidget(fb)
        db2=QPushButton("📁  Scan Folder"); db2.setFixedHeight(42); db2.clicked.connect(self._select_folder)
        db2.setStyleSheet("QPushButton{background:#1e293b;border:1px solid #334155;border-radius:10px;color:#94a3b8;font-weight:bold;}QPushButton:hover{background:#334155;color:#e2e8f0;}")
        cl.addWidget(db2)
        self.export_btn=QPushButton("💾  Export Report"); self.export_btn.setFixedHeight(42)
        self.export_btn.setEnabled(False); self.export_btn.clicked.connect(self._export)
        self.export_btn.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4,stop:1 #0097a7);border:none;border-radius:10px;color:black;font-weight:bold;}QPushButton:hover{background:#26C6DA;}QPushButton:disabled{background:#1e293b;color:#4b5563;}")
        cl.addWidget(self.export_btn)
        main.addWidget(ctrl)
        # Output
        self.output=QTextEdit(); self.output.setReadOnly(True)
        self.output.setStyleSheet("QTextEdit{background:#060c18;border:1px solid #1e293b;border-radius:10px;padding:10px;font-family:'Courier New';font-size:12px;color:#7dd3fc;}")
        main.addWidget(self.output)
        # Score
        self.progress=QProgressBar(); self.progress.setMaximum(150); self.progress.setFixedHeight(12)
        main.addWidget(self.progress)
        self.result_lbl=QLabel("Scan Result: —")
        self.result_lbl.setAlignment(Qt.AlignCenter)
        self.result_lbl.setFont(QFont("Segoe UI",16,QFont.Bold))
        self.result_lbl.setStyleSheet("background:transparent;")
        main.addWidget(self.result_lbl)

    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self,e):
        path=e.mimeData().urls()[0].toLocalFile()
        if os.path.isfile(path): self._run_file_scan(path)
        elif os.path.isdir(path): self._run_folder_scan(path)

    def _select_file(self):
        f,_=QFileDialog.getOpenFileName(self,"Select File to Scan")
        if f: self.output.clear(); self._run_file_scan(f)
    def _select_folder(self):
        d=QFileDialog.getExistingDirectory(self,"Select Folder to Scan")
        if d: self.output.clear(); self._run_folder_scan(d)

    def _run_folder_scan(self, folder):
        self._scan_log=[]; threats=0; scanned=0
        self.output.append(f"📁 Scanning folder: {folder}\n")
        for root,_,files in os.walk(folder):
            for fname in files:
                full=os.path.join(root,fname); scanned+=1
                status=self._scan_file(full, show_ui=False)
                if status!="Safe": threats+=1
        self.output.append("\n" + "─"*50)
        self.output.append(f"📊 Folder Scan Summary")
        self.output.append(f"   Total Files  : {scanned}")
        self.output.append(f"   Threats Found: {threats}")
        self._summary={"type":"folder","path":folder,"scanned":scanned,"threats":threats,"scanned_at":str(datetime.now())}
        if threats==0:
            self.result_lbl.setText("🟢  Folder is SAFE"); self.result_lbl.setStyleSheet("color:#10b981;font-size:18px;font-weight:bold;background:transparent;")
        else:
            self.result_lbl.setText(f"🔴  {threats} Threat(s) Found"); self.result_lbl.setStyleSheet("color:#ef4444;font-size:18px;font-weight:bold;background:transparent;")
        self.export_btn.setEnabled(True)

    def _run_file_scan(self, filepath):
        self._scan_log=[]; self._summary={}
        self.output.append(f"🔍 Scanning: {filepath}\n")
        status=self._scan_file(filepath, show_ui=True)
        self._summary={"type":"file","path":filepath,"status":status,
            "findings":self._scan_log,"scanned_at":str(datetime.now())}
        self.export_btn.setEnabled(True)

    def _scan_file(self, filepath, show_ui=True):
        risk=0; detected=[]
        try:
            if MAGIC_AVAILABLE:
                mime=magic.from_file(filepath,mime=True)
                if "executable" in mime: detected.append("Executable binary"); risk+=50
                if "script" in mime: detected.append("Script file"); risk+=30
            with open(filepath,"r",errors="ignore") as f: content=f.read()
            for pattern,desc,pts in SUSPICIOUS_PATTERNS:
                if re.search(pattern,content,re.IGNORECASE):
                    detected.append(desc); risk+=pts
            if "\x00" in content: detected.append("Hidden binary/null bytes"); risk+=40
        except Exception:
            return "Safe"
        risk=min(risk,150)
        if risk>=120: status="Dangerous"; color="#ef4444"
        elif risk>=60: status="Warning"; color="#f59e0b"
        else: status="Safe"; color="#10b981"
        if show_ui:
            self.progress.setValue(risk)
            self.output.append(f"📌 {os.path.basename(filepath)}")
            if detected:
                for d in detected: self.output.append(f"   ⚠  {d}")
            else: self.output.append("   ✅  No threats detected")
            self.output.append(f"   Risk Score: {risk}/150\n")
            self.result_lbl.setText(f"Status: {status}")
            self.result_lbl.setStyleSheet(f"color:{color};font-size:18px;font-weight:bold;background:transparent;")
        if detected:
            self._scan_log.append({"file":os.path.basename(filepath),"risk":risk,"issues":detected})
        return status

    def _export(self):
        if not self._summary: return
        path,_=QFileDialog.getSaveFileName(self,"Export Scan Report",
            f"filescan_{datetime.now().strftime('%Y%m%d_%H%M%S')}","JSON (*.json);;Text (*.txt)")
        if not path: return
        if path.endswith(".txt"):
            with open(path,"w") as f:
                f.write("CyberArmor File Scan Report\n"+"="*40+"\n")
                f.write(f"Path     : {self._summary.get('path')}\n")
                f.write(f"Scanned  : {self._summary.get('scanned_at')}\n\n")
                for item in self._scan_log:
                    f.write(f"File: {item['file']}  Risk: {item['risk']}/150\n")
                    for issue in item['issues']: f.write(f"  • {issue}\n")
                    f.write("\n")
        else:
            with open(path,"w") as f:
                data=dict(self._summary); data["findings"]=self._scan_log
                json.dump(data,f,indent=4)
        QMessageBox.information(self,"Saved",f"✅ Report saved:\n{path}")
