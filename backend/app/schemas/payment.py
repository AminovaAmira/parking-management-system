from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional
from decimal import Decimal


class SpotDetail(BaseModel):
    """Детали парковочного места"""
    spot_id: UUID
    spot_number: str
    spot_type: str

    class Config:
        from_attributes = True


class ZoneDetail(BaseModel):
    """Детали парковочной зоны"""
    zone_id: UUID
    name: str
    address: str

    class Config:
        from_attributes = True


class BookingDetail(BaseModel):
    """Детали бронирования"""
    booking_id: UUID
    start_time: datetime
    end_time: datetime
    status: str

    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    """Base payment schema"""
    amount: Decimal = Field(..., ge=0)
    payment_method: str = Field(..., min_length=1, max_length=50)  # card, cash, online


class PaymentCreate(PaymentBase):
    """Schema for creating a payment"""
    session_id: Optional[UUID] = None
    booking_id: Optional[UUID] = None


class PaymentUpdate(BaseModel):
    """Schema for updating a payment"""
    status: str = Field(..., max_length=50)  # completed, failed, refunded
    transaction_id: Optional[str] = Field(None, max_length=255)


class PaymentResponse(PaymentBase):
    """Schema for payment response"""
    payment_id: UUID
    session_id: Optional[UUID] = None
    booking_id: Optional[UUID] = None
    customer_id: UUID
    status: str
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentDetailResponse(PaymentResponse):
    """Детальная схема ответа платежа с информацией о бронировании и месте"""
    booking: Optional[BookingDetail] = None
    spot: Optional[SpotDetail] = None
    zone: Optional[ZoneDetail] = None

    class Config:
        from_attributes = True
