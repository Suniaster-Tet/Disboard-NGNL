"""Entrada de voz local (STT) para Tet.

- Usa `SpeechRecognition` con motor local (PocketSphinx, Vosk o Whisper).
- Nunca envía audio a la nube; si el motor local no está disponible, falla
  con un mensaje claro.

Uso:
    from tools.speech_input import listen_and_transcribe
    texto = listen_and_transcribe(seconds=5)
"""
from __future__ import annotations

import os
from typing import Optional


def _engine() -> str:
    return os.getenv("SPEECH_INPUT_BACKEND", "local-stt").lower()


def is_available() -> bool:
    try:
        import speech_recognition  # noqa: F401
    except ImportError:
        return False
    return True


def listen_and_transcribe(seconds: int = 5, language: str = "es-MX") -> Optional[str]:
    """Escucha el micrófono durante `seconds` y devuelve el texto transcrito."""
    if not is_available():
        raise RuntimeError(
            "SpeechRecognition no está instalado. "
            'Instálalo con: pip install -e ".[speech]"'
        )

    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print(f"🎤 Listening for {seconds}s...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=seconds, phrase_time_limit=seconds)

    engine = _engine()
    try:
        if engine == "local-stt":
            # Requiere pocketsphinx o vosk instalado en el sistema
            return recognizer.recognize_sphinx(audio, language=language)
        return recognizer.recognize_sphinx(audio, language=language)
    except Exception as e:
        print(f"⚠️ STT error: {e}")
        return None


if __name__ == "__main__":
    print(listen_and_transcribe())
