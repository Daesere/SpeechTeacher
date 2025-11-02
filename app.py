import webview
import os
import base64
from datetime import datetime
from pipeline import listener

from pydub import AudioSegment
import io
import pickle
import shutil

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
            score, substituted, inserted, deleted, conversation, target_phonemes = listener(
                sentence, filepath
            )
            # with open("out.pkl", "w") as f:
            #     pickle.dumps((score, substituted, inserted, deleted, conversation), f)
            print(score, substituted, inserted, deleted, conversation)

            corrections = substituted + inserted + deleted

            # Normalize viseme paths to absolute file:/// URIs so the webview can load them reliably
            for c in corrections:
                try:
                    if not isinstance(c, dict):
                        continue
                    # support either 'viseme_img_path' or older 'viseme_path' keys
                    img_path = c.get("viseme_img_path") or c.get("viseme_path")
                    if not img_path:
                        continue

                    # If already looks like a file URI, leave it and ensure canonical key exists
                    if isinstance(img_path, str) and img_path.startswith("file:///"):
                        print(f"Viseme file URI already: {img_path}")
                        c["viseme_img_path"] = img_path
                        continue

                    # Resolve to absolute path
                    abs_path = os.path.abspath(img_path)
                    resolved = None
                    if os.path.exists(abs_path):
                        resolved = abs_path
                    else:
                        # Try common alternative locations under the repo
                        candidates = [
                            os.path.join(os.getcwd(), img_path),
                            os.path.join(os.getcwd(), "viseme_feedback", img_path),
                            os.path.join(
                                os.getcwd(), "viseme_feedback", "visemes", os.path.basename(img_path)
                            ),
                            os.path.join(os.getcwd(), "viseme_feedback", "visemes", img_path),
                        ]
                        for cand in candidates:
                            if os.path.exists(cand):
                                resolved = cand
                                break

                    if resolved:
                        # Attempt to make the image available to the frontend as a relative path
                        frontend_dir = os.path.join(os.getcwd(), "frontend")
                        frontend_visemes_dir = os.path.join(frontend_dir, "visemes")
                        os.makedirs(frontend_visemes_dir, exist_ok=True)

                        try:
                            abs_frontend = os.path.abspath(frontend_dir)
                            abs_resolved = os.path.abspath(resolved)
                            # If resolved file is already inside frontend, use a frontend-relative path
                            if abs_resolved.startswith(abs_frontend + os.sep):
                                rel = os.path.relpath(abs_resolved, abs_frontend).replace("\\", "/")
                                c["viseme_img_path"] = rel
                                print(f"Using frontend-relative viseme path: {rel}")
                                # Also embed the image as base64 data so the frontend can render it
                                try:
                                    with open(abs_resolved if abs_resolved else resolved, "rb") as f:
                                        img_bytes = f.read()
                                    b64 = base64.b64encode(img_bytes).decode("ascii")
                                    _, ext = os.path.splitext(resolved)
                                    ext = ext.lower()
                                    if ext in (".jpg", ".jpeg"):
                                        mime = "image/jpeg"
                                    elif ext == ".png":
                                        mime = "image/png"
                                    elif ext == ".gif":
                                        mime = "image/gif"
                                    elif ext == ".svg":
                                        mime = "image/svg+xml"
                                    else:
                                        mime = "application/octet-stream"
                                    c["viseme_img_data"] = f"data:{mime};base64," + b64
                                except Exception as embed_ex:
                                    print(f"Failed to embed viseme image as base64: {embed_ex}")
                            else:
                                # Copy into frontend/visemes so it can be referenced relatively
                                dest_name = os.path.basename(resolved)
                                dest_path = os.path.join(frontend_visemes_dir, dest_name)
                                if os.path.exists(dest_path):
                                    base, ext = os.path.splitext(dest_name)
                                    dest_name = f"{base}_{int(datetime.now().timestamp())}{ext}"
                                    dest_path = os.path.join(frontend_visemes_dir, dest_name)
                                shutil.copy2(resolved, dest_path)
                                rel = os.path.relpath(dest_path, abs_frontend).replace("\\", "/")
                                c["viseme_img_path"] = rel
                                print(f"Copied viseme into frontend: {rel}")
                                # Embed the copied image as base64 as well
                                try:
                                    with open(dest_path, "rb") as f:
                                        img_bytes = f.read()
                                    b64 = base64.b64encode(img_bytes).decode("ascii")
                                    _, ext = os.path.splitext(dest_path)
                                    ext = ext.lower()
                                    if ext in (".jpg", ".jpeg"):
                                        mime = "image/jpeg"
                                    elif ext == ".png":
                                        mime = "image/png"
                                    elif ext == ".gif":
                                        mime = "image/gif"
                                    elif ext == ".svg":
                                        mime = "image/svg+xml"
                                    else:
                                        mime = "application/octet-stream"
                                    c["viseme_img_data"] = f"data:{mime};base64," + b64
                                except Exception as embed_ex:
                                    print(f"Failed to embed copied viseme image as base64: {embed_ex}")
                        except Exception as copy_ex:
                            # Fallback: file URI
                            abs_path_slash = resolved.replace("\\", "/")
                            file_uri = "file:///" + abs_path_slash
                            c["viseme_img_path"] = file_uri
                            print(f"Failed to copy viseme; using file URI: {file_uri} (error: {copy_ex})")
                    else:
                        # If path doesn't exist, leave original but log
                        print(f"Viseme path not found: {img_path} -> abs: {abs_path}")
                except Exception as ex:
                    print(f"Error normalizing viseme path: {ex}")
                    # If anything goes wrong normalizing, leave original path

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
