"""Salida de voz local (TTS) para Tet.

- Usa `pyttsx3` (motor local del sistema: espeak-ng en Linux, NSSpeechSynthesizer
  en macOS, SAPI5 en Windows).
- Nunca envía texto a la nube.

Uso:
    from tools.speech_output import speak
    speak("Hola, soy Stephanie Dola.")
"""
from __future__ import annotations

import os


def _engine() -> str:
    return os.getenv("SPEECH_OUTPUT_BACKEND", "kitten-tts").lower()


def is_available() -> bool:
    try:
        import pyttsx3  # noqa: F401
    except ImportError:
        return False
    return True


def speak(text: str, rate: int = 175, volume: float = 1.0) -> bool:
    """Lee el texto en voz alta con el motor TTS local."""
    if not is_available():
        raise RuntimeError(
            "pyttsx3 no está instalado. "
            'Instálalo con: pip install -e ".[speech]"'
        )

    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)
    engine.say(text)
    engine.runAndWait()
    return True


if __name__ == "__main__":
    speak("Disboard-NGNL speech output test.")
