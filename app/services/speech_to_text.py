# File: ielts-scorer/app/services/speech_to_text.py

import whisper
import torch
from typing import Dict

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_SIZE = "tiny"
print(f"Whisper will run on: {DEVICE}")

_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading Whisper model '{MODEL_SIZE}' on {DEVICE}...")
        _model = whisper.load_model(MODEL_SIZE, device=DEVICE)
    return _model


def transcribe_audio(file_path: str) -> Dict[str, str]:
    """
    Transcribes the audio file and returns both the text and detected language.
    """
    print(f"Transcribing audio file: {file_path}")
    model = get_model()
    use_fp16 = DEVICE != "cpu"

    result = model.transcribe(file_path, language='en', fp16=use_fp16)
    print(f"Transcription completed. Detected language: {result['language']}")

    return {
        "text": result["text"].strip(),
        "language": result["language"]
    }