# MindFuel - Email Automation System

## Navigation / Quick Access

- [Overview](#overview)
- [Features](#features)
- [System Architecture Diagram](#system-architecture-diagram)
- [Project Workflow](#project-workflow)
- [Weekly Subscriber Logic](#weekly-subscriber-logic)
- [Project Structure](#project-structure)
- [Technical Stack](#technical-stack)
- [Setup Guide](#setup-guide)
- [Logging](#logging)
- [Deployment and Scheduling](#deployment-and-scheduling)
- [Images from Successful Run](#images-from-sucessful-run)

## Overview
This project is a Python-based email automation system for MindFuel (a mental health wellness startup) that fetches motivational quotes from the [ZenQuotes API](https://zenquotes.io/), and delivers them as personalised emails to subscribed users.

## Features
#### **API Integration** 
Connects to the Zenquotes API  (`/today` endpoint) to retrieve daily motivational quotes, transforms the API response, and persists the data locally with caching to avoid redundant API calls.
#### **Database Integration**: 
Connects to a PostgreSQL database using SQLAlchemy and retrieves users in batches based on their email frequency preference (daily or weekly) and subscription status (active).
#### **Email Processing and Delivery** 
Uses Jinja2 templating to generate personalized HTML emails for each user. Each email includes the user's name, the daily quote, and author attribution that is then delivered using the SMTP server.
#### **Logging and Monitoring** 
Implements a detailed logging system with separate log files for API operations, email processing, and summary statistics. All actions, errors, and performance metrics are captured to ensure effective debugging and monitoring.
#### **Error Handling and Admin Alerting** 
Features robust error handling Triggers critical alerts on pipeline failures and sends summary reports on successful runs to admin via email. 
#### **Idempotency and Recovery** 
Maintains a checkpoint system that tracks the last successfully processed user ID, allowing the system to resume from the point of failure without sending duplicate emails.
#### **Database Integrity with Transaction Management** 
Ensures all database updates and activity use commit and rollback to ensure transactions are fully committed on success or rolled back on failure to maintain data consistency and integrity.
#### **Rate Limiting** 
Implements a 0.1-second delay between email sends (10 emails/second maximum) to comply with SMTP server rate limits and avoid emails being flagged as spam or sender getting blacklisted.

## System Architecture Diagram
<img width="2532" height="1675" alt="Blank diagram" src="https://github.com/user-attachments/assets/61810ae7-e050-40bb-8d4b-c861eb21cf4b" />

## Project Workflow

### 1. ETL Pipeline (Quote Retrieval)

**Data Extraction:**
- Connects to the ZenQuotes API using the `requests` library.
- Includes a retry logic with exponential backoff (a maximum of 3 attempts).
- Implements a 10-second timeout for API calls

**Data Validation:**
- Parses the API response as JSON.
- Validates that required keys ('q' for quote, 'a' for author) are present and non-empty.
- Logs malformed or incomplete data and halts processing if validation fails.

**Data Transformation:**
- Maps shorthand API keys to descriptive names: `'q'` → `'quote'`, `'a'` → `'author'`
- Enriches data with metadata (ingestion timestamps): current date and ISO timestamp.
- Structures data as: `{'quote': str, 'author': str, 'date': 'YYYY-MM-DD', 'fetched_at': ISO_timestamp}`

**Data Loading:**
- Persists transformed data to a local JSON file (`quote_data.json`).
- Implements file permission and OS error handling.

**Cache Mechanism:**
- Uses cached data if fresh, avoiding redundant API calls regardless of how many times the script runs in a day.
- Before making API calls, performs a check if a valid quote for today already exists.
- Validates cached data structure (all required keys present)
- Performs freshness check by comparing the cached date with today's date.

### 2. Database Connection and User Retrieval

**Connection Initialization:**
- Establishes a database engine using SQLAlchemy with `pool_pre_ping=True` for connection health checks.
- Connection is initialized automatically when the `db_conn` module is imported.

**Batch Processing with Generator:**
- Uses a Python generator function to retrieve users in batches (default: 1000 records per batch).
- Processes one batch at a time to manage memory efficiently for large users.

**User Selection Criteria:**
Users are retrieved based on the following SQL conditions:
- `subscription_status = 'active'`
- `email_frequency` matches the requested type ('daily' or 'weekly').
- `user_id > last_processed_id` (ensures resumption from checkpoint).
- `last_email_sent_at < CURRENT_DATE OR last_email_sent_at IS NULL` (prevents duplicate sends on the same day).

**Checkpoint Mechanism:**
- Tracks the last processed `user_id` in a JSON checkpoint file.
- After each successful batch, updates the checkpoint with the highest `user_id` processed.
- On pipeline restart, resumes from the last checkpoint to avoid reprocessing users.
- Resets checkpoint to 0 when all users for the day have been processed.

### 3. Email Template Rendering and Delivery

**Template Processing:**
- Uses Jinja2 to render both HTML and plain text email versions.
- Personalizes each email by injecting: `user's name`, `quote`, and `author` in email template.

**SMTP Configuration:**
- Opens a single SMTP connection per batch for efficiency.
- Implements TLS encryption with `server.starttls()`
- Authenticates with sender credentials before sending.

**Email Structure:**
- Uses MIME multipart messages to successfully create complex email body such as the HTML version..
- Includes both plain text and HTML versions for email client compatibility. 

**Retry Logic:**
- Each email has up to 3 send attempts with exponential backoff (2s, 4s, 8s).
- Tracks successful and failed email sends separately.
- Only users with successful email delivery are marked for database update.

**Rate Limiting:**
- Implements a 0.1-second delay between batch completions to not exceed SMTP provider limits.

### 4. Database Update and Feedback Loop

**Transactional Updates:**
- After each batch is fully processed, performs a bulk database update.
- Updates `last_email_sent_at` to `CURRENT_TIMESTAMP` for all users with successful email delivery.
- Uses SQLAlchemy's `session.commit()` to persist changes.

**Rollback Strategy:**
- If database update fails, calls `session.rollback()` to undo uncommitted changes, this also ensures data integrity by never leaving partial updates in the database.
- Re-raises the exception to halt further processing and trigger admin alert.

**Checkpoint Update:**
- Updates checkpoint file only after successful database commit.
- Stores the highest `user_id` from the successfully processed batch.
- Enables exact resumption if the next batch fails.

### 5. Logging, Monitoring, and Admin Alerts

**Logging Architecture:**
- **API Log:** Captures all operations involving API calls, cache, and save operations.
- **Main Log:** Records email processing, batch operations, database interactions, and SMTP activities.
- **Summary Log:** Stores high-level statistics and performance metrics.

**Statistics Tracking:**
Maintains real-time counters for:
- `records_processed`: Total users processed.
- `emails_sent`: Successfully delivered emails.
- `failed`: Failed email attempts.
- `daily`: Count of daily subscribers processed.
- `weekly`: Count of weekly subscribers processed (Mondays only).

**Performance Metrics:**
Calculates and logs:
- Success rate: `(emails_sent / records_processed) × 100`
- Duration: Total execution time in seconds and minutes.
- Throughput: `emails_sent / duration` (emails per second).

**Admin Alerting:**
- **Success Reports:** Sent after every successful run with complete statistics.
- **Failure Alerts:** Triggered on critical errors.
- Alert emails include formatted reports with timestamp, status, statistics, breakdown, and performance metrics

## Weekly Subscriber Logic

The system processes weekly subscribers only on Mondays. This logic is implemented in the main orchestration script:

```python
if day_name == "Monday":
    # Process weekly subscribers
else:
    # Skip weekly subscribers
```

Users with `email_frequency = 'weekly'` receive quotes once per week, while `email_frequency = 'daily'` users receive quotes every day.

## Project Structure

```
customer-automation/
├── api_data/             # Quote cache directory (auto-generated)
    ├── pipeline_checkpoint.json    # watermark to track pipeline's progress (auto-generated)
│   └── quote_data.json   # Today's quote (auto-generated)
|
│
|── config/                
    └── setup_config.py   # system's config file
|
├── logs/                 (auto-generated)
│   ├── api_ingest.log    # API interaction logs (auto-generated)
│   ├── process.log       # Other process and main logic logs (auto-generated)
│   └── summary.log       # Execution statistics (auto-generated)
│
|── src/
|   ├── alerts.py         # alerting system for monitoring
│   ├── api_ingest.py     # Api ingestion script
│   ├── db_conn.py        # database interaction
|   ├── email_utils.py    # Email config
│   ├── process.py        # Subscribed users processing
|   └── summary_log.py    # Summary logs config
│  
|── templates/
|   ├── alert_email.html   # Alerting email template
│   ├── email_plain.txt    # Plain email text (backup)
│   └── email.html         # Main email template
|
|── venv/                 # Virtual environment (create this)
|
├── fetch_quote.py         # ENTRYPOINT: Fetch today's quote or cached quote
├── main.py                # ENTRYPOINT: Email distribution script
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables (create this)
└── README.md              # This file
```

## Technical Stack

- **Language:** Python 3.12.4
- **Database:** PostgreSQL
- **Email:** SMTP with Python `smtplib` and `email.mime`
- **Templating:** Jinja2, HTML
- **Configuration:** python-dotenv for environment variables
- **Logging:** Python `logging` module

## Setup Guide

This section provides step-by-step instructions to reproduce the exact environment and run the system from scratch.

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/tahmee/customer-automation.git
cd customer-automation/
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### Configuration

#### 1. Gmail Setup (If Using Gmail)
1. Enable 2-Factor Authentication on your Google account.
2. Generate an App Password:
   - Go to your [Google Account](https://myaccount.google.com/) → Security
   - Select "2-Step Verification"
   - At the bottom, select "App passwords"
   - Generate a password for "Mail" (you can give it any name of your choice)
3. Use this App Password as `SENDER_PASSWORD` in your `.env` file

#### 2. Database Setup

Create the required database table:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    email_address VARCHAR(255) NOT NULL UNIQUE,
    subscription_status VARCHAR(20) NOT NULL,
    email_frequency VARCHAR(10) NOT NULL,
    last_email_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample data insertion
INSERT INTO users (first_name, email_address, subscription_status, email_frequency)
VALUES 
    ('Alice', 'alice.test@example.com', 'active', 'daily'),
    ('Bob', 'bob.test@example.com', 'active', 'daily'),
    ('Charlie', 'charlie.test@example.com', 'active', 'weekly'),
    ('Diana', 'diana.test@example.com', 'active', 'daily'),
    ('Eve', 'eve.test@example.com', 'active', 'weekly');
```

#### 3. Environment Variables Setup

Create a `.env` file in the project root directory:

```bash
# API Configuration
API_URL=https://zenquotes.io/api/today

# Database Configuration
DB_CREDENTIALS=postgresql://username:password@host:port/database_name
# Example: postgresql://admin:mypassword@localhost:5432/mindfuel_db

# File Paths
FILE_PATH=api_data/quote_data.json

# SMTP Configuration
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password-here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_TIMEOUT=30

# Alert Configuration
ALERT_EMAIL=admin@yourdomain.com
SEND_ALERTS=true
```
**Important**: Update the `.env` file with your actual credentials.


### Directory Structure Creation

The scripts will automatically create necessary directories, but you can also create them manually:

```bash
mkdir -p logs api_data
```
**important**: Ensure `api_data/` and `logs` has write permissions.

### Test Run

```bash
# Test quote ingestion
echo "Testing quote ingestion..."
python fetch_quote.py

# Verify quote was saved
cat api_data/quote_data.json

# Test email sending (dry run recommended first)
echo "Testing email distribution..."
python main.py
```

### Automated Scheduling
The scripts are scheduled to run once daily using CRON 

#### Linux/macOS (cron)

Edit your crontab:
```bash
crontab -e
```

Add the following lines:
```bash
# Fetch quote at 6:00 AM daily (Entry point: fetch_quote.py)
0 6 * * * cd /path/to/customer-automation && /path/to/venv/bin/python fetch_quote.py >> logs/cron.log 2>&1

# Send emails at 7:00 AM daily (Entry point: main.py)
0 7 * * * cd /path/to/customer-automation && /path/to/venv/bin/python main.py >> logs/cron.log 2>&1
```

## Logging

### Log Files

#### 1. `api_ingest.log`
- API connection attempts and results
- Response validation
- Caching operations
- Error details

**Example entries:**
```
2025-11-12 06:00:15 - INFO - Attempting to fetch data from https://zenquotes.io/api/today
2025-11-12 06:00:16 - INFO - Response status code: 200
2025-11-12 06:00:16 - INFO - Data successfully retrieved and parsed into JSON
2025-11-12 06:00:16 - INFO - Today's quote: 'The only way to do great work is to love what you...' by Steve Jobs
```

#### 2. `process.log`
- Detailed email sending operations
- Batch processing progress
- Individual email success/failure
- Retry attempts
- Database queries

**Example entries:**
```
2025-11-12 07:00:00 - INFO - BEGIN EMAIL AUTOMATION SCRIPT
2025-11-12 07:00:01 - INFO - Database engine created successfully
2025-11-12 07:00:01 - INFO - Quote loaded successfully: 'The only way to do great work...' by Steve Jobs
2025-11-12 07:00:02 - INFO - Fetched batch of 1000 daily users (total so far: 1000)
2025-11-12 07:00:05 - INFO - Email sent successfully John Doe, john@example.com on attempt 1!
```

#### 3. `summary.log`
- High-level statistics
- Success rates
- Performance metrics
- Execution summaries

**Example entries:**
```
2025-11-12 07:15:30 - EMAIL STATISTICS SUMMARY - 2025-11-12 07:15:30
2025-11-12 07:15:30 - Day: Tuesday
2025-11-12 07:15:30 - Total processed: 5000
2025-11-12 07:15:30 - Successfully sent: 4987
2025-11-12 07:15:30 - Failed: 13
2025-11-12 07:15:30 - Success rate: 99.74%
2025-11-12 07:15:30 - Duration: 180.45 seconds (3.01 minutes)
2025-11-12 07:15:30 - Throughput: 27.64 emails/second
```

## Deployment and Scheduling

The system is designed to be scheduled via cron for automated daily execution. The exit codes enable monitoring:
- Exit code 0: Successful execution
- Exit code 1: Critical failure (triggers cron notification)

## Images From Sucessful Run
<img width="1273" height="1481" alt="image1" src="https://github.com/user-attachments/assets/b367e621-dd3f-4c17-b09b-a22ab4163b64" />
<img width="1062" height="168" alt="image2" src="https://github.com/user-attachments/assets/18d60307-f1fb-497a-806a-4f686014c486" />
<img width="930" height="243" alt="image3" src="https://github.com/user-attachments/assets/55f1513b-1d8d-4391-b01e-493a05b93d39" />
<img width="820" height="261" alt="image4" src="https://github.com/user-attachments/assets/8a764fbd-7967-4499-b03e-06e8fb018a87" />
<img width="419" height="486" alt="image5" src="https://github.com/user-attachments/assets/d8da74a3-00a7-4fed-aff7-c8edb720fcfa" />

## Contact
For suggestions/ideas on improvement for this project or issues encountered during reproduction of this project please reach out to me on [LinkedIn](https://www.linkedin.com/in/susanamgbare/). I look forward to connecting, and having a chat.
  

