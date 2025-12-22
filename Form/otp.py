# Form/otp.py
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class OTPManager:
    def __init__(self, email_sender="cyberarmor.np@gmail.com", email_password="imoy jeaz swqp surl"):
        """
        Initialize OTP manager.
        email_sender: the email that will send the OTP
        email_password: app password or real password
        """
        self.email_sender = email_sender
        self.email_password = email_password
        self.generated_otp = ""

    def generate_otp(self, length=6):
        """Generate a random numeric OTP"""
        self.generated_otp = ''.join([str(random.randint(0,9)) for _ in range(length)])
        return self.generated_otp

    def send_otp_email(self, recipient_email, otp=None, subject="CyberArmor OTP Verification"):
        """
        Send the OTP to recipient email.
        If otp is None, generates a new OTP.
        """
        if otp is None:
            otp = self.generate_otp()

        message = MIMEMultipart()
        message["From"] = self.email_sender
        message["To"] = recipient_email
        message["Subject"] = subject

        body = f"""
        🛡️ CyberArmor Security Verification 🛡️

        Your One-Time Password (OTP) is: {otp}

        Do not share this OTP with anyone.
        """
        message.attach(MIMEText(body, "plain"))

        # --- Sending Email ---
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.email_sender, self.email_password)
            server.sendmail(self.email_sender, recipient_email, message.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending OTP: {e}")
            return False

    def verify_otp(self, user_input):
        """Check if the entered OTP matches the generated one"""
        return str(user_input).strip() == str(self.generated_otp)
