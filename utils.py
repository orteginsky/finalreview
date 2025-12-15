# utils.py
import sys
import os
import json
from config import settings

class DualOutput:
    """ 
    Clase auxiliar para escribir la salida tanto en la consola 
    como en un archivo de log simultáneamente.
    """
    def __init__(self, original_stdout, log_file):
        self.original_stdout = original_stdout
        self.log_file = log_file

    def write(self, s):
        self.original_stdout.write(s)
        self.log_file.write(s)
    
    def flush(self, *args, **kwargs):
        self.original_stdout.flush()
        self.log_file.flush()

def setup_logging():
    """Configura el sistema de logs dual (consola + archivo)."""
    original_stdout = sys.stdout
    
    # Abrir en modo 'append' (a) con codificación utf-8
    log_file = open(settings.LOG_FILE_PATH, 'a', encoding='utf-8')
    
    # Redirigir stdout
    sys.stdout = DualOutput(original_stdout, log_file)
    
    return original_stdout, log_file

def log_fail(row_data, error_message):
    """ 
    Registra una fila fallida en el archivo JSON definido en config.
    """
    fail_entry = {
        "fila_excel": row_data[0] if len(row_data) > 0 else 'N/A', 
        "cliente": row_data[1] if len(row_data) > 1 else 'N/A',
        "link": row_data[2] if len(row_data) > 2 else 'N/A',
        "error": error_message
    }
    
    try:
        # Leer datos existentes si el archivo ya existe
        if os.path.exists(settings.FAILS_LOG_FILE):
            with open(settings.FAILS_LOG_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list): data = []
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        data.append(fail_entry)

        # Escribir de nuevo
        with open(settings.FAILS_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Error registrado en '{settings.FAILS_LOG_FILE}'.")
        
    except Exception as e:
        print(f"No se pudo guardar el log de error en JSON: {e}")

def get_file_bytes(file_path):
    """ Lee un archivo local en modo binario. """
    try:
        with open(file_path, "rb") as f: return f.read()
    except Exception as e:
        print(f"Error al leer el archivo binario: {e}")
        return None