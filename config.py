import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'mysecretkey')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', "postgresql://postgres:sql1234@localhost:5432/eduaidb")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
# Database configs
# Database name eduaidb
# User name postgres
# port 5432