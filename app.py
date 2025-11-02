import webview
import os
import base64
from datetime import datetime
from pipeline import listener

from pydub import AudioSegment
import io
import pickle

# Create recordings directory if it doesn't exist
RECORDINGS_DIR = "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)


class API:
    def save_audio(self, audio_base64, sentence="untitled"):
        """Save audio recording to a WAV file"""
        try:
            if not audio_base64:
                return {"success": False, "error": "No audio data provided"}

            # Remove data URL prefix if present
            if "," in audio_base64:
                audio_base64 = audio_base64.split(",")[1]

            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_sentence = "".join(c for c in sentence if c.isalnum() or c in (" ", "-", "_")).strip()
            safe_sentence = safe_sentence[:30]  # Limit length
            filename = f"tmp.wav"
            filepath = os.path.join(RECORDINGS_DIR, filename)

            # Save audio file using pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            audio.export(filepath, format="wav")

            print(f"Audio saved: {filepath}")

            return {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "message": "Audio saved successfully",
            }

        except Exception as e:
            print(f"Error saving audio: {str(e)}")
            return {"success": False, "error": str(e)}

    def analyze_audio(self, audio_base64, sentence):
        """Placeholder for AI analysis endpoint"""
        sentence = sentence.strip()

        try:
            filename = f"tmp.wav"
            filepath = os.path.join(RECORDINGS_DIR, filename)
            score, substituted, inserted, deleted, conversation, target_phonemes = listener(sentence, filepath)
            # with open("out.pkl", "w") as f:
            #     pickle.dumps((score, substituted, inserted, deleted, conversation), f)
            print(score, substituted, inserted, deleted, conversation)

            corrections = substituted + inserted + deleted

            return {
                "success": True,
                "sentence": target_phonemes,
                "corrections": corrections,
                "message": conversation,
                "score": score,
            }

        except Exception as e:
            print(e.with_traceback())
            print(f"Error analyzing audio: {str(e)}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    api = API()
    window = webview.create_window(
        "Speech Teacher",
        "frontend/index.html",
        js_api=api,
        fullscreen=False,
        resizable=True,
    )

    def on_ready():
        window.maximize()

    webview.start(on_ready)
