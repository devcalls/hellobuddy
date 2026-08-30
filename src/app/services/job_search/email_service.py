import os
import mailtrap as mt
import smtplib

from pydantic import BaseModel, EmailStr
from app.config.job_settings import JobSearchSettings
#from config.config import ConfigManager


class EmailNotificationRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    markdown_filepath: str


class EmailService:
    def __init__(self, settings: JobSearchSettings):
        self.settings = settings
    
    def background_send_email_task(self, recipient: str, subject: str, html_body: str):
        """
        Executes an asynchronous API call to Mailtrap's infrastructure 
        using their official Python SDK to send a compiled HTML job report.
        """
        try:
            # 1. Fetch your verified token from the application's environment configuration
            #api_token = os.environ.get("MAILTRAP_API_TOKEN", "YOUR_ACTUAL_API_TOKEN")
            
            #config_manager = ConfigManager()
            #api_token = config_manager.get_value("API_KEYS", "MAILTRAP_API_TOKEN")
            api_token = self.settings.api_keys.mailtrap_api_token
            
            client = mt.MailtrapClient(token=api_token)
            
            # 2. Build the structured Mail object matching Mailtrap SDK components
            mail = mt.Mail(
                # NOTE: If using production streams, swap this placeholder email 
                # for your own verified sending domain (e.g., "alerts@hello-buddy.com")
                sender=mt.Address(email="hello@demomailtrap.co", name="Hellobuddy Alerts"),
                to=[mt.Address(email=recipient)],
                subject=subject,
                
                # Pass your generated responsive HTML string block directly here:
                html=html_body,
                
                # Plain text fallback for old email readers or watch devices
                text="Your job match report has arrived! Please view this email in an HTML-compatible client.",
                category="Job Match Alert"
            )
            
            # 3. Offload payload transmission to the Mailtrap Client
            response = client.send(mail)
            
            print(f"Notification sent successfully via Mailtrap SDK to {recipient}. Response: {response}")
            
        except Exception as e:
            # Catches network timeouts, missing token variables, or unverified domain restrictions
            print(f"Failed to deliver email via Mailtrap SDK background task: {e}")

