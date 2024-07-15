import requests
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Configuration
API_URL = 'https://api.tvmaze.com/schedule'
DATABASE = 'tv_shows.db'
EMAIL = 'your_email@example.com'
EMAIL_PASSWORD = 'your_password'
SMTP_SERVER = 'smtp.example.com'
SMTP_PORT = 587

# Fetch TV show schedules
def fetch_schedules():
    response = requests.get(API_URL)
    return response.json()

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS shows (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        airdate TEXT,
                        airtime TEXT,
                        channel TEXT,
                        email_sent INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# Save shows to database
def save_to_db(shows):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for show in shows:
        # Check if 'network' key exists
        if 'network' in show and show['network'] is not None:
            cursor.execute('''INSERT OR IGNORE INTO shows (name, airdate, airtime, channel)
                              VALUES (?, ?, ?, ?)''',
                           (show['name'], show['airdate'], show['airtime'], show['network']['name']))
        else:
            print(f"Skipping show {show['name']} as 'network' information is not available.")
    conn.commit()
    conn.close()

# Send email reminders
def send_email(subject, body, to_email):
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL, EMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(EMAIL, to_email, text)
    server.quit()

# Check for upcoming shows and send reminders
def check_and_send_reminders():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute('''SELECT id, name, airdate, airtime, channel FROM shows
                      WHERE email_sent = 0''')
    shows = cursor.fetchall()
    for show in shows:
        show_time = datetime.strptime(f"{show[2]} {show[3]}", "%Y-%m-%d %H:%M")
        if now <= show_time <= now + timedelta(minutes=30):
            send_email(
                subject=f"Reminder: {show[1]} is about to start",
                body=f"{show[1]} will start at {show[3]} on {show[4]}",
                to_email=EMAIL
            )
            cursor.execute('UPDATE shows SET email_sent = 1 WHERE id = ?', (show[0],))
    conn.commit()
    conn.close()

def main():
    init_db()
    shows = fetch_schedules()
    save_to_db(shows)
    check_and_send_reminders()

if __name__ == "__main__":
    main()
