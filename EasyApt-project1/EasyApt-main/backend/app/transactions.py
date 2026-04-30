"""
Transaction routes for EasyApt
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from .database import get_session
from .auth import get_current_user
from .models import User, Transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/my", response_model=List[dict])
def get_my_transactions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all transactions for current user"""
    stmt = select(Transaction).where(Transaction.user_id == current_user.id).order_by(Transaction.created_at.desc())
    transactions = session.exec(stmt).all()
    
    return [
        {
            "id": t.id,
            "amount": t.amount,
            "description": t.description,
            "transaction_type": t.transaction_type,
            "status": t.status,
            "created_at": t.created_at
        }
        for t in transactions
    ]
