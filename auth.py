# auth.py
import os
import google.auth
from google.oauth2 import service_account
from config import settings
from logger import setup_logger

logger = setup_logger(__name__, 'auth.log')

def get_google_creds():
    """
    Intenta cargar credenciales en este orden:
    1. Archivo JSON local (definido en settings.CREDENTIALS_FILE).
    2. Application Default Credentials (ADC) del entorno (Cloud Run / gcloud auth).
    """
    logger.info("Iniciando proceso de autenticación...")

    # --- ESTRATEGIA 1: LOCAL (Archivo JSON explícito) ---
    if os.path.exists(settings.CREDENTIALS_FILE):
        logger.info(f"✅ Modo Local detectado: Archivo '{settings.CREDENTIALS_FILE}' encontrado.")
        try:
            creds = service_account.Credentials.from_service_account_file(
                settings.CREDENTIALS_FILE,
                scopes=settings.SCOPES
            )
            logger.info("Credenciales cargadas exitosamente desde archivo JSON.")
            return creds
        except Exception as e:
            logger.error(f"Error crítico leyendo el archivo JSON: {e}", exc_info=True)
            raise

    # --- ESTRATEGIA 2: NUBE (ADC - Cloud Run / GCE) ---
    else:
        logger.info(f"☁️ Modo Nube detectado: Archivo '{settings.CREDENTIALS_FILE}' no existe.")
        logger.info("Intentando obtener Application Default Credentials (ADC)...")
        
        try:
            # google.auth.default busca credenciales inyectadas por el entorno (Cloud Run)
            creds, project_id = google.auth.default(scopes=settings.SCOPES)
            logger.info(f"Credenciales ADC obtenidas exitosamente (Proyecto: {project_id})")
            return creds
        except Exception as e:
            logger.error(f"Fallo total de autenticación (ni JSON ni ADC disponibles): {e}", exc_info=True)
            raise RuntimeError("No se encontraron credenciales válidas (ni sa_key.json ni ADC).")