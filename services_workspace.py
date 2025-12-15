import gspread
import requests
from googleapiclient.errors import HttpError
from logger import setup_logger
from config import settings

logger = setup_logger(__name__, 'services_workspace.log')

def write_formatted_doc_via_service(document_id, markdown_content):
    """
    Envía el contenido Markdown al microservicio externo para formateo nativo.
    """
    url = settings.MARKDOWN_WRITER_SERVICE_URL
    payload = {
        "markdown_content": markdown_content,
        "document_id": document_id
    }
    
    logger.info(f"Enviando solicitud de escritura al servicio externo para Doc ID: {document_id}")
    try:
        response = requests.post(url, json=payload, timeout=120) # Timeout generoso
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            logger.info("Escritura exitosa reportada por el servicio externo.")
            return True
        else:
            logger.warning(f"El servicio externo respondió 200 pero success=False: {data}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión con el servicio de escritura: {e}")
        return False

def update_sheet_status(creds, spreadsheet_id, sheet_name, row, col_letter, message):
    """ Actualiza una celda específica en Google Sheets con un mensaje. """
    try:
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(spreadsheet_id)
        ws = sh.worksheet(sheet_name)
        cell = f"{col_letter}{row}"
        ws.update_acell(cell, message)
        logger.info(f"Sheet actualizado [{cell}]: {message}")
    except Exception as e:
        logger.error(f"Error actualizando sheet: {e}")

def get_google_doc_content(docs_service, document_id):
    """ Lee el prompt maestro. """
    try:
        logger.debug(f"Leyendo contenido del Doc ID: {document_id}")
        doc = docs_service.documents().get(documentId=document_id).execute()
        doc_content = doc.get('body').get('content')
        full_text = ""
        for value in doc_content:
            if 'paragraph' in value:
                elements = value.get('paragraph').get('elements')
                for elem in elements:
                    if 'textRun' in elem:
                        full_text += elem.get('textRun').get('content')
        return full_text
    except Exception as e:
        logger.error(f"Error leyendo prompt maestro: {e}")
        return None