from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.models.parking_zone import ParkingZone
from app.models.parking_spot import ParkingSpot
from app.schemas.parking import (
    ParkingZoneResponse,
    ParkingSpotResponse,
    ParkingSpotCreate,
    ParkingSpotWithPriceResponse,
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
    stmt = select(ParkingZone).where(ParkingZone.is_active == is_active).options(
        selectinload(ParkingZone.parking_spots)
    )
    result = await db.execute(stmt)
    zones = result.scalars().all()
    return zones


@router.get("/{zone_id}", response_model=ParkingZoneResponse)
async def get_parking_zone(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific parking zone"""
    stmt = select(ParkingZone).where(ParkingZone.zone_id == zone_id).options(
        selectinload(ParkingZone.parking_spots)
    )
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


@router.get("/{zone_id}/available-spots", response_model=List[ParkingSpotWithPriceResponse])
async def get_available_spots_for_timerange(
    zone_id: UUID,
    start_time: str,
    end_time: str,
    db: AsyncSession = Depends(get_db)
):
    """Get available spots in a zone for a specific time range with pricing info"""
    from datetime import datetime
    from app.models.booking import Booking
    from app.models.tariff_plan import TariffPlan
    from sqlalchemy import and_, or_

    # Parse time strings
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
        )

    if start_dt >= end_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )

    # Get zone with tariff info
    zone_stmt = select(ParkingZone).where(ParkingZone.zone_id == zone_id)
    zone_result = await db.execute(zone_stmt)
    zone = zone_result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking zone not found"
        )

    # Get tariff if exists
    tariff = None
    if zone.tariff_id:
        tariff_stmt = select(TariffPlan).where(TariffPlan.tariff_id == zone.tariff_id)
        tariff_result = await db.execute(tariff_stmt)
        tariff = tariff_result.scalar_one_or_none()

    # Get all active spots in the zone
    stmt = select(ParkingSpot).where(
        ParkingSpot.zone_id == zone_id,
        ParkingSpot.is_active == True
    )
    result = await db.execute(stmt)
    all_spots = result.scalars().all()

    # Get bookings that overlap with requested time
    booking_stmt = select(Booking).where(
        Booking.spot_id.in_([spot.spot_id for spot in all_spots]),
        Booking.status.in_(["pending", "confirmed"]),
        and_(
            Booking.start_time < end_dt,
            Booking.end_time > start_dt
        )
    )
    booking_result = await db.execute(booking_stmt)
    conflicting_bookings = booking_result.scalars().all()

    # Get spot IDs that are booked
    booked_spot_ids = {booking.spot_id for booking in conflicting_bookings}

    # Filter out booked spots and add pricing info
    available_spots = []
    for spot in all_spots:
        if spot.spot_id not in booked_spot_ids:
            spot_with_price = ParkingSpotWithPriceResponse(
                spot_id=spot.spot_id,
                zone_id=spot.zone_id,
                spot_number=spot.spot_number,
                spot_type=spot.spot_type,
                is_active=spot.is_active,
                is_occupied=spot.is_occupied,
                created_at=spot.created_at,
                updated_at=spot.updated_at,
                price_per_hour=tariff.price_per_hour if tariff else None,
                price_per_day=tariff.price_per_day if tariff else None
            )
            available_spots.append(spot_with_price)

    return available_spots


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

    await db.commit()
    await db.refresh(new_spot)

    return new_spot
