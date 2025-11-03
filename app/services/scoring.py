import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .audio_analysis import analyze_fluency, analyze_pronunciation

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


def safe_float(val, default=5.5):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def evaluate_speaking(audio_path, transcript, topic_prompt):
    print("Starting evaluation...")

    pronunciation = analyze_pronunciation(audio_path)
    fluency = analyze_fluency(audio_path)

    grammar = vocabulary = task_response = 5.5
    grammar_feedback = vocabulary_feedback = task_response_feedback = overall_feedback = "N/A"

    if GEMINI_MODEL and transcript:
        response = None
        try:
            prompt = create_gemini_prompt(transcript, topic_prompt)
            print("Sending detailed request to Gemini API...")
            response = GEMINI_MODEL.generate_content(prompt)

            response_text = response.text.strip().replace("```json", "").replace("```", "")
            scores_data = json.loads(response_text)

            grammar_data = scores_data.get("grammar", {})
            vocab_data = scores_data.get("vocabulary", {})
            task_response_data = scores_data.get("task_response", {})

            grammar = safe_float(grammar_data.get("score"))
            vocabulary = safe_float(vocab_data.get("score"))
            task_response = safe_float(task_response_data.get("score"))

            grammar_feedback = grammar_data.get("feedback", "N/A")
            vocabulary_feedback = vocab_data.get("feedback", "N/A")
            task_response_feedback = task_response_data.get("feedback", "N/A")
            overall_feedback = scores_data.get("overall_feedback", "N/A")

            print("Gemini scores and feedback received successfully.")
        except Exception as e:
            print("\n" + "=" * 50)
            print("ERROR: Gemini API call failed.")
            print(f"Type: {type(e).__name__}, Details: {e}")
            if response:
                print("\n--- Gemini Raw Response ---")
                print(response.text)
                print("--- End ---\n")
            print("Fallback to default scores.")
            print("=" * 50 + "\n")

    overall = round((pronunciation + fluency + grammar + vocabulary + task_response) / 5, 1)

    print("Evaluation finished.")
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
