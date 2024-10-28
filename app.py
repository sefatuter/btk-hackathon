from datetime import timedelta
import json
from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, session
from flask_login import login_required, login_user, logout_user, UserMixin, LoginManager, current_user
from forms import RegistrationForm, LoginForm
from models import db, bcrypt, User, ChatHistory, CourseInfo, Course, Topic, Subtopic
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
    # Query to get only the 'ai' messages for the given course_id
    ai_messages = ChatHistory.query.filter_by(course_id=course_id, sender="ai").all()
    
    if ai_messages:
        latest_ai_message = ai_messages[-1]
        chat_data = {
            'sender': latest_ai_message.sender,
            'text': latest_ai_message.text,
            'timestamp': latest_ai_message.timestamp.isoformat()
        }
        print('Course Listed Successfully.')
        new = table(process_json_data(chat_data['text']),course_id=course_id)
        print(new['course_name'])
        #print(process_json_data(chat_data['text']))
        return render_template('list_course.html',course=new)
        #print(process_json_data(chat_data['text']))
        #return jsonify(chat_data)
    else:
        print('Cannot Find This Course.')
        return jsonify({"error": "No AI messages found for this course"}), 404


@app.route('/dashboard/student', methods=['GET', 'POST'])
@login_required
def student_dashboard():
    if request.method == 'POST':
        prompt = request.form.get('user_question')
        response_text = generate_text(prompt)
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



# AI section
def generate_text(prompt):
    recent_history = ChatHistory.query.order_by(ChatHistory.timestamp.desc()).limit(5).all()
    recent_history.reverse()
    
    conversation_context = ""
    for message in recent_history:
        conversation_context += f"{message.sender.capitalize()}: {message.text}\n"

    conversation_context += f"User: {prompt}\nAI:"

    response = model.generate_content(conversation_context)
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

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
#   system_instruction='''Tüm yanıtlarını ders bilgileri için belirlediğim özel JSON formatında ver. Bu format dışında hiçbir bilgi ekleme ve sadece istenilen JSON objesini döndür. Sorulan her dersle ilgili bilgiyi aşağıdaki formata uygun şekilde cevapla:
# {
#   "course_code": "<Dersin kodunu buraya yazın>",
#   "course_name": "<Dersin adını buraya yazın>",
#   "topics": [
#     {
#       "name": "<Ana konu başlığını buraya yazın>",
#       "subtopics": [
#         "<Alt konu başlığı 1>",
#         "<Alt konu başlığı 2>",
#         "<Alt konu başlığı 3>",
#         "..."
#       ]
#     },
#     ...
#   ]
# }'''  
  system_instruction='Tüm yanıtlarını ders bilgileri için belirlediğim özel JSON formatında ver. Bu format dışında hiçbir bilgi ekleme ve sadece istenilen JSON objesini döndür. Sorulan her dersle ilgili bilgiyi aşağıdaki formata uygun şekilde cevapla: { "course_code": "<Bu alana dersin kodunu yazın>", "course_name": "<Bu alana dersin adını yazın>", "description": "<Bu alana dersin içeriğini ve amacını açıklayan bir paragraf yazın." }. Eğer sorulan soru ders bilgileriyle alakasızsa, boş bir JSON objesi döndür.' 
)

# Create tables if not exists
with app.app_context():
    db.create_all()
    
if __name__ == "__main__":
    app.run(debug=True)



# @app.route('/dashboard/student/table', methods=['GET'])
def table(raw_data, course_id):
    
    existing_course = Course.query.filter(Course.courseInfo.has(CourseInfo.id == course_id)).first()
    if not existing_course:
        data = generate_text(raw_data)
        data = process_json_data(data)

        course = Course(course_name = data['course_name'],course_code = data['course_code'])
        for topic_data in data['topics']:

            topic = Topic(topic_name=topic_data['name'])
            for subtopic_name in topic_data['subtopics']:
                subtopic=Subtopic(name=subtopic_name)
                topic.subtopics.append(subtopic)
            
            course.topics.append(topic)    
        try:
            db.session.add(course)
            db.session.commit()
            return data
        except:
            return None
   
    else:
        return existing_course
    #print(data)


