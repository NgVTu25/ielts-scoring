# File: app/services/firebase_storage.py

import os
import firebase_admin
from firebase_admin import credentials, storage
import json

# Lấy nội dung JSON credentials từ biến môi trường
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_BUCKET_NAME = os.getenv("FIREBASE_BUCKET_NAME")


# Hàm khởi tạo Firebase
def initialize_firebase():
    if not firebase_admin._apps:
        if not FIREBASE_CREDENTIALS_JSON or not FIREBASE_BUCKET_NAME:
            raise ValueError("Firebase credentials or bucket name not configured.")

        # Chuyển chuỗi JSON thành dictionary
        cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)

        firebase_admin.initialize_app(cred, {
            'storageBucket': FIREBASE_BUCKET_NAME
        })
        print("Firebase initialized.")


def upload_audio_file(submission_id: str, audio_bytes: bytes, file_extension: str) -> str:
    """Upload file bytes to Firebase Storage and return the public URL."""
    initialize_firebase()
    bucket = storage.bucket()
    blob_name = f"ielts_submissions/{submission_id}{file_extension}"
    blob = bucket.blob(blob_name)

    # Upload file
    blob.upload_from_string(audio_bytes, content_type='audio/wav')  # Thay đổi content_type nếu cần

    # Tạo URL công khai có thể tải xuống
    blob.make_public()
    return blob.public_url


def delete_audio_file(public_url: str):
    """Delete file from Firebase Storage using its public URL."""
    initialize_firebase()
    bucket = storage.bucket()

    bucket_prefix = f"https://storage.googleapis.com/{FIREBASE_BUCKET_NAME}/"
    blob_name = public_url.replace(bucket_prefix, "")

    blob = bucket.blob(blob_name)
    if blob.exists():
        blob.delete()
        print(f"Deleted file: {blob_name}")