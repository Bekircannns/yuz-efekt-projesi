import cv2
import pyttsx3
import time
import numpy as np
import threading
import os
from datetime import datetime
import random
import math

# Klasörleri oluştur
os.makedirs('photos', exist_ok=True)
os.makedirs('filters', exist_ok=True)

# Uygulama ayarları
class AppSettings:
    DETECTION_COOLDOWN = 5  # Yüz algılama arasındaki bekleme süresi (saniye)
    FILTER_INFO_COLOR = (255, 0, 255)  # Mor
    EFFECT_INFO_COLOR = (0, 255, 0)    # Yeşil
    FACE_INFO_COLOR = (0, 0, 255)      # Kırmızı
    PHOTO_INFO_COLOR = (255, 255, 0)   # Sarı
    EMOTION_INFO_COLOR = (255, 165, 0) # Turuncu
    FACE_RECTANGLE_COLOR = (255, 0, 0) # Mavi
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SIZE = 0.7
    FONT_THICKNESS = 2

# Efekt ve filtre bilgileri
effect_names = ["Normal", "Gri Ton", "Negatif", "Sepya", "Piksel", "Kenar Algılama", "Bulanıklık", "Karikatür"]

# AR filtreler için görselleri yükle
print("AR filtreleri kontrol ediliyor...")
try:
    # Filtreleri yükle (PNG formatında şeffaf arka planlı olmalı)
    glasses = cv2.imread('filters/glasses.png', cv2.IMREAD_UNCHANGED)
    hat = cv2.imread('filters/hat.png', cv2.IMREAD_UNCHANGED)
    mustache = cv2.imread('filters/mustache.png', cv2.IMREAD_UNCHANGED)
    
    ar_filters = [glasses, hat, mustache]
    filter_names = ["Gözlük", "Şapka", "Bıyık"]
    
    # Her filtre için ayrı kontrol
    filters_status = []
    for i, f in enumerate(ar_filters):
        if f is not None:
            if len(f.shape) == 3 and f.shape[2] == 4:  # RGBA formatı kontrolü
                print(f"{filter_names[i]} filtresi başarıyla yüklendi (şeffaf).")
                filters_status.append(True)
            else:
                print(f"{filter_names[i]} filtresi yüklendi, ancak şeffaf değil.")
                filters_status.append(True)
        else:
            print(f"{filter_names[i]} filtresi yüklenemedi.")
            filters_status.append(False)
    
    has_ar_filters = any(filters_status)
    
    if not has_ar_filters:
        print("Hiçbir AR filtresi yüklenemedi. Filtreler olmadan devam ediliyor.")
except Exception as e:
    print(f"AR filtreler yüklenirken hata oluştu: {e}")
    has_ar_filters = False
    ar_filters = []
    filter_names = []

# Yüz landmarkları için cascade modeller
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

# Duygular ve mesajlar
emotions = {
    'Mutlu': ["Gülümsemen çok güzel Bekir!", "Mutlu görünüyorsun, harika!", "Neşeni görünce ben de mutlu oldum!"],
    'Üzgün': ["Üzgün görünüyorsun Bekir, bir şeye mi canın sıkıldı?", "Üzülme Bekir, her şey düzelecek.", "Bugün biraz moralsiz görünüyorsun."],
    'Kızgın': ["Biraz sinirli görünüyorsun Bekir.", "Sakin ol Bekir, her şey yoluna girecek.", "Kızgın mısın Bekir?"],
    'Şaşkın': ["Şaşırmış görünüyorsun Bekir.", "Bekir, bir şey mi oldu?", "Ne oldu Bekir, şaşırdın mı?"],
    'Normal': ["Hoş geldin Bekir! Seni algıladım.", "Merhaba Bekir! Bugün nasılsın?", "Selam Bekir! Seni görmek güzel."]
}

# Sesli okuma motoru
engine = pyttsx3.init()

# Ses ayarları
try:
    voices = engine.getProperty('voices')
    engine.setProperty('rate', 175)  # Konuşma hızı
    
    # Türkçe ses varsa onu kullan
    turkish_voice = None
    for voice in voices:
        if "turkish" in voice.name.lower():
            turkish_voice = voice.id
            break
    
    if turkish_voice:
        engine.setProperty('voice', turkish_voice)
