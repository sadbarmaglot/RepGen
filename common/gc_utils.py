import uuid

from google.cloud import storage

from settings import BUCKET_NAME

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

async def upload_to_gcs(file_path, suffix):
    filename = f"{uuid.uuid4()}.{suffix}"
    blob = bucket.blob(filename)
    blob.upload_from_filename(file_path)
    return blob, blob.public_url
