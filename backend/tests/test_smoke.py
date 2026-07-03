"""
Smoke / unit tests — no DB or LLM required.
Run: pytest backend/tests/test_smoke.py -v
"""


def test_config_loads():
    from backend.config import settings
    assert settings.algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30


def test_agent_state_keys():
    from backend.agents.state import AgentState
    required = {"patient_id", "query", "intent", "response", "department", "confidence_score"}
    assert required.issubset(AgentState.__annotations__.keys())


# ── Orchestrator routing ──────────────────────────────────────────────────────
def test_orchestrator_router_scheduling():
    from backend.agents.orchestrator.node import orchestrator_router
    assert orchestrator_router({"intent": "scheduling"}) == "scheduling"


def test_orchestrator_router_diagnosis():
    from backend.agents.orchestrator.node import orchestrator_router
    assert orchestrator_router({"intent": "diagnosis"}) == "diagnosis"


def test_orchestrator_router_emergency():
    from backend.agents.orchestrator.node import orchestrator_router
    assert orchestrator_router({"intent": "emergency"}) == "emergency"


def test_orchestrator_router_feedback():
    from backend.agents.orchestrator.node import orchestrator_router
    assert orchestrator_router({"intent": "feedback"}) == "feedback"


def test_orchestrator_router_unknown_falls_back_to_diagnosis():
    from backend.agents.orchestrator.node import orchestrator_router
    assert orchestrator_router({"intent": "unknown"}) == "diagnosis"


# ── Diagnosis routing ─────────────────────────────────────────────────────────
def test_diagnosis_router_hitl_on_low_confidence():
    from backend.agents.diagnosis.node import diagnosis_router
    assert diagnosis_router({"hitl_required": True, "urgency_score": 0.3}) == "hitl"


def test_diagnosis_router_emergency_on_high_urgency():
    from backend.agents.diagnosis.node import diagnosis_router
    assert diagnosis_router({"hitl_required": False, "urgency_score": 0.9}) == "emergency"


def test_diagnosis_router_scheduling_on_normal():
    from backend.agents.diagnosis.node import diagnosis_router
    assert diagnosis_router({"hitl_required": False, "urgency_score": 0.4}) == "scheduling"


def test_diagnosis_router_emergency_exact_threshold():
    from backend.agents.diagnosis.node import diagnosis_router
    # 0.85 = exactly at threshold → emergency
    assert diagnosis_router({"hitl_required": False, "urgency_score": 0.85}) == "emergency"
    # 0.84 → scheduling
    assert diagnosis_router({"hitl_required": False, "urgency_score": 0.84}) == "scheduling"


# ── Multimodal fusion ─────────────────────────────────────────────────────────
def test_fuse_all_inputs():
    from backend.services.multimodal import fuse_inputs
    result = fuse_inputs(text="chest pain", transcript="feeling tight", image_findings="ECG abnormal")
    assert "chest pain" in result
    assert "feeling tight" in result
    assert "ECG abnormal" in result


def test_fuse_text_only():
    from backend.services.multimodal import fuse_inputs
    result = fuse_inputs(text="headache")
    assert "headache" in result
    assert "transcript" not in result.lower()


def test_fuse_empty():
    from backend.services.multimodal import fuse_inputs
    assert fuse_inputs() == ""


# ── Auth ──────────────────────────────────────────────────────────────────────
def test_hash_and_verify_password():
    from backend.services.auth import hash_password, verify_password
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_token_round_trip():
    from backend.services.auth import create_access_token, decode_token
    token = create_access_token({"sub": "user-1", "patient_id": "p-abc"})
    payload = decode_token(token)
    assert payload["patient_id"] == "p-abc"
    assert payload["sub"] == "user-1"


def test_invalid_token_raises():
    from fastapi import HTTPException
    from backend.services.auth import decode_token
    try:
        decode_token("not.a.valid.token")
        assert False, "Should have raised"
    except HTTPException as e:
        assert e.status_code == 401


# ── Session service ───────────────────────────────────────────────────────────
def test_session_append_and_get():
    from backend.services import session as svc
    svc.clear_session("p-test-smoke")
    svc.append_message("p-test-smoke", "user", "hello")
    svc.append_message("p-test-smoke", "assistant", "hi there")
    hist = svc.get_history("p-test-smoke")
    assert len(hist) == 2
    assert hist[0]["role"] == "user"
    assert hist[1]["content"] == "hi there"
    svc.clear_session("p-test-smoke")


def test_session_max_history():
    from backend.services import session as svc
    svc.clear_session("p-max-test")
    for i in range(30):
        svc.append_message("p-max-test", "user", f"msg {i}")
    hist = svc.get_history("p-max-test")
    assert len(hist) <= 20
    svc.clear_session("p-max-test")


# ── Emergency tools (pure logic, no DB) ──────────────────────────────────────
def test_get_emergency_timer_heart_attack():
    from backend.tools.emergency import EMERGENCY_TIMERS
    assert EMERGENCY_TIMERS["heart attack"] == 30


def test_get_emergency_timer_stroke():
    from backend.tools.emergency import EMERGENCY_TIMERS
    assert EMERGENCY_TIMERS["stroke"] == 60


def test_high_risk_conditions_set():
    from backend.tools.emergency import HIGH_RISK_CONDITIONS
    assert "heart disease" in HIGH_RISK_CONDITIONS


# ── LLM registry ─────────────────────────────────────────────────────────────
def test_llm_registry_defined():
    from backend.llm import registry
    assert registry.ORCHESTRATOR_MODEL
    assert registry.DIAGNOSIS_MODEL
    assert registry.SCHEDULING_MODEL
    assert registry.EMERGENCY_MODEL
    assert registry.FEEDBACK_MODEL


# ── Graph compiles ────────────────────────────────────────────────────────────
def test_graph_compiles():
    from backend.agents.graph import graph
    assert graph is not None
