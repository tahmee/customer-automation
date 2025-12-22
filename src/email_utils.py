import os
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from jinja2 import Environment, FileSystemLoader
from config.setup_config import logging_setup, EmailConfig, AppConfig
import time

logger=logging_setup(AppConfig.LOG_PATH, __name__)

SCRIPT_DIR = Path(__file__).parent

TEMPLATE_DIR = SCRIPT_DIR.parent / 'templates'

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds 
RATE_LIMIT_DELAY = 0.1  # seconds between emails (10 emails/second)


# 3. Setup Jinja Environment
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def email_template(recipient_name, quote, author):
    """Generate HTML email using Jinja2."""
    try:
        html_template = env.get_template('email.html')
        email_plain = env.get_template('email_plain.txt')
        
        html_body = html_template.render(
            name=recipient_name,
            quote=quote,
            author=author
        )

        text_body = email_plain.render(
            recipient_name=recipient_name,
            quote=quote,
            author=author
        )

        return html_body, text_body
    
    except Exception as e:
        # If it fails, it's likely a pathing issue
        print(f"Error: Could not find template at {TEMPLATE_DIR / 'email.html'}")
        print(f"Details: {e}")
        return None
    

def send_email(user_name, user_email, quote, author, sender_name='MindFuel', subject = "Inspiration from MindFuel", max_retries=MAX_RETRIES):
    """Send email with max retry in place."""
    for attempt in range(1, max_retries + 1):
        try:
            # Create message
            message = MIMEMultipart('related')
            message['From'] = formataddr((sender_name, EmailConfig.SENDER_EMAIL))
            message['To'] = user_email
            message['Subject'] = subject

            # Alternative container
            msg_alternative = MIMEMultipart('alternative')
            message.attach(msg_alternative)

            html_body, text_body = email_template(user_name, quote=quote, author=author)
            # Attach text and HTML
            msg_alternative.attach(MIMEText(text_body, 'plain'))
            msg_alternative.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT, timeout=EmailConfig.SMTP_TIMEOUT) as server:
                server.starttls()
                server.login(EmailConfig.SENDER_EMAIL, EmailConfig.SENDER_PASSWORD)
                server.send_message(message)
             
                logger.info(f'Email sent successfully {user_name}, {user_email} on attempt {attempt}!')
            return True
        except (smtplib.SMTPException, Exception) as e:
            logger.warning(f'SMTP error sending to {user_email} (attempt {attempt}/{max_retries}): {e}')

            if attempt < max_retries:
                sleep_time = RETRY_DELAY * (2 ** (attempt - 1))
                time.sleep(sleep_time)
            else:
                logger.error(f'Failed to send email to {user_email} after {max_retries} attempts')
                return False
            
    return False