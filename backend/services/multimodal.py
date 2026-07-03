"""
Multimodal input processing.
  - Voice  → Whisper (Groq) → text transcript
  - Image  → Llama 3.2 Vision (Groq) → findings text
"""

import base64
import logging

import httpx

from backend.config import settings
from backend.llm.provider import _groq_client
from backend.llm.registry import DIAGNOSIS_VISION_MODEL

logger = logging.getLogger(__name__)


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """Send audio to Whisper via Groq and return the transcript."""
    try:
        resp = httpx.post(
            settings.whisper_api_url,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            files={"file": (filename, audio_bytes, "audio/wav")},
            data={"model": "whisper-large-v3"},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("text", "")
    except Exception as exc:
        logger.error("Whisper transcription failed: %s", exc)
        return ""


def analyze_image(image_bytes: bytes, patient_complaint: str = "") -> str:
    """Send image to Qwen2.5-VL and return medical findings."""
    try:
        b64 = base64.b64encode(image_bytes).decode()
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"You are a medical AI assistant. Analyze this medical image. "
                            f"Patient complaint: {patient_complaint}\n"
                            "Describe any visible abnormalities, lesions, or relevant findings in clinical terms."
                        ),
                    },
                ],
            }
        ]
        response = _groq_client.chat.completions.create(
            model=DIAGNOSIS_VISION_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=512,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.error("Image analysis failed: %s", exc)
        return ""


def fuse_inputs(text: str = "", transcript: str = "", image_findings: str = "") -> str:
    """Combine text, voice transcript, and image findings into a single complaint string."""
    parts = []
    if text:
        parts.append(f"Patient complaint: {text}")
    if transcript:
        parts.append(f"Voice transcript: {transcript}")
    if image_findings:
        parts.append(f"Image findings: {image_findings}")
    return "\n".join(parts)
