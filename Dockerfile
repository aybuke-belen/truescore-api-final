# Python'ın hafif bir versiyonunu temel al
FROM python:3.11-slim

# Kodun çalışacağı /app adında bir klasör oluştur
WORKDIR /app

# Önce gereksinimler dosyasını kopyala ve kütüphaneleri yükle
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Proje klasöründeki diğer tüm dosyaları kopyala
COPY . .

# Sunucuyu başlatmak için Gunicorn kullan
# Cloud Run'ın verdiği PORT'u kullanacak ve 0.0.0.0 ile dışarıya açacak
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "app:app"]
