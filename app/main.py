# File: ielts-scorer/app/main.py
from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from sqlalchemy.orm import Session
import os
from . import database, utils
from .models import submission as models
from .celery_app import process_submission
from typing import Dict, Any

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Free AI IELTS Speaking Scoring System")

if os.getenv("USE_NGROK", "false").lower() == "true":
    try:
        from .ngrok_setup import start_ngrok
        public_url = start_ngrok(port=8000)
        if public_url:
            print(f"🌍 Public API URL: {public_url}")
    except Exception as e:
        print(f"⚠️ Failed to start Ngrok: {e}")

UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)


@app.get("/")
def read_root():
    return {"message": "Welcome to the IELTS Speaking Scoring API"}


@app.post("/api/v1/submit", status_code=201)
def submit_speaking_test(
        user_id: str = Form(...),
        topic_prompt: str = Form(...),
        audio: UploadFile = File(...),
        db: Session = Depends(database.get_db)
) -> Dict[str, str]:
    submission_id = utils.generate_short_id()

    # --- PHẦN LOGIC LƯU FILE BỊ THIẾU ĐÃ ĐƯỢC THÊM LẠI ---
    try:
        file_extension = os.path.splitext(audio.filename)[1]
        if not file_extension:
            file_extension = ".mp3"
    except:
        file_extension = ".mp3"

    safe_filename = f"{submission_id}{file_extension}"
    file_location = os.path.join(UPLOADS_DIR, safe_filename)

    # Ghi nội dung file audio vào đĩa
    with open(file_location, "wb+") as file_object:
        file_object.write(audio.file.read())

    # Kiểm tra xem file có bị rỗng không
    if os.path.getsize(file_location) == 0:
        os.remove(file_location)
        raise HTTPException(status_code=400, detail="Uploaded file is empty or corrupted.")
    # --------------------------------------------------------

    # Bây giờ biến `file_location` đã tồn tại và hợp lệ
    db_submission = models.Submission(
        id=submission_id,
        user_id=user_id,
        audio_path=file_location,  # <-- Dòng này sẽ hoạt động
        status=models.SubmissionStatus.PENDING,
        topic_prompt=topic_prompt
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)

    process_submission.delay(submission_id, file_location, topic_prompt)

    return {"submission_id": submission_id, "status": "PENDING"}


@app.get("/api/v1/result/{submission_id}")
def get_result(
        submission_id: str,
        db: Session = Depends(database.get_db)
) -> Dict[str, Any]:
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return {
        "submission_id": submission.id,
        "user_id": submission.user_id,
        "status": submission.status,
        "topic_prompt": submission.topic_prompt,
        "transcript": submission.transcript,
        "scores": {
            "fluency": submission.fluency,
            "pronunciation": submission.pronunciation,
            "task_response": submission.task_response,
            "grammar": submission.grammar,
            "vocabulary": submission.vocabulary,
            "overall": submission.overall,
        },
        "feedback": {
            "task_response": submission.task_response_feedback,
            "grammar": submission.grammar_feedback,
            "vocabulary": submission.vocabulary_feedback,
            "overall": submission.overall_feedback
        }
    }