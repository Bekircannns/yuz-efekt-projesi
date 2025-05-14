# Yüz Algılama, Duygu Tanıma ve AR Filtre Projesi

![Demo](https://user-images.githubusercontent.com/your-demo-gif.gif)

## 🚀 Özellikler
- Gerçek zamanlı yüz algılama
- Temel duygu tanıma (mutlu, üzgün, kızgın, şaşkın, normal)
- AR filtreler: gözlük, şapka, bıyık (şeffaf PNG desteği)
- 8 farklı kamera efekti (gri ton, negatif, sepya, piksel, kenar, bulanık, karikatür)
- Yüz algılandığında rastgele sesli karşılama
- Fotoğraf çekme ve kaydetme
- Kullanıcı dostu klavye kontrolleri

## 📦 Kurulum
1. Python 3.8+ kurulu olmalı
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
3. `filters` klasörüne şeffaf arka planlı PNG filtreler ekleyin (ör: glasses.png, hat.png, mustache.png)

## 🖥️ Kullanım
- Kodu çalıştırın:
  ```bash
  python opencv_yuz_algilama.py
  ```
- Efektler: 1-8 arası tuşlar
- AR Filtreler: B (Gözlük), N (Şapka), M (Bıyık)
- Filtreyi kaldır: ESC
- Fotoğraf çek: P
- Çıkış: Q

## 📸 Fotoğraflar
Çekilen fotoğraflar `photos` klasörüne kaydedilir.

## 📝 Notlar
- AR filtreler için şeffaf PNG dosyaları gereklidir.
- Duygu tanıma temel seviyededir, derin öğrenme içermez.

## 👤 Proje Sahibi
Bekir

---
> Her türlü katkı ve öneriye açıktır!
