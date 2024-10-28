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
    
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course_info.id', ondelete='CASCADE'))  # Link to CourseInfo
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'ai'
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
class CourseInfo(db.Model):
    __tablename__ = 'course_info'
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(50), nullable=False)
    course_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    course = db.relationship('Course',backref='course_info',lazy=True,cascade="all, delete-orphan")

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(10), nullable=False)
    course_name = db.Column(db.String,nullable = False)
    topics = db.relationship('Topic',backref='course', lazy=True, cascade="all, delete-orphan")
    course_info_id = db.Column(db.Integer,db.ForeignKey('course_info.id'), nullable = False)

class Topic(db.Model):
    __tablename__ = 'topic'
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(50), nullable = False)
    subtopics = db.relationship('Subtopic', backref='topic',lazy = True, cascade="all, delete-orphan")
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
class Subtopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subtopic_name= db.Column(db.String(50),nullable = False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)

