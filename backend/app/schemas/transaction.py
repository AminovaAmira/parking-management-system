from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional
from decimal import Decimal


class TransactionCreate(BaseModel):
    """Schema for creating a transaction"""
    amount: Decimal


class TransactionResponse(BaseModel):
    """Schema for transaction response"""
    transaction_id: UUID
    customer_id: UUID
    booking_id: Optional[UUID]
    session_id: Optional[UUID]
    amount: Decimal
    type: str
    description: Optional[str]
    balance_before: Decimal
    balance_after: Decimal
    created_at: datetime

    class Config:
        from_attributes = True
