# services_dropbox.py
import dropbox
import requests
import time
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from logger import setup_logger

logger = setup_logger(__name__, 'services_dropbox.log')

class DropboxHandler:
    """ 
    Maneja la conexión a Dropbox obteniendo credenciales frescas 
    desde el microservicio AccessTokenDropbox en Cloud Run.
    """
    
    def __init__(self, service_url, signature, service_name="default_script"):
        logger.info(f"Inicializando DropboxHandler - Servicio: {service_name}")
        logger.debug("Contactando al microservicio de Dropbox para obtener token...")
        self.access_token = self._get_fresh_token(service_url, signature, service_name)

        if not self.access_token:
            logger.error("No se pudo obtener un token válido del microservicio")
            raise ValueError("No se pudo obtener un token válido del microservicio.")

        try:
            logger.debug("Inicializando cliente Dropbox con token obtenido")
            self.dbx = dropbox.Dropbox(self.access_token)
            # Verificación de conexión
            cuenta = self.dbx.users_get_current_account()
            logger.info(f"Conexión exitosa a Dropbox - Usuario: {cuenta.name.display_name}")
        except Exception as e:
            logger.error(f"Error crítico al conectar cliente Dropbox: {e}", exc_info=True)
            raise

    def _get_fresh_token(self, url, signature, service_name):
        """ Solicita un nuevo token al microservicio. """
        try:
            logger.debug(f"Solicitando token al microservicio: {url}")
            payload = {
                "signature": signature,
                "service": service_name
            }
            headers = {"Content-Type": "application/json"}

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status() # Lanza error si no es 200 OK

            data = response.json()
            token = data.get("access_token")

            if token:
                logger.info("Token fresco obtenido exitosamente del microservicio")
                return token
            else:
                logger.warning("El microservicio respondió, pero no envió 'access_token'")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con el microservicio de tokens: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Detalle respuesta del microservicio: {e.response.text}")
            return None

    def download_file(self, shared_link, local_path):
        """ Descarga un archivo transformando el link compartido. """
        if not shared_link or "NO HAY" in shared_link.upper():
            logger.warning(f"Link inválido o vacío: {shared_link}")
            return None

        try:
            logger.info(f"Descargando archivo de Dropbox: {shared_link}")

            parsed_url = urlparse(shared_link)
            query_dict = parse_qs(parsed_url.query)
            query_dict['dl'] = ['1']
            if 'st' in query_dict: del query_dict['st']

            new_query_string = urlencode(query_dict, doseq=True)
            direct_download_link = urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                 parsed_url.params, new_query_string, parsed_url.fragment)
            )

            logger.debug(f"Link de descarga directa generado: {direct_download_link}")

            # Usamos requests directos para la descarga (no consume API quota de la librería)
            response = requests.get(direct_download_link, stream=True)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                logger.error(f"Dropbox devolvió HTML en lugar de archivo. Verifique link/permisos. Content-Type: {content_type}")
                return None

            logger.debug(f"Guardando archivo en: {local_path}")
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Archivo descargado y guardado exitosamente: {local_path}")
            return local_path

        except Exception as e:
            logger.error(f"Error al descargar archivo de '{shared_link}': {e}", exc_info=True)
            return None