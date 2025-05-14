@echo off
echo Sanal ortam aktive ediliyor...
call venv\Scripts\activate
echo Gerekli paketler yükleniyor...
pip install -r requirements.txt
echo.
echo Paketler başarıyla yüklendi.
echo.
pause