import google.generativeai as genai

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
  system_instruction='''
  Give all your responses in the custom JSON format I specified for the course information. 
  Do not add any information outside this format and return only the requested JSON object. 
  Answer the question about each course in the format below: 
  { 
  “course_code": “<Type the course code in this field>”, 
  “course_name": “<Type the name of the course in this field>”,
  “description": “<Write a paragraph in this field describing the content and purpose of the course.” 
  }.  
  If the question is irrelevant to the course information, return an empty JSON object.
  ''' 
)

# Listing Model
model2 = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
  system_instruction=''''Give all your answers in the special JSON format I have specified for the course information. 
  Do not add any information outside this format and return only the requested JSON object. 
  Answer the question about each course in the format below:
    {
    “course_code": “<Type course code here>”,
    “course_name": “<Type course name here>”,
    “topics": [
        {
        “name": “<Type the main topic title here>”,
        “subtopics": [
            “<Subtopic 1>”,
            “<Subtopic 2>”,
            “<Subtopic 3>”,
            “...”
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
    Do not include any additional text or explanations outside the JSON structure.
    '''
)


# Normal Student Talk AI Model
model4 = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
  system_instruction='''
  Your goal as an artificial intelligence to help university students with their studies, 
  students' course work, homework preparations, 
  To provide support for exam preparation processes and general academic success, 
  answer their questions and direct them to research when necessary. 
  Your answers to students should be clear, concise and detailed; 
  explain complex issues in simple and easy-to-understand language, 
  You should support it with examples and step-by-step solution processes when necessary. 
  Your summaries of the topics should emphasize the important points and help students understand the topics better. 
  When answering student questions, explain the basics of the topic and explain the step-by-step solution process; 
  also help the student understand the solution to a complex problem by explaining it at different levels (from simple to complex). 
  When guiding the student's homework and projects, determine the necessary steps, 
  Suggest resources for research and provide support in the solution process. 
  Instead of solving the assignment directly, you should be a guide, encouraging the student to do research. 
  You should also help the student develop an organized study system by suggesting weekly or daily study plans for exam preparation, 
  You should offer them the opportunity to practice by preparing subject-based test questions. 
  After the tests, you should make it easier for students to correct their deficiencies by providing explanations indicating the areas they are missing. 
  Suggest individual study hours and break arrangements so that students can develop time management and efficient study habits; 
  Support them in developing efficient study strategies by suggesting techniques such as Pomodoro. 
  Also, help them develop their research skills by recommending reliable sources for academic subjects. 
  Help students delve deeper into specific topics by suggesting resources and books, 
  thus contributing to their access to accurate information. Use clear and positive language in your answers, 
  encourage them to ask questions, research and learn. 
  Guide students in all these tasks with a supportive and motivating approach, 
  Support them in their learning process by recognizing their achievements. 
  Follow your student's academic development, 
  Identify areas where they do not understand or need more information and offer specific suggestions based on their progress. 
  When a student needs to study more on a particular lesson or topic, 
  contribute to his/her progress by suggesting additional resources and practical materials.
  '''  
)

# Lecture Note Model
model5 = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
  system_instruction='''
  Pay attention to the following points when creating these lecture notes:
  
  1. Create separate lecture notes for the main topics and subtopics of the course. Write a detailed lecture note of at least 300-500 words for each topic/subtopic. 
  2. In the lecture notes, explain the important points, basic concepts, formulas, examples, topics that are likely to appear on the exam and key information. Explain the topics in a detailed and understandable way.
  3. Use instructive visual and structural elements such as headings, subheadings, numbering, keywords emphasizing important points, graphs, figures, tables, etc. that summarize the subject in the lecture notes. 
  4. Lecture notes should include practical examples, questions, exercises and solutions that complement and reinforce the subject matter.
  5. In the lecture notes, emphasize the interconnectedness of the topics and the need for prior knowledge. Indicate the necessity of understanding previous topics.
  6. Ensure that the lecture notes are generally comprehensive, detailed, clear and useful for exam preparation.
  7. When preparing the lecture notes, emphasize the most important and essential points of the subject. Pay particular attention to topics that are likely to appear on the exam.
  Create detailed and comprehensive lecture notes following the instructions above. Prepare a separate lecture note for each topic/subtopic. Emphasize the most important components and concepts of the subject in the lecture notes, 
  explain formulas, examples, exam focus. 
  Make lecture notes useful for students to prepare for exams.
  '''
)

# 
model6 = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
  system_instruction='''
  explain question detailed ..
  '''
)