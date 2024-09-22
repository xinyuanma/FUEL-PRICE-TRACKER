import smtplib
from email.mime.text import MIMEText
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD

def send_notification(recipient, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = recipient

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)

def notify_users(users, prices):
    for email, threshold in users:
        low_prices = [f"{station}: {price}" for station, price in prices if price <= threshold]
        if low_prices:
            subject = "Fuel Price Alert"
            body = f"The following stations have prices below your threshold of {threshold}:\n\n"
            body += "\n".join(low_prices)
            send_notification(email, subject, body)