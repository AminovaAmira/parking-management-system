from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime

from app.db.database import get_db
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.models.parking_session import ParkingSession
from app.models.parking_spot import ParkingSpot
from app.models.booking import Booking
from app.models.parking_zone import ParkingZone
from app.schemas.session import ParkingSessionCreate, ParkingSessionResponse, ParkingSessionEnd
from app.core.dependencies import get_current_customer

router = APIRouter()


@router.get("/", response_model=List[ParkingSessionResponse])
async def get_my_sessions(
    current_customer: Customer = Depends(get_current_customer),
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all parking sessions for current customer's vehicles"""

    # Get customer's vehicle IDs
    vehicles_stmt = select(Vehicle.vehicle_id).where(Vehicle.customer_id == current_customer.customer_id)
    vehicles_result = await db.execute(vehicles_stmt)
    vehicle_ids = [row[0] for row in vehicles_result.all()]

    if not vehicle_ids:
        return []

    # Get sessions for customer's vehicles
    stmt = select(ParkingSession).where(ParkingSession.vehicle_id.in_(vehicle_ids))

    if status:
        stmt = stmt.where(ParkingSession.status == status)

    stmt = stmt.order_by(ParkingSession.entry_time.desc())

    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return sessions


@router.post("/", response_model=ParkingSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_parking_session(
    session_data: ParkingSessionCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Start a new parking session"""

    # Verify vehicle belongs to customer
    stmt = select(Vehicle).where(
        Vehicle.vehicle_id == session_data.vehicle_id,
        Vehicle.customer_id == current_customer.customer_id
    )
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )

    # Verify parking spot exists
    stmt = select(ParkingSpot).where(ParkingSpot.spot_id == session_data.spot_id)
    result = await db.execute(stmt)
    spot = result.scalar_one_or_none()

    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking spot not found"
        )

    # Check if spot is already occupied
    if spot.is_occupied:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parking spot is already occupied"
        )

    # If booking_id provided, verify it exists and belongs to this customer
    if session_data.booking_id:
        stmt = select(Booking).where(
            Booking.booking_id == session_data.booking_id,
            Booking.customer_id == current_customer.customer_id,
            Booking.vehicle_id == session_data.vehicle_id,
            Booking.spot_id == session_data.spot_id
        )
        result = await db.execute(stmt)
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or does not match session parameters"
            )

        if booking.status != "confirmed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking must be confirmed to start a session"
            )

    # Create parking session
    new_session = ParkingSession(
        **session_data.model_dump(),
        status="active"
    )

    # Mark spot as occupied
    spot.is_occupied = True

    # Update zone's available spots
    stmt = select(ParkingZone).where(ParkingZone.zone_id == spot.zone_id)
    result = await db.execute(stmt)
    zone = result.scalar_one_or_none()
    if zone:
        zone.available_spots = max(0, zone.available_spots - 1)

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return new_session


@router.get("/active", response_model=List[ParkingSessionResponse])
async def get_active_sessions(
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Get all active parking sessions for current customer"""

    # Get customer's vehicle IDs
    vehicles_stmt = select(Vehicle.vehicle_id).where(Vehicle.customer_id == current_customer.customer_id)
    vehicles_result = await db.execute(vehicles_stmt)
    vehicle_ids = [row[0] for row in vehicles_result.all()]

    if not vehicle_ids:
        return []

    # Get active sessions
    stmt = select(ParkingSession).where(
        ParkingSession.vehicle_id.in_(vehicle_ids),
        ParkingSession.status == "active"
    )

    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return sessions


@router.get("/{session_id}", response_model=ParkingSessionResponse)
async def get_session(
    session_id: UUID,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific parking session"""

    # Get customer's vehicle IDs
    vehicles_stmt = select(Vehicle.vehicle_id).where(Vehicle.customer_id == current_customer.customer_id)
    vehicles_result = await db.execute(vehicles_stmt)
    vehicle_ids = [row[0] for row in vehicles_result.all()]

    if not vehicle_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    stmt = select(ParkingSession).where(
        ParkingSession.session_id == session_id,
        ParkingSession.vehicle_id.in_(vehicle_ids)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return session


@router.patch("/{session_id}/end", response_model=ParkingSessionResponse)
async def end_parking_session(
    session_id: UUID,
    session_end: ParkingSessionEnd,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """End a parking session"""

    # Get customer's vehicle IDs
    vehicles_stmt = select(Vehicle.vehicle_id).where(Vehicle.customer_id == current_customer.customer_id)
    vehicles_result = await db.execute(vehicles_stmt)
    vehicle_ids = [row[0] for row in vehicles_result.all()]

    if not vehicle_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    stmt = select(ParkingSession).where(
        ParkingSession.session_id == session_id,
        ParkingSession.vehicle_id.in_(vehicle_ids)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active"
        )

    # Validate exit time
    if session_end.exit_time < session.entry_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exit time must be after entry time"
        )

    # Update session
    session.exit_time = session_end.exit_time
    session.status = "completed"

    # Mark spot as available
    stmt = select(ParkingSpot).where(ParkingSpot.spot_id == session.spot_id)
    result = await db.execute(stmt)
    spot = result.scalar_one_or_none()

    if spot:
        spot.is_occupied = False

        # Update zone's available spots
        stmt = select(ParkingZone).where(ParkingZone.zone_id == spot.zone_id)
        result = await db.execute(stmt)
        zone = result.scalar_one_or_none()
        if zone:
            zone.available_spots = min(zone.total_spots, zone.available_spots + 1)

    await db.commit()
    await db.refresh(session)

    return session
