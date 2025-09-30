#!/usr/bin/env python3
"""Test script for Whisper transcription."""
import asyncio
import sys
from openrouter.whisper import transcribe_audio


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_whisper.py <audio_file>")
        sys.exit(1)

    audio_path = sys.argv[1]
    print(f"Transcribing: {audio_path}")

    try:
        text = await transcribe_audio(audio_path)
        print(f"\nTranscription:\n{text}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
