from __future__ import annotations

from html import escape
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from certificate_generator.certificates import safe_filename


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def connect_smtp(sender_email: str, email_password: str) -> smtplib.SMTP:
    """Open and authenticate a Gmail SMTP connection using STARTTLS."""
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    try:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, email_password)
    except (OSError, smtplib.SMTPException):
        try:
            server.close()
        except (OSError, smtplib.SMTPException):
            pass
        raise
    return server


def send_email(
    sender_email: str,
    recipient_email: str,
    student_name: str,
    certificate: bytes,
    server: smtplib.SMTP,
    verification_url: str,
) -> None:
    """Send a single certificate; return only after SMTP accepts the recipient."""
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = (
        f"🎉 Congratulations {student_name}! Your Internship Certificate"
    )
    safe_name = escape(student_name)
    safe_url = escape(verification_url, quote=True)
    message.attach(
        MIMEText(
            f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #0f3460;">Congratulations, {safe_name}! 🎓</h2>
                <p>We are delighted to inform you that your <b>Internship Certificate</b>
                has been successfully generated.</p>
                <p>Please find your certificate attached to this email. We appreciate
                your hard work and dedication during the internship program.</p>
                <p>You can also view your certificate and verify its UID at
                <a href="{safe_url}">this certificate verification link</a>.
                This unique link expires six months after issue. Do not share it
                publicly.</p>
                <p>Best Regards,<br><b>Dreambot Pvt Ltd</b></p>
                <hr style="border: none; border-top: 1px solid #e0e0e0;">
                <p style="font-size: 0.85rem; color: #888;">
                    This is an automated email. Please do not reply.
                </p>
            </body>
            </html>
            """,
            "html",
        )
    )

    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(certificate)
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition",
        f'attachment; filename="{safe_filename(student_name)}_Certificate.jpg"',
    )
    message.attach(attachment)

    refused = server.sendmail(sender_email, recipient_email, message.as_string())
    if refused:
        raise smtplib.SMTPRecipientsRefused(refused)
