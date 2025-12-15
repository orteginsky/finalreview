# auth.py
import os
from google.oauth2 import service_account
from config import settings
from logger import setup_logger

logger = setup_logger(__name__, 'auth.log')

def get_google_creds():
    """
    Carga las credenciales desde una Cuenta de Servicio (sa_key.json).
    """
    logger.info("Iniciando autenticación con Google Service Account")

    if not os.path.exists(settings.CREDENTIALS_FILE):
        logger.error(f"Archivo de credenciales no encontrado: {settings.CREDENTIALS_FILE}")
        raise FileNotFoundError(f"No se encontró el archivo de llave: {settings.CREDENTIALS_FILE}")

    try:
        logger.debug(f"Cargando credenciales desde: {settings.CREDENTIALS_FILE}")
        logger.debug(f"Scopes solicitados: {', '.join(settings.SCOPES)}")

        creds = service_account.Credentials.from_service_account_file(
            settings.CREDENTIALS_FILE,
            scopes=settings.SCOPES
        )

        logger.info("Credenciales de Google cargadas exitosamente")
        return creds
    except Exception as e:
        logger.error(f"Error al cargar la cuenta de servicio: {e}", exc_info=True)
        raise