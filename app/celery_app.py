# File: app/celery_app.py
from celery import Celery
from .database import SessionLocal
from .models.submission import Submission, SubmissionStatus
from .services.speech_to_text import transcribe_audio
from .services.scoring import evaluate_speaking
from .services.b2_storage import delete_audio_file, download_audio_file
from . import database
import os
import re
import tempfile
import librosa

MIN_DURATION_SECONDS = 45

# --- Init Database Schema ---
database.Base.metadata.create_all(bind=database.engine)

# --- Constants ---
MIN_ENGLISH_RATIO = 0.5
REDIS_URL = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL")

# --- Celery App Config ---
celery_app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.task_acks_late = True
celery_app.conf.broker_transport_options = {"visibility_timeout": 1800}
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.worker_prefetch_multiplier = 1  


def set_scores_to_zero(submission, reason: str):
    submission.transcript = reason
    submission.fluency = 0.0
    submission.pronunciation = 0.0
    submission.grammar = 0.0
    submission.vocabulary = 0.0
    submission.task_response = 0.0
    submission.overall = 0.0
    submission.grammar_feedback = "Scoring aborted."
    submission.vocabulary_feedback = "Scoring aborted."
    submission.task_response_feedback = "Scoring aborted."
    submission.overall_feedback = "Scoring aborted."
    submission.status = SubmissionStatus.COMPLETED


@celery_app.task(
    name="process_submission",
    autoretry_for=(),   # Tắt auto retry
    retry=False,        # Không lặp task khi fail
    acks_late=True,     # Xác nhận sau khi xử lý xong
)
def process_submission(submission_id: str, blob_name: str, topic_prompt: str):
    db = SessionLocal()
    temp_audio_path = None

    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            print(f"Submission {submission_id} not found.")
            return

        submission.status = SubmissionStatus.PROCESSING
        db.commit()

        print(f"Downloading audio key from B2: {blob_name}")
        audio_bytes = download_audio_file(blob_name)
        if not audio_bytes:
            raise ValueError("Tải file thất bại (file rỗng).")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            temp_audio_path = tmp_file.name

            try:
                # Dùng librosa để lấy độ dài file audio một cách hiệu quả
                duration = librosa.get_duration(path=temp_audio_path)
                print(f"Audio duration: {duration:.2f} seconds.")

                if duration < MIN_DURATION_SECONDS:
                    reason = (
                        f"[Insufficient audio length. "
                        f"{duration:.2f}s is less than the required {MIN_DURATION_SECONDS}s. "
                        f"Scoring aborted.]"
                    )
                    set_scores_to_zero(submission, reason)
                    db.commit()
                    return  # Quan trọng: Kết thúc task ngay tại đây

            except Exception as e:
                # Nếu không thể đọc file audio (ví dụ file hỏng), báo lỗi và thất bại
                print(f"ERROR: Could not get audio duration: {e}")
                submission.status = SubmissionStatus.FAILED
                submission.transcript = f"[ERROR] Could not process audio file: {e}"
                db.commit()
                return  # Kết thúc task


        transcription_result = transcribe_audio(temp_audio_path)
        transcript = transcription_result["text"]
        language = transcription_result["language"]

        if language.lower() != "en":
            set_scores_to_zero(submission, f"[Language Detected: {language.upper()}. Only English is scored.]")
            db.commit()
            return

        total_words = len(transcript.split())
        if total_words < 5:
            set_scores_to_zero(submission, "[Insufficient content. Too few words to score.]")
            db.commit()
            return

        english_words = re.findall(r"[a-zA-Z]+", transcript)
        english_ratio = len(english_words) / max(total_words, 1)
        if english_ratio < MIN_ENGLISH_RATIO:
            set_scores_to_zero(submission, f"[Insufficient English content (Ratio: {english_ratio:.2f}). Scoring aborted.]")
            db.commit()
            return

        print(f"Submission {submission_id}: All checks passed. Proceeding to scoring.")
        submission.transcript = transcript
        results = evaluate_speaking(temp_audio_path, transcript, topic_prompt)

        submission.fluency = results.get("fluency")
        submission.pronunciation = results.get("pronunciation")
        submission.grammar = results.get("grammar")
        submission.vocabulary = results.get("vocabulary")
        submission.task_response = results.get("task_response")
        submission.overall = results.get("overall")

        submission.task_response_feedback = results.get("feedback", {}).get("task_response")
        submission.grammar_feedback = results.get("feedback", {}).get("grammar")
        submission.vocabulary_feedback = results.get("feedback", {}).get("vocabulary")
        submission.overall_feedback = results.get("feedback", {}).get("overall")

        submission.status = SubmissionStatus.COMPLETED
        db.commit()

        print(f"✅ Successfully processed submission {submission_id}")

    except Exception as e:
        print(f"❌ Error processing submission {submission_id}: {e}")
        if 'submission' in locals():
            submission.status = SubmissionStatus.FAILED
            submission.transcript = f"[ERROR] {e}"
            db.commit()

    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

        if blob_name:
            try:
                delete_audio_file(blob_name)
            except Exception as e:
                print(f"⚠️ WARNING: Failed to delete B2 file {blob_name}: {e}")

        db.close()
