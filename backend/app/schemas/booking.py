from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class BookingBase(BaseModel):
    """Base booking schema"""
    vehicle_id: UUID
    spot_id: UUID
    start_time: datetime
    end_time: datetime


class BookingCreate(BookingBase):
    """Schema for creating a booking"""
    pass


class BookingUpdate(BaseModel):
    """Schema for updating a booking"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=50)


class BookingResponse(BookingBase):
    """Schema for booking response"""
    booking_id: UUID
    customer_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingStatusUpdate(BaseModel):
    """Schema for updating booking status"""
    status: str = Field(..., max_length=50)  # confirmed, cancelled, completed
