"""
Groq API Client and AI Inference Service.
Manages chat completions with robust model fallbacks and Whisper speech-to-text transcription.
"""

import os
import io
import streamlit as st
from groq import Groq


DEFAULT_CHAT_MODELS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "llama3-70b-8192",
    "llama-3.1-8b-instant",
]

DEFAULT_WHISPER_MODELS = [
    "whisper-large-v3",
    "whisper-large-v3-turbo",
]


def get_api_key():
    """Retrieves Groq API key from Streamlit secrets or OS environment."""
    key = ""
    try:
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    if not key:
        key = os.environ.get("GROQ_API_KEY", "")

    return key.strip()


def get_groq_client():
    """Instantiates a Groq client if the API key is available."""
    api_key = get_api_key()
    if not api_key:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception as exc:
        print(f"Failed to initialize Groq client: {exc}")
        return None


def call_groq_llm(
    client,
    system_prompt,
    user_prompt,
    model=None,
    temperature=0.4,
    max_tokens=800,
    response_format=None,
):
    """
    Executes a chat completion call with automatic fallback across supported models.
    Supports optional response_format (e.g. {"type": "json_object"}).
    """
    if not client:
        raise ValueError("Groq client is not initialized. Please configure GROQ_API_KEY.")

    candidate_models = [model] if model else DEFAULT_CHAT_MODELS

    last_err = None
    for m in candidate_models:
        if not m:
            continue
        try:
            kwargs = {
                "model": m,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format

            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            last_err = exc
            continue

    raise RuntimeError(f"All Groq model attempts failed. Last error: {last_err}")


def transcribe_speech(client, audio_data, filename="recording.wav"):
    """
    Transcribes audio using Groq Whisper API.
    Handles bytes, BytesIO, or file-like objects.
    """
    if not client or not audio_data:
        return ""

    try:
        if hasattr(audio_data, "getvalue"):
            raw_bytes = audio_data.getvalue()
        elif hasattr(audio_data, "read"):
            raw_bytes = audio_data.read()
        elif isinstance(audio_data, (bytes, bytearray)):
            raw_bytes = bytes(audio_data)
        else:
            return ""

        if not raw_bytes:
            return ""

        bio = io.BytesIO(raw_bytes)
        bio.name = filename or "recording.wav"

        for whisper_model in DEFAULT_WHISPER_MODELS:
            try:
                bio.seek(0)
                resp = client.audio.transcriptions.create(
                    file=(bio.name, bio),
                    model=whisper_model,
                )
                if hasattr(resp, "text") and resp.text:
                    return resp.text.strip()
                if isinstance(resp, str) and resp:
                    return resp.strip()
                if isinstance(resp, dict) and resp.get("text"):
                    return resp["text"].strip()
            except Exception:
                continue

    except Exception as exc:
        print(f"Speech transcription error: {exc}")

    return ""
