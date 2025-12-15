from fastapi import FastAPI
import uvicorn
from routes import router
from logger import setup_logger

logger = setup_logger(__name__, 'main.log')

app = FastAPI(title="AI Document Processor API")

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    logger.info("=== Iniciando AI Document Processor API ===")
    logger.info("API iniciada exitosamente")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=== Deteniendo AI Document Processor API ===")
    logger.info("API detenida exitosamente")
