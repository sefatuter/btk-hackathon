from datetime import timedelta
import json
from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, session
from flask_login import login_required, login_user, logout_user, UserMixin, LoginManager, current_user
from forms import RegistrationForm, LoginForm
from models import db, bcrypt, User, ChatHistory, CourseInfo, Course, Topic, Subtopic, Quiz, SubtopicQuiz
from dotenv import load_dotenv
import requests
import os
import google.generativeai as genai


load_dotenv()
app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)
bcrypt.init_app(app)
app.permanent_session_lifetime = timedelta(days=1)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# AI Configuration
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

@app.route('/generate_topic_quiz/<int:topic_id>', methods=['POST'])
@login_required
def generate_topic_quiz(topic_id):
    try:
        topic = Topic.query.get_or_404(topic_id)
        
        subtopics_text = ", ".join([st.subtopic_name for st in topic.subtopics])
        prompt = f"Generate 10 multiple choice questions about {topic.topic_name}. Include topics: {subtopics_text}."
        
        response = generate_text(prompt, model=model3)
        questions_data = process_json_data(response)
        
        if questions_data and 'questions' in questions_data:
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
        
        flash('Failed to generate quiz questions.', 'danger')
        return redirect(url_for('list_course', course_id=topic.course_id))
        
    except Exception as e:
        print(f"Error in generate_topic_quiz: {str(e)}")
        flash('An error occurred while generating the quiz.', 'danger')
        return redirect(url_for('student_dashboard'))

@app.route('/take_topic_quiz/<int:topic_id>')
@login_required
def take_topic_quiz(topic_id):
    try:
        topic = Topic.query.get_or_404(topic_id)
        questions = Quiz.query.filter_by(topic_id=topic_id).all()
        
        if not questions:
            flash('No quiz questions available for this topic.', 'warning')
            return redirect(url_for('list_course', course_id=topic.course_id))
            
        return render_template('quiz.html', topic=topic, questions=questions, is_subtopic_quiz=False)
        
    except Exception as e:
        print(f"Error in take_topic_quiz: {str(e)}")
        flash('An error occurred while loading the quiz.', 'danger')
        return redirect(url_for('student_dashboard'))

@app.route('/generate_subtopic_quiz/<int:subtopic_id>', methods=['POST'])
@login_required
def generate_subtopic_quiz(subtopic_id):
    try:
        print(f"Starting generate_subtopic_quiz for subtopic_id: {subtopic_id}")
        
        subtopic = Subtopic.query.get_or_404(subtopic_id)
        print(f"Found subtopic: {subtopic.subtopic_name}")
        
        topic = Topic.query.get(subtopic.topic_id)
        print(f"Found topic: {topic.topic_name}")
        
        prompt = f"Generate 5 multiple choice questions specifically about {subtopic.subtopic_name}, which is a subtopic of {topic.topic_name}."
        
        response = generate_text(prompt, model=model3)
        print(f"Got Gemini response: {response[:100]}...")
        
        questions_data = process_json_data(response)
        print(f"Processed questions data: {questions_data is not None}")
        
        if questions_data and 'questions' in questions_data:
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
            print("Successfully saved quiz questions")
            
            return redirect(url_for('take_subtopic_quiz', subtopic_id=subtopic_id))
        
        print("Failed to generate or process questions")
        flash('Failed to generate quiz questions.', 'danger')
        return redirect(url_for('list_course', course_id=topic.course_id))
        
    except Exception as e:
        print(f"Error in generate_subtopic_quiz: {str(e)}")
        flash('An error occurred while generating the quiz.', 'danger')
        return redirect(url_for('student_dashboard'))

@app.route('/take_subtopic_quiz/<int:subtopic_id>')
@login_required
def take_subtopic_quiz(subtopic_id):
    try:
        subtopic = Subtopic.query.get_or_404(subtopic_id)
        topic = Topic.query.get(subtopic.topic_id)
        questions = SubtopicQuiz.query.filter_by(subtopic_id=subtopic_id).all()
        
        if not questions:
            flash('No quiz questions available for this subtopic.', 'warning')
            return redirect(url_for('list_course', course_id=topic.course_id))
            
        return render_template('quiz.html', topic=topic, subtopic=subtopic, questions=questions, is_subtopic_quiz=True)
        
    except Exception as e:
        print(f"Error in take_subtopic_quiz: {str(e)}")
        flash('An error occurred while loading the quiz.', 'danger')
        return redirect(url_for('student_dashboard'))

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

@app.route('/delete_course/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    course = CourseInfo.query.get(course_id)
    
    if course:
        ChatHistory.query.filter_by(course_id=course.id).delete()
        db.session.delete(course)
        db.session.commit()
        print('Course Deleted Successfully.')
    else:
        print('Course not found!')

    return redirect(url_for('student_dashboard'))

@app.route('/list_course/<int:course_id>', methods=['POST'])
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

# AI section
def generate_text(prompt, model):
    recent_history = ChatHistory.query.order_by(ChatHistory.timestamp.desc()).limit(5).all()
    recent_history.reverse()
    
    conversation_context = ""
    for message in recent_history:
        conversation_context += f"{message.sender.capitalize()}: {message.text}\n"

    conversation_context += f"User: {prompt}\nAI:"
    
    
    # system_instruction = get_system_instruction(name)
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


# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

# Course Model
model1 = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
  system_instruction='Tüm yanıtlarını ders bilgileri için belirlediğim özel JSON formatında ver. Bu format dışında hiçbir bilgi ekleme ve sadece istenilen JSON objesini döndür. Sorulan her dersle ilgili bilgiyi aşağıdaki formata uygun şekilde cevapla: { "course_code": "<Bu alana dersin kodunu yazın>", "course_name": "<Bu alana dersin adını yazın>", "description": "<Bu alana dersin içeriğini ve amacını açıklayan bir paragraf yazın." }. Eğer sorulan soru ders bilgileriyle alakasızsa, boş bir JSON objesi döndür.' 
)

