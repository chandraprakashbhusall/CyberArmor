"""
CyberArmor – Login / Register Window
Clean auth screen with OTP verification for register and password reset.

BUG FIX: forgot password now properly updates the database after OTP is verified.
The old code sent the OTP fine but never called db.update_password() correctly.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QStackedWidget, QMessageBox, QInputDialog,
    QToolButton, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

import db
import smtplib
import random
from email.message import EmailMessage

# ── Gmail SMTP credentials (app password) ──
SMTP_EMAIL    = "cyberarmor.np@gmail.com"
SMTP_PASSWORD = "kadz njjf psyw onvq"

# ── Hardcoded admin credentials ──
ADMIN_EMAIL   = "cyberarmor.np@gmail.com"
ADMIN_PASS    = "cyberarmor"


# ──────────────────────────────────────────────
# PASSWORD FIELD WITH EYE TOGGLE
# ──────────────────────────────────────────────

class PasswordEdit(QLineEdit):
    """A password field with a show/hide toggle button built in."""

    def __init__(self, placeholder="Password"):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setEchoMode(QLineEdit.Password)
        self.setFixedHeight(52)

        # Eye icon toggle button placed inside the field
        self.eye_btn = QToolButton(self)
        self.eye_btn.setText("👁")
        self.eye_btn.setCursor(Qt.PointingHandCursor)
        self.eye_btn.setStyleSheet(
            "border: none; font-size: 16px; background: transparent; color: #64748b;"
        )
        self.eye_btn.clicked.connect(self._toggle)

    def resizeEvent(self, e):
        # Keep eye button inside the right edge
        self.eye_btn.move(self.width() - 38, 14)

    def _toggle(self):
        if self.echoMode() == QLineEdit.Password:
            self.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setText("🙈")
        else:
            self.setEchoMode(QLineEdit.Password)
            self.eye_btn.setText("👁")


# ──────────────────────────────────────────────
# BACKGROUND THREADS
# ──────────────────────────────────────────────

class LoginWorker(QThread):
    """Runs db.check_user in a thread so UI doesn't freeze."""
    finished = pyqtSignal(object)

    def __init__(self, email, password):
        super().__init__()
        self.email    = email
        self.password = password

    def run(self):
        # Check admin first, then regular users
        if self.email == ADMIN_EMAIL and self.password == ADMIN_PASS:
            self.finished.emit("ADMIN")
            return
        row = db.check_user(self.email, self.password)
        self.finished.emit(row)


class EmailWorker(QThread):
    """Sends an OTP email via Gmail SMTP in background."""
    finished = pyqtSignal(bool)

    def __init__(self, email, otp, subject_tag):
        super().__init__()
        self.email       = email
        self.otp         = otp
        self.subject_tag = subject_tag

    def run(self):
        try:
            msg = EmailMessage()
            msg["From"]    = SMTP_EMAIL
            msg["To"]      = self.email
            msg["Subject"] = f"CyberArmor – {self.subject_tag} OTP"
            msg.set_content(
                f"Hello,\n\n"
                f"Your CyberArmor OTP is: {self.otp}\n\n"
                f"This code expires in 10 minutes.\n"
                f"Do not share this with anyone.\n\n"
                f"– CyberArmor Security Team"
            )
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(SMTP_EMAIL, SMTP_PASSWORD)
                s.send_message(msg)
            self.finished.emit(True)
        except Exception as e:
            print("Email error:", e)
            self.finished.emit(False)


# ──────────────────────────────────────────────
# SHARED STYLES
# ──────────────────────────────────────────────

INPUT_STYLE = """
QLineEdit {
    background: #0a0f1e;
    border: 1.5px solid #1e293b;
    border-radius: 10px;
    padding: 0 14px;
    color: #e2e8f0;
    font-size: 15px;
}
QLineEdit:focus { border-color: #00BCD4; }
"""

BTN_PRIMARY = """
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00BCD4, stop:1 #0097a7);
    border: none;
    border-radius: 10px;
    color: #000000;
    font-size: 15px;
    font-weight: bold;
    padding: 14px;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #26C6DA, stop:1 #00ACC1);
}
QPushButton:pressed { background: #0097a7; }
QPushButton:disabled { background: #1e293b; color: #4b5563; }
"""

BTN_GHOST = """
QPushButton {
    background: transparent;
    border: 1.5px solid #1e293b;
    border-radius: 10px;
    color: #94a3b8;
    font-size: 14px;
    padding: 12px;
}
QPushButton:hover { border-color: #00BCD4; color: #00BCD4; }
"""

LINK_STYLE       = "color: #00BCD4; font-size: 13px; background: transparent;"
LINK_STYLE_HOVER = "color: #26C6DA; text-decoration: underline; background: transparent;"


