import librosa
import numpy as np
from pydub import AudioSegment, silence

DEFAULT_SCORE_ON_FAILURE = 5.0


def analyze_pronunciation(audio_path):

    try:
        y, sr = librosa.load(audio_path)
        # Nếu audio quá ngắn, trả về điểm mặc định
        if len(y) < sr * 0.5:  # Yêu cầu audio dài ít nhất 0.5 giây
            print("Warning: Audio too short for pronunciation analysis.")
            return DEFAULT_SCORE_ON_FAILURE

        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

        median_magnitude = np.median(magnitudes)
        if median_magnitude > 0:
            pitch_values = pitches[magnitudes > median_magnitude]
        else:
            pitch_values = []

        # Nếu sau khi lọc vẫn không có pitch nào hợp lệ
        if len(pitch_values) == 0 or np.all(pitch_values <= 0):
            print("Warning: Could not detect a reliable pitch track. Returning default score.")
            return DEFAULT_SCORE_ON_FAILURE

        # Chỉ lấy các pitch dương để tính toán
        positive_pitches = pitch_values[pitch_values > 0]

        if len(positive_pitches) == 0:
            return DEFAULT_SCORE_ON_FAILURE
        pitch_std_dev = np.std(positive_pitches)
        clarity_score = max(5.0, 9.0 - (pitch_std_dev / 15))  # Tăng mẫu số để điểm không bị trừ quá nhiều

        return round(clarity_score, 1)

    except Exception as e:
        # Nếu có bất kỳ lỗi nào khác xảy ra trong librosa
        print(f"ERROR in pronunciation analysis: {e}. Returning default score.")
        return DEFAULT_SCORE_ON_FAILURE


def analyze_fluency(audio_path):
    try:
        audio = AudioSegment.from_file(audio_path)

        if len(audio) == 0:
            return DEFAULT_SCORE_ON_FAILURE

        # Ngưỡng im lặng tương đối: thấp hơn 16 dB so với mức trung bình của audio
        silence_thresh = audio.dBFS - 16

        silences = silence.detect_silence(
            audio,
            min_silence_len=1000,  # Khoảng lặng tối thiểu 0.5 giây
            silence_thresh=silence_thresh
        )

        total_silence_ms = sum([end - start for start, end in silences])
        total_duration_ms = len(audio)

        silence_ratio = total_silence_ms / total_duration_ms

        # Công thức heuristic: tỷ lệ im lặng thấp -> điểm cao
        fluency_score = max(5.0, 9.0 - silence_ratio * 15)
        return round(fluency_score, 1)

    except Exception as e:
        print(f"ERROR in fluency analysis: {e}. Returning default score.")
        return DEFAULT_SCORE_ON_FAILURE