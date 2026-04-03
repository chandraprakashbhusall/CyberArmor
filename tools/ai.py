"""
CyberArmor – AI Chat (GPT4All)
Streaming responses, session history, export.
"""
import os, json
from datetime import datetime
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QLineEdit, QPushButton, QListWidget, QMessageBox,
    QSplitter, QFrame, QFileDialog
)
from PyQt5.QtGui import QFont

try:
    from gpt4all import GPT4All
    GPT4ALL_AVAILABLE = True
except ImportError:
    GPT4ALL_AVAILABLE = False; GPT4All = None

BTN_PRIMARY="QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4,stop:1 #0097a7);border:none;border-radius:10px;color:black;font-weight:bold;}QPushButton:hover{background:#26C6DA;}QPushButton:disabled{background:#1e293b;color:#4b5563;}"
BTN_GHOST="QPushButton{background:#1e293b;border:1px solid #334155;border-radius:10px;color:#94a3b8;font-weight:bold;}QPushButton:hover{background:#334155;color:#e2e8f0;}"

class AIWorker(QThread):
    token=pyqtSignal(str); finished=pyqtSignal()
    def __init__(self,model,prompt):
        super().__init__(); self.model=model; self.prompt=prompt
    def run(self):
        try:
            if not self.model: self.token.emit("\n[Model not loaded]\n"); self.finished.emit(); return
            for chunk in self.model.generate(self.prompt,max_tokens=300,temp=0.3,
                top_k=40,top_p=0.9,repeat_penalty=1.1,streaming=True):
                self.token.emit(chunk)
            self.finished.emit()
        except Exception as e:
            self.token.emit(f"\nError: {e}\n"); self.finished.emit()

