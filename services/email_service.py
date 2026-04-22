import smtplib
import time
from email.message import EmailMessage
from config import EMAIL_ADDRESS, EMAIL_PASSWORD

def send_email(email: str, subject: str, content: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email 
    msg.set_content(content)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def send_bulk_email(emails, subject, content):

    for email in emails:
        send_email(email, subject, content)

        time.sleep(1) 

def send_weekly_notes(emails, notes):
    msg = ""
    
    for note in notes:
        msg += f"Tytuł: {note.title} \n Autor: {note.author}\n {note.content} \n Data {note.created_at}\n\n"

    if msg:
        send_bulk_email(emails, "Weekly Notes", msg)

    