import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from jinja2 import Environment, FileSystemLoader
from config.setup_config import EmailConfig
from pathlib import Path
from config.setup_config import EmailConfig, AppConfig, logging_setup


#logging config
logger = logging_setup(AppConfig.LOG_PATH, __name__)

# Define the base directory of the current script (project/utils/email_script.py -> project/utils)
SCRIPT_DIR = Path(__file__).parent

# Define the template directory (project/templates)
TEMPLATE_DIR = SCRIPT_DIR.parent / 'templates'

# Setup Jinja Environment 
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def send_alert_email(summary_text, subject="MindFuel Email Automation Summary"):
    """
    Sends a multipart (Plain Text + HTML) alert email to the configured administrator.

    This function uses SMTP to send a summary report. It renders an HTML template 
    using Jinja2 and falls back to plain text for email clients that do not support HTML.

    Args:
        summary_text (str): The raw text data/statistics to include in the email.
        subject (str, optional): The subject line of the email. 
            Defaults to "MindFuel Email Automation Summary".

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    # Check if the alert feature is globally enabled in AppConfig
    if not AppConfig.SEND_ALERTS:
        logger.info("Alert emails disabled (SEND_ALERTS=false)")
        return False
    
    # Verify that a recipient email address has been provided
    if not AppConfig.ALERT_EMAIL:
        logger.warning("ALERT_EMAIL not configured, skipping alert email")
        return False
        
    try:
        # Load and render the Jinja2 HTML templates
        html_summary = env.get_template('alert_email.html')
        html_content = html_summary.render(summary_text=summary_text)
        
        # Create a multipart email object
        message = MIMEMultipart('alternative')
        message['From'] = formataddr(('MindFuel Alert System', AppConfig.SENDER_EMAIL))
        message['To'] = AppConfig.ALERT_EMAIL
        message['Subject'] = subject
        
        # Attach both versions (Plain text must be attached first)
        message.attach(MIMEText(summary_text, 'plain'))
        message.attach(MIMEText(html_content, 'html'))

        # Establish a secure SMTP connection
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT, timeout=EmailConfig.SMTP_TIMEOUT) as server:
            server.starttls()
            server.login(EmailConfig.SENDER_EMAIL, EmailConfig.SENDER_PASSWORD)
            server.send_message(message)
        
        logger.info(f"Alert email sent successfully to {AppConfig.ALERT_EMAIL}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}", exc_info=True)
        return False
