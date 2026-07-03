import uuid

from langchain_core.tools import tool

from backend.database.base import get_patient_session
from backend.database.patient_db.models import Patient, Offer, LoyaltyTransaction

POINTS_PER_BOOKING = 50


@tool
def check_available_offers(patient_id: str) -> str:
    """Check a patient's loyalty points and return applicable offers."""
    with get_patient_session() as db:
        patient = db.query(Patient).filter(
            Patient.patient_id == uuid.UUID(patient_id)
        ).first()
        if not patient:
            return "Patient not found."
        offers = (
            db.query(Offer)
            .filter(Offer.required_points <= patient.loyalty_points, Offer.is_active == True)
            .all()
        )
        if not offers:
            return f"You have {patient.loyalty_points} points. No offers available yet."
        offer_lines = [
            f"[{o.offer_id}] {o.offer_name} ({o.description}) — {o.required_points} pts"
            for o in offers
        ]
        return (
            f"You have {patient.loyalty_points} points. Eligible offers:\n"
            + "\n".join(offer_lines)
        )


@tool
def add_points(patient_id: str, reason: str = "Appointment booked") -> str:
    """Award loyalty points to a patient after a booking."""
    with get_patient_session() as db:
        patient = db.query(Patient).filter(
            Patient.patient_id == uuid.UUID(patient_id)
        ).first()
        if not patient:
            return "Patient not found."
        patient.loyalty_points += POINTS_PER_BOOKING
        db.add(
            LoyaltyTransaction(
                patient_id=patient.patient_id,
                points=POINTS_PER_BOOKING,
                reason=reason,
            )
        )
        return (
            f"{POINTS_PER_BOOKING} points added. "
            f"New total: {patient.loyalty_points} points."
        )


@tool
def redeem_points(patient_id: str, offer_id: str) -> str:
    """Redeem loyalty points for an offer during appointment booking."""
    with get_patient_session() as db:
        patient = db.query(Patient).filter(
            Patient.patient_id == uuid.UUID(patient_id)
        ).first()
        offer = db.query(Offer).filter(Offer.offer_id == uuid.UUID(offer_id)).first()
        if not patient or not offer:
            return "Patient or offer not found."
        if patient.loyalty_points < offer.required_points:
            return (
                f"Insufficient points. Need {offer.required_points}, "
                f"you have {patient.loyalty_points}."
            )
        patient.loyalty_points -= offer.required_points
        db.add(
            LoyaltyTransaction(
                patient_id=patient.patient_id,
                points=-offer.required_points,
                reason=f"Redeemed: {offer.offer_name}",
            )
        )
        return (
            f"Offer '{offer.offer_name}' applied ({offer.discount_percent}% discount). "
            f"Remaining points: {patient.loyalty_points}."
        )
