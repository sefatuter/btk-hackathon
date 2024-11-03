# btk-hackathon2024

- Sources
```
https://www.youtube.com/playlist?list=PLCC34OHNcOtolz2Vd9ZSeSXWc8Bq23yEz
https://www.tutorialspoint.com/flask/index.htm
```
- bash terminal

```
git clone https://github.com/sefatuter/btk-hackathon2024.git
cd btk-hackathon2024

pip install -r requirements.txt
flask run --debug
```


- To do

```
1- Flask taslağı ve yapısını öğren

2- Öğrenci ve öğretmen giriş yks sayfası
  * kullanıcıların veritabanına kaydı

3- Öğrenci sayfası şablonu
  * ders programı
  * ödevler

4- Öğretmen sayfası şablonu
  * ders programı giriş sayfası
  * ödev ekleme kısmı
  * Eğitim materyalleri ekleme kısmı + veritabanına kaydedilmesi

5- Öğrencinin ai ile etkileşim kurabileceği sayfanın oluşturulması
  * yapay zekadan gelen verilerin ekranda gösterilmesi ve depolanması

6- Öğretmenin ai ile etkileşim kurma sayfası
  * ai verilerinin gösterilmesi

7- Listele kısmı eklenecek, listeleye tıkladıktan sonra ders hakkında bilgi ve açıklamalar
  * Quiz yap butonu (gemini'ye ders bilgileri gönderilecek ve önceden belirlenmiş quiz formatında quiz hazırlayacak)
  * Not oluştur, quiz yap, kaynak önerileri getir - butonları
  * Alt başlıklı listeleme olacak her birine özel quiz, notlara göre quiz yap butonu
  * notlara göre quiz, yaratılmış quizlerin notları saklanacak(geliştirilebilri), quizler saklanacak
  * yeniden listele (sil ve oluştur yeniden)
  * konu ekle butonu belki 


B.D -------------------------------------------------------

Ders - Kodu	Ders Adı - Açıklama

Ders Kodu	Ders Adı	Açıklama	
CS101	Bilgisayar Programlamaya Giriş	Programlama kavramlarına giriş, problem çözme, algoritma geliştirme ve temel veri yapıları.

Kısımları sana dashboarddan aşağıdaki şekilde gelecek

'''
Computer Science 101 kursu
course_code, course_name, description
{
  "course_code": "CSE101",
  "course_name": "Introduction to Computer Science",
  "description": "This introductory course provides a foundation in the fundamental concepts of computer science, including programming fundamentals, basic algorithms, data structures, and computational problem-solving." 
}
'''

gelen bu jsonu kullanarak yine gemini'ye udemydeki gibi başlıklar ve alt başlıklar oluşturacak şekilde tablo oluşturup sitede göstereceksin + Not oluştur butonu işlevsiz olsun

Computer Science 101 kursu
course_code, course_name, topics , subtopics
içerecek şekilde json formatında listele

1 course_code
1 course_name
1 topics
max 10 topics[name]
max 10 subtopics[i]

{
  "course_code": "CSE101",
  "course_name": "Introduction to Computer Science",
  "topics": [
    {
      "name": "Introduction to Programming",
      "subtopics": [
        "Data Types and Variables",
        "Operators and Expressions",
        "Control Flow (if/else, loops)",
        "Functions",
        "Arrays"
      ]
    },
    {
      "name": "Basic Algorithms and Problem Solving",
      "subtopics": [
        "Searching (Linear, Binary)",
        "Sorting (Bubble, Insertion)",
        "Recursion",
        "Time and Space Complexity (Big O Notation)"
      ]
    },
  ]
}



promptu bi daha gemini ye yolla



P.K -------------------------------------------------------

1 course_name 
max 10 topics[name]
max 10 subtopic[i]

course_name   - kurs isminin yanındaki quiz yap butonuna tıklanırsa topics + course_name bilgi olarak gidecek.
topics[name]  - topiclerin yanındaki tıklanırsa o topic + subtopics bilgi olarak gidecek.
subtopics[i]  - subtopiclerin yanındaki quiz yap butonuna tıklanınca sadece subtopic bilgi olarak gidecek.

quiz formatı örneği:

[
  {
    "question": "What is the most appropriate data type to store the age of a person?",
    "options": ["String", "Integer", "Boolean", "Float"],
    "answer": "Integer"
  },
  {
    "question": "Which operator is used to combine two strings together?",
    "options": ["+", "-", "*", "/"],
    "answer": "+"
  },
  {
    "question": "What is the result of the expression: 10 % 3 ?",
    "options": ["3", "1", "0", "10"],
    "answer": "1"
  },
  {
    "question": "Which keyword is used to define a block of code that gets executed repeatedly?",
    "options": ["if", "else", "for", "function"],
    "answer": "for"
  },
.
.
.
]

format değiştirilebilir, question, options altında alt başlık [a, b, c, d], answer gibi
quiz sorusu maksimum 20 olsun.
şimdilik kontrol sistemi olmasın.
...

system_instruction = '''Tüm yanıtlarını ders bilgileri için belirlediğim özel JSON formatında ver. Bu format dışında hiçbir bilgi ekleme ve sadece istenilen JSON objesini döndür. Sorulan her dersle ilgili bilgiyi aşağıdaki formata uygun şekilde cevapla:
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
    "..."
  ]
}'''

S.T -------------------------------------------------------

  Oluşturulan tabloya chat üzerinden yönlendirme butonu olabilir
  konuşma içerisinde oluşturuuldu! git tarzı
  
  tablo ekranına, progress kısmı, öğrenci ilerlemesini kayıt altına alma

  login yaptıktan sonra "You are taking a step through Edugate!" türü bir pop up çıkar

  take subtopic and topic quiz button "ai is processing.." pop up 

  arama butonu üstüne not ekleyebilirsin

  radio button çevresini görünür hale getir, dark mode için 

  menüden çıkarken geçiş yerinde kalıyor fix

  quiz ekranı tarzı düzenle

  butonlar renk ve düzeni, list, create note, delete butonları iconlu düzen

  register - login sayfası düzenleme, home page düzenleme

  recreate butonunda, show explanation butonunda ai is processing çıkar

  chatbot'a öneri sorular eklenebilir.

  chat kısmına öneri cümlesi

```

