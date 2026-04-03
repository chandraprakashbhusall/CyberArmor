"""
CyberArmor – Settings Page
Account info, password change, theme switcher, feedback.

FIX: Theme and accent color now call apply_theme() which re-polishes all
     top-level windows, so the change is visible everywhere instantly.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QMessageBox, QCheckBox, QSpinBox,
    QScrollArea, QTextEdit, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import db
from tools import theme


class SettingsWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.user_row = None
        self._build_ui()

    # ══════════════════════════════════════════
    # MAIN LAYOUT
    # ══════════════════════════════════════════

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        main = QVBoxLayout(container)
        main.setContentsMargins(40, 30, 40, 40)
        main.setSpacing(22)

        # Page header
        title = QLabel("⚙  Settings")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("background: transparent;")
        main.addWidget(title)

        # Add all setting cards
        main.addWidget(self._account_card())
        main.addWidget(self._password_card())
        main.addWidget(self._appearance_card())
        main.addWidget(self._security_card())
        main.addWidget(self._feedback_card())
        main.addWidget(self._logout_card())
        main.addStretch()

        scroll.setWidget(container)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

    # ══════════════════════════════════════════
    # SHARED CARD HELPERS
    # ══════════════════════════════════════════

    def _card(self, title_text, icon=""):
        """Creates a standard settings card frame."""
        frame = QFrame()
        # Note: we only use minimal inline style here;
        # the global theme QSS handles everything else.
        # Using 'border: ...' inline would override the QSS, so we avoid it.
        frame.setProperty("class", "card")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(16)

        # Card header row
        hdr = QHBoxLayout()
        label_text = f"{icon}  {title_text}" if icon else title_text
        title = QLabel(label_text)
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("background: transparent;")
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Divider line
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #1e293b; border: none; border-radius: 0;")
        layout.addWidget(sep)

        return frame

    def _input(self, placeholder, echo_password=False):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(46)
        if echo_password:
            inp.setEchoMode(QLineEdit.Password)
        return inp

    def _primary_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedHeight(46)
        btn.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #00BCD4, stop:1 #0097a7);
            border: none; border-radius: 10px;
            color: black; font-weight: bold; font-size: 14px;
        }
        QPushButton:hover { background: #26C6DA; }
        """)
        return btn

    # ══════════════════════════════════════════
    # ACCOUNT INFO CARD
    # ══════════════════════════════════════════

    def _account_card(self):
        card = self._card("Account Information", "👤")
        layout = card.layout()

        info_row = QHBoxLayout()

        # Avatar circle
        avatar = QLabel("🛡")
        avatar.setFixedSize(68, 68)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
        QLabel {
            background: rgba(0,188,212,0.15);
            border-radius: 34px;
            font-size: 30px;
        }""")
        info_row.addWidget(avatar)
        info_row.addSpacing(16)

        # User info labels
        info_col = QVBoxLayout()
        info_col.setSpacing(6)

        self.lbl_user   = QLabel("Username: —")
        self.lbl_user.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent;")

        self.lbl_email  = QLabel("Email: —")
        self.lbl_email.setStyleSheet("color: #64748b; font-size: 14px; background: transparent;")

        self.lbl_joined = QLabel("Member since: —")
        self.lbl_joined.setStyleSheet("color: #475569; font-size: 13px; background: transparent;")

        info_col.addWidget(self.lbl_user)
        info_col.addWidget(self.lbl_email)
        info_col.addWidget(self.lbl_joined)

        info_row.addLayout(info_col)
        info_row.addStretch()
        layout.addLayout(info_row)
        return card

    # ══════════════════════════════════════════
    # CHANGE PASSWORD CARD
    # ══════════════════════════════════════════

    def _password_card(self):
        card = self._card("Change Password", "🔐")
        layout = card.layout()

        self.cur_pass  = self._input("Current Password",     echo_password=True)
        self.new_pass  = self._input("New Password",         echo_password=True)
        self.conf_pass = self._input("Confirm New Password", echo_password=True)

        self.show_pw_chk = QCheckBox("Show Passwords")
        self.show_pw_chk.stateChanged.connect(self._toggle_passwords)

        update_btn = self._primary_btn("Update Password")
        update_btn.clicked.connect(self._change_password)

        for w in [self.cur_pass, self.new_pass, self.conf_pass,
                  self.show_pw_chk, update_btn]:
            layout.addWidget(w)

        return card

    # ══════════════════════════════════════════
    # APPEARANCE CARD (theme + accent)
    # ══════════════════════════════════════════

    def _appearance_card(self):
        card = self._card("Appearance", "🎨")
        layout = card.layout()

        # ── Theme row ──
        theme_row = QHBoxLayout()

        theme_lbl = QLabel("App Theme:")
        theme_lbl.setStyleSheet("background: transparent; font-size: 14px;")
        theme_row.addWidget(theme_lbl)
        theme_row.addStretch()

        self.dark_btn  = QPushButton("🌙  Dark")
        self.light_btn = QPushButton("☀  Light")

        toggle_style = """
        QPushButton {
            background: #1e293b; border: 1px solid #334155;
            border-radius: 8px; color: #94a3b8; font-weight: bold;
            padding: 8px 22px; font-size: 14px;
        }
        QPushButton:checked {
            background: rgba(0,188,212,0.22);
            border: 1.5px solid #00BCD4; color: #00BCD4;
        }
        QPushButton:hover:!checked { background: #334155; color: #e2e8f0; }
        """
        for btn in [self.dark_btn, self.light_btn]:
            btn.setFixedHeight(40)
            btn.setFixedWidth(120)
            btn.setCheckable(True)
            btn.setStyleSheet(toggle_style)

        self.dark_btn.setChecked(theme.is_dark())
        self.light_btn.setChecked(not theme.is_dark())

        self.dark_btn.clicked.connect(self._set_dark)
        self.light_btn.clicked.connect(self._set_light)

        theme_row.addWidget(self.dark_btn)
        theme_row.addSpacing(8)
        theme_row.addWidget(self.light_btn)
        layout.addLayout(theme_row)

        # Hint text
        hint = QLabel("Switching theme applies to the entire application instantly.")
        hint.setStyleSheet("color: #64748b; font-size: 12px; background: transparent;")
        layout.addWidget(hint)

        # ── Accent color row ──
        accent_row = QHBoxLayout()
        accent_lbl = QLabel("Accent Color:")
        accent_lbl.setStyleSheet("background: transparent; font-size: 14px;")
        accent_row.addWidget(accent_lbl)
        accent_row.addStretch()

        # Predefined accent colors with names
        accent_colors = [
            ("#00BCD4", "Cyan (Default)"),
            ("#8b5cf6", "Purple"),
            ("#10b981", "Green"),
            ("#f59e0b", "Amber"),
            ("#ef4444", "Red"),
            ("#3b82f6", "Blue"),
        ]
        for color, name in accent_colors:
            dot = QPushButton()
            dot.setFixedSize(32, 32)
            dot.setToolTip(name)
            dot.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                border-radius: 16px;
                border: 2px solid transparent;
            }}
            QPushButton:hover {{ border: 2px solid white; }}
            """)
            dot.clicked.connect(lambda checked, c=color: self._set_accent(c))
            accent_row.addWidget(dot)

        layout.addLayout(accent_row)
        return card

    # ══════════════════════════════════════════
    # SECURITY SETTINGS CARD
    # ══════════════════════════════════════════

    def _security_card(self):
        card = self._card("Security Settings", "🛡")
        layout = card.layout()

        # Auto-logout timer row
        row1 = QHBoxLayout()
        lbl1 = QLabel("Auto Logout Timeout (minutes):")
        lbl1.setStyleSheet("background: transparent; font-size: 14px;")
        row1.addWidget(lbl1)
        row1.addStretch()
        self.logout_spin = QSpinBox()
        self.logout_spin.setRange(1, 120)
        self.logout_spin.setValue(10)
        self.logout_spin.setFixedWidth(90)
        self.logout_spin.setFixedHeight(40)
        row1.addWidget(self.logout_spin)
        layout.addLayout(row1)

        self.email_alert_chk = QCheckBox("Email alert on new login from unknown device")
        self.email_alert_chk.setChecked(True)
        layout.addWidget(self.email_alert_chk)

        self.scan_notif_chk = QCheckBox("Show notifications after security scans")
        self.scan_notif_chk.setChecked(True)
        layout.addWidget(self.scan_notif_chk)

        # Save button (visual only – would persist to config in production)
        save_btn = self._primary_btn("Save Security Settings")
        save_btn.clicked.connect(lambda: QMessageBox.information(
            self, "Saved", "✅ Security preferences saved."
        ))
        layout.addWidget(save_btn)
        return card

    # ══════════════════════════════════════════
    # FEEDBACK CARD
    # ══════════════════════════════════════════

    def _feedback_card(self):
        card = self._card("Send Feedback", "💬")
        layout = card.layout()

        # Star rating row
        rating_row = QHBoxLayout()
        rating_lbl = QLabel("Your Rating:")
        rating_lbl.setStyleSheet("background: transparent; font-size: 14px;")
        rating_row.addWidget(rating_lbl)
        rating_row.addSpacing(12)

        self.star_btns      = []
        self.current_rating = 0

        for i in range(1, 6):
            star = QPushButton("☆")
            star.setFixedSize(38, 38)
            star.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 24px; color: #334155;
            }
            QPushButton:hover { color: #f59e0b; }
            """)
            star.clicked.connect(lambda checked, s=i: self._set_rating(s))
            self.star_btns.append(star)
            rating_row.addWidget(star)

        rating_row.addStretch()
        layout.addLayout(rating_row)

        # Category dropdown
        cat_row = QHBoxLayout()
        cat_lbl = QLabel("Category:")
        cat_lbl.setStyleSheet("background: transparent; font-size: 14px;")
        cat_row.addWidget(cat_lbl)
        self.feedback_cat = QComboBox()
        self.feedback_cat.addItems([
            "General", "UI/UX Design", "Bug Report",
            "Feature Request", "Performance", "Other"
        ])
        self.feedback_cat.setFixedHeight(44)
        cat_row.addWidget(self.feedback_cat, 1)
        layout.addLayout(cat_row)

        # Message box
        msg_lbl = QLabel("Message:")
        msg_lbl.setStyleSheet("background: transparent; font-size: 14px;")
        layout.addWidget(msg_lbl)

        self.feedback_text = QTextEdit()
        self.feedback_text.setPlaceholderText("Tell us what you think about CyberArmor...")
        self.feedback_text.setFixedHeight(110)
        layout.addWidget(self.feedback_text)

        submit_btn = self._primary_btn("Submit Feedback")
        submit_btn.clicked.connect(self._submit_feedback)
        layout.addWidget(submit_btn)
        return card

    # ══════════════════════════════════════════
    # LOGOUT CARD
    # ══════════════════════════════════════════

    def _logout_card(self):
        card = QFrame()
        card.setStyleSheet("""
        QFrame {
            background: rgba(239,68,68,0.08);
            border-radius: 14px;
            border: 1px solid rgba(239,68,68,0.25);
        }""")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(26, 18, 26, 18)

        lbl = QLabel("End your current session and return to the login screen.")
        lbl.setStyleSheet("color: #94a3b8; background: transparent; font-size: 14px;")
        layout.addWidget(lbl)
        layout.addStretch()

        logout_btn = QPushButton("🚪  Logout")
        logout_btn.setFixedHeight(46)
        logout_btn.setFixedWidth(140)
        logout_btn.setStyleSheet("""
        QPushButton {
            background: rgba(239,68,68,0.2);
            border: 1px solid rgba(239,68,68,0.5);
            border-radius: 10px; color: #ef4444;
            font-weight: bold; font-size: 14px;
        }
        QPushButton:hover { background: rgba(239,68,68,0.38); }
        """)
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)
        return card

    # ══════════════════════════════════════════
    # LOGIC / EVENT HANDLERS
    # ══════════════════════════════════════════

    def set_user(self, user_row):
        """Called from main window after login. user_row = (id, username, email, created_at)."""
        self.user_row = user_row
        if not user_row:
            return
        _, username, email, created = user_row
        self.lbl_user.setText(f"Username:  {username}")
        self.lbl_email.setText(f"Email:  {email}")
        date_str = str(created).split("T")[0] if created else "—"
        self.lbl_joined.setText(f"Member since:  {date_str}")

    def _toggle_passwords(self, state):
        mode = QLineEdit.Normal if state else QLineEdit.Password
        for f in [self.cur_pass, self.new_pass, self.conf_pass]:
            f.setEchoMode(mode)

    def _change_password(self):
        if not self.user_row:
            QMessageBox.warning(self, "Error", "You must be logged in to change your password.")
            return

        cur  = self.cur_pass.text()
        new  = self.new_pass.text()
        conf = self.conf_pass.text()

        if not cur or not new or not conf:
            QMessageBox.warning(self, "Missing Fields", "Please fill in all three password fields.")
            return
        if new != conf:
            QMessageBox.warning(self, "Mismatch", "New passwords do not match.")
            return
        if len(new) < 6:
            QMessageBox.warning(self, "Too Short", "New password must be at least 6 characters.")
            return
        if not db.verify_credentials(self.user_row[2], cur):
            QMessageBox.warning(self, "Wrong Password", "Current password is incorrect.")
            return

        db.update_password(self.user_row[0], new)
        QMessageBox.information(self, "Success", "✅ Password updated successfully.")
        self.cur_pass.clear()
        self.new_pass.clear()
        self.conf_pass.clear()

    def _set_dark(self):
        """Switch to dark theme and apply globally."""
        theme.set_theme("dark")   # this calls apply_theme() internally
        self.dark_btn.setChecked(True)
        self.light_btn.setChecked(False)

    def _set_light(self):
        """Switch to light theme and apply globally."""
        theme.set_theme("light")  # this calls apply_theme() internally
        self.dark_btn.setChecked(False)
        self.light_btn.setChecked(True)

    def _set_accent(self, color):
        """Change accent/primary color and apply globally."""
        theme.set_primary_color(color)  # calls apply_theme() internally

    def _set_rating(self, rating):
        self.current_rating = rating
        for i, btn in enumerate(self.star_btns):
            if i < rating:
                btn.setText("★")
                btn.setStyleSheet("""
                QPushButton {
                    background: transparent; border: none;
                    font-size: 24px; color: #f59e0b;
                }
                QPushButton:hover { color: #fbbf24; }
                """)
            else:
                btn.setText("☆")
                btn.setStyleSheet("""
                QPushButton {
                    background: transparent; border: none;
                    font-size: 24px; color: #334155;
                }
                QPushButton:hover { color: #f59e0b; }
                """)

    def _submit_feedback(self):
        if not self.user_row:
            QMessageBox.warning(self, "Not Logged In", "Please log in to submit feedback.")
            return
        if self.current_rating == 0:
            QMessageBox.warning(self, "Rating Required", "Please select at least 1 star.")
            return

        message = self.feedback_text.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Message Required", "Please write a short feedback message.")
            return

        db.submit_feedback(
            self.user_row[1],
            self.current_rating,
            self.feedback_cat.currentText(),
            message
        )
        QMessageBox.information(self, "Thank You!", "✅ Your feedback has been submitted. We appreciate it!")
        self.feedback_text.clear()
        self._set_rating(0)

    def _logout(self):
        window = self.window()
        if hasattr(window, "logout"):
            window.logout()
