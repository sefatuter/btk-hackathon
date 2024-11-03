# BTK Hackathon 2024 - Edugate Projemiz

Edugate projemizi sizlere sunmaktan büyük mutluluk duyuyoruz. Projemiz, üniversite öğrencilerinin dersler hakkında detaylı bilgi edinebileceği, konularla ilgili notlar çıkarabileceği, çeşitli sınavlar oluşturup bu sınavların takibini yapabileceği kapsamlı bir eğitim platformudur. Tüm bu işlevler, Gemini AI teknolojisi kullanılarak geliştirilmiş olup yapay zekânın avantajlarından maksimum düzeyde yararlanılmıştır.

## Proje Özellikleri

1. **Kullanıcı Yönetimi**
   - Öğrencilere özel kayıt olma ve giriş yapma sayfaları
   - Kişiselleştirilmiş kullanıcı paneli

2. **Kurs Yönetimi**
   - Öğrencilerin istedikleri üniversite derslerini ekleyebilme
   - Otomatik müfredat (syllabus) oluşturma
   - Oluşturulan kursları düzenleme ve silme imkânı

3. **Dashboard Özellikleri**
   - Oluşturulan kursların listesi
   - Quiz istatistikleri (toplam quiz sayısı, doğru/yanlış oranları)
   - Çözülen soru sayısı ve başarı oranları
   - Genel performans göstergeleri

4. **Quiz Sistemi**
   - Müfredattaki herhangi bir konu veya alt konu için quiz oluşturabilme
   - Quizleri yeniden oluşturma ve tekrar çözme imkânı
   - Her soru için Gemini AI destekli detaylı açıklama özelliği
   - Quiz sonuçlarının anlık görüntülenmesi

5. **Not Sistemi**
   - Seçilen konu başlıklarıyla ilgili detaylı ders notu oluşturma
   - Notları görüntüleme imkânı

6. **EduAI Chatbot Asistanı**
   - Dashboard üzerinden erişilebilen yapay zeka destekli sohbet robotu
   - Oluşturulan quiz ve dersleri görüntüleme
   - Konularla ilgili sorulara detaylı cevaplar verebilme
   - Öğrenme sürecinde rehberlik ve destek sağlama

## Team Margo
- **Pelinsu Kaleli**
- **Sefa Bayram Tuter**
- **Bulut Demir**

---

## Kurulum Talimatları

PostgreSQL veritabanını kurduğunuzu ve aşağıdaki bilgilere sahip olduğunuzu varsayıyoruz:
- **Veritabanı Kullanıcısı**: `postgres`
- **Şifre**: `sql1234`

Bu bilgileri değiştirmek için `config.py` dosyasını düzenleyebilirsiniz.

### Adımlar

- `eduaidb` adlı veritabanını oluşturun:
```
psql -U postgres
CREATE DATABASE eduaidb;
\q
```

- .env dosyası oluşturup içine gemini keyini giriniz:
```
GEMINI_API_KEY=
```

- 
```
git clone https://github.com/sefatuter/hackathon.git
cd hackathon
pip install -r requirements.txt
flask run --debug
```