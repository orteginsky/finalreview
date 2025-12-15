# config.py
import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

class Settings:
    """
    Clase de configuración centralizada.
    Lee las variables de entorno y define valores por defecto.
    """
    
    # --- Google Auth ---
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents.readonly',
        'https://www.googleapis.com/auth/cloud-platform'
    ]
    
    # Rutas de archivos de credenciales
    CREDENTIALS_FILE: str = os.getenv('GOOGLE_CREDENTIALS_FILE', 'sa_key.json')
    TOKEN_FILE: str = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')

    # --- Google Workspace ---
    SPREADSHEET_ID: str = os.getenv('SPREADSHEET_ID')
    WORKSHEET_NAME: str = os.getenv('WORKSHEET_NAME', 'FINAL REVIEW')
    DRIVE_DESTINATION_FOLDER_ID: str = os.getenv('DRIVE_DESTINATION_FOLDER_ID')
    PROMPT_DOC_ID: str = os.getenv('PROMPT_DOC_ID')

    # --- Google Cloud Storage & Vertex AI ---
    GCS_BUCKET_NAME: str = os.getenv('GCS_BUCKET_NAME')
    GCS_TEMP_FOLDER: str = os.getenv('GCS_TEMP_FOLDER', 'temp_uploads')
    GCS_PROJECT_ID: str = os.getenv('GCS_PROJECT_ID', 'supportccc')
    
    # Convertimos a float/int porque env devuelve strings
    INLINE_SIZE_LIMIT_MB: float = float(os.getenv('INLINE_SIZE_LIMIT_MB', 45))

    # --- Microservicio Dropbox ---
    DROPBOX_SERVICE_URL: str = os.getenv('DROPBOX_SERVICE_URL')
    DROPBOX_SIGNATURE: str = os.getenv('DROPBOX_SIGNATURE')
    DROPBOX_SERVICE_NAME: str = os.getenv('DROPBOX_SERVICE_NAME', 'script_client')

    # --- Microservicio Markdown Writer ---
    MARKDOWN_WRITER_SERVICE_URL: str = os.getenv('MARKDOWN_WRITER_SERVICE_URL')

    # --- Configuración Local y Logs ---
    # Estas suelen ser constantes del sistema de archivos, pueden quedarse hardcoded o en env
    FAILS_LOG_FILE: str = 'links_fails_final_review.json'
    TEMP_DOWNLOAD_DIR: str = 'temp_downloads_final_review'
    LOG_FILE_PATH: str = 'FINAL-REVIEW_LOG.txt'

    # --- Configuración del Proceso ---
    STARTING_ROW_NUMBER: int = int(os.getenv('STARTING_ROW_NUMBER', 1))

# Instancia única para importar en otros archivos
settings = Settings()