# File: ielts-scorer/app/services/speech_to_text.py
# VUI LÒNG ĐẢM BẢO FILE CỦA BẠN CÓ NỘI DUNG NHƯ THẾ NÀY

import whisper
import torch
from typing import Dict

# Check for GPU availability
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Whisper will run on: {DEVICE}")

# Load the model once
model = whisper.load_model("small", device=DEVICE)


def transcribe_audio(file_path: str) -> Dict[str, str]:
    """
    Transcribes the audio file and returns both the text and detected language.
    """
    print(f"Transcribing audio file: {file_path}")
    # Thêm 'language': 'en' để ưu tiên và tăng độ chính xác cho tiếng Anh
    result = model.transcribe(file_path, language='en', fp16=False if DEVICE == 'cpu' else True)
    print(f"Transcription completed. Detected language: {result['language']}")

    # HÀM NÀY PHẢI TRẢ VỀ MỘT DICTIONARY
    return {
        "text": result["text"].strip(),
        "language": result["language"]
    }