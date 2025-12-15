# ai_processor.py
import time
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part, HarmCategory, HarmBlockThreshold
from prompts import SYSTEM_INSTRUCTIONS
from logger import setup_logger

logger = setup_logger(__name__, 'ai_processor.log')

# AHORA ACEPTA EL PARAMETRO 'credentials'
def init_ai_model(project_id, credentials, location="us-central1"):
    """
    Inicializa Vertex AI usando credenciales explícitas de Service Account.
    """
    try:
        logger.info(f"Inicializando Vertex AI - Proyecto: {project_id}, Ubicación: {location}")
        # Pasamos credentials explícitamente
        vertexai.init(project=project_id, location=location, credentials=credentials)

        logger.debug("Configurando modelo generativo gemini-2.5-flash")
        model = GenerativeModel(
            "gemini-2.5-flash",
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 50000
            },
            safety_settings={
                # ... (tus settings de seguridad igual que antes) ...
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        logger.info("Modelo de IA inicializado correctamente con Service Account")
        return model
    except Exception as e:
        logger.error(f"Error crítico al inicializar el modelo de IA: {e}", exc_info=True)
        return None


def analyze_document(model, document_parts_list, client_name, user_prompt_text):
    """
    Envía las partes del documento (Imágenes o PDF) a la IA con reintentos.
    """
    if not model:
        logger.error("Modelo de IA no proporcionado")
        return None
    if not user_prompt_text:
        logger.error("El prompt de usuario está vacío")
        return None

    logger.info(f"Iniciando análisis de documento para cliente: {client_name}")
    logger.debug(f"Partes del documento: {len(document_parts_list)}, Longitud del prompt: {len(user_prompt_text)}")

    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            # Construcción del mensaje para Gemini
            contents = [
                Part.from_text(SYSTEM_INSTRUCTIONS),
                *document_parts_list,
                Part.from_text(user_prompt_text)
            ]

            logger.info(f"Intento {attempt + 1}/{max_retries} analizando para '{client_name}'")

            response = model.generate_content(contents=contents)

            if not response.candidates:
                if response.prompt_feedback:
                    error_msg = f"Bloqueado por seguridad: {response.prompt_feedback.block_reason}"
                    logger.warning(f"Respuesta bloqueada para {client_name}: {error_msg}")
                    raise ValueError(error_msg)
                else:
                    logger.warning(f"Respuesta vacía sin motivo aparente para {client_name}")
                    raise ValueError("Respuesta vacía sin motivo aparente.")

            logger.info(f"Análisis IA completado exitosamente para {client_name} ({len(response.text)} caracteres)")
            return response.text

        except Exception as e:
            # Errores fatales que no se deben reintentar
            if "exceeds max allowed file size" in str(e):
                logger.error(f"Error fatal de tamaño de archivo para {client_name}: {e}")
                return None

            logger.warning(f"Error en IA para {client_name} (intento {attempt + 1}/{max_retries}): {e.__class__.__name__} - {e}")

            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.info(f"Reintentando en {wait_time:.2f} segundos...")
                time.sleep(wait_time)
            else:
                logger.error(f"Se agotaron los {max_retries} intentos de IA para {client_name}")
                return None