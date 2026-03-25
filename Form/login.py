from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import db
import smtplib
from email.message import EmailMessage
import random


SMTP_EMAIL="cyberarmor.np@gmail.com"
SMTP_PASSWORD="kadz njjf psyw onvq"


# ================= ADMIN LOGIN =================

ADMIN_EMAIL="cyberarmor.np@gmail.com"
ADMIN_PASS="cyberarmor"


# ================= PASSWORD FIELD =================

class PasswordEdit(QLineEdit):

    def __init__(self):
        super().__init__()

        self.setEchoMode(QLineEdit.Password)

        self.eye=QToolButton(self)
        self.eye.setText("👁")
        self.eye.clicked.connect(self.toggle)
        self.eye.setCursor(Qt.PointingHandCursor)
        self.eye.setStyleSheet("border:none;font-size:18px;")


    def resizeEvent(self,e):

        self.eye.move(self.width()-32,8)


    def toggle(self):

        if self.echoMode()==QLineEdit.Password:
            self.setEchoMode(QLineEdit.Normal)
        else:
            self.setEchoMode(QLineEdit.Password)



# ================= LOGIN THREAD =================

class LoginWorker(QThread):

    finished=pyqtSignal(object)

    def __init__(self,email,password):

        super().__init__()

        self.email=email
        self.password=password


    def run(self):

        # ✅ ADMIN LOGIN FIRST
        if self.email==ADMIN_EMAIL and self.password==ADMIN_PASS:
            self.finished.emit("ADMIN")
            return

        # Normal user login
        row=db.check_user(self.email,self.password)

        self.finished.emit(row)




# ================= EMAIL THREAD =================

class EmailWorker(QThread):

    finished=pyqtSignal(bool)

    def __init__(self,parent,email,otp,mode):

        super().__init__()

        self.parent=parent
        self.email=email
        self.otp=otp
        self.mode=mode

    def run(self):

        ok=self.parent._send_email(
            self.email,
            self.otp,
            self.mode
        )

        self.finished.emit(ok)




# ================= AUTH WINDOW =================

class AuthWindow(QWidget):

    login_successful=pyqtSignal(object)

    def __init__(self):

        super().__init__()

        self.resize(1300,800)

        self.setWindowTitle("CyberArmor")

        self.setStyleSheet("""

        QWidget{
        background:#020617;
        color:white;
        font-family:Segoe UI;
        }

        QFrame#card{
        background:#0f172a;
        border-radius:20px;
        }

        QLineEdit{
        padding:14px;
        border-radius:8px;
        border:2px solid #1e293b;
        background:#020617;
        font-size:16px;
        }

        QLineEdit:focus{
        border:2px solid #06b6d4;
        }

        QPushButton{
        padding:14px;
        border-radius:8px;
        background:#06b6d4;
        font-size:16px;
        font-weight:bold;
        }

        QPushButton:hover{
        background:#0891b2;
        }

        QLabel#link{
        color:#22d3ee;
        font-size:14px;
        }

        QLabel#link:hover{
        text-decoration:underline;
        }

        """)

        self.initUI()

        self.otp=None



# ================= UI =================

    def initUI(self):

        root=QHBoxLayout(self)

        root.setContentsMargins(40,40,40,40)

        root.setSpacing(40)



# LEFT PANEL

        left=QFrame()

        left.setFixedWidth(520)

        left.setStyleSheet("""

        background:qlineargradient(
        x1:0,y1:0,x2:1,y2:1,
        stop:0 #0f172a,
        stop:1 #020617);

        border-radius:20px;

        """)

        L=QVBoxLayout(left)



        icon=QLabel("🛡")

        icon.setFont(QFont("Segoe UI",95))

        icon.setAlignment(Qt.AlignCenter)



        title=QLabel("CyberArmor")

        title.setFont(QFont("Segoe UI",35,QFont.Bold))

        title.setAlignment(Qt.AlignCenter)



        sub=QLabel("AI Cybersecurity Platform")

        sub.setAlignment(Qt.AlignCenter)

        sub.setStyleSheet("color:#94a3b8;font-size:18px")



        info=QLabel("""

✔ Secure Login
✔ OTP Verification
✔ Encrypted Passwords
✔ AI Protection

""")

        info.setAlignment(Qt.AlignCenter)

        info.setStyleSheet("color:#22d3ee;font-size:16px")


        L.addStretch()

        L.addWidget(icon)

        L.addWidget(title)

        L.addWidget(sub)

        L.addSpacing(20)

        L.addWidget(info)

        L.addStretch()


        root.addWidget(left)



