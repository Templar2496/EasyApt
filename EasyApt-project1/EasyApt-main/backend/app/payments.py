"""
Stripe payment integration for EasyApt
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
import stripe

from .config import settings
from .database import get_session
from .auth import get_current_user
from .models import User, Provider, Appointment

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/payments", tags=["payments"])

class CreatePaymentIntent(BaseModel):
    provider_id: int
    start_time: str
    end_time: str

class PaymentIntentResponse(BaseModel):
    client_secret: str
    amount: float
    provider_name: str

@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
def create_payment_intent(
    payment_data: CreatePaymentIntent,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe payment intent for appointment booking
    """
    # Get provider and their fee
    provider = session.get(Provider, payment_data.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    amount = provider.consultation_fee
    
    # Create Stripe payment intent
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe uses cents
            currency="usd",
            metadata={
                "provider_id": str(provider.id),
                "patient_id": str(current_user.id),
                "start_time": payment_data.start_time,
                "end_time": payment_data.end_time
            }
        )
        
        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            amount=amount,
            provider_name=provider.name
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/publishable-key")
def get_publishable_key():
    """Return Stripe publishable key for frontend"""
    return {"publishable_key": settings.STRIPE_PUBLISHABLE_KEY}
