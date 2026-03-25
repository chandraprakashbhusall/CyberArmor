from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QMessageBox, QCheckBox, QSpinBox
)

from PyQt5.QtCore import Qt
import db


# ==========================================
# SETTINGS PAGE
# ==========================================

class SettingsWidget(QWidget):

    def __init__(self):

        super().__init__()

        self.user_row = None

        self.init_ui()


# ==========================================
# UI
# ==========================================

    def init_ui(self):

        main = QVBoxLayout(self)

        main.setContentsMargins(40,30,40,30)
        main.setSpacing(25)


# TITLE

        title = QLabel("⚙ Settings")
        title.setStyleSheet("font-size:28px;font-weight:bold;")

        main.addWidget(title)


# ==========================================
# ACCOUNT INFO
# ==========================================

        acc = self.create_card("👤 Account")

        self.lbl_user = QLabel("Username : Not Logged")
        self.lbl_email = QLabel("Email : Not Logged")

        acc.layout().addWidget(self.lbl_user)
        acc.layout().addWidget(self.lbl_email)

        main.addWidget(acc)


# ==========================================
# PASSWORD CHANGE
# ==========================================

        pw = self.create_card("🔐 Change Password")

        self.current = QLineEdit()
        self.current.setPlaceholderText("Current Password")
        self.current.setEchoMode(QLineEdit.Password)

        self.new = QLineEdit()
        self.new.setPlaceholderText("New Password")
        self.new.setEchoMode(QLineEdit.Password)

        self.confirm = QLineEdit()
        self.confirm.setPlaceholderText("Confirm Password")
        self.confirm.setEchoMode(QLineEdit.Password)

        pw.layout().addWidget(self.current)
        pw.layout().addWidget(self.new)
        pw.layout().addWidget(self.confirm)


# SHOW PASSWORD

        self.show_pass = QCheckBox("Show Password")
        self.show_pass.stateChanged.connect(self.toggle_password)

        pw.layout().addWidget(self.show_pass)


# BUTTON

        btn_update = QPushButton("Update Password")
        btn_update.setMinimumHeight(40)
        btn_update.clicked.connect(self.change_password)

        pw.layout().addWidget(btn_update)

        main.addWidget(pw)


# ==========================================
# SECURITY SETTINGS
# ==========================================

        security = self.create_card("🛡 Security")


# AUTO LOGOUT

        row1 = QHBoxLayout()

        row1.addWidget(QLabel("Auto Logout (minutes)"))

        self.logout_time = QSpinBox()
        self.logout_time.setRange(1,120)
        self.logout_time.setValue(10)

        row1.addStretch()
        row1.addWidget(self.logout_time)

        security.layout().addLayout(row1)


# LOGIN ALERT

        self.login_alert = QCheckBox("Email alert on login")
        self.login_alert.setChecked(True)

        security.layout().addWidget(self.login_alert)


# SECURITY SCAN ALERT

        self.scan_alert = QCheckBox("Security scan notifications")
        self.scan_alert.setChecked(True)

        security.layout().addWidget(self.scan_alert)


        main.addWidget(security)


# ==========================================
# LOGOUT
# ==========================================

        logout = QPushButton("🚪 Logout")

        logout.setMinimumHeight(45)

        logout.clicked.connect(self.logout)

        main.addWidget(logout)


        main.addStretch()


# ==========================================
# CARD STYLE
# ==========================================

    def create_card(self,title):

        card = QFrame()

        layout = QVBoxLayout(card)

        lbl = QLabel(title)

        lbl.setStyleSheet(
        "font-size:18px;font-weight:bold;"
        )

        layout.addWidget(lbl)

        return card


# ==========================================
# SET USER
# ==========================================

    def set_user(self,user_row):

        self.user_row = user_row

        if not user_row:
            return

        username = user_row[1]
        email = user_row[2]

        self.lbl_user.setText("Username : "+username)
        self.lbl_email.setText("Email : "+email)


# ==========================================
# PASSWORD TOGGLE
# ==========================================

    def toggle_password(self):

        mode = QLineEdit.Normal if self.show_pass.isChecked() else QLineEdit.Password

        self.current.setEchoMode(mode)
        self.new.setEchoMode(mode)
        self.confirm.setEchoMode(mode)


# ==========================================
# CHANGE PASSWORD
# ==========================================

    def change_password(self):

        if not self.user_row:

            QMessageBox.warning(self,"Error","Login required")
            return

        user_id=self.user_row[0]

        cur=self.current.text()
        new=self.new.text()
        conf=self.confirm.text()


        if new!=conf:

            QMessageBox.warning(self,"Error","Passwords mismatch")
            return


        if not db.verify_credentials(self.user_row[2],cur):

            QMessageBox.warning(self,"Error","Wrong password")
            return


        conn=db.connect()
        cursor=conn.cursor()

        cursor.execute(
        "UPDATE users SET password=? WHERE id=?",
        (db.hash_password(new),user_id)
        )

        conn.commit()
        conn.close()

        QMessageBox.information(self,"Success","Password Updated")


# ==========================================
# LOGOUT
# ==========================================

    def logout(self):

        self.window().logout()
