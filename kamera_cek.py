import cv2

# Kamerayı aç
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    cv2.imshow("Fotoğraf için 's' tuşuna bas, çıkmak için 'q'", frame)
    key = cv2.waitKey(1)
    if key == ord('s'):
        # Fotoğrafı kaydet
        cv2.imwrite("benim_yuzum.jpg", frame)
        print("Fotoğraf kaydedildi: benim_yuzum.jpg")
        break
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
