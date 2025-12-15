import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_file: str = 'app.log', level=logging.INFO):
    """
    Configura y retorna un logger con formato consistente.

    Args:
        name: Nombre del logger (usualmente __name__ del módulo)
        log_file: Nombre del archivo de log
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logger configurado
    """
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evitar duplicar handlers si ya existen
    if logger.handlers:
        return logger

    # Formato del log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para archivo con rotación (máximo 10MB, 5 backups)
    log_path = Path(log_file)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Agregar handlers al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str):
    """
    Obtiene un logger ya configurado o crea uno nuevo.

    Args:
        name: Nombre del logger (usualmente __name__ del módulo)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)
