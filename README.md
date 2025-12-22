# MindFuel - Email Automation System

## Navigation / Quick Access

- [Overview](#overview)
- [Features](#features)
- [System Architecture Diagram](#system-architecture-diagram)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Project Workflow](#project-workflow)
- [Reproducibility Guide](#reproducibility-guide)
- [Images from Successful Run](#images-from-sucessful-run)
- [Logging](#logging)
- [Error Handling](#error-handling)


## Overview
This project is a robust Python-based email automation system for MindFuel (a mental health wellness startup). It fetches inspirational quotes from [ZenQuotes](https://zenquotes.io/) and delivers them to subscribers retrieved from a database via personalised emails. This system supports both daily and weekly subscription frequencies with comprehensive logging, error handling, and batch processing capabilities.

## Features
**MindFuel** is a three-stage automation system designed to:
1. **Quote Ingestion** (`api_ingest.py`): Fetch daily inspirational quotes from the [ZenQuotes API](https://docs.zenquotes.io/zenquotes-documentation/) and cache them locally.
  - **The exact API endpoint used is `https://zenquotes.io/api/today/[your_key]`** with key being optional.
2. **User Retrieval** (`process.py`): Fetch users records from a database based off their subscription frequency (i.e daily/weekly).
3. **Email Distribution** (`process.py`): Send personalised emails to subscribers with the day's quote, supporting both daily and weekly delivery schedules.

## System Architecture Diagram
<img width="2387" height="1555" alt="img1" src="https://github.com/user-attachments/assets/3f4d1cba-387d-429e-b7e3-e0a9c5205b54" />

## Project Structure

```
customer-automation/
├── api_ingest.py          # Quote fetching script
├── process.py             # Email distribution script
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── README.md             # This file
│
├── api_data/             # Quote cache directory
│   └── quote_data.json   # Today's quote (auto-generated)
│
├── logs/                 # Log files directory
│   ├── api_ingest.log    # API interaction logs
│   ├── process.log       # Email sending detailed logs
│   └── summary.log       # Execution statistics
│
└── venv/                 # Virtual environment (create this)
```

## Prerequisites

### System Requirements
- Python 3.8 or higher
- PostgreSQL or any local/cloud based database
- SMTP server access (e.g., Gmail)
- Internet connection for API access

## Project Workflow

### Quote Ingestion (API)
- Connect to ZenQuotes Api using the today API endpoint, fetch the daily quote and saves into a local JSON file (`quote_data.json`)
  - A mechanism is in place to ensure a new api connection is not made (based off the timezone used for quotes being refreshed at the API endpoint) and to rely on the cached quote. This mechanism is in place to accomodate different timezone (for this implementation the `process.py` file will have to be modified.)

### ETL process (Email Delivery)
- When the `process.py` script is run:
  - A connection to the database is made and subscribers are retrieved based off conditions on (i.e daily/weekly where weekly is scheduled to receive quote only on mondays)
  - The local JSON file is opened and the quote is retrieved.
  - Using the email template setup, dynamic field like subscriber name and quote are filled based off data retrieved. This is to ensure emails are personalised per subscriber.
  - Connecting to the SMTP server emails are then delivered.

### Automation (Cron)
- Configured a cron job to run `api_ingest.py` daily at 6:00am and `process.py` daily at 7:00am.

## Reproducibility Guide

This section provides step-by-step instructions to reproduce the exact environment and run the system from scratch

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/tahmee/de-launchpad-automation-and-analytics.git
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

### Test Run

```bash
# Test quote ingestion
echo "Testing quote ingestion..."
python api_ingest.py

# Verify quote was saved
cat api_data/quote_data.json

# Test email sending (dry run recommended first)
echo "Testing email distribution..."
python process.py
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
# Fetch quote at 6:00 AM daily
0 6 * * * cd /path/to/customer-automation && /path/to/venv/bin/python api_ingest.py >> logs/cron.log 2>&1

# Send emails at 7:00 AM daily
0 7 * * * cd /path/to/customer-automation && /path/to/venv/bin/python process.py >> logs/cron.log 2>&1
```

## Images From Sucessful Run
<img width="1273" height="1481" alt="img3" src="https://github.com/user-attachments/assets/ecec0bac-73eb-4113-aa23-b04e89748e05" />
<img width="1153" height="488" alt="Screenshot 2025-11-13 at 8 46 48 AM" src="https://github.com/user-attachments/assets/173150cc-4a09-4f46-b10f-fe9814afb9d9" />
<img width="1280" height="633" alt="PHOTO-2025-11-13-08-52-33" src="https://github.com/user-attachments/assets/ce0a8ae9-204d-40a8-a610-796fa3e48a02" />
<img width="865" height="427" alt="Screenshot 2025-11-13 at 8 48 45 AM" src="https://github.com/user-attachments/assets/866e1f1b-d6d2-4994-be7b-7690e8438883" />
<img width="796" height="1280" alt="PHOTO-2025-11-13-08-55-41" src="https://github.com/user-attachments/assets/d29bddea-bb60-4bce-a84c-ae2513de501a" />



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

## Error Handling

### 1. Retry Mechanism

The system implements exponential backoff for failed email sends:

- **Attempt 1**: Immediate
- **Attempt 2**: Wait 2 seconds
- **Attempt 3**: Wait 4 seconds (2^2)

### 2. Alert System

Administrator receive email alerts for:
- Script completion with statistics
- Critical failures
- Database connection issues
- Abnormally high failure rates


## Contact
For suggestions/ideas on improvement for this project or issues encountered during reproduction of this project please reach out to me on [LinkedIn](https://www.linkedin.com/in/susanamgbare/). I look forward to connecting, and having a chat.
  
