import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# config.py
class Config:    
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')  # Set this in .env
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')     # Set this in .env
    
    
