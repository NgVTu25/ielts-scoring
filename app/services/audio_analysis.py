import librosa
import numpy as np
from pydub import AudioSegment, silence

DEFAULT_SCORE_ON_FAILURE = 5.0


def analyze_pronunciation(audio_path):
    try:
        # Load audio (mono)
        y, sr = librosa.load(audio_path, sr=None)
        duration = len(y) / sr

        # File
        if duration < 0.5:
            print("Warning: Audio too short for pronunciation analysis.")
            return DEFAULT_SCORE_ON_FAILURE

        # Check volume
        mean_amp = np.mean(np.abs(y))
        if mean_amp < 0.005:
            print("Warning: Audio volume too low. Returning default score.")
            return DEFAULT_SCORE_ON_FAILURE

        # -------------------------------
        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7')
            )
            valid_f0 = f0[~np.isnan(f0)]

            if len(valid_f0) > 0:
                pitch_std_dev = np.std(valid_f0)
            else:
                raise ValueError("No valid f0 detected with pyin")

        except Exception as e:
            print(f"Fallback to piptrack due to pyin error: {e}")

            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            median_magnitude = np.median(magnitudes)
            pitch_values = pitches[magnitudes > median_magnitude]
            positive_pitches = pitch_values[pitch_values > 0]

            if len(positive_pitches) == 0:
                print("Warning: Could not detect reliable pitch track even with piptrack.")
                return DEFAULT_SCORE_ON_FAILURE

            pitch_std_dev = np.std(positive_pitches)


        clarity_score = 9.0 - (pitch_std_dev / 15)

        clarity_score = min(max(clarity_score, 3.0), 9.0)
        return round(clarity_score, 1)

    except Exception as e:
        print(f"ERROR in pronunciation analysis: {e}. Returning default score.")
        return DEFAULT_SCORE_ON_FAILURE


def analyze_fluency(audio_path):
    try:
        audio = AudioSegment.from_file(audio_path)

        if len(audio) == 0:
            return DEFAULT_SCORE_ON_FAILURE

        # Ngưỡng im lặng tương đối: thấp hơn 16 dB so với mức trung bình của audio
        silence_thresh = audio.dBFS - 14

        silences = silence.detect_silence(
            audio,
            min_silence_len=700,  # Khoảng lặng tối thiểu 0.5 giây
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