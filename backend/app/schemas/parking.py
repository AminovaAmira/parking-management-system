from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional
from decimal import Decimal


# Tariff Plan Schemas
class TariffPlanBase(BaseModel):
    """Base tariff plan schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price_per_hour: Decimal = Field(..., ge=0)
    price_per_day: Optional[Decimal] = Field(None, ge=0)
    is_active: bool = True


class TariffPlanCreate(TariffPlanBase):
    """Schema for creating a tariff plan"""
    pass


class TariffPlanResponse(TariffPlanBase):
    """Schema for tariff plan response"""
    tariff_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Parking Zone Schemas
class ParkingZoneBase(BaseModel):
    """Base parking zone schema"""
    name: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., min_length=1, max_length=255)
    total_spots: int = Field(..., ge=1)
    tariff_id: Optional[UUID] = None
    is_active: bool = True


class ParkingZoneCreate(ParkingZoneBase):
    """Schema for creating a parking zone"""
    pass


class ParkingZoneUpdate(BaseModel):
    """Schema for updating a parking zone"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, min_length=1, max_length=255)
    tariff_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class ParkingZoneResponse(ParkingZoneBase):
    """Schema for parking zone response"""
    zone_id: UUID
    available_spots: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Parking Spot Schemas
class ParkingSpotBase(BaseModel):
    """Base parking spot schema"""
    zone_id: UUID
    spot_number: str = Field(..., min_length=1, max_length=20)
    spot_type: str = Field(..., min_length=1, max_length=50)  # standard, disabled, electric, vip
    is_active: bool = True


class ParkingSpotCreate(ParkingSpotBase):
    """Schema for creating a parking spot"""
    pass


class ParkingSpotUpdate(BaseModel):
    """Schema for updating a parking spot"""
    spot_type: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None


class ParkingSpotResponse(ParkingSpotBase):
    """Schema for parking spot response"""
    spot_id: UUID
    is_occupied: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ParkingSpotWithPriceResponse(BaseModel):
    """Schema for parking spot response with pricing information"""
    spot_id: UUID
    zone_id: UUID
    spot_number: str
    spot_type: str
    is_active: bool
    is_occupied: bool
    created_at: datetime
    updated_at: datetime
    # Pricing info
    price_per_hour: Optional[Decimal] = None
    price_per_day: Optional[Decimal] = None

    class Config:
        from_attributes = True


# Availability Check
class AvailabilityRequest(BaseModel):
    """Schema for checking parking availability"""
    zone_id: UUID
    start_time: datetime
    end_time: datetime
    spot_type: Optional[str] = None


class AvailabilityResponse(BaseModel):
    """Schema for availability response"""
    zone_id: UUID
    available_spots: int
    spots: list[ParkingSpotResponse]
