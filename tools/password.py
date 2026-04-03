"""
CyberArmor – Password Manager
Generate, analyze strength, save hashed passwords. Export vault.
"""
import os, json, math, random, string, hashlib
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QFormLayout, QProgressBar,
    QFrame, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

DATA_FILE = "password_vault.json"
SYMBOLS   = "!@#$%^&*()_+-=[]{}|;:,.<>?"

def generate_password(length=16):
    chars=string.ascii_letters+string.digits+SYMBOLS
    pwd=[random.choice(string.ascii_uppercase),
         random.choice(string.ascii_lowercase),
         random.choice(string.digits),
         random.choice(SYMBOLS)]
    pwd+=[random.choice(chars) for _ in range(length-4)]
    random.shuffle(pwd)
    return "".join(pwd)

def check_strength(pw):
    score=0
    if len(pw)>=8: score+=1
    if len(pw)>=12: score+=1
    if any(c.islower() for c in pw): score+=1
    if any(c.isupper() for c in pw): score+=1
    if any(c.isdigit() for c in pw): score+=1
    if any(c in SYMBOLS for c in pw): score+=1
    score=min(score,5)
    if score<=2: return "Weak",score,"#ef4444"
    elif score==3: return "Fair",score,"#f59e0b"
    elif score==4: return "Strong",score,"#10b981"
    else: return "Very Strong",score,"#00BCD4"

def calc_entropy(pw):
    cs=0
    if any(c.islower() for c in pw): cs+=26
    if any(c.isupper() for c in pw): cs+=26
    if any(c.isdigit() for c in pw): cs+=10
    if any(c in SYMBOLS for c in pw): cs+=len(SYMBOLS)
    return round(len(pw)*math.log2(cs),1) if cs else 0

def crack_time(entropy):
    s=(2**entropy)/1e9
    if s<60: return "Instant"
    if s<3600: return "Minutes"
    if s<86400: return "Hours"
    if s<2592000: return "Days"
    if s<31536000: return "Months"
    return "Years+"

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def load_vault():
    try:
        with open(DATA_FILE,"r") as f: return json.load(f)
    except: return []

def save_vault(data):
    with open(DATA_FILE,"w") as f: json.dump(data,f,indent=4)

def _group(title):
    g=QGroupBox(title); g.setLayout(QVBoxLayout()); return g

class PasswordManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        main=QVBoxLayout(self)
        main.setContentsMargins(28,22,28,22); main.setSpacing(18)
        title=QLabel("🔐  Secure Password Manager")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px;font-weight:bold;background:transparent;")
        main.addWidget(title)
        # Generate
        gen=_group("⚡  Generate Password")
        gr=QHBoxLayout()
        self.len_in=QLineEdit(); self.len_in.setPlaceholderText("Length (default 16)"); self.len_in.setFixedHeight(40)
        self.gen_out=QLineEdit(); self.gen_out.setReadOnly(True); self.gen_out.setFixedHeight(40)
        gr.addWidget(self.len_in); gr.addWidget(self.gen_out)
        gen.layout().addLayout(gr)
        gb=QPushButton("Generate"); gb.setFixedHeight(40); gb.clicked.connect(self._generate)
        gb.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4,stop:1 #0097a7);border:none;border-radius:10px;color:black;font-weight:bold;}QPushButton:hover{background:#26C6DA;}")
        gen.layout().addWidget(gb); main.addWidget(gen)
        # Strength checker
        sc=_group("🛡  Strength Analyzer")
        self.str_in=QLineEdit(); self.str_in.setPlaceholderText("Type or paste password..."); self.str_in.setFixedHeight(40)
        self.str_in.textChanged.connect(self._live_check)
        sc.layout().addWidget(self.str_in)
        self.str_bar=QProgressBar(); self.str_bar.setMaximum(5); self.str_bar.setFixedHeight(10); self.str_bar.setTextVisible(False)
        sc.layout().addWidget(self.str_bar)
        self.str_lbl=QLabel("Strength: —"); self.str_lbl.setStyleSheet("background:transparent;font-size:13px;")
        sc.layout().addWidget(self.str_lbl); main.addWidget(sc)
        # Save
        sv=_group("💾  Save Password")
        sf=QFormLayout()
        self.plat_in=QLineEdit(); self.plat_in.setFixedHeight(40)
        self.user_in=QLineEdit(); self.user_in.setFixedHeight(40)
        self.pw_in=QLineEdit(); self.pw_in.setFixedHeight(40); self.pw_in.setEchoMode(QLineEdit.Password)
        sf.addRow("Platform:", self.plat_in); sf.addRow("Username:", self.user_in); sf.addRow("Password:", self.pw_in)
        sv.layout().addLayout(sf)
        save_b=QPushButton("Save to Vault"); save_b.setFixedHeight(40); save_b.clicked.connect(self._save)
        save_b.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4,stop:1 #0097a7);border:none;border-radius:10px;color:black;font-weight:bold;}QPushButton:hover{background:#26C6DA;}")
        sv.layout().addWidget(save_b); main.addWidget(sv)
        # Table + export
        th=QHBoxLayout()
        tl=QLabel("🔒  Saved Passwords"); tl.setStyleSheet("font-size:14px;font-weight:bold;background:transparent;"); th.addWidget(tl); th.addStretch()
        exp_b=QPushButton("💾  Export Vault"); exp_b.setFixedHeight(36); exp_b.clicked.connect(self._export)
        exp_b.setStyleSheet("QPushButton{background:#1e293b;border:1px solid #334155;border-radius:8px;color:#94a3b8;font-weight:bold;}QPushButton:hover{background:#334155;color:#e2e8f0;}")
        th.addWidget(exp_b); main.addLayout(th)
        self.table=QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(["Platform","Username","Strength","Rating","Entropy","Crack Time"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True); self.table.verticalHeader().setVisible(False)
        main.addWidget(self.table)
        self._load_table()

    def _generate(self):
        length=int(self.len_in.text()) if self.len_in.text().isdigit() else 16
        self.gen_out.setText(generate_password(length))

    def _live_check(self):
        pw=self.str_in.text()
        if not pw: self.str_bar.setValue(0); self.str_lbl.setText("Strength: —"); return
        strength,rating,color=check_strength(pw)
        entropy=calc_entropy(pw); crack=crack_time(entropy)
        self.str_bar.setValue(rating)
        self.str_bar.setStyleSheet(f"QProgressBar{{background:#1e293b;border:none;border-radius:5px;}}QProgressBar::chunk{{background:{color};border-radius:5px;}}")
        self.str_lbl.setText(f"Strength: {strength}  ({rating}/5)  |  Entropy: {entropy} bits  |  Crack: {crack}")
        self.str_lbl.setStyleSheet(f"color:{color};font-size:13px;background:transparent;")

    def _save(self):
        platform=self.plat_in.text().strip()
        username=self.user_in.text().strip()
        password=self.pw_in.text()
        if not platform or not username or not password:
            QMessageBox.warning(self,"Missing Fields","All fields are required."); return
        strength,rating,_=check_strength(password)
        entropy=calc_entropy(password); crack=crack_time(entropy)
        data=load_vault()
        data.append({"platform":platform,"username":username,
            "password_hash":hash_pw(password),"strength":strength,
            "rating":rating,"entropy":entropy,"crack_time":crack,
            "saved_at":str(datetime.now())})
        save_vault(data)
        self.plat_in.clear(); self.user_in.clear(); self.pw_in.clear()
        self._load_table()
        QMessageBox.information(self,"Saved",f"✅ Password for '{platform}' saved securely.")

    def _load_table(self):
        data=load_vault(); self.table.setRowCount(0)
        for row,item in enumerate(data):
            self.table.insertRow(row)
            for c,val in enumerate([item["platform"],item["username"],item["strength"],
                                     f"{item['rating']}/5",str(item["entropy"]),item["crack_time"]]):
                ti=QTableWidgetItem(val); ti.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row,c,ti)

    def _export(self):
        data=load_vault()
        if not data: QMessageBox.information(self,"Empty","No passwords saved yet."); return
        path,_=QFileDialog.getSaveFileName(self,"Export Password Vault",
            f"password_vault_{datetime.now().strftime('%Y%m%d')}","JSON (*.json);;Text (*.txt)")
        if not path: return
        export_data=[{"platform":d["platform"],"username":d["username"],
            "strength":d["strength"],"entropy":d["entropy"],"crack_time":d["crack_time"]} for d in data]
        if path.endswith(".txt"):
            with open(path,"w") as f:
                f.write("CyberArmor Password Vault Export\n"+"="*40+"\n(Passwords are NOT included — hashes only)\n\n")
                for e in export_data:
                    f.write(f"Platform : {e['platform']}\nUsername : {e['username']}\nStrength : {e['strength']}\nEntropy  : {e['entropy']} bits\nCrack    : {e['crack_time']}\n\n")
        else:
            with open(path,"w") as f: json.dump(export_data,f,indent=4)
        QMessageBox.information(self,"Exported",f"✅ Vault exported:\n{path}")
