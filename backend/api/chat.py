import logging
from fastapi import APIRouter, Depends, File, UploadFile, Form
from pydantic import BaseModel

from backend.agents.graph import graph
from backend.llm.langfuse_handler import get_langfuse_callback
from backend.services.auth import get_current_patient_id, oauth2_scheme
from backend.services.multimodal import transcribe_audio, analyze_image

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


def _base_state(patient_id: str, query: str, modality: str = "text") -> dict:
    return {
        "patient_id": patient_id,
        "patient_name": "",
        "query": query,
        "modality": modality,
        "voice_transcript": None,
        "image_findings": None,
        "intent": "",
        "medical_history_summary": None,
        "department": None,
        "confidence_score": None,
        "urgency_score": None,
        "emergency_risk": None,
        "emergency_dispatched": False,
        "hitl_required": False,
        "hitl_case_id": None,
        "appointment_id": None,
        "response": "",
        "error": None,
    }


def _invoke(state: dict) -> dict:
    callbacks = []
    cb = get_langfuse_callback()
    if cb:
        callbacks.append(cb)
    config = {"callbacks": callbacks} if callbacks else {}
    try:
        return graph.invoke(state, config=config)
    except Exception as exc:
        logger.error("Graph invocation error: %s", exc)
        state["response"] = "I'm sorry, something went wrong. Please try again."
        state["error"] = str(exc)
        return state


class ChatRequest(BaseModel):
    query: str


@router.post("/text")
def chat_text(body: ChatRequest, token: str = Depends(oauth2_scheme)):
    patient_id = get_current_patient_id(token)
    state = _base_state(patient_id, body.query)
    result = _invoke(state)
    return {
        "response": result["response"],
        "intent": result.get("intent"),
        "department": result.get("department"),
        "confidence_score": result.get("confidence_score"),
        "urgency_score": result.get("urgency_score"),
        "hitl_required": result.get("hitl_required"),
        "emergency_dispatched": result.get("emergency_dispatched"),
    }


@router.post("/voice")
async def chat_voice(audio: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    patient_id = get_current_patient_id(token)
    audio_bytes = await audio.read()
    transcript = transcribe_audio(audio_bytes, filename=audio.filename or "audio.wav")
    if not transcript:
        return {"response": "Sorry, I couldn't transcribe the audio. Please try again."}
    state = _base_state(patient_id, transcript, modality="voice")
    state["voice_transcript"] = transcript
    result = _invoke(state)
    return {"response": result["response"], "transcript": transcript, "intent": result.get("intent")}


@router.post("/image")
async def chat_image(
    image: UploadFile = File(...),
    complaint: str = Form(default=""),
    token: str = Depends(oauth2_scheme),
):
    patient_id = get_current_patient_id(token)
    image_bytes = await image.read()
    findings = analyze_image(image_bytes, patient_complaint=complaint)
    query = complaint or "I'm submitting a medical image for analysis."
    state = _base_state(patient_id, query, modality="image")
    state["image_findings"] = findings
    result = _invoke(state)
    return {
        "response": result["response"],
        "image_findings": findings,
        "department": result.get("department"),
    }
