from pydantic import BaseModel

class ProcessRequest(BaseModel):
    dropbox_link: str
    client_name: str
    
    # Datos del Google Doc destino (ya creado por GAS)
    destination_doc_id: str 
    
    # Datos para actualizar el estado en Sheets
    spreadsheet_id: str
    worksheet_name: str
    row_number: int
    status_column: str # Ejemplo: "E"
    result_column: str # Ejemplo: "D"

    # Opcional: ID del Doc que contiene el Prompt Maestro
    prompt_doc_id: str