except Exception as e:
    print(f"Ses ayarları yapılandırılırken hata: {e}")

# Sesli okuma için thread fonksiyonu
def speak_text(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Sesli okuma hatası: {e}")

# Duygu tanıma fonksiyonu
def detect_emotion(face_roi, gray_face, face_x, face_y, face_w, face_h):
    # Yüz oranlarını ve ifade özelliklerini analiz ederek duyguyu belirle
    emotion = 'Normal'
    emotion_conf = 0
    
    try:
        # Gülümseme tespiti
        smile = smile_cascade.detectMultiScale(
            gray_face,
            scaleFactor=1.7,
            minNeighbors=22,
            minSize=(25, 25)
        )
        
        # Göz tespiti
        eyes = eye_cascade.detectMultiScale(gray_face)
        
        # Gülümseme varsa ve yeterince güçlüyse
        if len(smile) > 0:
            # Gülümseme büyüklüğüne göre değerlendir
            smile_area = sum([w*h for (x, y, w, h) in smile])
            face_area = face_w * face_h
            smile_ratio = smile_area / face_area
            
            if smile_ratio > 0.05:
                emotion = 'Mutlu'
                emotion_conf = min(smile_ratio * 10, 1.0)
        
        # Göz ve kaş hareketlerine bakarak şaşkınlık/kızgınlık/üzgünlük tespiti
        if len(eyes) >= 2:
            # Göz pozisyonları ve büyüklükleri
            eye_y_positions = [y for (x, y, w, h) in eyes]
            eye_sizes = [w*h for (x, y, w, h) in eyes]
            eye_size_ratio = max(eye_sizes) / (min(eye_sizes) + 0.001)
            
            # Gözler çok açık ve kaşlar yukarıdaysa: Şaşkın
            if eye_size_ratio > 1.5 and min(eye_y_positions) < face_h/5:
                if emotion != 'Mutlu' or emotion_conf < 0.7:
                    emotion = 'Şaşkın'
                    emotion_conf = 0.7
            
            # Derin yüz analizi
            # Yüzün alt ve üst yarısındaki piksel yoğunlukları
            upper_face = gray_face[0:int(face_h/2), :]
            lower_face = gray_face[int(face_h/2):, :]
            
            upper_avg = np.mean(upper_face)
            lower_avg = np.mean(lower_face)
            face_contrast = abs(upper_avg - lower_avg)
            
            # Yüksek kontrast ve gülümseme yoksa: Kızgın veya Üzgün
            if face_contrast > 30 and (emotion == 'Normal' or emotion_conf < 0.6):
                if upper_avg < lower_avg:
                    emotion = 'Kızgın'
                else:
                    emotion = 'Üzgün'
                emotion_conf = min(face_contrast / 50, 0.9)
        
        return emotion, emotion_conf
    except Exception as e:
        print(f"Duygu tanıma hatası: {e}")
        return 'Normal', 0.5

# Kamerayı aç
cap = cv2.VideoCapture(0)

# Kamera çözünürlüğünü ayarla (opsiyonel)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Durum değişkenleri
face_detected = False
last_detection_time = 0
is_speaking = False
photos_taken = 0
current_effect = 0
current_filter = -1  # -1: filtre yok
current_emotion = 'Normal'
last_emotion_time = 0
emotion_cooldown = 3  # Duygu değişimi için bekleme süresi (saniye)

# Kullanım talimatları
print("\n=== YÜZ ALGILAMA, DUYGU TANIMA VE EFEKT UYGULAMASI ===")
print("Kamera açıldı. Yüzünü göster!")
print("\nKONTROLLER:")
print("- Efektler: 1-8 arası tuşlar")
print("- AR Filtreler: B (Gözlük), N (Şapka), M (Bıyık)")
print("- Filtreyi kaldır: ESC tuşu")
print("- Fotoğraf çek: P tuşu")
print("- Çıkış: Q tuşu")
print("\nHazır! Kamera görüntüsü açılıyor...\n")

def apply_cartoon_effect(img):
    # Gri tonlamaya çevir
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Bulanıklaştır
    gray = cv2.medianBlur(gray, 5)
    # Kenarları algıla
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    # Renkleri azalt
    color = cv2.bilateralFilter(img, 9, 300, 300)
    # Kenarları ve renkleri birleştir
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    return cartoon

def apply_pixelate_effect(img, blocks=10):
    # Görüntüyü küçült
    h, w = img.shape[:2]
    temp = cv2.resize(img, (blocks, blocks), interpolation=cv2.INTER_LINEAR)
    # Görüntüyü orijinal boyuta geri getir
    return cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)

