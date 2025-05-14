"""
Sanal ortam test dosyası
------------------------
Bu dosya, sanal ortamınızın doğru çalıştığını test etmek için oluşturulmuştur.
"""

def merhaba():
    """Basit bir merhaba dünya fonksiyonu."""
    print("Merhaba! Sanal ortam başarıyla kuruldu ve çalışıyor!")
    
    try:
        import numpy
        print("NumPy başarıyla yüklendi!")
    except ImportError:
        print("NumPy yüklü değil. Lütfen 'paketleri_yukle.bat' dosyasını çalıştırın.")
    
    try:
        import pandas
        print("Pandas başarıyla yüklendi!")
    except ImportError:
        print("Pandas yüklü değil. Lütfen 'paketleri_yukle.bat' dosyasını çalıştırın.")

if __name__ == "__main__":
    merhaba()
    input("\nDevam etmek için Enter tuşuna basın...")