# Listing Model
model2 = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
  system_instruction='''Tüm yanıtlarını ders bilgileri için belirlediğim özel JSON formatında ver. Bu format dışında hiçbir bilgi ekleme ve sadece istenilen JSON objesini döndür. Sorulan her dersle ilgili bilgiyi aşağıdaki formata uygun şekilde cevapla:
    {
    "course_code": "<Dersin kodunu buraya yazın>",
    "course_name": "<Dersin adını buraya yazın>",
    "topics": [
        {
        "name": "<Ana konu başlığını buraya yazın>",
        "subtopics": [
            "<Alt konu başlığı 1>",
            "<Alt konu başlığı 2>",
            "<Alt konu başlığı 3>",
            "..."
        ]
        },
        ...
    ]
    }'''  
)

# Quiz Model
model3 = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction='''Generate quiz questions in the following JSON format only:
    {
        "questions": [
            {
                "question": "Clear, concise question text",
                "options": [
                    "A) First option",
                    "B) Second option",
                    "C) Third option",
                    "D) Fourth option"
                ],
                "correct": "A"
            }
        ]
    }
    Generate challenging but fair questions that test understanding of the topic.
    Each question should have exactly 4 options.
    Make sure the correct answer is clearly marked with A, B, C, or D.
    Do not include any additional text or explanations outside the JSON structure.'''
)

# Create tables if not exists
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

# Normal Student Talk AI Model
model4 = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
  system_instruction='''Üniversite öğrencilerine derslerinde yardımcı olacak bir yapay zeka olarak amacın, öğrencilere ders çalışmaları, ödev hazırlıkları, sınavlara hazırlık süreçleri ve genel akademik başarılarında destek sağlamak, sorularına yanıt vermek ve gerektiğinde onları araştırmaya yönlendirmektir. Öğrencilere sunacağın yanıtlar net, anlaşılır ve detaylı olmalı; karmaşık konuları basit ve kolay anlaşılır bir dilde açıklamalı, gerektiğinde örnekler ve adım adım çözüm süreçleriyle desteklemelisin. Konulara dair sunacağın özetler, önemli noktaları vurgulamalı ve öğrencilerin konuları daha iyi anlamasına yardımcı olmalı. Öğrencinin sorularını yanıtlarken konunun temellerini anlatarak adım adım çözüm sürecini izah et; ayrıca, karmaşık bir sorunun çözümünü farklı seviyelerde (basitten karmaşığa) açıklayarak öğrencinin anlamasına yardımcı ol. Öğrencinin ödev ve projelerine yönelik rehberlik yaparken, gerekli adımları belirle, araştırma yapmaları için kaynak önerilerinde bulun ve çözüm sürecinde destek sağla. Öğrenciye doğrudan ödevi çözmek yerine, onu yönlendiren, araştırmaya teşvik eden bir rehber olmalısın. Ayrıca, sınav hazırlığı için haftalık ya da günlük çalışma planları önererek öğrencinin düzenli bir çalışma sistemi geliştirmesine yardımcı olmalı, konu bazlı test soruları hazırlayarak ona pratik yapma imkanı sunmalısın. Testler sonrası öğrencinin eksik kaldığı alanları belirten açıklamalar sağlayarak eksikliklerini gidermesini kolaylaştırmalısın. Öğrencilerin zaman yönetimi ve verimli çalışma alışkanlıklarını geliştirebilmeleri için bireysel çalışma saatleri ve mola düzenlemeleri öner; Pomodoro gibi teknikler önererek onların verimli çalışma stratejileri geliştirmelerini destekle. Ayrıca, akademik konular için güvenilir kaynaklar önererek, araştırma yapma yeteneklerini geliştirmelerine katkı sağla. Kaynak ve kitap önerileri sunarak, öğrencilerin belirli konuları daha derinlemesine incelemelerine yardımcı ol, böylece doğru bilgiye erişmelerine katkı sağla. Yanıtlarında net ve pozitif bir dil kullan, onları soru sormaya, araştırmaya ve öğrenmeye teşvik et. Tüm bu görevlerde öğrencilere destekleyici ve motive edici bir yaklaşımla rehberlik et, başarılarını takdir ederek öğrenme süreçlerinde onları destekle. Öğrencinin akademik gelişimini takip et, anlamadığı veya daha fazla bilgiye ihtiyaç duyduğu alanları belirle ve gelişimlerine göre özel öneriler sun. Öğrencinin belirli bir derse veya konuya dair daha fazla çalışması gerektiğinde, onun için ek kaynaklar ve pratik materyaller önererek ilerleyişine katkıda bulun.'''  
)

# Create tables if not exists
with app.app_context():
    db.create_all()
    
if __name__ == "__main__":
    app.run(debug=True)


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