# RIGHT PANEL

        card=QFrame()

        card.setObjectName("card")

        card.setMinimumWidth(520)

        layout=QVBoxLayout(card)


        self.stack=QStackedWidget()

        self.stack.addWidget(self.loginPage())

        self.stack.addWidget(self.registerPage())

        layout.addWidget(self.stack)


        root.addWidget(card,1)



# ================= LOGIN PAGE =================

    def loginPage(self):

        w=QWidget()

        L=QVBoxLayout(w)


        title=QLabel("Login")

        title.setFont(QFont("Segoe UI",32,QFont.Bold))

        L.addWidget(title)


        self.login_email=QLineEdit()
        self.login_email.setPlaceholderText("Email")

        L.addWidget(self.login_email)


        self.login_pass=PasswordEdit()
        self.login_pass.setPlaceholderText("Password")

        L.addWidget(self.login_pass)


        btn=QPushButton("Login")
        btn.clicked.connect(self.login)

        L.addWidget(btn)


        forgot=QLabel("Forgot Password?")
        forgot.setObjectName("link")
        forgot.mousePressEvent=lambda e:self.forgot_password()

        L.addWidget(forgot)


        create=QLabel("Don't have account? Create account")
        create.setObjectName("link")
        create.mousePressEvent=lambda e:self.stack.setCurrentIndex(1)

        L.addWidget(create)


        L.addStretch()

        return w




# ================= LOGIN =================

    def login(self):

        worker=LoginWorker(
            self.login_email.text(),
            self.login_pass.text()
        )

        worker.finished.connect(self.on_login)

        worker.start()

        self.worker=worker



    def on_login(self,row):

        # ADMIN LOGIN
        if row=="ADMIN":

            QMessageBox.information(self,"Admin","Admin Login Successful")

            self.login_successful.emit("ADMIN")

            return


        # USER LOGIN
        if row:

            self.login_successful.emit(row)

        else:

            QMessageBox.warning(self,"Error","Invalid Login")




# ================= REGISTER =================

    def registerPage(self):

        w=QWidget()

        L=QVBoxLayout(w)


        title=QLabel("Create Account")

        title.setFont(QFont("Segoe UI",32,QFont.Bold))

        L.addWidget(title)


        self.reg_user=QLineEdit()
        self.reg_user.setPlaceholderText("Username")

        L.addWidget(self.reg_user)


        self.reg_email=QLineEdit()
        self.reg_email.setPlaceholderText("Email")

        L.addWidget(self.reg_email)


        self.reg_pass=PasswordEdit()
        self.reg_pass.setPlaceholderText("Password")

        L.addWidget(self.reg_pass)


        btn=QPushButton("Register")
        btn.clicked.connect(self.send_register_otp)

        L.addWidget(btn)


        back=QLabel("Already have account? Login")
        back.setObjectName("link")
        back.mousePressEvent=lambda e:self.stack.setCurrentIndex(0)

        L.addWidget(back)


        L.addStretch()

        return w




# ================= OTP =================

    def send_register_otp(self):

        self.verify_email=self.reg_email.text()

        self.otp=str(random.randint(100000,999999))

        worker=EmailWorker(self,self.verify_email,self.otp,"register")

        worker.finished.connect(self.register_otp_sent)

        worker.start()

        self.email_worker=worker


    def register_otp_sent(self,ok):

        if ok:

            otp=QInputDialog.getText(self,"OTP","Enter OTP")[0]

            if otp==self.otp:

                db.add_user(
                    self.reg_user.text(),
                    self.reg_email.text(),
                    self.reg_pass.text()
                )

                QMessageBox.information(self,"Success","Account Created")

                self.stack.setCurrentIndex(0)




# ================= RESET =================

    def forgot_password(self):

        self.reset_email=self.login_email.text()

        self.otp=str(random.randint(100000,999999))

        worker=EmailWorker(self,self.reset_email,self.otp,"reset")

        worker.finished.connect(self.reset_otp_sent)

        worker.start()

        self.email_worker=worker


    def reset_otp_sent(self,ok):

        if ok:

            otp=QInputDialog.getText(self,"OTP","Enter OTP")[0]

            if otp==self.otp:

                pw=QInputDialog.getText(self,"Password","New Password")[0]

                db.update_password(self.reset_email,pw)

                QMessageBox.information(self,"Success","Password Updated")




# ================= EMAIL =================

    def _send_email(self,email,otp,mode):

        try:

            msg=EmailMessage()

            msg["From"]=SMTP_EMAIL
            msg["To"]=email
            msg["Subject"]="CyberArmor OTP"

            msg.set_content(f"Your OTP is {otp}")

            s=smtplib.SMTP_SSL("smtp.gmail.com",465)

            s.login(SMTP_EMAIL,SMTP_PASSWORD)

            s.send_message(msg)

            s.quit()

            return True

        except Exception as e:

            print(e)

            return False