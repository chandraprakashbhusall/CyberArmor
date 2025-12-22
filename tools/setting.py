from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFrame, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt
import db


class SettingsWidget(QWidget):
    def __init__(self, user_row=None):
        super().__init__()

        self.user_row = user_row

        self.setStyleSheet("""
            QWidget {
                background:#0c0c0c;
                color:white;
                font-size:14px;
            }
            QLineEdit {
                padding:10px;
                border-radius:6px;
                background:#1a1a1a;
                border:1px solid #333;
            }
            QPushButton {
                padding:12px;
                border-radius:6px;
                font-weight:bold;
            }
            QCheckBox {
                spacing:8px;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(30, 30, 30, 30)
        main.setSpacing(20)

        # ---------- TITLE ----------
        title = QLabel("⚙ Settings")
        title.setStyleSheet("font-size:26px; font-weight:bold; color:cyan;")
        main.addWidget(title)

        # ---------- ACCOUNT INFO ----------
        acc_box = QFrame()
        acc_box.setStyleSheet("background:#111; border-radius:10px;")
        acc_layout = QVBoxLayout(acc_box)

        acc_layout.addWidget(QLabel("👤 Account Information"))

        # ✅ SAFE ACCESS (THIS IS THE FIX)
        username = self.user_row["username"] if self.user_row else "—"
        email = self.user_row["email"] if self.user_row else "—"

        acc_layout.addWidget(QLabel(f"Username: {username}"))
        acc_layout.addWidget(QLabel(f"Email: {email}"))

        main.addWidget(acc_box)

        # ---------- CHANGE PASSWORD ----------
        pass_box = QFrame()
        pass_box.setStyleSheet("background:#111; border-radius:10px;")
        pass_layout = QVBoxLayout(pass_box)

        pass_layout.addWidget(QLabel("🔐 Change Password"))

        self.current_pass = QLineEdit()
        self.current_pass.setPlaceholderText("Current Password")
        self.current_pass.setEchoMode(QLineEdit.Password)

        self.new_pass = QLineEdit()
        self.new_pass.setPlaceholderText("New Password")
        self.new_pass.setEchoMode(QLineEdit.Password)

        self.confirm_pass = QLineEdit()
        self.confirm_pass.setPlaceholderText("Confirm New Password")
        self.confirm_pass.setEchoMode(QLineEdit.Password)

        pass_layout.addWidget(self.current_pass)
        pass_layout.addWidget(self.new_pass)
        pass_layout.addWidget(self.confirm_pass)

        self.show_pass = QCheckBox("Show passwords")
        self.show_pass.stateChanged.connect(self.toggle_password)
        pass_layout.addWidget(self.show_pass)

        btn_update = QPushButton("Update Password")
        btn_update.setStyleSheet("background:#00bcd4; color:black;")
        btn_update.clicked.connect(self.change_password)

        pass_layout.addWidget(btn_update)
        main.addWidget(pass_box)

        # ---------- SECURITY ----------
        sec_box = QFrame()
        sec_box.setStyleSheet("background:#111; border-radius:10px;")
        sec_layout = QVBoxLayout(sec_box)

        sec_layout.addWidget(QLabel("🛡 Security Preferences"))
        sec_layout.addWidget(QCheckBox("Auto logout after inactivity"))
        sec_layout.addWidget(QCheckBox("Remember this device"))

        main.addWidget(sec_box)
        main.addStretch()

    # ---------- HELPERS ----------
    def toggle_password(self):
        mode = QLineEdit.Normal if self.show_pass.isChecked() else QLineEdit.Password
        self.current_pass.setEchoMode(mode)
        self.new_pass.setEchoMode(mode)
        self.confirm_pass.setEchoMode(mode)

    def change_password(self):
        if not self.user_row:
            QMessageBox.warning(self, "Error", "Login required to change password.")
            return

        cur = self.current_pass.text().strip()
        new = self.new_pass.text().strip()
        conf = self.confirm_pass.text().strip()

        if not cur or not new or not conf:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        if new != conf:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        if len(new) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters.")
            return

        if not db.verify_password(self.user_row["id"], cur):
            QMessageBox.warning(self, "Error", "Current password incorrect.")
            return

        db.update_password(self.user_row["id"], new)
        QMessageBox.information(self, "Success", "Password updated.")

        self.current_pass.clear()
        self.new_pass.clear()
        self.confirm_pass.clear()
