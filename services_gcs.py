# services_gcs.py
from google.cloud import storage
from logger import setup_logger

logger = setup_logger(__name__, 'services_gcs.log')

def upload_to_gcs(local_path, gcs_path, bucket_name, storage_client):
    """
    Sube un archivo local a Google Cloud Storage y devuelve su URI (gs://...).
    """
    try:
        logger.debug(f"Preparando subida a GCS - Bucket: {bucket_name}, Path: {gcs_path}")
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)

        logger.info(f"Subiendo archivo a GCS: gs://{bucket_name}/{gcs_path}")
        blob.upload_from_filename(local_path)

        gcs_uri = f"gs://{bucket_name}/{gcs_path}"
        logger.info(f"Archivo subido exitosamente a GCS: {gcs_uri}")
        return gcs_uri

    except Exception as e:
        logger.error(f"Error al subir archivo a GCS (bucket: {bucket_name}, path: {gcs_path}): {e}", exc_info=True)
        return None

def delete_from_gcs(gcs_path_list, bucket_name, storage_client):
    """
    Elimina una lista de archivos del bucket de GCS para limpiar espacio.
    """
    if not gcs_path_list:
        logger.debug("No hay archivos para eliminar de GCS")
        return

    logger.info(f"Iniciando eliminación de {len(gcs_path_list)} archivos de GCS")
    bucket = storage_client.bucket(bucket_name)

    for gcs_path in gcs_path_list:
        try:
            blob = bucket.blob(gcs_path)
            if blob.exists():
                logger.debug(f"Eliminando archivo de GCS: gs://{bucket_name}/{gcs_path}")
                blob.delete()
                logger.info(f"Archivo eliminado de GCS: {gcs_path}")
            else:
                logger.warning(f"Archivo no encontrado en GCS para eliminar: {gcs_path}")
        except Exception as e:
            logger.error(f"Error al eliminar archivo de GCS '{gcs_path}': {e}", exc_info=True)