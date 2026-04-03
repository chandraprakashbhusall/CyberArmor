"""
CyberArmor – Email Spam Checker
"""
import os, re, json, email
from email import policy
from datetime import datetime
from urllib.parse import urlparse

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

SPAM_KEYWORDS = [
    "urgent","limited time","winner","prize","free","click here",
    "buy now","act now","lottery","bank account","credit card",
    "congratulations","verify your account","suspend","confirm your identity"
]
SUSPICIOUS_DOMAINS = ["xyz.com","abc123.net","mailinator.com","tempmail.com","guerrillamail.com"]
SUSPICIOUS_EXTENSIONS = [".exe",".scr",".zip",".js",".bat",".vbs",".ps1"]

class EmailSpamAnalyzer:
    def __init__(self, filepath):
        self.filepath=filepath; self.subject=""; self.sender=""
        self.body=""; self.links=[]; self.score=0; self.reasoning=[]
    def parse_email(self):
        with open(self.filepath,"r",encoding="utf-8",errors="ignore") as f:
            msg=email.message_from_file(f,policy=policy.default)
        self.sender=msg.get("From",""); self.subject=msg.get("Subject","")
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type()=="text/plain":
                    try: self.body+=part.get_content()+"\n"
                    except: pass
        else:
            try: self.body=msg.get_content()
            except: self.body=""
        self.links=re.findall(r"https?://[^\s\"<>]+",self.body)
    def analyze(self):
        self.score=0; self.reasoning=[]
        sender_domain=self.sender.split("@")[-1].lower() if "@" in self.sender else ""
        if any(d in sender_domain for d in SUSPICIOUS_DOMAINS):
            self.score+=25; self.reasoning.append(("Suspicious sender domain",25))
        for word in SPAM_KEYWORDS:
            if word.lower() in self.subject.lower():
                self.score+=6; self.reasoning.append((f"Keyword in subject: '{word}'",6))
        for word in SPAM_KEYWORDS:
            count=len(re.findall(re.escape(word),self.body,re.IGNORECASE))
            if count>0:
                pts=min(count*3,15); self.score+=pts
                self.reasoning.append((f"Keyword '{word}' in body ({count}x)",pts))
        for link in self.links:
            domain=urlparse(link).netloc.lower()
            if any(d in domain for d in SUSPICIOUS_DOMAINS):
                self.score+=12; self.reasoning.append((f"Suspicious link: {domain}",12))
            for ext in SUSPICIOUS_EXTENSIONS:
                if link.lower().endswith(ext):
                    self.score+=15; self.reasoning.append((f"Dangerous file link",15))
        self.score=min(self.score,100)
        return self.score, self.reasoning

class EmailSpamCheckerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.email_path=None; self._last_result=None
        main=QVBoxLayout(self)
        main.setContentsMargins(28,22,28,22); main.setSpacing(18)
        title=QLabel("📧  Email Spam Analyzer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px;font-weight:bold;background:transparent;")
        main.addWidget(title)
        # File card
        card=QFrame()
        card.setStyleSheet("QFrame{background:#111827;border-radius:12px;border:1px solid #1e293b;}")
        cl=QVBoxLayout(card); cl.setContentsMargins(20,16,20,16); cl.setSpacing(12)
        self.file_lbl=QLabel("No file selected")
        self.file_lbl.setAlignment(Qt.AlignCenter)
        self.file_lbl.setStyleSheet("color:#00BCD4;font-size:13px;font-weight:bold;background:transparent;")
        cl.addWidget(self.file_lbl)
        br=QHBoxLayout()
        sb=QPushButton("📂  Select File"); sb.setFixedHeight(42); sb.clicked.connect(self._select)
        sb.setStyleSheet("QPushButton{background:#1e293b;border:1px solid #334155;border-radius:10px;color:#94a3b8;font-weight:bold;}QPushButton:hover{background:#334155;color:#e2e8f0;}")
        br.addWidget(sb)
        self.analyze_btn=QPushButton("🔍  Analyze"); self.analyze_btn.setFixedHeight(42); self.analyze_btn.clicked.connect(self._analyze)
        self.analyze_btn.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4,stop:1 #0097a7);border:none;border-radius:10px;color:black;font-weight:bold;}QPushButton:hover{background:#26C6DA;}")
        br.addWidget(self.analyze_btn)
        self.export_btn=QPushButton("💾  Export"); self.export_btn.setFixedHeight(42); self.export_btn.setEnabled(False); self.export_btn.clicked.connect(self._export)
        self.export_btn.setStyleSheet("QPushButton{background:#1e293b;border:1px solid #334155;border-radius:10px;color:#94a3b8;font-weight:bold;}QPushButton:hover{background:#334155;}QPushButton:disabled{color:#4b5563;}")
        br.addWidget(self.export_btn)
        cl.addLayout(br); main.addWidget(card)
        self.info_text=QTextEdit(); self.info_text.setReadOnly(True); self.info_text.setFixedHeight(100)
        self.info_text.setStyleSheet("QTextEdit{background:#060c18;border:1px solid #1e293b;border-radius:10px;padding:10px;font-family:'Courier New';font-size:12px;color:#7dd3fc;}")
        main.addWidget(self.info_text)
        self.table=QTableWidget(0,2); self.table.setHorizontalHeaderLabels(["Reason","Points"])
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Fixed)
        self.table.setColumnWidth(1,80); self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True); self.table.verticalHeader().setVisible(False)
        self.table.setFixedHeight(150); main.addWidget(self.table)
        sc=QFrame(); sc.setStyleSheet("QFrame{background:#111827;border-radius:12px;border:1px solid #1e293b;}")
        sl=QVBoxLayout(sc); sl.setContentsMargins(20,14,20,14); sl.setSpacing(8)
        self.progress=QProgressBar(); self.progress.setMaximum(100); self.progress.setFixedHeight(12)
        sl.addWidget(self.progress)
        self.score_lbl=QLabel("Spam Score: —"); self.score_lbl.setAlignment(Qt.AlignCenter)
        self.score_lbl.setFont(QFont("Segoe UI",16,QFont.Bold)); self.score_lbl.setStyleSheet("background:transparent;")
        sl.addWidget(self.score_lbl)
        self.verdict_lbl=QLabel(""); self.verdict_lbl.setAlignment(Qt.AlignCenter)
        self.verdict_lbl.setStyleSheet("color:#64748b;font-size:13px;background:transparent;")
        sl.addWidget(self.verdict_lbl); main.addWidget(sc)

    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self,e):
        path=e.mimeData().urls()[0].toLocalFile()
        if path.endswith((".eml",".txt")):
            self.email_path=path; self.file_lbl.setText(f"✅  {os.path.basename(path)}")
    def _select(self):
        path,_=QFileDialog.getOpenFileName(self,"Select Email","","Email Files (*.eml *.txt)")
        if path: self.email_path=path; self.file_lbl.setText(f"✅  {os.path.basename(path)}")
    def _analyze(self):
        if not self.email_path:
            QMessageBox.warning(self,"No File","Please select an email file first."); return
        try:
            a=EmailSpamAnalyzer(self.email_path); a.parse_email(); score,reasons=a.analyze()
        except Exception as e:
            QMessageBox.critical(self,"Error",f"Failed to read email:\n{e}"); return
        self._last_result={"file":os.path.basename(self.email_path),"sender":a.sender,
            "subject":a.subject,"score":score,"reasons":reasons,"analyzed_at":str(datetime.now())}
        self.info_text.setPlainText(f"From    : {a.sender}\nSubject : {a.subject}\nLinks   : {len(a.links)} found\n\nBody preview:\n{a.body[:350].strip()}")
        self.table.setRowCount(0)
        for i,(reason,pts) in enumerate(reasons):
            self.table.insertRow(i); self.table.setItem(i,0,QTableWidgetItem(reason))
            pi=QTableWidgetItem(f"+{pts}"); pi.setTextAlignment(Qt.AlignCenter); self.table.setItem(i,1,pi)
        self.progress.setValue(score)
        if score>=70: color="#ef4444"; verdict="🔴  HIGH RISK — Likely Spam"; bar="QProgressBar{background:#1e293b;border:none;border-radius:6px;}QProgressBar::chunk{background:#ef4444;border-radius:6px;}"
        elif score>=40: color="#f59e0b"; verdict="🟡  MEDIUM RISK — Suspicious"; bar="QProgressBar{background:#1e293b;border:none;border-radius:6px;}QProgressBar::chunk{background:#f59e0b;border-radius:6px;}"
        else: color="#10b981"; verdict="🟢  LOW RISK — Looks Clean"; bar="QProgressBar{background:#1e293b;border:none;border-radius:6px;}QProgressBar::chunk{background:#10b981;border-radius:6px;}"
        self.progress.setStyleSheet(bar)
        self.score_lbl.setText(f"Spam Score: {score} / 100"); self.score_lbl.setStyleSheet(f"color:{color};font-size:18px;font-weight:bold;background:transparent;")
        self.verdict_lbl.setText(verdict); self.export_btn.setEnabled(True)
    def _export(self):
        if not self._last_result: return
        path,_=QFileDialog.getSaveFileName(self,"Export Report",f"spam_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}","JSON (*.json);;Text (*.txt)")
        if not path: return
        if path.endswith(".txt"):
            with open(path,"w") as f:
                f.write(f"CyberArmor Email Spam Report\n{'='*40}\n")
                f.write(f"File: {self._last_result['file']}\nFrom: {self._last_result['sender']}\n")
                f.write(f"Subject: {self._last_result['subject']}\nScore: {self._last_result['score']}/100\n\nReasons:\n")
                for r,p in self._last_result['reasons']: f.write(f"  +{p}  {r}\n")
        else:
            with open(path,"w") as f: json.dump(self._last_result,f,indent=4)
        QMessageBox.information(self,"Saved",f"✅ Report saved:\n{path}")
