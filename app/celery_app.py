# File: app/celery_app.py (Đã chuyển sang B2)

from celery import Celery
from .database import SessionLocal
from .models.submission import Submission, SubmissionStatus
from .services.speech_to_text import transcribe_audio
from .services.scoring import evaluate_speaking
import os
import re
import requests
import tempfile
# --- THAY ĐỔI 1: Import từ b2_storage ---
from .services.b2_storage import delete_audio_file

MIN_ENGLISH_RATIO = 0.5
REDIS_URL = os.getenv("CELERY_BROKER_URL")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)


# ... (hàm set_scores_to_zero giữ nguyên) ...
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


@celery_app.task(name="process_submission")
def process_submission(submission_id: str, public_url: str, topic_prompt: str):
    db = SessionLocal()
    temp_audio_path = None
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            print(f"Submission {submission_id} not found.")
            return

        submission.status = SubmissionStatus.PROCESSING
        db.commit()

        # --- TẢI FILE (Logic này giữ nguyên, vì nó hoạt động với mọi URL) ---
        print(f"Downloading audio from: {public_url}")

        response = requests.get(public_url, timeout=30)
        if response.status_code != 200:
            raise ValueError(f"Failed to download audio. Status: {response.status_code}")

        file_extension = os.path.splitext(public_url)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(response.content)
            temp_audio_path = tmp_file.name

        audio_file_path = temp_audio_path
        # -----------------------------------------------------------------

        # BƯỚC 2: Chuyển đổi giọng nói (Giữ nguyên)
        transcription_result = transcribe_audio(audio_file_path)
        transcript = transcription_result["text"]
        language = transcription_result["language"]

        # BƯỚC 3: Kiểm tra sơ bộ (Giữ nguyên)
        # ... (toàn bộ logic kiểm tra ngôn ngữ, số lượng từ, v.v. giữ nguyên) ...
        if language != "en":
            set_scores_to_zero(submission, f"[Language Detected: {language.upper()}. Only English is scored.]")
            db.commit()
            return
        total_words = len(transcript.split()) if transcript else 0
        if total_words < 5:
            set_scores_to_zero(submission, "[Insufficient content. Too few words to score.]")
            db.commit()
            return
        english_words = re.findall(r'[a-zA-Z]+', transcript)
        if total_words > 0 and (len(english_words) / total_words) < MIN_ENGLISH_RATIO:
            english_ratio = len(english_words) / total_words
            set_scores_to_zero(submission,
                               f"[Insufficient English content (Ratio: {english_ratio:.2f}). Scoring aborted.]")
            db.commit()
            return

        # BƯỚC 4: Chấm điểm (Giữ nguyên)
        print(f"Submission {submission_id}: All checks passed. Proceeding to scoring.")
        submission.transcript = transcript

        results = evaluate_speaking(audio_file_path, transcript, topic_prompt)

        # BƯỚC 5: Lưu kết quả (Giữ nguyên)
        # ... (toàn bộ logic lưu điểm và feedback giữ nguyên) ...
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
        # Dọn dẹp file tạm
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

        # Dọn dẹp file B2
        if public_url:
            try:
                delete_audio_file(public_url)
            except Exception as e:
                # --- THAY ĐỔI 2: Cập nhật thông báo lỗi ---
                print(f"WARNING: Failed to delete B2 file {public_url}: {e}")

        if db.is_active:
            db.close()