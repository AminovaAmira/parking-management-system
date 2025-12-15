from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional
from decimal import Decimal


class ParkingSessionBase(BaseModel):
    """Base parking session schema"""
    vehicle_id: UUID
    spot_id: UUID
    entry_time: datetime


class ParkingSessionCreate(BaseModel):
    """Schema for creating a parking session"""
    vehicle_id: UUID
    spot_id: UUID
    booking_id: Optional[UUID] = None
    entry_time: Optional[datetime] = None  # Auto-set to current time if not provided


class ParkingSessionEnd(BaseModel):
    """Schema for ending a parking session"""
    exit_time: datetime


class ParkingSessionResponse(ParkingSessionBase):
    """Schema for parking session response"""
    session_id: UUID
    booking_id: Optional[UUID]
    exit_time: Optional[datetime]
    duration_minutes: Optional[int]
    total_cost: Optional[Decimal]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Nested schemas for detailed session history
class SessionSpotDetail(BaseModel):
    """Spot details for session history"""
    spot_id: UUID
    spot_number: str
    spot_type: str

    class Config:
        from_attributes = True


class SessionZoneDetail(BaseModel):
    """Zone details for session history"""
    zone_id: UUID
    name: str
    address: str

    class Config:
        from_attributes = True


class SessionVehicleDetail(BaseModel):
    """Vehicle details for session history"""
    vehicle_id: UUID
    license_plate: str
    model: str
    color: Optional[str]

    class Config:
        from_attributes = True


class SessionPaymentDetail(BaseModel):
    """Payment details for session history"""
    payment_id: UUID
    amount: Decimal
    status: str
    payment_method: str
    created_at: datetime

    class Config:
        from_attributes = True


class ParkingSessionHistoryResponse(BaseModel):
    """Detailed schema for parking session history"""
    session_id: UUID
    entry_time: datetime
    exit_time: Optional[datetime]
    duration_minutes: Optional[int]
    total_cost: Optional[Decimal]
    status: str
    created_at: datetime
    spot: SessionSpotDetail
    zone: SessionZoneDetail
    vehicle: SessionVehicleDetail
    payment: Optional[SessionPaymentDetail]

    class Config:
        from_attributes = True


class ActiveSessionDetailResponse(BaseModel):
    """Detailed schema for active parking session"""
    session_id: UUID
    entry_time: datetime
    status: str
    spot: SessionSpotDetail
    zone: SessionZoneDetail
    vehicle: SessionVehicleDetail

    class Config:
        from_attributes = True
