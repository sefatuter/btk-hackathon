from datetime import timedelta
import json
from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, session
from flask_login import login_required, login_user, logout_user, UserMixin, LoginManager, current_user
from forms import RegistrationForm, LoginForm
from models import db, bcrypt, User, ChatHistory
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

@app.route('/dashboard/student', methods=['GET', 'POST'])
@login_required
def student_dashboard():
    if request.method == 'POST':
        prompt = request.form.get('user_question')
        
        user_message = ChatHistory(sender='user', text=prompt)
        db.session.add(user_message)

        response_text = generate_text(prompt)
        ai_message = ChatHistory(sender='ai', text=response_text)
        db.session.add(ai_message)

        db.session.commit()

        if request.is_json:
            return jsonify({'user_message': prompt, 'ai_message': response_text})

    history = ChatHistory.query.order_by(ChatHistory.timestamp).all()
    last_messages = ChatHistory.query.order_by(ChatHistory.timestamp.desc()).limit(1).all()
    
    # Convert the last messages to JSON
    last_conversation_json = [
        {'sender': message.sender, 'text': message.text, 'timestamp': message.timestamp.isoformat()}
        for message in reversed(last_messages)  # Reverse to maintain chronological order
    ]
    
    # if last_conversation_json:
        # last_text = last_conversation_json[0]['text']
        # json_gemini = ask_gemini_auto(last_text + ' convert it to json in format : "course_code": "..", "course_name": "...", "description": "..." only.')

        # Clear json_gemini answer
        # json_text_cleaned = json_gemini.replace('```json\n', '').replace('```', '').strip()
        # json_data = json.loads(json_text_cleaned)
        # json_data_list = []
        # json_data_list.append(json_data)
        
        # json_data_list = list(json_data.values())

        # print(json_data_list)

    # else:
        # json_gemini = ''
    
    return render_template('student_dashboard.html', history=history, last_conversation_json=last_conversation_json) # json_gemini=json_gemini, json_to_table=json_data_list


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

def ask_gemini_auto(prompt):
    response_auto = model.generate_content(prompt).text
    # print(response_auto)
    return response_auto

# Get data from JSON file
def process_json_data(raw_json):
    # Clear json_gemini answer
    json_text_cleaned = raw_json.replace('```json', '').replace('```', '').strip()
   
    try:
        # Handle possible line breaks and extra spaces
        json_text_cleaned = ' '.join(json_text_cleaned.split())
        print("Clean: " + json_text_cleaned)
        json_data = json.loads(json_text_cleaned)
        json_data_list = [json_data]
        print(json_data_list)
        return json_data_list
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
  system_instruction='Tüm yanıtlarını ders bilgileri için belirlediğim özel JSON formatında ver. Bu format dışında hiçbir bilgi ekleme ve sadece istenilen JSON objesini döndür. Sorulan her dersle ilgili bilgiyi aşağıdaki formata uygun şekilde cevapla: { "course_code": "<Bu alana dersin kodunu yazın>", "course_name": "<Bu alana dersin adını yazın,>", "description": "<Bu alana dersin içeriğini ve amacını açıklayan bir paragraf yazın." }'
  )

# Create tables if not exists
with app.app_context():
    db.create_all()
    
if __name__ == "__main__":
    app.run(debug=True)