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

class Course(db.Model):
    # name = ''
    # def __init__(self, name, code, topics):
    #     self.name = name
    #     self.code = code
    #     self.topics = topics
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(10), nullable=False)
    course_name = db.Column(db.String,nullable = False)
    topics = db.relationship('Topic',backref='course', lazy=True, cascade="all, delete-orphan")
# class Course():
#     name = ''
#     code = ''
#     topics = []
#     def __init__(self, name, code, topics):
#         self.name = name
#         self.code = code
#         self.topics = topics

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(50), nullable = False)
    subtopics = db.relationship('Subtopic', backref='topic',lazy = True, cascade="all, delete-orphan")
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
class Subtopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subtopic_name= db.Column(db.String(50),nullable = False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)

# class Quiz(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     step_id = db.Column(db.Integer, db.ForeignKey('curriculum.id'))
#     questions = db.Column(db.JSON)
    
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'ai'
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)