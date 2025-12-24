from datetime import datetime
from config.setup_config import logging_setup, AppConfig


summary_logger = logging_setup(AppConfig.SUMMARY_LOG_PATH, __name__)

def generate_summary(stats, day_name, duration, success=True):
    """Generate summary text for alert email."""
    total = stats['records_processed']
    success_rate = (stats['emails_sent'] / total * 100) if total > 0 else 0
    
    summary = f"""
        MindFuel Email Automation Report
        {'=' * 30}
        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Day: {day_name}
        Status: {'SUCCESS' if success else 'FAILED'}

        STATISTICS:
        -----------
        Total processed: {total}
        Successfully sent: {stats['emails_sent']}
        Failed: {stats['failed']}
        Success rate: {success_rate:.2f}%

        BREAKDOWN:
        ----------
        Daily subscribers: {stats['daily']}
        Weekly subscribers: {stats['weekly']}

        PERFORMANCE:
        ------------
        Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)
        Throughput: {stats['emails_sent'] / duration:.2f} emails/second
        """
    return summary


def log_final_summary(stats, day_name, duration):
    """Log final summary to file."""
    summary_logger.info("=" * 30)
    summary_logger.info(f"EMAIL STATISTICS SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_logger.info(f"Day: {day_name}")
    summary_logger.info(f"Total processed: {stats['records_processed']}")
    summary_logger.info(f"Daily subscribers: {stats['daily']}")
    summary_logger.info(f"Weekly subscribers: {stats['weekly']}")
    summary_logger.info(f"Successfully sent: {stats['emails_sent']}")
    summary_logger.info(f"Failed: {stats['failed']}")
    
    if stats['records_processed'] > 0:
        success_rate = (stats['emails_sent'] / stats['records_processed']) * 100
        summary_logger.info(f"Success rate: {success_rate:.2f}%")
    
    summary_logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    
    if duration > 0:
        throughput = stats['emails_sent'] / duration
        summary_logger.info(f"Throughput: {throughput:.2f} emails/second")
