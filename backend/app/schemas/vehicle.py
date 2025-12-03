from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class VehicleBase(BaseModel):
    """Base vehicle schema"""
    license_plate: str = Field(..., min_length=1, max_length=20)
    vehicle_type: str = Field(..., min_length=1, max_length=50)  # sedan, suv, truck, motorcycle
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)


class VehicleCreate(VehicleBase):
    """Schema for creating a vehicle"""
    pass


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle"""
    vehicle_type: Optional[str] = Field(None, min_length=1, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)


class VehicleResponse(VehicleBase):
    """Schema for vehicle response"""
    vehicle_id: UUID
    customer_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
