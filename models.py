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
    course_name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    course = db.relationship('Course',backref='course_info',lazy=True,cascade="all, delete-orphan")

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(50), nullable=False)
    course_name = db.Column(db.Text,nullable = False)
    topics = db.relationship('Topic',backref='course', lazy=True, cascade="all, delete-orphan")
    course_info_id = db.Column(db.Integer,db.ForeignKey('course_info.id'), nullable = False)

class Topic(db.Model):
    __tablename__ = 'topic'
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.Text, nullable = False)
    subtopics = db.relationship('Subtopic', backref='topic',lazy = True, cascade="all, delete-orphan")
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
class Subtopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subtopic_name= db.Column(db.Text,nullable = False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)

class SubtopicQuiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subtopic_id = db.Column(db.Integer, db.ForeignKey('subtopic.id'), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    
    subtopic = db.relationship('Subtopic', backref='quizzes')

class Note(db.Model):
    __tablename__ = 'note'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    subtopic_id = db.Column(db.Integer, db.ForeignKey('subtopic.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    course = db.relationship('Course', backref='notes')
    topic = db.relationship('Topic', backref='notes')
    subtopic = db.relationship('Subtopic', backref='notes')
