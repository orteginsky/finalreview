import os
import time
import shutil
import fitz # PyMuPDF
from googleapiclient.discovery import build
from google.cloud import storage
from vertexai.preview.generative_models import Part

# Importaciones propias
from config import settings
import auth
from services_dropbox import DropboxHandler
from services_gcs import upload_to_gcs, delete_from_gcs
from services_workspace import get_google_doc_content, write_formatted_doc_via_service, update_sheet_status
from ai_processor import init_ai_model, analyze_document
from schemas import ProcessRequest
from logger import setup_logger

logger = setup_logger(__name__, 'worker.log')

def process_row_task(request: ProcessRequest):
    """
    Función que se ejecuta en segundo plano (Background Task).
    """
    logger.info(f"Iniciando procesamiento para cliente: {request.client_name}, fila: {request.row_number}")

    creds = auth.get_google_creds()

    # 1. Reportar inicio
    update_sheet_status(creds, request.spreadsheet_id, request.worksheet_name,
                        request.row_number, request.status_column, "Iniciando descarga...")
    logger.debug(f"Estado actualizado a 'Iniciando descarga...' para {request.client_name}")

    local_temp_folder = None
    gcs_paths_to_delete = []

    try:
        # Servicios
        logger.debug("Inicializando servicios de Google...")
        docs_service = build('docs', 'v1', credentials=creds)
        storage_client = storage.Client(credentials=creds)
        logger.info("Servicios de Google inicializados correctamente")

        # Dropbox
        logger.debug("Inicializando handler de Dropbox...")
        dropbox_handler = DropboxHandler(
            service_url=settings.DROPBOX_SERVICE_URL,
            signature=settings.DROPBOX_SIGNATURE,
            service_name=settings.DROPBOX_SERVICE_NAME
        )
        logger.info("Handler de Dropbox inicializado correctamente")

        # IA Init
        logger.debug("Inicializando modelo de IA...")
        ia_model = init_ai_model(project_id="supportccc", credentials=creds)
        logger.info("Modelo de IA inicializado correctamente")

        # Obtener Prompt
        logger.debug(f"Obteniendo prompt maestro del documento: {request.prompt_doc_id}")
        user_prompt_text = get_google_doc_content(docs_service, request.prompt_doc_id)
        if not user_prompt_text:
            logger.error("No se pudo leer el Prompt Maestro")
            raise ValueError("No se pudo leer el Prompt Maestro")
        logger.info(f"Prompt maestro obtenido correctamente ({len(user_prompt_text)} caracteres)")

        # --- Descarga y Procesamiento ---
        local_temp_folder = os.path.join(settings.TEMP_DOWNLOAD_DIR, request.client_name)
        os.makedirs(local_temp_folder, exist_ok=True)
        temp_pdf_path = os.path.join(local_temp_folder, "source.pdf")
        logger.debug(f"Carpeta temporal creada: {local_temp_folder}")

        logger.info(f"Descargando archivo desde Dropbox: {request.dropbox_link}")
        if not dropbox_handler.download_file(request.dropbox_link, temp_pdf_path):
            logger.error(f"Fallo en la descarga desde Dropbox: {request.dropbox_link}")
            raise Exception("Fallo descarga Dropbox")
        logger.info(f"Archivo descargado correctamente: {temp_pdf_path}")

        # Reportar estado
        update_sheet_status(creds, request.spreadsheet_id, request.worksheet_name,
                        request.row_number, request.status_column, "Procesando PDF/Imágenes...")
        logger.debug("Estado actualizado a 'Procesando PDF/Imágenes...'")

        # Lógica PDF vs Imágenes (Reutilizada)
        file_size_mb = os.path.getsize(temp_pdf_path) / (1024 * 1024)
        logger.info(f"Tamaño del archivo: {file_size_mb:.2f} MB")
        document_parts_list = []

        if file_size_mb >= settings.INLINE_SIZE_LIMIT_MB:
            logger.info(f"Archivo grande detectado ({file_size_mb:.2f} MB >= {settings.INLINE_SIZE_LIMIT_MB} MB), procesando como imágenes...")
            doc = fitz.open(temp_pdf_path)
            total_pages = len(doc)
            logger.info(f"PDF abierto correctamente, total de páginas: {total_pages}")

            for page_num in range(total_pages):
                logger.debug(f"Procesando página {page_num + 1}/{total_pages}")
                pix = doc.load_page(page_num).get_pixmap(dpi=150)
                local_img = os.path.join(local_temp_folder, f"p_{page_num:03d}.png")
                pix.save(local_img)
                gcs_path = f"{settings.GCS_TEMP_FOLDER}/{request.client_name}_{int(time.time())}/p_{page_num:03d}.png"
                gcs_uri = upload_to_gcs(local_img, gcs_path, settings.GCS_BUCKET_NAME, storage_client)
                if gcs_uri:
                    document_parts_list.append(Part.from_uri(gcs_uri, mime_type="image/png"))
                    gcs_paths_to_delete.append(gcs_path)
                    logger.debug(f"Página {page_num + 1} subida a GCS: {gcs_uri}")
                os.remove(local_img)
            doc.close()
            logger.info(f"Procesamiento de {total_pages} páginas completado")
        else:
            logger.info(f"Archivo pequeño ({file_size_mb:.2f} MB < {settings.INLINE_SIZE_LIMIT_MB} MB), subiendo PDF completo...")
            gcs_path = f"{settings.GCS_TEMP_FOLDER}/{request.client_name}_{int(time.time())}.pdf"
            gcs_uri = upload_to_gcs(temp_pdf_path, gcs_path, settings.GCS_BUCKET_NAME, storage_client)
            if gcs_uri:
                document_parts_list.append(Part.from_uri(gcs_uri, mime_type="application/pdf"))
                gcs_paths_to_delete.append(gcs_path)
                logger.info(f"PDF completo subido a GCS: {gcs_uri}")

        # --- Análisis IA ---
        update_sheet_status(creds, request.spreadsheet_id, request.worksheet_name,
                        request.row_number, request.status_column, "Analizando con IA...")
        logger.info(f"Iniciando análisis de IA para {request.client_name}")

        analysis_text = analyze_document(ia_model, document_parts_list, request.client_name, user_prompt_text)

        if not analysis_text:
            logger.error("Respuesta de IA vacía")
            raise Exception("Respuesta IA vacía")
        logger.info(f"Análisis de IA completado ({len(analysis_text)} caracteres)")

        # --- Escritura en Doc Destino ---
        update_sheet_status(creds, request.spreadsheet_id, request.worksheet_name,
                        request.row_number, request.status_column, "Escribiendo reporte...")
        logger.info(f"Escribiendo reporte en documento: {request.destination_doc_id}")

        success = write_formatted_doc_via_service(request.destination_doc_id, analysis_text)
        
        if not success:
            logger.error(f"Fallo al escribir en Google Doc vía microservicio: {request.destination_doc_id}")
            # Opcional: Fallback a escritura plana si el servicio falla, o lanzar error
            raise Exception("Fallo escritura formateada en Google Doc")
            
        logger.info("Reporte escrito y formateado correctamente en Google Doc")
        # --- Finalización ---
        # 1. Poner "OK" en estado
        update_sheet_status(creds, request.spreadsheet_id, request.worksheet_name,
                        request.row_number, request.status_column, "OK - Completado")

        # 2. Poner Link del Doc en la columna de resultado
        doc_url = f"https://docs.google.com/document/d/{request.destination_doc_id}/edit"
        update_sheet_status(creds, request.spreadsheet_id, request.worksheet_name,
                        request.row_number, request.result_column, doc_url)

        logger.info(f"Procesamiento completado exitosamente para {request.client_name}")

    except Exception as e:
        logger.error(f"Error en worker para {request.client_name}: {e}", exc_info=True)
        # Reportar error en Sheet
        update_sheet_status(creds, request.spreadsheet_id, request.worksheet_name,
                        request.row_number, request.status_column, f"Error: {str(e)[:50]}")
    finally:
        # Limpiezas
        logger.debug("Iniciando limpieza de archivos temporales")
        if gcs_paths_to_delete:
            logger.info(f"Eliminando {len(gcs_paths_to_delete)} archivos de GCS")
            delete_from_gcs(gcs_paths_to_delete, settings.GCS_BUCKET_NAME, storage_client)
        if local_temp_folder and os.path.exists(local_temp_folder):
            logger.debug(f"Eliminando carpeta temporal: {local_temp_folder}")
            shutil.rmtree(local_temp_folder, ignore_errors=True)
        logger.info(f"Limpieza completada para {request.client_name}")