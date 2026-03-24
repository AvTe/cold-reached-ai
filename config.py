import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///outreach.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email Signature
    EMAIL_SIGNATURE = os.getenv('EMAIL_SIGNATURE', 'Best regards,\n[Your Name]\n[Your Website]')
    
    # Hunter.io config
    HUNTER_API_KEY = os.getenv('HUNTER_API_KEY')
    
    # Gmail SMTP config
    GMAIL_USER = os.getenv('GMAIL_USER')
    GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
    
    # Send limits
    DAILY_EMAIL_LIMIT = int(os.getenv('DAILY_EMAIL_LIMIT', 30))
    DRY_RUN = os.getenv('DRY_RUN', 'True').lower() == 'true'
