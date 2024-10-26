from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # Either 'student' or 'teacher'

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

# class Curriculum(db.Model):
#     __tablename__ = 'curriculum'
#     id = db.Column(db.Integer, primary_key=True)
#     step_name = db.Column(db.String(255), nullable=False)
#     sub_steps = db.Column(db.JSON)
#     multimedia_content = db.Column(db.JSON)
    
# class Quiz(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     step_id = db.Column(db.Integer, db.ForeignKey('curriculum.id'))
#     questions = db.Column(db.JSON)
    
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'ai'
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)