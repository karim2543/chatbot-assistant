import requests  # type: ignore
import pyttsx3
import os
import logging
import threading
from queue import Queue
from datetime import datetime
from Service.prompting import Prompting


class ResponseGenerationError(Exception):
    """Raised when Ollama cannot produce a valid assistant response."""


class VoiceGenerationError(Exception):
    """Raised when the text-to-speech engine cannot create a valid audio file."""


_voice_tasks = Queue()
_voice_worker_lock = threading.Lock()
_voice_worker_started = False


def _voice_worker():
    while True:
        generator, text, on_success = _voice_tasks.get()
        try:
            file_path = generator.generate_voice_response(text)
            if on_success:
                on_success(file_path)
        except Exception:
            logging.exception("Voice generation or persistence error")
        finally:
            _voice_tasks.task_done()


class ResponseGenerator:
    def __init__(self, settings=None, history_limit=None):
        self.model = "qwen2.5:3b"
        self.host = "http://localhost:11434"
        configured_limit = os.environ.get("OLLAMA_HISTORY_LIMIT", "20")
        self.history_limit = (
            int(configured_limit) if history_limit is None else history_limit
        )

        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # dossier pour fichiers audio
        self.voice_dir = os.path.join(root_dir, "voice_responses")
        os.makedirs(self.voice_dir, exist_ok=True)

        # dossier pour réponses texte
        self.text_dir = "text_responses"
        os.makedirs(self.text_dir, exist_ok=True)

    # ----------------------------
    # 1️⃣ Génération texte (Ollama)
    # ----------------------------
    def generate_text_response(
        self,
        text,
        conversation_history=None,
        current_message_id=None,
    ):
        if not text.strip():
            raise ResponseGenerationError("Empty message.")

        history = list(conversation_history or [])
        if current_message_id is not None:
            history = [
                message
                for message in history
                if (
                    message.get("id")
                    if isinstance(message, dict)
                    else getattr(message, "id", None)
                ) != current_message_id
            ]

        if self.history_limit > 0:
            history = history[-max(0, self.history_limit - 1):]
        else:
            history = []

        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": Prompting.build_messages(history, current_text=text),
                    "stream": False
                },
                timeout=10
            )

            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ResponseGenerationError("Invalid Ollama response.")
            message = data.get("message")
            ai_response = message.get("content") if isinstance(message, dict) else None
            if not isinstance(ai_response, str) or not ai_response.strip():
                raise ResponseGenerationError("Invalid Ollama response.")

            # ----------------------------
            # 💾 Sauvegarde dans fichier
            # ----------------------------
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_path = os.path.join(
                self.text_dir,
                f"response_{timestamp}.txt"
            )

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(ai_response)

            return ai_response

        except ResponseGenerationError:
            raise
        except requests.RequestException as error:
            raise ResponseGenerationError(
                "Ollama is unavailable or has rejected the request."
            ) from error
        except (ValueError, KeyError, AttributeError, TypeError) as error:
            raise ResponseGenerationError(
                "Invalid Ollama response."
            ) from error
    # ---------------------------------
    # 2️⃣ Génération vocale (TTS offline)
    # ---------------------------------
    def enqueue_voice_response(self, text, on_success=None):
        global _voice_worker_started

        with _voice_worker_lock:
            if not _voice_worker_started:
                threading.Thread(
                    target=_voice_worker,
                    name="chatbot-voice-worker",
                    daemon=True,
                ).start()
                _voice_worker_started = True

        _voice_tasks.put((self, text, on_success))

    def generate_voice_response(self, text):
        if not text.strip():
            return None
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 150)
            engine.setProperty("volume", 1.0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_path = os.path.join(
                self.voice_dir,
                f"response_{timestamp}.wav"
            )

            engine.save_to_file(text, file_path)
            engine.runAndWait()
        except (OSError, RuntimeError) as error:
            raise VoiceGenerationError(
                "Voice synthesis failed."
            ) from error

        if not os.path.isfile(file_path) or os.path.getsize(file_path) == 0:
            raise VoiceGenerationError(
                "Voice synthesis did not produce a valid audio file."
            )

        return file_path