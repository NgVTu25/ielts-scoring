# File: ielts-scorer/app/services/speech_to_text.py
from faster_whisper import WhisperModel
from typing import Dict
import torch

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_SIZE = "tiny"
print(f"Faster-Whisper will run on: {DEVICE}")

_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading Faster-Whisper model '{MODEL_SIZE}' on {DEVICE}...")
        _model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type="int8")
    return _model


def transcribe_audio(file_path: str) -> Dict[str, str]:
    print(f"Transcribing audio file: {file_path}")
    model = get_model()

    segments, info = model.transcribe(file_path, language="en")

    text = " ".join([segment.text for segment in segments]).strip()
    print(f"Transcription completed. Detected language: {info.language}")

    return {
        "text": text,
        "language": info.language
    }
