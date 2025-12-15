from fastapi import APIRouter, BackgroundTasks, HTTPException
from schemas import ProcessRequest
from worker import process_row_task
from logger import setup_logger

logger = setup_logger(__name__, 'routes.log')

router = APIRouter()

@router.post("/process-document")
async def trigger_process(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Endpoint que recibe la solicitud de Google Sheets.
    Retorna "OK" inmediatamente y lanza el proceso en segundo plano.
    """
    logger.info(f"Solicitud recibida para procesar documento - Cliente: {request.client_name}, Fila: {request.row_number}")

    if not request.dropbox_link:
        logger.warning(f"Solicitud rechazada - Falta link de Dropbox para cliente: {request.client_name}")
        raise HTTPException(status_code=400, detail="Falta link de Dropbox")

    logger.debug(f"Agregando tarea en segundo plano para {request.client_name}")
    # Agregamos la tarea pesada a la cola de fondo
    background_tasks.add_task(process_row_task, request)

    logger.info(f"Tarea en segundo plano iniciada para {request.client_name}")
    return {
        "status": "received",
        "message": f"Procesamiento iniciado para {request.client_name}. Se actualizará la hoja en breve."
    }