from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional
from decimal import Decimal


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
    estimated_cost: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingStatusUpdate(BaseModel):
    """Schema for updating booking status"""
    status: str = Field(..., max_length=50)  # confirmed, cancelled, completed


# Nested schemas for detailed response
class SpotDetail(BaseModel):
    """Nested spot details"""
    spot_id: UUID
    spot_number: str
    spot_type: str

    class Config:
        from_attributes = True


class ZoneDetail(BaseModel):
    """Nested zone details"""
    zone_id: UUID
    name: str
    address: str

    class Config:
        from_attributes = True


class VehicleDetail(BaseModel):
    """Nested vehicle details"""
    vehicle_id: UUID
    license_plate: str
    model: str
    color: Optional[str] = None

    class Config:
        from_attributes = True


class BookingDetailResponse(BaseModel):
    """Extended booking response with nested details"""
    booking_id: UUID
    customer_id: UUID
    start_time: datetime
    end_time: datetime
    estimated_cost: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    # Nested objects
    spot: SpotDetail
    zone: ZoneDetail
    vehicle: VehicleDetail

    class Config:
        from_attributes = True
