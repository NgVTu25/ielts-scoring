# File: ielts-scorer/app/services/scoring.py
# PHIÊN BẢN ĐÃ SỬA LỖI HOÀN CHỈNH

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .audio_analysis import analyze_fluency, analyze_pronunciation

# Tải biến môi trường từ file .env
load_dotenv()

# Cấu hình Gemini API
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_MODEL = genai.GenerativeModel('gemini-flash-latest')
    print("Gemini API configured successfully.")
except Exception as e:
    print(f"WARNING: Gemini API configuration failed. Falling back to default scores. Error: {e}")
    GEMINI_MODEL = None


def create_gemini_prompt(transcript, topic_prompt):
    """Prompt được nâng cấp để chấm cả Task Response."""
    return f"""
    You are a professional IELTS examiner providing a detailed evaluation.

    **Instructions:**

    1.  **Analyze the transcript** based on three criteria: "Task Response", "Grammatical Range and Accuracy", and "Lexical Resource" (Vocabulary).
    2.  For **"Task Response"**, evaluate how well the candidate addressed the provided topic. Is the answer relevant, fully developed, and coherent?
    3.  **Provide a score** from 1.0 to 9.0 for each criterion.
    4.  **Provide detailed, constructive feedback** for each criterion, including strengths and weaknesses with specific examples.
    5.  **Provide an "Overall Feedback"** and the single most important piece of advice.
    6.  **Your final output MUST be a single, valid JSON object** without any surrounding text or markdown.

    **JSON Output Structure:**

    {{
      "task_response": {{
        "score": <float>,
        "feedback": "Feedback on relevance, development, and coherence."
      }},
      "grammar": {{
        "score": <float>,
        "feedback": "Feedback on grammar."
      }},
      "vocabulary": {{
        "score": <float>,
        "feedback": "Feedback on vocabulary."
      }},
      "overall_feedback": "Overall summary and main advice."
    }}

    ---
    **Topic/Prompt:**
    {topic_prompt}
    ---
    **Transcript to Evaluate:**
    {transcript}
    ---
    """


def evaluate_speaking(audio_path, transcript, topic_prompt):  # <-- SỬA LỖI 1: Thêm topic_prompt vào đây
    print("Starting evaluation...")
    pronunciation = analyze_pronunciation(audio_path)
    fluency = analyze_fluency(audio_path)

    grammar, vocabulary, task_response = 5.5, 5.5, 5.5
    grammar_feedback, vocabulary_feedback, task_response_feedback, overall_feedback = "N/A", "N/A", "N/A", "N/A"

    if GEMINI_MODEL and transcript:
        # --- THAY THẾ KHỐI TRY...EXCEPT CŨ BẰNG KHỐI NÀY ---
        response = None  # Khởi tạo biến response
        try:
            prompt = create_gemini_prompt(transcript, topic_prompt)
            print("Sending detailed request to Gemini API...")
            response = GEMINI_MODEL.generate_content(prompt)

            # Cố gắng parse JSON
            response_text = response.text.strip().replace('```json', '').replace('```', '')
            scores_data = json.loads(response_text)

            # ... (phần code lấy điểm và feedback từ scores_data giữ nguyên) ...
            grammar_data = scores_data.get("grammar", {})
            vocab_data = scores_data.get("vocabulary", {})
            task_response_data = scores_data.get("task_response", {})

            grammar = float(grammar_data.get("score", 5.5))
            vocabulary = float(vocab_data.get("score", 5.5))
            task_response = float(task_response_data.get("score", 5.5))

            grammar_feedback = grammar_data.get("feedback", "N/A")
            vocabulary_feedback = vocab_data.get("feedback", "N/A")
            task_response_feedback = task_response_data.get("feedback", "N/A")
            overall_feedback = scores_data.get("overall_feedback", "N/A")

            print(f"Gemini scores and feedback received successfully.")

        except Exception as e:
            print("\n" + "=" * 50)
            print("ERROR: An exception occurred during the Gemini API call.")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Details: {e}")
            if response:
                print("\n--- Gemini's Raw Response ---")
                print(response.text)
                print("--- End of Raw Response ---\n")
            print("Falling back to default scores.")
            print("=" * 50 + "\n")

    overall = (pronunciation + fluency + grammar + vocabulary) / 4

    print("Evaluation finished.")
    return {
        "fluency": fluency,
        "pronunciation": pronunciation,
        "grammar": round(grammar, 1),
        "vocabulary": round(vocabulary, 1),
        "overall": round(overall, 1),
        "grammar_feedback": grammar_feedback,
        "vocabulary_feedback": vocabulary_feedback,
        "overall_feedback": overall_feedback,
        # --- SỬA LỖI 3: Thêm lại các trường bị thiếu vào kết quả trả về ---
        "task_response": round(task_response, 1),
        "task_response_feedback": task_response_feedback
        # -------------------------------------------------------------
    }