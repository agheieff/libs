"""OpenAI Whisper transcription API."""
from __future__ import annotations
import os
import httpx
from typing import Union

_API_KEY = os.getenv("OPENAI_API_KEY")
if not _API_KEY:
    raise RuntimeError("OPENAI_API_KEY env var not set")

_WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"
_HEADERS = {
    "Authorization": f"Bearer {_API_KEY}",
}


async def transcribe_audio(audio: Union[bytes, str], model: str = "whisper-1") -> str:
    """
    Transcribe audio to text using OpenAI Whisper API.

    Args:
        audio: Audio data as bytes or path to audio file
        model: Whisper model to use (default: whisper-1)

    Returns:
        Transcribed text as string
    """
    # Load audio file if path provided
    if isinstance(audio, str):
        with open(audio, "rb") as f:
            audio_bytes = f.read()
            filename = os.path.basename(audio)
    else:
        audio_bytes = audio
        filename = "audio.mp3"

    # Prepare multipart form data
    files = {
        "file": (filename, audio_bytes, "audio/mpeg"),
        "model": (None, model),
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(_WHISPER_URL, headers=_HEADERS, files=files)
        response.raise_for_status()
        result = response.json()

        return result["text"].strip()