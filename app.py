from datetime import timedelta
import json
from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, session
from flask_login import login_required, login_user, logout_user, UserMixin, LoginManager, current_user
from forms import RegistrationForm, LoginForm
from models import db, bcrypt, User, ChatHistory, CourseInfo, Course, Topic, Subtopic, Quiz, SubtopicQuiz, Note
from dotenv import load_dotenv
import requests
import os
import google.generativeai as genai
from gemini import generation_config, model1, model2, model3, model4, model5, model6
from markdown2 import Markdown
from markupsafe import Markup
import random

load_dotenv()
app = Flask(__name__)
login_manager = LoginManager()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

app.config.from_object('config.Config')
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
app.permanent_session_lifetime = timedelta(days=1)


@app.route('/')
def index():
    return redirect('/home')


@app.route('/home')
def home():
    # ... code
    return render_template('index.html')


@app.route('/base')
def base():
    # ... code        
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)  # Log the user in
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard'))  # Adjust redirection based on user role
        else:
            flash('Login failed. Check your email and password.', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login')) 

@app.route('/delete_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def delete_course(course_id):
    try:
        course_info = CourseInfo.query.get(course_id)
        
        if course_info:
            # Get the associated course record
            course = Course.query.filter_by(course_info_id=course_id).first()
            
            if course:
                # Delete all associated records in the correct order
                for topic in course.topics:
                    # Delete quizzes associated with the topic
                    Quiz.query.filter_by(topic_id=topic.id).delete()
                    
                    # Delete subtopic quizzes
                    for subtopic in topic.subtopics:
                        SubtopicQuiz.query.filter_by(subtopic_id=subtopic.id).delete()
                        
                        # Delete notes associated with subtopics
                        Note.query.filter_by(topic_id=topic.id).delete()
                        
                        # Delete the subtopic
                        db.session.delete(subtopic)
                    
                    # Delete the topic
                    db.session.delete(topic)
                
                # Delete the course
                db.session.delete(course)
            
            # Delete chat history
            ChatHistory.query.filter_by(course_id=course_info.id).delete()
            
            # Delete the course info
            db.session.delete(course_info)
            
            # Commit all changes
            db.session.commit()
            flash('Course and all related data deleted successfully.', 'success')
        else:
            flash('Course not found!', 'error')

    except Exception as e:
        db.session.rollback()
        print(f'Error deleting course: {str(e)}')
        flash('An error occurred while deleting the course.', 'error')
    
    return redirect(url_for('student_dashboard'))

@app.route('/list_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def list_course(course_id):
    # Retrieve AI message for the course
    ai_messages = ChatHistory.query.filter_by(course_id=course_id, sender="ai").all()
    
    if ai_messages:
        # Use the latest AI message text to generate data
        latest_ai_message = ai_messages[-1]
        chat_data = {
            'sender': latest_ai_message.sender,
            'text': latest_ai_message.text,
            'timestamp': latest_ai_message.timestamp.isoformat()
        }
        
        # Generate or fetch the course data and save it if necessary
        course = table(process_json_data(chat_data['text']), course_id=course_id)
        
        # Verify course was saved/retrieved successfully
        if course:
            return render_template('list_course.html', course=course)
        else:
            return jsonify({"error": "Failed to save or retrieve course data"}), 500
    else:
        return jsonify({"error": "No AI messages found for this course"}), 404

def table(raw_data, course_id):
    # Check if the course already exists based on `course_id`
    existing_course = Course.query.filter(Course.course_info.has(CourseInfo.id == course_id)).first()
    if not existing_course:
        # Generate and process the raw data
        data = generate_text(raw_data, model=model2)
        data = process_json_data(data)
        
        # Create a new Course object
        course = Course(course_name=data['course_name'], course_code=data['course_code'], course_info_id=course_id)
        
        # Add topics and subtopics
        for topic_data in data['topics']:
            topic = Topic(topic_name=topic_data['name'])
            for subtopic_name in topic_data['subtopics']:
                subtopic = Subtopic(subtopic_name=subtopic_name)
                topic.subtopics.append(subtopic)
            
            course.topics.append(topic)
        
        try:
            db.session.add(course)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error saving data: {e}")
            return None

    # Return the course data, whether it was newly created or already existing
    return existing_course or course

@app.route('/dashboard/student', methods=['GET', 'POST'])
@login_required
def student_dashboard():
    if request.method == 'POST':
        prompt = request.form.get('user_question')
        response_text = generate_text(prompt, model=model1)
        if response_text:
            # If json data is returns empty
            if process_json_data(response_text) == {}:
                invalid_ans = True
            else:
                ai_json_response = process_json_data(response_text)
                existing_course = CourseInfo.query.filter_by(course_code=ai_json_response['course_code']).first()
                if not existing_course:
                    course_info = CourseInfo(
                        course_code=ai_json_response['course_code'],
                        course_name=ai_json_response['course_name'],
                        description=ai_json_response['description']
                    )
                    db.session.add(course_info)                
                    db.session.commit()
                    
                    user_message = ChatHistory(
                        sender='user', 
                        course_id=course_info.id, 
                        text=prompt)
                    db.session.add(user_message)
                    db.session.commit()
                    chat_history_entry = ChatHistory(
                    course_id=course_info.id,  # Use the newly assigned ID from CourseInfo
                    sender='ai',
                    text=response_text
                    )
                    db.session.add(chat_history_entry)
                    db.session.commit()

    courses= CourseInfo.query.all()
    
    historyAI = ChatHistory.query.filter_by(sender='ai').order_by(ChatHistory.timestamp).all()
    historyUser = ChatHistory.query.filter_by(sender='user').order_by(ChatHistory.timestamp).all()
   
           
    return render_template('student_dashboard.html', historyUser=historyUser, historyAI=historyAI, json_to_table=courses)

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'POST':
        data = request.get_json()
        user_message = data.get('message')
        
        # Generate response using model3
        ai_response = generate_text(user_message, model=model4)
        
        return jsonify({'response': ai_response})
    
    return render_template('chat_ai.html')

@app.route('/generate_topic_quiz/<int:topic_id>', methods=['POST', 'GET'])
@login_required
def generate_topic_quiz(topic_id):
    try:
        # Check if quiz alread  y exists
        existing_quiz = Quiz.query.filter_by(topic_id=topic_id).first()
        session_key = f'quiz_topic_{topic_id}'
        
        if existing_quiz or session.get(session_key):
            return redirect(url_for('take_topic_quiz', topic_id=topic_id))
        
        topic = Topic.query.get_or_404(topic_id)
        
        # Create a more generic prompt
        prompt = f"""Please create 10 multiple choice questions in JSON format about {topic.topic_name}. 
        Focus on fundamental concepts and general understanding.
        Each question should have 4 options (A, B, C, D) and indicate the correct answer.
        
        The response should be in this exact JSON format:
        {{
            "questions": [
                {{
                    "question": "What is...",
                    "options": [
                        "A) First option",
                        "B) Second option",
                        "C) Third option",
                        "D) Fourth option"
                    ],
                    "correct": "A"
                }},
                ...
            ]
        }}"""
        
        try:
            response = generate_text(prompt, model=model3)
            questions_data = process_json_data(response)
            
            if not questions_data or 'questions' not in questions_data:
                # Fallback to simplified prompt if first attempt fails
                fallback_prompt = f"""Create 10 basic multiple choice questions about {topic.topic_name}.
                Focus only on fundamental concepts. Return in JSON format with question, options, and correct answer."""
                
                response = generate_text(fallback_prompt, model=model3)
                questions_data = process_json_data(response)
            
            # Randomize the answers
            questions_data = process_and_randomize_quiz(questions_data)
            
            if questions_data and 'questions' in questions_data:
                # Delete any existing quiz
                Quiz.query.filter_by(topic_id=topic_id).delete()
                
                for q_data in questions_data['questions']:
                    quiz = Quiz(
                        topic_id=topic_id,
                        question=q_data['question'],
                        option_a=q_data['options'][0][3:],
                        option_b=q_data['options'][1][3:],
                        option_c=q_data['options'][2][3:],
                        option_d=q_data['options'][3][3:],
                        correct_answer=q_data['correct']
                    )
                    db.session.add(quiz)
                
                db.session.commit()
                flash('Quiz generated successfully!', 'success')
                return redirect(url_for('take_topic_quiz', topic_id=topic_id))
            
            flash('Unable to generate quiz questions. Please try again.', 'warning')
            return redirect(url_for('list_course', course_id=topic.course.course_info.id))
            
        except Exception as e:
            print(f"Generation error: {str(e)}")
            db.session.rollback()
            flash('Error generating quiz questions. Please try again.', 'danger')
            return redirect(url_for('list_course', course_id=topic.course.course_info.id))
            
    except Exception as e:
        print(f"Error in generate_topic_quiz: {str(e)}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('student_dashboard'))

@app.route('/take_topic_quiz/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def take_topic_quiz(topic_id):
    try:
        topic = Topic.query.get_or_404(topic_id)
        
        # Try to get existing quiz from session
        session_key = f'quiz_topic_{topic_id}'
        questions = session.get(session_key)
        
        if not questions:
            # If no quiz in session, get from database
            questions = Quiz.query.filter_by(topic_id=topic_id).all()
            
            if not questions:
                flash('No quiz questions available for this topic.', 'warning')
                return redirect(url_for('list_course', course_id=topic.course.course_info.id))
            
            # Store questions in session
            session[session_key] = [
                {
                    'id': q.id,
                    'question': q.question,
                    'option_a': q.option_a,
                    'option_b': q.option_b,
                    'option_c': q.option_c,
                    'option_d': q.option_d,
                    'correct_answer': q.correct_answer
                }
                for q in questions
            ]
            
        return render_template('quiz.html', topic=topic, questions=questions, is_subtopic_quiz=False)
        
    except Exception as e:
        print(f"Error in take_topic_quiz: {str(e)}")
        flash('An error occurred while loading the quiz.', 'danger')
        return redirect(url_for('student_dashboard'))

@app.route('/generate_subtopic_quiz/<int:subtopic_id>', methods=['POST', 'GET'])
@login_required
def generate_subtopic_quiz(subtopic_id):
    try:
        session_key = f'quiz_subtopic_{subtopic_id}'
        existing_quiz = SubtopicQuiz.query.filter_by(subtopic_id=subtopic_id).first()
        
        if existing_quiz or session.get(session_key):
            return redirect(url_for('take_subtopic_quiz', subtopic_id=subtopic_id))
        
        subtopic = Subtopic.query.get_or_404(subtopic_id)
        topic = Topic.query.get(subtopic.topic_id)
        
        prompt = f"""Create 5 multiple choice questions in JSON format about {subtopic.subtopic_name}.
        Focus on testing understanding of basic concepts related to this specific subtopic.
        Each question should have 4 options (A, B, C, D) and indicate the correct answer.
        
        The response should be in this exact JSON format:
        {{
            "questions": [
                {{
                    "question": "What is...",
                    "options": [
                        "A) First option",
                        "B) Second option",
                        "C) Third option",
                        "D) Fourth option"
                    ],
                    "correct": "A"
                }},
                ...
            ]
        }}"""
        
        try:
            response = generate_text(prompt, model=model3)
            questions_data = process_json_data(response)
            
            if not questions_data or 'questions' not in questions_data:
                fallback_prompt = f"""Generate 5 basic multiple choice questions about {subtopic.subtopic_name}.
                Focus on fundamental concepts only. Return in JSON format with question, options, and correct answer."""
                
                response = generate_text(fallback_prompt, model=model3)
                questions_data = process_json_data(response)
            
            # Randomize the answers
            questions_data = process_and_randomize_quiz(questions_data)
            
            if questions_data and 'questions' in questions_data:
                # Delete existing quiz if it exists
                SubtopicQuiz.query.filter_by(subtopic_id=subtopic_id).delete()
                
                for q_data in questions_data['questions']:
                    quiz = SubtopicQuiz(
                        subtopic_id=subtopic_id,
                        question=q_data['question'],
                        option_a=q_data['options'][0][3:],
                        option_b=q_data['options'][1][3:],
                        option_c=q_data['options'][2][3:],
                        option_d=q_data['options'][3][3:],
                        correct_answer=q_data['correct']
                    )
                    db.session.add(quiz)
                
                db.session.commit()
                
                # Clear the session key to force fresh load
                if session_key in session:
                    session.pop(session_key)
                    
                flash('Quiz generated successfully!', 'success')
                return redirect(url_for('take_subtopic_quiz', subtopic_id=subtopic_id))
            
            flash('Unable to generate quiz questions. Please try again.', 'warning')
            return redirect(url_for('list_course', course_id=topic.course.course_info.id))
            
        except Exception as e:
            print(f"Generation error: {str(e)}")
            db.session.rollback()
            flash('Error generating quiz questions. Please try again.', 'danger')
            return redirect(url_for('list_course', course_id=topic.course.course_info.id))
            
    except Exception as e:
        print(f"Error in generate_subtopic_quiz: {str(e)}")
        return redirect(url_for('student_dashboard'))

@app.route('/take_subtopic_quiz/<int:subtopic_id>')
@login_required
def take_subtopic_quiz(subtopic_id):
    try:
        subtopic = Subtopic.query.get_or_404(subtopic_id)
        topic = Topic.query.get(subtopic.topic_id)
        
        # Try to get existing quiz from session
        session_key = f'quiz_subtopic_{subtopic_id}'
        questions = session.get(session_key)
        
        if not questions:
            # If no quiz in session, get from database
            questions = SubtopicQuiz.query.filter_by(subtopic_id=subtopic_id).all()
            
            if not questions:
                flash('No quiz questions available for this subtopic.', 'warning')
                return redirect(url_for('list_course', course_id=topic.course.course_info.id))
            
            # Store questions in session
            session[session_key] = [
                {
                    'id': q.id,
                    'question': q.question,
                    'option_a': q.option_a,
                    'option_b': q.option_b,
                    'option_c': q.option_c,
                    'option_d': q.option_d,
                    'correct_answer': q.correct_answer
                }
                for q in questions
            ]
            
        return render_template('quiz.html', topic=topic, subtopic=subtopic, questions=questions, is_subtopic_quiz=True)
        
    except Exception as e:
        print(f"Error in take_subtopic_quiz: {str(e)}")
        flash('An error occurred while loading the quiz.', 'danger')
        return redirect(url_for('student_dashboard'))

def process_and_randomize_quiz(questions_data):
    """Helper function to process quiz data and randomize answers"""
    if not questions_data or 'questions' not in questions_data:
        return None
        
    for question in questions_data['questions']:
        # Get the correct answer's content
        correct_option = question['options'][ord(question['correct']) - ord('A')]
        
        # Randomly shuffle the options
        random.shuffle(question['options'])
        
        # Find the new position of the correct answer
        for i, option in enumerate(question['options']):
            if option == correct_option:
                question['correct'] = chr(ord('A') + i)
                break
    
    return questions_data

@app.route('/check_answer', methods=['POST'])
@login_required
def check_answer():
    question_id = request.form.get('question_id')
    selected_answer = request.form.get('answer')
    quiz_type = request.form.get('quiz_type', 'topic')
    
    if quiz_type == 'subtopic':
        question = SubtopicQuiz.query.get_or_404(question_id)
    else:
        question = Quiz.query.get_or_404(question_id)
        
    is_correct = question.correct_answer == selected_answer
    
    return jsonify({
        'correct': is_correct,
        'correct_answer': question.correct_answer
    })
    
@app.route('/retake_quiz/<int:topic_id>', methods=['POST'])
@login_required
def retake_quiz(topic_id):
    try:
        is_subtopic = request.args.get('is_subtopic', 'false') == 'true'
        subtopic_id = request.args.get('subtopic_id', None)
        
        # Clear any stored answers/state
        if is_subtopic:
            session_key = f'quiz_subtopic_{subtopic_id}'
            session.pop(session_key, None)
            return redirect(url_for('take_subtopic_quiz', subtopic_id=subtopic_id))
        else:
            session_key = f'quiz_topic_{topic_id}'
            session.pop(session_key, None)
            return redirect(url_for('take_topic_quiz', topic_id=topic_id))
            
    except Exception as e:
        print(f"Error in retake_quiz: {str(e)}")
        flash('An error occurred while retaking the quiz.', 'danger')
        return redirect(url_for('student_dashboard'))

@app.route('/recreate_quiz/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def recreate_quiz(topic_id):
    try:
        is_subtopic = request.args.get('is_subtopic') == 'true'
        subtopic_id = request.args.get('subtopic_id')
        
        if is_subtopic:
            # Delete existing subtopic quiz
            SubtopicQuiz.query.filter_by(subtopic_id=subtopic_id).delete()
            session_key = f'quiz_subtopic_{subtopic_id}'
            if session_key in session:
                session.pop(session_key)
            db.session.commit()
            
            # Generate new subtopic quiz
            return redirect(url_for('generate_subtopic_quiz', subtopic_id=subtopic_id))
        else:
            # Delete existing topic quiz
            Quiz.query.filter_by(topic_id=topic_id).delete()
            session_key = f'quiz_topic_{topic_id}'
            if session_key in session:
                session.pop(session_key)
            db.session.commit()
            
            # Generate new topic quiz
            return redirect(url_for('generate_topic_quiz', topic_id=topic_id))
            
    except Exception as e:
        print(f"Error in recreate_quiz: {str(e)}")
        db.session.rollback()
        flash('An error occurred while recreating the quiz.', 'danger')
        return redirect(url_for('student_dashboard'))
    
  
@app.route('/create_note/<int:course_id>', methods=['GET', 'POST'])
def create_note(course_id):
    try:
        # First get the CourseInfo
        course_info = CourseInfo.query.get(course_id)
        if course_info is None:
            flash('Course not found!', 'error')
            return redirect(url_for('student_dashboard'))
        
        # Create markdown converter with math support
        markdowner = Markdown(extras={
            'fenced-code-blocks': None,
            'tables': None,
            'break-on-newline': True,
            'header-ids': None,
            'markdown-in-html': True,
            'math': None
        })

        # Then get the associated Course
        course = Course.query.filter_by(course_info_id=course_id).first()
        if course is None:
            flash('Course details not found!', 'error')
            return redirect(url_for('student_dashboard'))

        # Prepare topics and subtopics data
        topics_with_subtopics = [
            {
                "topic_name": topic.topic_name,
                "subtopics": [subtopic.subtopic_name for subtopic in topic.subtopics]
            }
            for topic in course.topics
        ]
        
        # Form data handling
        selected_topic = request.form.get('topic')
        selected_subtopic = request.form.get('subtopic')
        subtopics = []
        lecture_note = None

        if selected_topic:
            topic = next((t for t in course.topics if t.topic_name == selected_topic), None)
            if topic:
                subtopics = [subtopic.subtopic_name for subtopic in topic.subtopics]

                if selected_subtopic:
                    subtopic = next((s for s in topic.subtopics if s.subtopic_name == selected_subtopic), None)

                    if subtopic:
                        # Check if the note already exists
                        existing_note = Note.query.filter_by(
                            course_id=course.id,  # Use course.id instead of course_id
                            topic_id=topic.id,
                            subtopic_id=subtopic.id
                        ).first()

                        if existing_note:
                            # Use the existing note
                            lecture_note = existing_note.content
                        else:
                            try:
                                # Generate a new note if it doesn't exist
                                prompt = f"{selected_topic} - {selected_subtopic} hakkında ders notu istiyorum."
                                lecture_note = generate_text(prompt, model=model5)
                                
                                # Convert markdown to HTML
                                html_content = markdowner.convert(lecture_note)
                                
                                # Make it safe for rendering
                                lecture_note = Markup(html_content)
                                                            
                                # Save the generated note to the database
                                new_note = Note(
                                    content=lecture_note,
                                    course_id=course.id,  # Use course.id instead of course_id
                                    topic_id=topic.id,
                                    subtopic_id=subtopic.id
                                )
                                db.session.add(new_note)
                                db.session.commit()
                                flash('Note created successfully!', 'success')
                            except Exception as e:
                                db.session.rollback()
                                flash(f'Error creating note: {str(e)}', 'error')
                                return redirect(url_for('create_note', course_id=course_id))

        
        # Render the template with generated note content
        return render_template(
            "create_note.html",
            course_id=course_id,
            course_name=course_info.course_name,
            topics_with_subtopics=topics_with_subtopics,
            selected_topic=selected_topic,
            subtopics=subtopics,
            note_content=lecture_note
        )

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('student_dashboard'))


# to be continued..
def generate_explanation_prompt(question, options):
    """Generate a comprehensive prompt for the AI explanation"""
    return f"""Explain this multiple choice question in detail:

Question: {question}

Options:
A) {options['A']}
B) {options['B']}
C) {options['C']}
D) {options['D']}

Please provide:
1. A detailed explanation of the correct answer
2. Why other options are incorrect
3. Key concepts and points to remember"""

@app.route('/api/get_explanation/<int:question_id>', methods=['GET'])
def get_explanation(question_id):
    try:
        # Fetch question from database
        question = Quiz.query.get_or_404(question_id)
        
        # Create options dictionary
        options = {
            'A': question.option_a,
            'B': question.option_b,
            'C': question.option_c,
            'D': question.option_d
        }
        
        # Generate prompt for AI
        prompt = generate_explanation_prompt(question.question, options)
        
        # Get explanation from AI using existing generate_text function
        explanation = generate_text(prompt, model6)
        
        return jsonify({
            'success': True,
            'explanation': explanation
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# AI section

def generate_text(prompt, model):
    recent_history = ChatHistory.query.order_by(ChatHistory.timestamp.desc()).limit(5).all()
    recent_history.reverse()
    
    conversation_context = ""
    for message in recent_history:
        conversation_context += f"{message.sender.capitalize()}: {message.text}\n"

    conversation_context += f"User: {prompt}\nAI:"
    
    response = model.generate_content(conversation_context)
    model.generate_content
    return response.text


# Get data from JSON file
def process_json_data(raw_json):
    json_text_cleaned = raw_json.replace('```json', '').replace('```', '').strip()
   
    try:
        json_text_cleaned = ' '.join(json_text_cleaned.split())
        json_data = json.loads(json_text_cleaned)
        return json_data
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Cleaned text was: {json_text_cleaned}")
        return None


# Create tables if not exists
with app.app_context():
    db.create_all()
    
if __name__ == "__main__":
    app.run(debug=True)