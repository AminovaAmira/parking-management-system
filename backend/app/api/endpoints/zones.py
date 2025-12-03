from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.models.parking_zone import ParkingZone
from app.models.parking_spot import ParkingSpot
from app.schemas.parking import (
    ParkingZoneResponse,
    ParkingSpotResponse,
    ParkingSpotCreate,
    AvailabilityRequest,
    AvailabilityResponse
)

router = APIRouter()


@router.get("/", response_model=List[ParkingZoneResponse])
async def get_parking_zones(
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get all parking zones"""
    stmt = select(ParkingZone).where(ParkingZone.is_active == is_active)
    result = await db.execute(stmt)
    zones = result.scalars().all()
    return zones


@router.get("/{zone_id}", response_model=ParkingZoneResponse)
async def get_parking_zone(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific parking zone"""
    stmt = select(ParkingZone).where(ParkingZone.zone_id == zone_id)
    result = await db.execute(stmt)
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking zone not found"
        )

    return zone


@router.get("/{zone_id}/spots", response_model=List[ParkingSpotResponse])
async def get_zone_spots(
    zone_id: UUID,
    is_occupied: bool = None,
    spot_type: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all parking spots in a zone"""
    stmt = select(ParkingSpot).where(ParkingSpot.zone_id == zone_id)

    if is_occupied is not None:
        stmt = stmt.where(ParkingSpot.is_occupied == is_occupied)

    if spot_type:
        stmt = stmt.where(ParkingSpot.spot_type == spot_type)

    result = await db.execute(stmt)
    spots = result.scalars().all()
    return spots


@router.post("/availability", response_model=AvailabilityResponse)
async def check_availability(
    availability_request: AvailabilityRequest,
    db: AsyncSession = Depends(get_db)
):
    """Check parking availability for a zone"""

    # Get zone
    stmt = select(ParkingZone).where(ParkingZone.zone_id == availability_request.zone_id)
    result = await db.execute(stmt)
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking zone not found"
        )

    # Get available spots
    stmt = select(ParkingSpot).where(
        ParkingSpot.zone_id == availability_request.zone_id,
        ParkingSpot.is_occupied == False,
        ParkingSpot.is_active == True
    )

    if availability_request.spot_type:
        stmt = stmt.where(ParkingSpot.spot_type == availability_request.spot_type)

    result = await db.execute(stmt)
    available_spots = result.scalars().all()

    return {
        "zone_id": availability_request.zone_id,
        "available_spots": len(available_spots),
        "spots": available_spots
    }


@router.post("/{zone_id}/spots", response_model=ParkingSpotResponse, status_code=status.HTTP_201_CREATED)
async def create_parking_spot(
    zone_id: UUID,
    spot_data: ParkingSpotCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new parking spot (admin only - for now no auth check)"""

    # Verify zone exists
    stmt = select(ParkingZone).where(ParkingZone.zone_id == zone_id)
    result = await db.execute(stmt)
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking zone not found"
        )

    # Check if spot number already exists in this zone
    stmt = select(ParkingSpot).where(
        ParkingSpot.zone_id == zone_id,
        ParkingSpot.spot_number == spot_data.spot_number
    )
    result = await db.execute(stmt)
    existing_spot = result.scalar_one_or_none()

    if existing_spot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Spot number already exists in this zone"
        )

    # Create new spot
    new_spot = ParkingSpot(**spot_data.model_dump())
    db.add(new_spot)

    # Update zone's available spots count
    zone.available_spots += 1

    await db.commit()
    await db.refresh(new_spot)

    return new_spot
