# tools/ai.py
import os
from datetime import datetime
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit,
    QPushButton, QHBoxLayout, QFileDialog, QMessageBox
)

# GPT4All
try:
    from gpt4all import GPT4All
    GPT4ALL_AVAILABLE = True
except ImportError:
    GPT4ALL_AVAILABLE = False
    GPT4All = None


# ================= AI Worker =================
class AIWorker(QThread):
    token = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, model, prompt):
        super().__init__()
        self.model = model
        self.prompt = prompt

    def run(self):
        try:
            if not self.model:
                self.token.emit("\n❌ Model not loaded\n")
                self.finished.emit()
                return

            # STREAMING = FAST FEELING
            for chunk in self.model.generate(
                self.prompt,
                max_tokens=128,        # MUCH FASTER
                temp=0.2,              # More exact answers
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1,
                streaming=True
            ):
                self.token.emit(chunk)

            self.finished.emit()

        except Exception as e:
            self.token.emit(f"\n❌ Error: {e}\n")
            self.finished.emit()


# ================= AI Widget =================
class AIWidget(QWidget):
    def __init__(self, model_path=None):
        super().__init__()

        self.setStyleSheet("background:#0c0c0c; color:white;")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ---------- Title ----------
        title = QLabel("🤖 CyberSecurity AI")
        title.setStyleSheet("font-size:22px; font-weight:bold; color:cyan;")
        layout.addWidget(title)

        # ---------- Chat ----------
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet(
            "background:#111; border:1px solid #333; font-size:15px; padding:10px;"
        )
        layout.addWidget(self.chat_area)

        # ---------- Input ----------
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask cybersecurity / Linux / hacking question…")
        self.send_btn = QPushButton("Send")

        self.send_btn.setStyleSheet(
            "padding:8px 16px; background:#1a1a1a; border-radius:6px;"
        )

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

        # ---------- Model ----------
        self.model_path = model_path or os.path.abspath("tools/falcon.gguf")
        self.model = None
        self.load_model()

        # Signals
        self.send_btn.clicked.connect(self.ask)
        self.input_box.returnPressed.connect(self.ask)

    # ---------- Load Model ----------
    def load_model(self):
        if not GPT4ALL_AVAILABLE:
            self.chat_area.append("❌ Install GPT4All:\n pip install gpt4all")
            self.send_btn.setEnabled(False)
            return

        if not os.path.exists(self.model_path):
            self.chat_area.append(f"❌ Model not found:\n{self.model_path}")
            self.send_btn.setEnabled(False)
            return

        try:
            self.chat_area.append("⏳ Loading Falcon model...")
            self.model = GPT4All(
                self.model_path,
                allow_download=False,
                device="cpu"
            )
            self.chat_area.append("🟢 Falcon model loaded. Ask me anything.")
        except Exception as e:
            self.chat_area.append(f"❌ Failed to load model:\n{e}")
            self.send_btn.setEnabled(False)

    # ---------- Ask ----------
    def ask(self):
        question = self.input_box.text().strip()
        if not question or not self.model:
            return

        self.input_box.clear()
        self.send_btn.setEnabled(False)

        self.chat_area.append(f"\n🟢 You: {question}")
        self.chat_area.append("🤖 AI: ")

        # SYSTEM PROMPT = EXACT ANSWERS
        system_prompt = (
            "You are CyberArmor AI.\n"
            "You are a cybersecurity, Linux, and networking expert.\n"
            "Answer clearly, briefly, and accurately.\n"
            "No emojis, no stories, no fluff.\n\n"
            f"User question: {question}\nAnswer:"
        )

        self.worker = AIWorker(self.model, system_prompt)
        self.worker.token.connect(self.stream_text)
        self.worker.finished.connect(self.done)
        self.worker.start()

    def stream_text(self, text):
        self.chat_area.moveCursor(self.chat_area.textCursor().End)
        self.chat_area.insertPlainText(text)
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

    def done(self):
        self.chat_area.append("\n")
        self.send_btn.setEnabled(True)

    # ---------- Save Chat ----------
    def save_chat(self):
        history = self.chat_area.toPlainText()
        if not history.strip():
            QMessageBox.information(self, "Save Chat", "Nothing to save.")
            return

        fname, _ = QFileDialog.getSaveFileName(
            self, "Save Chat", "chat.txt", "Text Files (*.txt)"
        )
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(history)
            QMessageBox.information(self, "Saved", "Chat saved successfully.")
