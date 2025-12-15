AI Document Processor & Report Generator
Este sistema automatiza el flujo de trabajo de análisis de documentos legales/administrativos. Conecta Dropbox, Google Sheets y Google Docs orquestados por una API en FastAPI que utiliza Google Vertex AI (Gemini) para analizar el contenido y generar reportes formateados.

🚀 Flujo de Trabajo
Fragmento de código

graph TD
    A[Google Sheet<br>(Trigger)] -->|POST Request| B(FastAPI Endpoint)
    B -->|Background Task| C{Worker}
    C -->|1. Descargar| D[Dropbox]
    C -->|2. Procesar| E{¿Archivo > 45MB?}
    E -->|Si| F[Convertir a Imágenes<br>PyMuPDF]
    E -->|No| G[Subir PDF a GCS]
    F --> H[Google Cloud Storage]
    G --> H
    H -->|3. Analizar| I[Vertex AI<br>Gemini 1.5 Pro]
    I -->|4. Generar Markdown| J[Texto Analizado]
    J -->|5. Formatear| K[Microservicio<br>Markdown-to-Docs]
    K -->|6. Escribir| L[Google Doc Final]
    C -->|7. Actualizar Estado| A
✨ Características
Arquitectura Asíncrona: La API responde inmediatamente a Google Sheets ("Received") mientras procesa documentos pesados en segundo plano (BackgroundTasks), evitando timeouts.

Manejo Inteligente de Archivos:

Descarga directa desde enlaces compartidos de Dropbox.

Detecta archivos grandes (>45MB) y los convierte automáticamente a imágenes para evitar límites de la API de IA.

Inteligencia Artificial: Utiliza modelos gemini-pro de Vertex AI con instrucciones maestras leídas dinámicamente desde un Google Doc.

Formato Profesional: Integra un microservicio externo para convertir la salida Markdown de la IA en un Google Doc nativo (Negritas, H1, H2, Listas).

Logging Robusto: Sistema de logs detallado en consola y archivos rotativos para auditoría.

🛠️ Requisitos Previos
Python 3.10+

Cuenta de Servicio de Google (Service Account) con permisos habilitados para:

Google Drive API

Google Docs API

Google Sheets API

Vertex AI API

Cloud Storage API

Archivo de credenciales: sa_key.json (JSON de la Service Account).

Microservicio de Formateo: URL del servicio Markdown to Google Docs Writer.

📦 Instalación
Clonar el repositorio:

Bash

git clone <tu-repo-url>
cd nombre-del-proyecto
Crear entorno virtual:

Bash

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
Instalar dependencias:

Bash

pip install -r requirements.txt
⚙️ Configuración
Crea un archivo .env en la raíz del proyecto basándote en el siguiente ejemplo:

Ini, TOML

# .env

# --- Google Auth ---
GOOGLE_CREDENTIALS_FILE=sa_key.json

# --- IDs de Recursos (Producción) ---
SPREADSHEET_ID=tu_id_de_google_sheet
WORKSHEET_NAME=FINAL REVIEW
PROMPT_DOC_ID=id_del_doc_con_instrucciones_maestras
DRIVE_DESTINATION_FOLDER_ID=id_carpeta_drive_destino

# --- Google Cloud Platform ---
GCS_PROJECT_ID=tu-proyecto-gcp
GCS_BUCKET_NAME=nombre-del-bucket
GCS_TEMP_FOLDER=temp_uploads

# --- Microservicios ---
# Servicio para token de Dropbox (si aplica)
DROPBOX_SERVICE_URL=https://tu-servicio-dropbox.run.app/api/v1/token
DROPBOX_SIGNATURE=tu_firma_secreta
DROPBOX_SERVICE_NAME=script_client

# Servicio de Escritura de Docs
MARKDOWN_WRITER_SERVICE_URL=https://tu-servicio-markdown.run.app/api/v1/write

# --- Configuración del Proceso ---
STARTING_ROW_NUMBER=134
INLINE_SIZE_LIMIT_MB=45.0
Nota Importante: Asegúrate de que la Service Account (client_email en sa_key.json) tenga permisos de Editor en el Google Sheet, en la carpeta de Drive destino y en el Google Doc que se va a editar.

▶️ Uso
1. Iniciar el Servidor
Ejecuta el servidor FastAPI localmente o en un servidor:

Bash

uvicorn main:app --reload --host 0.0.0.0 --port 8000
(Si usas puerto 8003 como en tus pruebas, ajusta el comando).

2. Configurar Google Sheets (App Script)
En tu hoja de cálculo, ve a Extensiones > Apps Script y utiliza el siguiente disparador para conectar con tu API:

JavaScript

function procesarFila() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var row = sheet.getActiveCell().getRow();
  var dropboxLink = sheet.getRange(row, 3).getValue(); // Asume Col C
  var cliente = "Cliente_" + row;

  // 1. Crear Doc vacío
  var doc = DocumentApp.create(cliente + " - Reporte IA");
  var docId = doc.getId();
  
  // 2. Llamar a la API
  var payload = {
    "dropbox_link": dropboxLink,
    "client_name": cliente,
    "destination_doc_id": docId,
    "spreadsheet_id": SpreadsheetApp.getActiveSpreadsheet().getId(),
    "worksheet_name": sheet.getName(),
    "row_number": row,
    "status_column": "E",
    "result_column": "D",
    "prompt_doc_id": "ID_DEL_PROMPT_MAESTRO"
  };

  var options = {
    'method' : 'post',
    'contentType': 'application/json',
    'payload' : JSON.stringify(payload)
  };
  
  // Reemplaza con la URL pública de tu API (ej. ngrok)
  UrlFetchApp.fetch('https://tu-api.ngrok-free.app/process-document', options);
  sheet.getRange(row, 5).setValue("En cola...");
}
📂 Estructura del Proyecto
Plaintext

.
├── ai_processor.py       # Lógica de interacción con Vertex AI (Gemini)
├── auth.py               # Manejo de credenciales de Google
├── config.py             # Clase de configuración (carga .env)
├── logger.py             # Configuración centralizada de logs
├── main.py               # Punto de entrada de FastAPI
├── routes.py             # Definición de endpoints (/process-document)
├── schemas.py            # Modelos Pydantic (Request/Response)
├── services_dropbox.py   # Lógica de descarga de Dropbox
├── services_gcs.py       # Subida/Bajada de archivos a Google Cloud Storage
├── services_workspace.py # Escritura en Docs y actualización de Sheets
├── worker.py             # Tarea en segundo plano (Orquestador principal)
├── requirements.txt      # Dependencias
├── .env                  # Variables de entorno (NO SUBIR A GIT)
└── logs/                 # Carpeta de logs generados
🐛 Troubleshooting Común
Error 403 (Forbidden) al escribir en el Doc:

Verifica que compartiste el Google Doc (o la carpeta donde se creó) con el email de la Service Account.

Error 403 en el Microservicio Markdown Writer:

Asegúrate de que el servicio en Cloud Run tenga habilitada la opción "Allow unauthenticated invocations" o implementa el envío de tokens ID.

El proceso se queda en "En cola...":

Revisa los logs en la carpeta logs/worker.log para ver si hubo error en la descarga o en la IA.

📄 Licencia
Propiedad confidencial. Uso interno.