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

# Define the directory structure for templates
SCRIPT_DIR = Path(__file__).parent
TEMPLATE_DIR = SCRIPT_DIR.parent / 'templates'

# Retry logic for SMTP stability
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds 

# Initialize Jinja Environment to load both HTML and Plain Text templates
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def email_template(recipient_name, quote, author):
    """
    Renders the email content into both HTML and Plain Text formats.

    Args:
        recipient_name (str): The user's first name for personalisation.
        quote (str): The daily inspirational quote.
        author (str): The author of the quote.

    Returns:
        tuple (str, str) | None: (html_body, text_body) if successful, None if template loading fails.
    """
    try:
        # Load specific template files from the /templates directory
        html_template = env.get_template('email.html')
        email_plain = env.get_template('email_plain.txt')
        
        # Render HTML version
        html_body = html_template.render(
            name=recipient_name,
            quote=quote,
            author=author
        )

        # Render Plain Text version
        text_body = email_plain.render(
            recipient_name=recipient_name,
            quote=quote,
            author=author
        )

        return html_body, text_body
    
    except Exception as e:
        logger.error(f"Could not find templates at {TEMPLATE_DIR}. Error: {e}")
        return None
    

def send_email(server, user_name, user_email, quote, author, sender_name='MindFuel', subject = "Inspiration from MindFuel", max_retries=MAX_RETRIES):
    """
    Constructs and sends an email with built-in retry logic using an existing SMTP session.

    This function uses an 'exponential backoff' strategy: if an attempt fails, it 
    waits progressively longer before trying again (2s, 4s, etc.).

    Args:
        server (smtplib.SMTP): An active, authenticated SMTP session.
        user_name (str): Recipient's name.
        user_email (str): Recipient's email address.
        quote (str): The quote text.
        author (str): The quote author.
        sender_name (str): Display name for the 'From' field.
        subject (str): Email subject line.
        max_retries (int): Total attempts allowed before giving up.

    Returns:
        bool: True if the email was delivered to the SMTP server, False otherwise.
    """
    for attempt in range(1, max_retries + 1):
        try:
            # Initialize Message Container for HTML
            message = MIMEMultipart('related')
            message['From'] = formataddr((sender_name, EmailConfig.SENDER_EMAIL))
            message['To'] = user_email
            message['Subject'] = subject

            # Create the 'alternative' part for the Text
            msg_alternative = MIMEMultipart('alternative')
            message.attach(msg_alternative)

            # Get rendered templates
            html_body, text_body = email_template(user_name, quote=quote, author=author)
            # Attach Content (text and HTML)
            msg_alternative.attach(MIMEText(text_body, 'plain'))
            msg_alternative.attach(MIMEText(html_body, 'html'))

            # Send email
            server.send_message(message)
            logger.info(f'Email sent successfully {user_name}, {user_email} on attempt {attempt}!')
            return True
        
        except (smtplib.SMTPException, Exception) as e:
            logger.warning(f'SMTP error sending to {user_email} (attempt {attempt}/{max_retries}): {e}')

            if attempt < max_retries:
                # Exponential backoff: RETRY_DELAY * 2^(attempt-1)
                sleep_time = RETRY_DELAY * (2 ** (attempt - 1))
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f'Failed to send email to {user_email} after {max_retries} attempts')
                return False
            
    return False