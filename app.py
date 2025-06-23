from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os
from google.cloud import storage
import logging # Standart print yerine daha güvenilir olan logging kütüphanesini kullanacağız

# Logging ayarlarını yap
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

BUCKET_NAME = 'eatrue-app-source' # Lütfen bu ismin doğru olduğundan emin olun
MODEL_FILE_NAME = 'truescore_model.joblib'
SCALER_FILE_NAME = 'truescore_scaler.joblib'
EXCEL_FILE_NAME = 'Truescore.xlsx'

DESTINATION_MODEL_PATH = f'/tmp/{MODEL_FILE_NAME}'
DESTINATION_SCALER_PATH = f'/tmp/{SCALER_FILE_NAME}'
DESTINATION_EXCEL_PATH = f'/tmp/{EXCEL_FILE_NAME}'

model = None
scaler = None
df_params = None
df_oneri = None

def download_files_and_load_models():
    global model, scaler, df_params, df_oneri
    try:
        logging.info("--- Uygulama başlatılıyor: Dosya indirme ve model yükleme süreci başladı. ---")

        if not os.path.exists(DESTINATION_MODEL_PATH):
            logging.info("Lokalde dosyalar bulunamadı, Google Cloud Storage'dan indirilecek.")

            logging.info("Adım 1: Google Cloud Storage istemcisi başlatılıyor...")
            client = storage.Client()
            logging.info("Adım 1 BAŞARILI: İstemci başlatıldı.")

            logging.info(f"Adım 2: '{BUCKET_NAME}' bucket'ına erişiliyor...")
            bucket = client.bucket(BUCKET_NAME)
            logging.info("Adım 2 BAŞARILI: Bucket'a erişildi.")

            # Modeli İndir
            logging.info(f"Adım 3: '{MODEL_FILE_NAME}' modeli indiriliyor...")
            bucket.blob(MODEL_FILE_NAME).download_to_filename(DESTINATION_MODEL_PATH)
            logging.info("Adım 3 BAŞARILI: Model indirildi.")

            # Scaler'ı İndir
            logging.info(f"Adım 4: '{SCALER_FILE_NAME}' scaler'ı indiriliyor...")
            bucket.blob(SCALER_FILE_NAME).download_to_filename(DESTINATION_SCALER_PATH)
            logging.info("Adım 4 BAŞARILI: Scaler indirildi.")

            # Excel'i İndir
            logging.info(f"Adım 5: '{EXCEL_FILE_NAME}' excel'i indiriliyor...")
            bucket.blob(EXCEL_FILE_NAME).download_to_filename(DESTINATION_EXCEL_PATH)
            logging.info("Adım 5 BAŞARILI: Excel indirildi.")
        else:
            logging.info("Dosyalar zaten /tmp klasöründe mevcut.")

        # Dosyaları Yükle
        logging.info(f"Adım 6: '{MODEL_FILE_NAME}' modeli joblib ile yükleniyor...")
        model = joblib.load(DESTINATION_MODEL_PATH)
        logging.info("Adım 6 BAŞARILI: Model yüklendi.")

        logging.info(f"Adım 7: '{SCALER_FILE_NAME}' scaler'ı joblib ile yükleniyor...")
        scaler = joblib.load(DESTINATION_SCALER_PATH)
        logging.info("Adım 7 BAŞARILI: Scaler yüklendi.")

        logging.info(f"Adım 8: '{EXCEL_FILE_NAME}' excel'i pandas ile okunuyor...")
        df_params = pd.read_excel(DESTINATION_EXCEL_PATH, sheet_name='Parametreler')
        df_oneri = pd.read_excel(DESTINATION_EXCEL_PATH, sheet_name='Öneri Sistemi')
        logging.info("Adım 8 BAŞARILI: Excel okundu.")

        logging.info("--- TÜM MODELLER VE VERİ DOSYALARI BAŞARIYLA YÜKLENDİ! ---")

    except Exception as e:
        # Bu, hatanın tam olarak ne olduğunu loglara yazdıracak.
        logging.exception("!!! BEKLENMEDİK BİR HATA OLUŞTU !!!")
        model = None # Hata durumunda modeli None yap

download_files_and_load_models()

@app.route('/score', methods=['POST'])
def get_score():
    if model is None:
        return jsonify({'error': 'Model is not loaded. Check server logs.'}), 500
    # ... (geri kalan kod aynı) ...
    try:
        data = request.get_json()
        input_features = pd.DataFrame([data])[list(model.feature_names_in_)]
        scaled_features = scaler.transform(input_features)
        prediction = model.predict(scaled_features)
        score = int(prediction[0])
        oneri_row = df_oneri[df_oneri['TrueScore'] == score]
        oneri_text = oneri_row.iloc[0]['Öneri'] if not oneri_row.empty else "Bu skor için özel bir öneri bulunamadı."
        return jsonify({'TrueScore': score, 'Oneri': oneri_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
