from flask import Flask, request, jsonify
import pandas as pd
import joblib
import os
from google.cloud import storage

app = Flask(__name__)

# --- LÜTFEN GÜNCELLEYİN ---
BUCKET_NAME = 'eatrue-app-e96de-source' # Dosyaları yüklediğiniz bucket'ın tam adı
# -------------------------

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
        if not os.path.exists(DESTINATION_MODEL_PATH):
            print("Downloading files from Google Cloud Storage...")
            client = storage.Client()
            bucket = client.bucket(BUCKET_NAME)

            # Modeli, Scaler'ı ve Excel'i indir
            bucket.blob(MODEL_FILE_NAME).download_to_filename(DESTINATION_MODEL_PATH)
            bucket.blob(SCALER_FILE_NAME).download_to_filename(DESTINATION_SCALER_PATH)
            bucket.blob(EXCEL_FILE_NAME).download_to_filename(DESTINATION_EXCEL_PATH)
            print("All files downloaded successfully.")
        else:
            print("Files already exist in /tmp directory.")

        # Dosyaları yükle
        model = joblib.load(DESTINATION_MODEL_PATH)
        scaler = joblib.load(DESTINATION_SCALER_PATH)
        df_params = pd.read_excel(DESTINATION_EXCEL_PATH, sheet_name='Parametreler')
        df_oneri = pd.read_excel(DESTINATION_EXCEL_PATH, sheet_name='Öneri Sistemi')
        print("Models and data files loaded successfully.")
    except Exception as e:
        print(f"FATAL ERROR: Could not load models or data. Error: {e}")

# Sunucu ilk başladığında modelleri ve dosyaları yükle
download_files_and_load_models()

@app.route('/score', methods=['POST'])
def get_score():
    if model is None:
        return jsonify({'error': 'Model is not loaded. Check server logs.'}), 500
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
