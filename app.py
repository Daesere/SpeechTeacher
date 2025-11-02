import webview
import os
import base64
from datetime import datetime

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
            filename = f"{timestamp}_{safe_sentence}.wav"
            filepath = os.path.join(RECORDINGS_DIR, filename)

            # Save audio file
            with open(filepath, "wb") as f:
                f.write(audio_bytes)

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
            # This is where you'll integrate your AI model
            # For now, return mock feedback
            # correction: (start_index, end_index, insertion|substitution|deletion, viseme_img_path)
            corrections_output = [
                (10, 12, "substitution", "visemes/viseme-id-0.jpg"),
                (23, 24, "insertion"),
            ]

            corrections = []
            for correction in corrections_output:
                corrections.append(
                    {
                        "start_index": correction[0],
                        "end_index": correction[1],
                        "type": correction[2],
                    }
                )
                if len(correction) > 3:
                    corrections[-1]["viseme_img_path"] = correction[3]

            return {
                "success": True,
                "sentence": sentence,
                "corrections": corrections,
                "message": "Great job! Your pronunciation is clear and accurate.",
                "score": 85,
            }

        except Exception as e:
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