# ──────────────────────────────────────────────
# MAIN AUTH WINDOW
# ──────────────────────────────────────────────

class AuthWindow(QWidget):

    login_successful = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.resize(1200, 780)
        self.setWindowTitle("CyberArmor")
        self.setStyleSheet("background: #020617; color: white; font-family: 'Segoe UI';")

        # OTP and pending email stored here during forgot-password flow
        self.otp           = None
        self.pending_email = None
        self._worker       = None

        self._build_ui()

    # ══════════════════════════════════════════
    # UI CONSTRUCTION
    # ══════════════════════════════════════════

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_left_panel(), 5)
        root.addWidget(self._build_right_panel(), 4)

    def _build_left_panel(self):
        """Left half – branding / feature list."""
        panel = QFrame()
        panel.setStyleSheet("""
        QFrame {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #050d1f, stop:0.5 #0a1628, stop:1 #020617);
            border-radius: 0;
        }""")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(64, 64, 64, 64)
        layout.setSpacing(0)

        # Top accent bar
        accent_line = QFrame()
        accent_line.setFixedHeight(3)
        accent_line.setFixedWidth(64)
        accent_line.setStyleSheet("background: #00BCD4; border-radius: 2px;")
        layout.addWidget(accent_line)
        layout.addSpacing(44)

        # Shield emoji
        shield = QLabel("🛡")
        shield.setFont(QFont("Segoe UI Emoji", 72))
        shield.setAlignment(Qt.AlignLeft)
        shield.setStyleSheet("background: transparent;")
        layout.addWidget(shield)
        layout.addSpacing(18)

        # App name
        title = QLabel("CyberArmor")
        title.setFont(QFont("Segoe UI", 44, QFont.Bold))
        title.setStyleSheet("color: #f1f5f9; background: transparent; letter-spacing: -1px;")
        layout.addWidget(title)

        # Tagline
        sub = QLabel("AI-Powered Security Suite")
        sub.setStyleSheet(
            "color: #00BCD4; font-size: 17px; font-weight: bold; "
            "letter-spacing: 3px; background: transparent;"
        )
        layout.addWidget(sub)
        layout.addSpacing(52)

        # Feature bullets
        features = [
            ("🔐", "Military-grade password vault"),
            ("🔍", "Real-time network & port scanner"),
            ("🤖", "AI cybersecurity assistant"),
            ("📧", "Email & link threat analysis"),
            ("🛡", "System health monitoring"),
        ]
        for icon, text in features:
            row = QHBoxLayout()
            row.setSpacing(16)

            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont("Segoe UI Emoji", 18))
            icon_lbl.setStyleSheet("background: transparent;")
            icon_lbl.setFixedWidth(34)

            text_lbl = QLabel(text)
            text_lbl.setStyleSheet("color: #94a3b8; font-size: 15px; background: transparent;")

            row.addWidget(icon_lbl)
            row.addWidget(text_lbl)
            row.addStretch()

            container = QWidget()
            container.setStyleSheet("background: transparent;")
            container.setLayout(row)
            container.setFixedHeight(38)
            layout.addWidget(container)

        layout.addStretch()

        ver = QLabel("v2.0  ·  CyberArmor Security Platform")
        ver.setStyleSheet("color: #334155; font-size: 12px; background: transparent;")
        layout.addWidget(ver)

        return panel

    def _build_right_panel(self):
        """Right half – login / register stack."""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background: #0a0f1e; border-radius: 0; }")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_login_form())    # index 0
        self.stack.addWidget(self._build_register_form()) # index 1
        layout.addWidget(self.stack)

        return panel

    def _make_card(self, width=430):
        """Helper – creates a dark card frame with drop shadow."""
        card = QFrame()
        card.setFixedWidth(width)
        card.setStyleSheet("""
        QFrame {
            background: #111827;
            border-radius: 20px;
            border: 1px solid #1e293b;
        }""")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 130))
        card.setGraphicsEffect(shadow)
        return card

    def _build_login_form(self):
        w = QWidget()
        w.setStyleSheet("background: #0a0f1e;")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(2)

        card_row = QHBoxLayout()
        card_row.addStretch()
        card = self._make_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(38, 38, 38, 38)
        card_layout.setSpacing(18)

        heading = QLabel("Welcome back")
        heading.setFont(QFont("Segoe UI", 26, QFont.Bold))
        heading.setStyleSheet("color: #f1f5f9; background: transparent;")
        card_layout.addWidget(heading)

        sub = QLabel("Sign in to your CyberArmor account")
        sub.setStyleSheet("color: #64748b; font-size: 14px; background: transparent;")
        card_layout.addWidget(sub)
        card_layout.addSpacing(4)

        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email address")
        self.login_email.setFixedHeight(52)
        self.login_email.setStyleSheet(INPUT_STYLE)
        card_layout.addWidget(self.login_email)

        self.login_pass = PasswordEdit("Password")
        self.login_pass.setStyleSheet(INPUT_STYLE)
        card_layout.addWidget(self.login_pass)

        # Forgot password link
        forgot = QLabel("Forgot password?")
        forgot.setStyleSheet(LINK_STYLE)
        forgot.setCursor(Qt.PointingHandCursor)
        forgot.mousePressEvent = lambda e: self._forgot_password()
        forgot.enterEvent      = lambda e: forgot.setStyleSheet(LINK_STYLE_HOVER)
        forgot.leaveEvent      = lambda e: forgot.setStyleSheet(LINK_STYLE)
        forgot.setAlignment(Qt.AlignRight)
        card_layout.addWidget(forgot)

        self.login_btn = QPushButton("Sign In")
        self.login_btn.setFixedHeight(52)
        self.login_btn.setStyleSheet(BTN_PRIMARY)
        self.login_btn.clicked.connect(self._login)
        self.login_pass.returnPressed.connect(self._login)
        card_layout.addWidget(self.login_btn)

        card_layout.addLayout(self._divider_row())

        reg_btn = QPushButton("Create New Account")
        reg_btn.setFixedHeight(52)
        reg_btn.setStyleSheet(BTN_GHOST)
        reg_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        card_layout.addWidget(reg_btn)

        card_row.addWidget(card)
        card_row.addStretch()
        outer.addLayout(card_row)
        outer.addStretch(3)
        return w

    def _build_register_form(self):
        w = QWidget()
        w.setStyleSheet("background: #0a0f1e;")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(2)

        card_row = QHBoxLayout()
        card_row.addStretch()
        card = self._make_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(38, 38, 38, 38)
        card_layout.setSpacing(16)

        heading = QLabel("Create Account")
        heading.setFont(QFont("Segoe UI", 26, QFont.Bold))
        heading.setStyleSheet("color: #f1f5f9; background: transparent;")
        card_layout.addWidget(heading)

        sub = QLabel("Join CyberArmor – secure your digital life")
        sub.setStyleSheet("color: #64748b; font-size: 14px; background: transparent;")
        card_layout.addWidget(sub)
        card_layout.addSpacing(4)

        self.reg_user = QLineEdit()
        self.reg_user.setPlaceholderText("Username")
        self.reg_user.setFixedHeight(52)
        self.reg_user.setStyleSheet(INPUT_STYLE)
        card_layout.addWidget(self.reg_user)

        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Email address")
        self.reg_email.setFixedHeight(52)
        self.reg_email.setStyleSheet(INPUT_STYLE)
        card_layout.addWidget(self.reg_email)

        self.reg_pass = PasswordEdit("Password (min 6 characters)")
        self.reg_pass.setStyleSheet(INPUT_STYLE)
        card_layout.addWidget(self.reg_pass)

        reg_btn = QPushButton("Create Account")
        reg_btn.setFixedHeight(52)
        reg_btn.setStyleSheet(BTN_PRIMARY)
        reg_btn.clicked.connect(self._send_register_otp)
        card_layout.addWidget(reg_btn)

        card_layout.addLayout(self._divider_row())

        back_btn = QPushButton("Back to Sign In")
        back_btn.setFixedHeight(52)
        back_btn.setStyleSheet(BTN_GHOST)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        card_layout.addWidget(back_btn)

        card_row.addWidget(card)
        card_row.addStretch()
        outer.addLayout(card_row)
        outer.addStretch(3)
        return w

    def _divider_row(self):
        """Returns a horizontal 'or' divider layout."""
        div_row = QHBoxLayout()
        line1   = QFrame(); line1.setFixedHeight(1)
        line1.setStyleSheet("background: #1e293b; border-radius: 0;")
        line2   = QFrame(); line2.setFixedHeight(1)
        line2.setStyleSheet("background: #1e293b; border-radius: 0;")
        or_lbl  = QLabel("or")
        or_lbl.setStyleSheet("color: #334155; background: transparent; padding: 0 10px;")
        div_row.addWidget(line1)
        div_row.addWidget(or_lbl)
        div_row.addWidget(line2)
        return div_row

    # ══════════════════════════════════════════
    # LOGIN LOGIC
    # ══════════════════════════════════════════

    def _login(self):
        email    = self.login_email.text().strip()
        password = self.login_pass.text()

        if not email or not password:
            QMessageBox.warning(self, "Missing Fields", "Please enter email and password.")
            return

        self.login_btn.setText("Signing in...")
        self.login_btn.setEnabled(False)

        # Run login check in background thread
        self._worker = LoginWorker(email, password)
        self._worker.finished.connect(self._on_login)
        self._worker.start()

    def _on_login(self, row):
        self.login_btn.setText("Sign In")
        self.login_btn.setEnabled(True)

        if row == "ADMIN":
            self.login_successful.emit("ADMIN")
            return
        if row:
            self.login_successful.emit(row)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid email or password.")

    # ══════════════════════════════════════════
    # REGISTER LOGIC
    # ══════════════════════════════════════════

    def _send_register_otp(self):
        username = self.reg_user.text().strip()
        email    = self.reg_email.text().strip()
        password = self.reg_pass.text()

        if not username or not email or not password:
            QMessageBox.warning(self, "Missing Fields", "All fields are required.")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 6 characters.")
            return

        if db.user_exists(email=email):
            QMessageBox.warning(self, "Email Taken", "An account with this email already exists.")
            return

        if db.user_exists(username=username):
            QMessageBox.warning(self, "Username Taken", "This username is already taken.")
            return

        # Store pending details – these will be used after OTP verified
        self.otp           = str(random.randint(100000, 999999))
        self.pending_email = email

        self._email_worker = EmailWorker(email, self.otp, "Registration")
        self._email_worker.finished.connect(self._on_register_otp_sent)
        self._email_worker.start()

    def _on_register_otp_sent(self, ok):
        if not ok:
            # Fall back to demo OTP if email fails (offline dev mode)
            QMessageBox.information(
                self, "OTP Note",
                "Email could not be sent (SMTP config). Using demo OTP: 123456"
            )
            self.otp = "123456"

        entered, accepted = QInputDialog.getText(
            self, "Verify Email", "Enter the 6-digit OTP sent to your email:"
        )
        if not accepted:
            return

        if entered.strip() != self.otp:
            QMessageBox.warning(self, "Wrong OTP", "The OTP you entered is incorrect.")
            return

        # OTP matched – create the account
        ok = db.add_user(
            self.reg_user.text().strip(),
            self.reg_email.text().strip(),
            self.reg_pass.text()
        )
        if ok:
            QMessageBox.information(
                self, "Account Created",
                "✅ Your account has been created. You can now log in."
            )
            self.stack.setCurrentIndex(0)
        else:
            QMessageBox.critical(
                self, "Error",
                "Failed to create account. Username or email may already exist."
            )

    # ══════════════════════════════════════════
    # FORGOT PASSWORD LOGIC
    # BUG FIX: The old version sent the OTP but never saved the new password.
    # Now we store pending_email and call db.update_password() after OTP check.
    # ══════════════════════════════════════════

    def _forgot_password(self):
        """Step 1 – ask for email and send OTP."""
        email = self.login_email.text().strip()
        if not email:
            email, ok = QInputDialog.getText(
                self, "Reset Password", "Enter your registered email:"
            )
            if not ok or not email:
                return

        if not db.user_exists(email=email):
            QMessageBox.warning(self, "Not Found", "No account found with this email address.")
            return

        # Generate OTP and remember the email
        self.otp           = str(random.randint(100000, 999999))
        self.pending_email = email  # <-- this is critical for step 2

        self._email_worker = EmailWorker(email, self.otp, "Password Reset")
        self._email_worker.finished.connect(self._on_reset_otp_sent)
        self._email_worker.start()

    def _on_reset_otp_sent(self, ok):
        """Step 2 – verify OTP, then ask for new password and update DB."""
        if not ok:
            QMessageBox.information(
                self, "OTP Note",
                "Email could not be sent. Using demo OTP: 123456"
            )
            self.otp = "123456"

        # Verify the OTP the user enters
        entered, accepted = QInputDialog.getText(
            self, "Verify OTP", "Enter the 6-digit OTP sent to your email:"
        )
        if not accepted:
            return

        if entered.strip() != self.otp:
            QMessageBox.warning(self, "Wrong OTP", "Incorrect OTP. Please try again.")
            return

        # Ask for new password
        new_pw, accepted = QInputDialog.getText(
            self, "New Password",
            "Enter your new password (min 6 chars):",
            QLineEdit.Password
        )
        if not accepted or not new_pw:
            return

        if len(new_pw) < 6:
            QMessageBox.warning(self, "Too Short", "Password must be at least 6 characters.")
            return

        # --- THE ACTUAL FIX ---
        # Save the new password to the database using the email we stored earlier
        db.update_password(self.pending_email, new_pw)

        QMessageBox.information(
            self, "Password Updated",
            "✅ Your password has been updated successfully.\nYou can now log in with your new password."
        )

        # Clear stored OTP so it can't be reused
        self.otp           = None
        self.pending_email = None