def overlay_transparent(background, overlay, x, y, overlay_size=None):
    """Şeffaf bir PNG'yi arka plan üzerine yerleştir"""
    try:
        if overlay is None:
            return background
            
        if overlay_size is not None:
            overlay = cv2.resize(overlay, overlay_size)
            
        bg_h, bg_w = background.shape[:2]
        ov_h, ov_w = overlay.shape[:2]
        
        # Görüntü sınırlarını kontrol et
        if y >= bg_h or x >= bg_w or y + ov_h <= 0 or x + ov_w <= 0:
            return background
            
        # Kesişim bölgesini hesapla
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(bg_w, x + ov_w)
        y2 = min(bg_h, y + ov_h)
        
        # Overlay'in kesişim bölgesini hesapla
        ox1 = max(0, -x)
        oy1 = max(0, -y)
        ox2 = ox1 + (x2 - x1)
        oy2 = oy1 + (y2 - y1)
        
        # Overlay'in alpha kanalını al
        if len(overlay.shape) == 3 and overlay.shape[2] == 4:  # RGBA
            # Alpha kanalı var
            alpha = overlay[oy1:oy2, ox1:ox2, 3] / 255.0
            alpha = np.expand_dims(alpha, axis=-1)
            
            # Arka planı al
            bg_section = background[y1:y2, x1:x2]
            
            # Overlay'i al
            ov_section = overlay[oy1:oy2, ox1:ox2, :3]
            
            # Birleştir
            background[y1:y2, x1:x2] = (ov_section * alpha + bg_section * (1 - alpha))
        else:
            # Alpha kanalı yok, direkt kopyala
            background[y1:y2, x1:x2] = overlay[oy1:oy2, ox1:ox2]
            
        return background
    except Exception as e:
        print(f"Filtre uygulanırken hata: {e}")
        return background