class AIWidget(QWidget):
    def __init__(self, model_path=None):
        super().__init__()
        self.model_path=model_path or os.path.abspath("tools/falcon.gguf")
        self.model=None; self.worker=None
        self.chat_dir="chat_sessions"; os.makedirs(self.chat_dir,exist_ok=True)
        self.current_session=None; self.messages=[]
        self._build_ui(); self._load_model(); self._load_sessions()

    def _build_ui(self):
        main=QHBoxLayout(self); main.setContentsMargins(0,0,0,0)
        splitter=QSplitter(Qt.Horizontal)
        # Left: chat
        left=QWidget(); left.setStyleSheet("background:#0a0f1e;")
        ll=QVBoxLayout(left); ll.setContentsMargins(20,18,12,18); ll.setSpacing(12)
        title=QLabel("🤖  CyberArmor AI Assistant")
        title.setFont(QFont("Segoe UI",16,QFont.Bold)); title.setStyleSheet("background:transparent;")
        ll.addWidget(title)
        self.chat_area=QTextEdit(); self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("QTextEdit{background:#060c18;border:1px solid #1e293b;border-radius:10px;padding:12px;font-size:13px;color:#e2e8f0;}")
        ll.addWidget(self.chat_area)
        ir=QHBoxLayout(); ir.setSpacing(10)
        self.input_box=QLineEdit(); self.input_box.setPlaceholderText("Ask about cybersecurity, Linux, networking...")
        self.input_box.setFixedHeight(44); self.input_box.returnPressed.connect(self._ask)
        ir.addWidget(self.input_box)
        self.send_btn=QPushButton("Send"); self.send_btn.setFixedHeight(44); self.send_btn.setFixedWidth(90)
        self.send_btn.clicked.connect(self._ask); self.send_btn.setStyleSheet(BTN_PRIMARY)
        ir.addWidget(self.send_btn); ll.addLayout(ir)
        # Right: sessions
        right=QWidget(); right.setStyleSheet("background:#070d1a;"); right.setFixedWidth(240)
        rl=QVBoxLayout(right); rl.setContentsMargins(12,18,16,18); rl.setSpacing(10)
        hl=QLabel("🗂  Chat History"); hl.setFont(QFont("Segoe UI",12,QFont.Bold)); hl.setStyleSheet("background:transparent;")
        rl.addWidget(hl)
        self.session_list=QListWidget()
        self.session_list.setStyleSheet("QListWidget{background:#0a0f1e;border:1px solid #1e293b;border-radius:8px;}QListWidget::item{padding:8px;color:#94a3b8;}QListWidget::item:selected{color:#00BCD4;background:rgba(0,188,212,0.15);}QListWidget::item:hover{background:#111827;}")
        self.session_list.itemClicked.connect(self._load_session)
        rl.addWidget(self.session_list)
        new_btn=QPushButton("＋  New Chat"); new_btn.setFixedHeight(38); new_btn.clicked.connect(self._new_chat)
        new_btn.setStyleSheet(BTN_PRIMARY); rl.addWidget(new_btn)
        exp_btn=QPushButton("💾  Export Chat"); exp_btn.setFixedHeight(38); exp_btn.clicked.connect(self._export)
        exp_btn.setStyleSheet(BTN_GHOST); rl.addWidget(exp_btn)
        splitter.addWidget(left); splitter.addWidget(right)
        splitter.setStretchFactor(0,1); splitter.setStretchFactor(1,0)
        main.addWidget(splitter)

    def _load_model(self):
        if not GPT4ALL_AVAILABLE:
            self.chat_area.append("⚠  GPT4All not installed.\nRun: pip install gpt4all"); self.send_btn.setEnabled(False); return
        if not os.path.exists(self.model_path):
            self.chat_area.append(f"⚠  Model file not found at:\n{self.model_path}\n\nPlace your .gguf model file there."); self.send_btn.setEnabled(False); return
        try:
            self.chat_area.append("⏳  Loading AI model...")
            self.model=GPT4All(self.model_path,allow_download=False,device="cpu")
            self.chat_area.append("✅  CyberArmor AI ready!\n")
        except Exception as e:
            self.chat_area.append(f"❌  Model load failed: {e}"); self.send_btn.setEnabled(False)

    def _ask(self):
        q=self.input_box.text().strip()
        if not q or not self.model: return
        if not self.current_session: self._new_chat()
        self.input_box.clear(); self.send_btn.setEnabled(False)
        self.chat_area.append(f"\n👤 You: {q}")
        self.messages.append({"role":"user","content":q})
        prompt=(f"You are CyberArmor AI, a cybersecurity and Linux expert.\n"
                f"Answer clearly and concisely.\n\nQuestion: {q}\nAnswer:")
        self.chat_area.append("🤖 AI: ")
        self.worker=AIWorker(self.model,prompt)
        self.worker.token.connect(lambda t: self.chat_area.insertPlainText(t))
        self.worker.finished.connect(self._done); self.worker.start()

    def _done(self):
        text=self.chat_area.toPlainText(); ans=text.split("🤖 AI:")[-1].strip()
        self.messages.append({"role":"assistant","content":ans})
        self._save_session(); self.send_btn.setEnabled(True); self.chat_area.append("\n")

    def _new_chat(self):
        ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe=ts.replace(":","-")
        self.current_session=f"chat_{safe}.json"; self.messages=[]; self.chat_area.clear()
        self.session_list.addItem(f"Chat {ts}")

    def _save_session(self):
        if not self.current_session: return
        path=os.path.join(self.chat_dir,self.current_session)
        with open(path,"w",encoding="utf-8") as f: json.dump(self.messages,f,indent=4)

    def _load_sessions(self):
        self.session_list.clear()
        for fname in sorted(os.listdir(self.chat_dir),reverse=True):
            if fname.endswith(".json"):
                clean=fname.replace("chat_","").replace(".json","").replace("-",":")
                self.session_list.addItem(f"Chat {clean}")

    def _load_session(self, item):
        display=item.text().replace("Chat ",""); safe=display.replace(":","-")
        path=os.path.join(self.chat_dir,f"chat_{safe}.json")
        if not os.path.exists(path): return
        with open(path,"r",encoding="utf-8") as f: self.messages=json.load(f)
        self.current_session=f"chat_{safe}.json"; self.chat_area.clear()
        for m in self.messages:
            prefix="👤 You" if m["role"]=="user" else "🤖 AI"
            self.chat_area.append(f"\n{prefix}: {m['content']}")

    def _export(self):
        if not self.messages: QMessageBox.information(self,"Empty","No messages to export."); return
        path,_=QFileDialog.getSaveFileName(self,"Export Chat",f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}","Text (*.txt);;JSON (*.json)")
        if not path: return
        if path.endswith(".json"):
            with open(path,"w") as f: json.dump(self.messages,f,indent=4)
        else:
            with open(path,"w") as f:
                for m in self.messages:
                    role="You" if m["role"]=="user" else "AI"; f.write(f"{role}: {m['content']}\n\n")
        QMessageBox.information(self,"Saved",f"✅ Chat saved:\n{path}")

    def closeEvent(self,e):
        if self.worker and self.worker.isRunning(): self.worker.quit(); self.worker.wait()
        e.accept()
