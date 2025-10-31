# File: app/celery_app.py

from celery import Celery
from .database import SessionLocal
from .models.submission import Submission, SubmissionStatus
from .services.speech_to_text import transcribe_audio
from .services.scoring import evaluate_speaking
import os
import re

MIN_ENGLISH_RATIO = 0.5

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)


def set_scores_to_zero(submission, reason: str):
    """Hàm phụ được cập nhật để gán điểm 0 cho tất cả các tiêu chí."""
    submission.transcript = reason
    submission.fluency = 0.0
    submission.pronunciation = 0.0
    submission.grammar = 0.0
    submission.vocabulary = 0.0
    submission.task_response = 0.0  # <-- Thêm reset
    submission.overall = 0.0
    # Xóa các feedback cũ
    submission.grammar_feedback = "Scoring aborted."
    submission.vocabulary_feedback = "Scoring aborted."
    submission.task_response_feedback = "Scoring aborted."
    submission.overall_feedback = "Scoring aborted."
    submission.status = SubmissionStatus.COMPLETED


@celery_app.task(name="process_submission")
def process_submission(submission_id: str, audio_path: str, topic_prompt: str):  # <-- SỬA LỖI 2: Thêm topic_prompt
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            print(f"Submission {submission_id} not found.")
            return

        # BƯỚC 1: Cập nhật trạng thái sang PROCESSING
        submission.status = SubmissionStatus.PROCESSING
        db.commit()

        # BƯỚC 2: Chuyển đổi giọng nói thành văn bản
        transcription_result = transcribe_audio(audio_path)
        transcript = transcription_result["text"]
        language = transcription_result["language"]

        # BƯỚC 3: Thực hiện các kiểm tra sơ bộ
        if language != "en":
            print(f"Submission {submission_id}: Non-English language ('{language}') detected. Scoring aborted.")
            set_scores_to_zero(submission, f"[Language Detected: {language.upper()}. Only English is scored.]")
            db.commit()
            return

        total_words = len(transcript.split()) if transcript else 0
        if total_words < 5:
            print(f"Submission {submission_id}: Insufficient content ({total_words} words). Scoring aborted.")
            set_scores_to_zero(submission, "[Insufficient content. Too few words to score.]")
            db.commit()
            return

        english_words = re.findall(r'[a-zA-Z]+', transcript)
        if total_words > 0 and (len(english_words) / total_words) < MIN_ENGLISH_RATIO:
            english_ratio = len(english_words) / total_words
            print(
                f"Submission {submission_id}: English content ratio ({english_ratio:.2f}) is below threshold. Scoring aborted.")
            set_scores_to_zero(submission,
                               f"[Insufficient English content (Ratio: {english_ratio:.2f}). Scoring aborted.]")
            db.commit()
            return

        # BƯỚC 4: Nếu tất cả kiểm tra đều qua, tiến hành chấm điểm (CHỈ MỘT LẦN)
        print(f"Submission {submission_id}: All checks passed. Proceeding to scoring.")
        submission.transcript = transcript  # Lưu transcript thật vào DB

        results = evaluate_speaking(audio_path, transcript, topic_prompt)

        # BƯỚC 5: Lưu tất cả kết quả vào CSDL
        submission.fluency = results["fluency"]
        submission.pronunciation = results["pronunciation"]
        submission.grammar = results["grammar"]
        submission.vocabulary = results["vocabulary"]
        submission.task_response = results["task_response"]
        submission.overall = results["overall"]

        submission.grammar_feedback = results["grammar_feedback"]
        submission.vocabulary_feedback = results["vocabulary_feedback"]
        submission.task_response_feedback = results["task_response_feedback"]
        submission.overall_feedback = results["overall_feedback"]

        submission.status = SubmissionStatus.COMPLETED
        db.commit()
        print(f"Successfully processed submission {submission_id}")

    except Exception as e:
        print(f"Error processing submission {submission_id}: {e}")
        if 'submission' in locals() and db.is_active:
            submission.status = SubmissionStatus.FAILED
            submission.transcript = f"[ERROR] An error occurred during processing: {e}"
            db.commit()
    finally:
        if db.is_active:
            db.close()