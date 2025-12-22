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

# setup path structure for email templates
SCRIPT_DIR = Path(__file__).parent

TEMPLATE_DIR = SCRIPT_DIR.parent / 'templates'

# Setup Jinja Environment
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def send_alert_email(summary_text, subject="MindFuel Email Automation Summary"):
    """Send alert email with statistics summary to admin."""
    if not AppConfig.SEND_ALERTS:
        logger.info("Alert emails disabled (SEND_ALERTS=false)")
        return False
        
    if not AppConfig.ALERT_EMAIL:
        logger.warning("ALERT_EMAIL not configured, skipping alert email")
        return False
        
    try:
        # Pass email template and render jinja values
        html_summary = env.get_template('alert_email.html')

        html_content = html_summary.render(summary_text=summary_text)
        
        # Configure email structure
        message = MIMEMultipart('alternative')
        message['From'] = formataddr(('MindFuel Alert System', AppConfig.SENDER_EMAIL))
        message['To'] = AppConfig.ALERT_EMAIL
        message['Subject'] = subject
        
        message.attach(MIMEText(summary_text, 'plain'))
        message.attach(MIMEText(html_content, 'html'))

        # Open session to send email
        with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT, timeout=EmailConfig.SMTP_TIMEOUT) as server:
            server.starttls()
            server.login(EmailConfig.SENDER_EMAIL, EmailConfig.SENDER_PASSWORD)
            server.send_message(message)
        
        logger.info(f"Alert email sent successfully to {AppConfig.ALERT_EMAIL}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}", exc_info=True)
        return False
