import cv2
import face_recognition
import pyttsx3
import time

# Sesli okuma motoru
engine = pyttsx3.init()

# Referans yüzünü yükle
known_image = face_recognition.load_image_file("benim_yuzum.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]

# Kamerayı aç
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    rgb_frame = frame[:, :, ::-1]  # BGR'den RGB'ye çevir

    # Kameradaki yüzleri bul
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding in face_encodings:
        # Yüz karşılaştırması
        matches = face_recognition.compare_faces([known_encoding], face_encoding)
        if True in matches:
            # Yüz bulundu, metni oku
            print("Yüz algılandı! Metin okunuyor...")
            engine.say("Hoş geldin Bekir! Seni algıladım.")
            engine.runAndWait()
            time.sleep(1)
            cap.release()
            cv2.destroyAllWindows()
            exit()  # Programı tamamen sonlandır

    cv2.imshow("Kamera", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()