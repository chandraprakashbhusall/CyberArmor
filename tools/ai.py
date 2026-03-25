# tools/ai.py
import os
import json
from datetime import datetime
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit,
    QPushButton, QHBoxLayout, QListWidget, QMessageBox,
    QSplitter
)

from tools import theme

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
                self.token.emit("\n[Model not loaded]\n")
                self.finished.emit()
                return

            for chunk in self.model.generate(
                self.prompt,
                max_tokens=200,
                temp=0.3,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1,
                streaming=True
            ):
                self.token.emit(chunk)

            self.finished.emit()

        except Exception as e:
            self.token.emit(f"\nError: {e}\n")
            self.finished.emit()


# ================= AI Widget =================
class AIWidget(QWidget):
    def __init__(self, model_path=None):
        super().__init__()

        # ❌ NO HARDCODED STYLE HERE
        # Theme will be controlled globally

        self.model_path = model_path or os.path.abspath("tools/falcon.gguf")
        self.model = None
        self.worker = None

        self.chat_history_dir = "chat_sessions"
        os.makedirs(self.chat_history_dir, exist_ok=True)

        self.current_session = None
        self.messages = []

        self.init_ui()
        self.load_model()
        self.load_sessions()

    # ---------------- UI ----------------
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # ===== LEFT SIDE (Chat) =====
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        title = QLabel("🤖 CyberArmor AI")
        title.setStyleSheet("font-size:20px; font-weight:bold;")
        left_layout.addWidget(title)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        left_layout.addWidget(self.chat_area)

        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask something...")

        self.send_btn = QPushButton("Send")

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)
        left_layout.addLayout(input_layout)

        # ===== RIGHT SIDE (Sessions) =====
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        history_label = QLabel("🗂 Chat History")
        history_label.setStyleSheet("font-weight:bold;")
        right_layout.addWidget(history_label)

        self.session_list = QListWidget()
        right_layout.addWidget(self.session_list)

        self.new_chat_btn = QPushButton("New Chat")
        right_layout.addWidget(self.new_chat_btn)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # Signals
        self.send_btn.clicked.connect(self.ask)
        self.input_box.returnPressed.connect(self.ask)
        self.new_chat_btn.clicked.connect(self.new_chat)
        self.session_list.itemClicked.connect(self.load_selected_session)

    # ---------------- Load Model ----------------
    def load_model(self):
        if not GPT4ALL_AVAILABLE:
            self.chat_area.append("Install GPT4All: pip install gpt4all")
            self.send_btn.setEnabled(False)
            return

        if not os.path.exists(self.model_path):
            self.chat_area.append("Model file not found.")
            self.send_btn.setEnabled(False)
            return

        try:
            self.chat_area.append("Loading model...")
            self.model = GPT4All(
                self.model_path,
                allow_download=False,
                device="cpu"
            )
            self.chat_area.append("Model loaded successfully.\n")
        except Exception as e:
            self.chat_area.append(f"Model load failed: {e}")
            self.send_btn.setEnabled(False)

    # ---------------- Ask ----------------
    def ask(self):
        question = self.input_box.text().strip()
        if not question or not self.model:
            return

        if not self.current_session:
            self.new_chat()

        self.input_box.clear()
        self.send_btn.setEnabled(False)

        self.chat_area.append(f"\nYou: {question}")
        self.messages.append({"role": "user", "content": question})

        system_prompt = (
            "You are CyberArmor AI.\n"
            "You are a cybersecurity and Linux expert.\n"
            "Answer clearly and briefly.\n\n"
            f"User question: {question}\nAnswer:"
        )

        self.chat_area.append("AI: ")

        self.worker = AIWorker(self.model, system_prompt)
        self.worker.token.connect(self.stream_text)
        self.worker.finished.connect(self.done)
        self.worker.start()

    def stream_text(self, text):
        self.chat_area.insertPlainText(text)

    def done(self):
        full_text = self.chat_area.toPlainText()
        answer = full_text.split("AI:")[-1].strip()

        self.messages.append({"role": "assistant", "content": answer})
        self.save_session()

        self.send_btn.setEnabled(True)
        self.chat_area.append("\n")

    # ---------------- Sessions ----------------
    def new_chat(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe_name = timestamp.replace(":", "-")

        self.current_session = f"chat_{safe_name}.json"
        self.messages = []
        self.chat_area.clear()

        # Show clean name without .json
        self.session_list.addItem(f"Chat {timestamp}")

    def save_session(self):
        if not self.current_session:
            return

        path = os.path.join(self.chat_history_dir, self.current_session)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, indent=4)

    def load_sessions(self):
        self.session_list.clear()

        files = sorted(os.listdir(self.chat_history_dir), reverse=True)

        for file in files:
            if file.endswith(".json"):
                clean_name = file.replace("chat_", "").replace(".json", "")
                clean_name = clean_name.replace("-", ":")
                self.session_list.addItem(f"Chat {clean_name}")

    def load_selected_session(self, item):
        display_name = item.text().replace("Chat ", "")
        safe_name = display_name.replace(":", "-")

        file_name = f"chat_{safe_name}.json"
        path = os.path.join(self.chat_history_dir, file_name)

        if not os.path.exists(path):
            return

        with open(path, "r", encoding="utf-8") as f:
            self.messages = json.load(f)

        self.current_session = file_name
        self.chat_area.clear()

        for msg in self.messages:
            if msg["role"] == "user":
                self.chat_area.append(f"You: {msg['content']}")
            else:
                self.chat_area.append(f"AI: {msg['content']}")

    # ---------------- Clean Close ----------------
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        event.accept()