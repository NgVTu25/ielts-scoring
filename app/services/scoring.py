import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .audio_analysis import analyze_fluency, analyze_pronunciation
import time
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found.")
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_MODEL = genai.GenerativeModel("gemini-flash-latest")
    print("Gemini API configured successfully.")
except Exception as e:
    print(f"WARNING: Gemini API configuration failed. Falling back to defaults. {e}")
    GEMINI_MODEL = None


def create_gemini_prompt(transcript, topic_prompt):
    # (Hàm này giữ nguyên, không thay đổi)
    return f"""
    You are a professional IELTS examiner providing a detailed evaluation.

    **Instructions:**
    1. Analyze the transcript based on Task Response, Grammatical Range and Accuracy, and Lexical Resource (Vocabulary).
    2. Give scores (1.0–9.0) and feedback for each criterion.
    3. Provide one "Overall Feedback" summarizing strengths and weaknesses.
    4. Output a single valid JSON only — no markdown.

    {{
      "task_response": {{"score": <float>, "feedback": "..." }},
      "grammar": {{"score": <float>, "feedback": "..." }},
      "vocabulary": {{"score": <float>, "feedback": "..." }},
      "overall_feedback": "..."
    }}

    ---
    Topic: {topic_prompt}
    ---
    Transcript: {transcript}
    ---
    """

# Điều này cần thiết để submit nó vào thread pool
def get_gemini_scores(transcript, topic_prompt):
    if not GEMINI_MODEL or not transcript:
        print("⚠️ Skipping Gemini: Model not configured or no transcript.")
        return None

    try:
        prompt = create_gemini_prompt(transcript, topic_prompt)
        print("Sending request to Gemini... (with timeout)")

        start_gemini = time.time()
        response = GEMINI_MODEL.generate_content(
            prompt,
            request_options={"timeout": 210}
        )
        print(f"[TIME] Gemini API call: {time.time() - start_gemini:.2f}s")

        response_text = response.text.strip().replace("```json", "").replace("```", "")
        scores_data = json.loads(response_text)
        print("✅ Gemini scoring completed.")
        return scores_data

    except Exception as e:
        print(f"⚠️ Gemini request failed: {e}")
        return None


def safe_float(val, default=5.5):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def evaluate_speaking(audio_path, transcript, topic_prompt):
    print("Starting evaluation...")
    overall_start_time = time.time()  # Thêm log tổng thời gian

    pronunciation = 5.5
    fluency = 5.5
    grammar = 5.5
    vocabulary = 5.5
    task_response = 5.5
    grammar_feedback = "N/A"
    vocabulary_feedback = "N/A"
    task_response_feedback = "N/A"
    overall_feedback = "N/A"

    gemini_results = None

    # [TỐI ƯU] 3. Sử dụng ThreadPoolExecutor để chạy 3 tác vụ song song
    with ThreadPoolExecutor(max_workers=3) as executor:
        print("Submitting tasks: Pronunciation, Fluency, Gemini...")

        # Submit 3 tác vụ
        future_pron = executor.submit(analyze_pronunciation, audio_path)
        future_fluency = executor.submit(analyze_fluency, audio_path)
        future_gemini = executor.submit(get_gemini_scores, transcript, topic_prompt)

        # Lấy kết quả (hàm .result() sẽ chờ cho đến khi tác vụ đó hoàn thành)
        try:
            # Lấy kết quả phân tích phát âm
            pronunciation = future_pron.result()
            print(f"[TIME] Pronunciation analysis finished.")
        except Exception as e:
            print(f"⚠️ Pronunciation analysis failed: {e}")
            # pronunciation vẫn là 5.5 (mặc định)

        try:
            # Lấy kết quả phân tích trôi chảy
            fluency = future_fluency.result()
            print(f"[TIME] Fluency analysis finished.")
        except Exception as e:
            print(f"⚠️ Fluency analysis failed: {e}")
            # fluency vẫn là 5.5 (mặc định)

        try:
            # Lấy kết quả từ Gemini
            gemini_results = future_gemini.result()
            # Log thời gian đã được chuyển vào hàm get_gemini_scores()
        except Exception as e:
            print(f"⚠️ Gemini task submission/result failed: {e}")
            # gemini_results vẫn là None

    # --- Xử lý kết quả Gemini (nếu thành công) ---
    if gemini_results:
        print("Processing Gemini results...")
        grammar_data = gemini_results.get("grammar", {})
        vocab_data = gemini_results.get("vocabulary", {})
        task_response_data = gemini_results.get("task_response", {})

        grammar = safe_float(grammar_data.get("score"))
        vocabulary = safe_float(vocab_data.get("score"))
        task_response = safe_float(task_response_data.get("score"))

        grammar_feedback = grammar_data.get("feedback", "N/A")
        vocabulary_feedback = vocab_data.get("feedback", "N/A")
        task_response_feedback = task_response_data.get("feedback", "N/A")
        overall_feedback = gemini_results.get("overall_feedback", "N/A")
    else:
        print("→ Using default midpoint scores for Grammar, Vocab, TR.")

    # Compute final overall band
    overall = round((pronunciation + fluency + grammar + vocabulary + task_response) / 5, 1)

    print(f"\n[TIME] Total evaluation finished in: {time.time() - overall_start_time:.2f}s")
    return {
        "fluency": fluency,
        "pronunciation": pronunciation,
        "grammar": round(grammar, 1),
        "vocabulary": round(vocabulary, 1),
        "task_response": round(task_response, 1),
        "overall": overall,
        "feedback": {
            "grammar": grammar_feedback,
            "vocabulary": vocabulary_feedback,
            "task_response": task_response_feedback,
            "overall": overall_feedback
        }
    }