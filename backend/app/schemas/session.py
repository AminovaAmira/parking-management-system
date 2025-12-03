from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class ParkingSessionBase(BaseModel):
    """Base parking session schema"""
    vehicle_id: UUID
    spot_id: UUID
    entry_time: datetime


class ParkingSessionCreate(ParkingSessionBase):
    """Schema for creating a parking session"""
    booking_id: Optional[UUID] = None


class ParkingSessionEnd(BaseModel):
    """Schema for ending a parking session"""
    exit_time: datetime


class ParkingSessionResponse(ParkingSessionBase):
    """Schema for parking session response"""
    session_id: UUID
    booking_id: Optional[UUID]
    exit_time: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
