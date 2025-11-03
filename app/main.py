# File: ielts-scorer/app/main.py
from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from . import database, utils
from .models import submission as models
from .celery_app import process_submission
from typing import Dict, Any
from .services.b2_storage import upload_audio_file

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Free AI IELTS Speaking Scoring System")

@app.get("/")
def read_root():
    return {"message": "Welcome to the IELTS Speaking Scoring API"}


@app.post("/api/v1/submit", status_code=201)
async def submit_speaking_test(
        user_id: str = Form(...),
        topic_prompt: str = Form(...),
        audio: UploadFile = File(...),
        db: Session = Depends(database.get_db)
) -> Dict[str, str]:
    submission_id = utils.generate_short_id()

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        public_url = upload_audio_file(submission_id, audio_bytes, audio.content_type)
        print(f"File uploaded to B2: {public_url}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to storage: {e}")

    db_submission = models.Submission(
        id=submission_id,
        user_id=user_id,
        audio_path=public_url,
        status=models.SubmissionStatus.PENDING,
        topic_prompt=topic_prompt
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)

    process_submission.delay(submission_id, public_url, topic_prompt)

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