# Ana döngü
while True:
    # Kameradan görüntü al
    ret, frame = cap.read()
    if not ret:
        print("Kamera görüntüsü alınamıyor!")
        break
    
    # Görüntüyü ayna görüntüsü yap (daha doğal görünüm için)
    frame = cv2.flip(frame, 1)
        
    # Efektleri uygula
    if current_effect == 0:
        # Normal
        display_frame = frame.copy()
    elif current_effect == 1:
        # Gri ton
        display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        display_frame = cv2.cvtColor(display_frame, cv2.COLOR_GRAY2BGR)
    elif current_effect == 2:
        # Negatif
        display_frame = cv2.bitwise_not(frame)
    elif current_effect == 3:
        # Sepya
        display_frame = frame.copy()
        display_frame = cv2.transform(display_frame, np.matrix([
            [0.272, 0.534, 0.131],
            [0.349, 0.686, 0.168],
            [0.393, 0.769, 0.189]
        ]))
        display_frame[display_frame > 255] = 255
        display_frame = np.array(display_frame, dtype=np.uint8)
    elif current_effect == 4:
        # Piksel
        display_frame = apply_pixelate_effect(frame, 50)
    elif current_effect == 5:
        # Kenar algılama
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        display_frame = cv2.Canny(gray, 100, 200)
        display_frame = cv2.cvtColor(display_frame, cv2.COLOR_GRAY2BGR)
    elif current_effect == 6:
        # Bulanıklık
        display_frame = cv2.GaussianBlur(frame, (15, 15), 0)
    elif current_effect == 7:
        # Karikatür
        display_frame = apply_cartoon_effect(frame)
    else:
        display_frame = frame.copy()
        
    # Yüz algılama için gri tonlama
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Yüzleri algıla
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    current_time = time.time()
    
    # Yüz varsa işlemler
    for (x, y, w, h) in faces:
        # Yüz çerçevesi çiz
        cv2.rectangle(display_frame, (x, y), (x+w, y+h), 
                     AppSettings.FACE_RECTANGLE_COLOR, 2)
        
        # Yüz bölgesini çıkar
        face_roi = frame[y:y+h, x:x+w]
        gray_face = gray[y:y+h, x:x+w]
        
        # Duygu tanıma
        emotion, confidence = detect_emotion(face_roi, gray_face, x, y, w, h)
        
        # Duyguyu yalnızca belirli aralıklarla güncelle
        if current_time - last_emotion_time > emotion_cooldown:
            current_emotion = emotion
            last_emotion_time = current_time
        
        # Ekranda duyguyu göster
        emotion_text = f"{current_emotion} ({confidence:.2f})"
        cv2.putText(display_frame, emotion_text, (x, y-10), 
                    AppSettings.FONT, AppSettings.FONT_SIZE, 
                    AppSettings.EMOTION_INFO_COLOR, AppSettings.FONT_THICKNESS)
        
        # AR filtreler (eğer filtreler yüklüyse)
        if has_ar_filters and current_filter >= 0 and current_filter < len(ar_filters):
            try:
                filter_img = ar_filters[current_filter]
                if filter_img is not None:
                    if current_filter == 0:  # Gözlük
                        # Gözleri bul
                        eyes = eye_cascade.detectMultiScale(gray_face)
                        if len(eyes) >= 2:
                            # Gözlerin ortalamasını al
                            eye_x = int(np.mean([ex + ew/2 for ex, ey, ew, eh in eyes]))
                            eye_y = int(np.mean([ey + eh/2 for ex, ey, ew, eh in eyes]))
                            
                            # Gözlük boyutunu ayarla
                            glasses_width = w
                            glasses_height = int(h/3)
                            
                            # Gözlüğü yerleştir
                            display_frame = overlay_transparent(
                                display_frame, 
                                filter_img, 
                                x + eye_x - glasses_width//2, 
                                y + eye_y - glasses_height//2,
                                (glasses_width, glasses_height)
                            )
                        else:
                            # Göz bulunamadıysa tahmini konum
                            glasses_width = w
                            glasses_height = int(h/3)
                            display_frame = overlay_transparent(
                                display_frame,
                                filter_img,
                                x,
                                y + int(h/4),  # Yüzün üst kısmından biraz aşağı
                                (glasses_width, glasses_height)
                            )
                    elif current_filter == 1:  # Şapka
                        hat_width = w * 1.2  # Biraz daha geniş
                        hat_height = int(h/2)
                        display_frame = overlay_transparent(
                            display_frame, 
                            filter_img, 
                            int(x - w*0.1),  # Biraz daha kenarlara taşsın
                            y - hat_height + 10,
                            (int(hat_width), hat_height)
                        )
                    elif current_filter == 2:  # Bıyık
                        mustache_width = int(w/2)
                        mustache_height = int(h/8)
                        display_frame = overlay_transparent(
                            display_frame, 
                            filter_img, 
                            x + w//4, 
                            y + h//2 + h//8,
                            (mustache_width, mustache_height)
                        )
            except Exception as e:
                print(f"AR filtre uygulama hatası: {e}")
        
        # Eğer henüz sesli mesaj okunmadıysa veya cooldown süresi geçtiyse ve şu an konuşmuyorsa
        if (not face_detected or (current_time - last_detection_time > AppSettings.DETECTION_COOLDOWN)) and not is_speaking:
            # Duyguya göre mesajı seç
            if current_emotion in emotions:
                message = random.choice(emotions[current_emotion])
            else:
                message = random.choice(emotions['Normal'])
                
            print(f"Yüz algılandı! Duygu: {current_emotion}, Mesaj: {message}")
            
            is_speaking = True
            # Sesli okumayı ayrı bir thread'de başlat
            speech_thread = threading.Thread(target=speak_text, args=(message,))
            speech_thread.daemon = True
            speech_thread.start()
            face_detected = True
            last_detection_time = current_time
            
            # Thread'in bitmesini beklemeden bir zamanlayıcı başlat
            def reset_speaking_flag():
                global is_speaking
                time.sleep(3)  # Konuşmanın bitmesi için yaklaşık süre
                is_speaking = False
                
            timer_thread = threading.Thread(target=reset_speaking_flag)
            timer_thread.daemon = True
            timer_thread.start()
    
    # Ekrana bilgi yazıları
    cv2.putText(display_frame, f"Efekt: {effect_names[current_effect]}", (10, 30), 
                AppSettings.FONT, AppSettings.FONT_SIZE, AppSettings.EFFECT_INFO_COLOR, AppSettings.FONT_THICKNESS)
    
    if has_ar_filters and current_filter >= 0 and current_filter < len(filter_names):
        cv2.putText(display_frame, f"Filtre: {filter_names[current_filter]}", (10, 60), 
                    AppSettings.FONT, AppSettings.FONT_SIZE, AppSettings.FILTER_INFO_COLOR, AppSettings.FONT_THICKNESS)
    
    cv2.putText(display_frame, f"Yuz bulundu: {len(faces) > 0}", (10, 90), 
                AppSettings.FONT, AppSettings.FONT_SIZE, AppSettings.FACE_INFO_COLOR, AppSettings.FONT_THICKNESS)
    
    cv2.putText(display_frame, f"Cekilen fotograf: {photos_taken}", (10, 120), 
                AppSettings.FONT, AppSettings.FONT_SIZE, AppSettings.PHOTO_INFO_COLOR, AppSettings.FONT_THICKNESS)
    
    if len(faces) > 0:
        cv2.putText(display_frame, f"Duygu: {current_emotion}", (10, 150), 
                    AppSettings.FONT, AppSettings.FONT_SIZE, AppSettings.EMOTION_INFO_COLOR, AppSettings.FONT_THICKNESS)
    
    # Kullanım bilgileri
    info_text = "Filtreler: B (Gozluk), N (Sapka), M (Biyik), ESC (Kaldir)"
    cv2.putText(display_frame, info_text, (10, display_frame.shape[0] - 40), 
                AppSettings.FONT, 0.5, (255, 255, 255), 1)
    cv2.putText(display_frame, "Foto cek: P, Cikis: Q", (10, display_frame.shape[0] - 20), 
                AppSettings.FONT, 0.5, (255, 255, 255), 1)
    
    # Görüntüyü göster
    cv2.imshow("Yüz Algılama ve Efektler", display_frame)
    
    # Tuş kontrolü
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("Çıkış yapılıyor...")
        break
    elif key >= ord('1') and key <= ord('8'):
        current_effect = key - ord('1')
        print(f"Efekt değiştirildi: {effect_names[current_effect]}")
    elif key == ord('p'):
        # Fotoğraf çek
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photos/bekir_{timestamp}.jpg"
        cv2.imwrite(filename, display_frame)
        print(f"Fotoğraf kaydedildi: {filename}")
        photos_taken += 1
        
        # Fotoğraf çekildiğini sesli bildir
        if not is_speaking:
            is_speaking = True
            photo_thread = threading.Thread(target=speak_text, args=(f"Fotoğraf çekildi ve kaydedildi.",))
            photo_thread.daemon = True
            photo_thread.start()
            
            # Konuşma bitince is_speaking'i sıfırla
            def reset_photo_speaking():
                global is_speaking
                time.sleep(2)
                is_speaking = False
                
            reset_thread = threading.Thread(target=reset_photo_speaking)
            reset_thread.daemon = True
            reset_thread.start()
    elif key == ord('b'):  # B tuşu - Gözlük
        if has_ar_filters and len(ar_filters) > 0 and ar_filters[0] is not None:
            current_filter = 0
            print(f"Filtre değiştirildi: {filter_names[current_filter]}")
    elif key == ord('n'):  # N tuşu - Şapka
        if has_ar_filters and len(ar_filters) > 1 and ar_filters[1] is not None:
            current_filter = 1
            print(f"Filtre değiştirildi: {filter_names[current_filter]}")
    elif key == ord('m'):  # M tuşu - Bıyık
        if has_ar_filters and len(ar_filters) > 2 and ar_filters[2] is not None:
            current_filter = 2
            print(f"Filtre değiştirildi: {filter_names[current_filter]}")
    elif key == 27:  # ESC tuşu
        current_filter = -1  # Filtreyi kaldır
        print("Filtre kaldırıldı")

# Temizlik
cap.release()
cv2.destroyAllWindows()
print("Program sonlandırıldı.")