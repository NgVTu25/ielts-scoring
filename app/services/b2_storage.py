# File: app/services/b2_storage.py
import os
import boto3
from botocore.client import Config

B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
B2_ENDPOINT_URL = os.getenv("B2_ENDPOINT_URL")
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")

_b2_resource = None


def get_b2_resource():
    global _b2_resource
    if _b2_resource is None:
        if not all([B2_BUCKET_NAME, B2_ENDPOINT_URL, B2_KEY_ID, B2_APPLICATION_KEY]):
            raise ValueError("Chưa cấu hình đầy đủ biến môi trường B2.")

        _b2_resource = boto3.resource(
            's3',
            endpoint_url=B2_ENDPOINT_URL,
            aws_access_key_id=B2_KEY_ID,
            aws_secret_access_key=B2_APPLICATION_KEY,
            config=Config(signature_version='s3v4')
        )
        print("B2 Resource initialized.")
    return _b2_resource


def upload_audio_file(submission_id: str, audio_bytes: bytes, content_type: str) -> str:
    s3 = get_b2_resource()
    bucket = s3.Bucket(B2_BUCKET_NAME)

    blob_name = f"ielts_submissions/{submission_id}"

    bucket.put_object(
        Key=blob_name,
        Body=audio_bytes,
        ContentType=content_type,
        ACL='public-read'
    )

    public_url = f"{B2_ENDPOINT_URL}/{B2_BUCKET_NAME}/{blob_name}"
    return public_url


def delete_audio_file(public_url: str):
    s3 = get_b2_resource()
    bucket = s3.Bucket(B2_BUCKET_NAME)

    try:
        prefix_to_remove = f"{B2_ENDPOINT_URL}/{B2_BUCKET_NAME}/"
        blob_name = public_url.replace(prefix_to_remove, "")

        # Xóa object
        bucket.Object(blob_name).delete()
        print(f"Đã xóa file B2: {blob_name}")
    except Exception as e:
        print(f"Lỗi khi xóa file B2 {public_url}: {e}")