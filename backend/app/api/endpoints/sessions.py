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
from app.models.tariff_plan import TariffPlan
from app.models.payment import Payment
from app.schemas.session import (
    ParkingSessionCreate,
    ParkingSessionResponse,
    ParkingSessionEnd,
    ParkingSessionHistoryResponse,
    SessionSpotDetail,
    SessionZoneDetail,
    SessionVehicleDetail,
    SessionPaymentDetail
)
from app.core.dependencies import get_current_customer
from app.services.notification_service import notification_service
from decimal import Decimal
import math

router = APIRouter()


async def calculate_session_cost(session: ParkingSession, db: AsyncSession) -> Decimal:
    """Calculate parking session cost based on duration and tariff"""

    if not session.exit_time:
        return Decimal("0.00")

    # Calculate duration in minutes
    duration = session.exit_time - session.entry_time
    duration_minutes = int(duration.total_seconds() / 60)

    # Get spot and zone to find tariff
    spot_stmt = select(ParkingSpot).where(ParkingSpot.spot_id == session.spot_id)
    spot_result = await db.execute(spot_stmt)
    spot = spot_result.scalar_one_or_none()

    if not spot:
        return Decimal("0.00")

    zone_stmt = select(ParkingZone).where(ParkingZone.zone_id == spot.zone_id)
    zone_result = await db.execute(zone_stmt)
    zone = zone_result.scalar_one_or_none()

    if not zone or not zone.tariff_id:
        return Decimal("0.00")

    tariff_stmt = select(TariffPlan).where(TariffPlan.tariff_id == zone.tariff_id)
    tariff_result = await db.execute(tariff_stmt)
    tariff = tariff_result.scalar_one_or_none()

    if not tariff:
        return Decimal("0.00")

    # Calculate cost
    # If parking is less than 1 day, use hourly rate
    if duration_minutes < 1440:  # 24 hours = 1440 minutes
        hours = math.ceil(duration_minutes / 60)  # Round up to next hour
        cost = tariff.price_per_hour * hours

        # Apply daily max if exists
        if tariff.price_per_day and cost > tariff.price_per_day:
            cost = tariff.price_per_day
    else:
        # For multi-day parking
        days = math.ceil(duration_minutes / 1440)
        cost = tariff.price_per_day * days if tariff.price_per_day else tariff.price_per_hour * 24 * days

    return Decimal(str(cost))


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

    # Send session started notification
    await notification_service.send_session_started(
        customer_email=current_customer.email,
        customer_name=f"{current_customer.first_name} {current_customer.last_name}",
        session_id=str(new_session.session_id),
        zone_name=zone.name if zone else "Unknown",
        spot_number=spot.spot_number,
        vehicle_plate=vehicle.license_plate,
        entry_time=new_session.entry_time
    )

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

    # Calculate duration in minutes
    duration = session.exit_time - session.entry_time
    session.duration_minutes = int(duration.total_seconds() / 60)

    # Calculate cost
    session.total_cost = await calculate_session_cost(session, db)

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

    # Auto-create payment for the session
    # Check if payment already exists
    payment_stmt = select(Payment).where(Payment.session_id == session.session_id)
    payment_result = await db.execute(payment_stmt)
    existing_payment = payment_result.scalar_one_or_none()

    if not existing_payment and session.total_cost > 0:
        # Create payment record
        new_payment = Payment(
            session_id=session.session_id,
            customer_id=current_customer.customer_id,
            amount=session.total_cost,
            payment_method="pending",  # User will choose method later
            status="pending"
        )
        db.add(new_payment)

    await db.commit()
    await db.refresh(session)

    # Get vehicle for notification
    vehicle_stmt = select(Vehicle).where(Vehicle.vehicle_id == session.vehicle_id)
    vehicle_result = await db.execute(vehicle_stmt)
    vehicle = vehicle_result.scalar_one_or_none()

    # Send session ended notification
    if vehicle and spot and zone:
        await notification_service.send_session_ended(
            customer_email=current_customer.email,
            customer_name=f"{current_customer.first_name} {current_customer.last_name}",
            session_id=str(session.session_id),
            zone_name=zone.name,
            spot_number=spot.spot_number,
            vehicle_plate=vehicle.license_plate,
            entry_time=session.entry_time,
            exit_time=session.exit_time,
            duration_minutes=session.duration_minutes,
            total_cost=float(session.total_cost)
        )

    return session


@router.get("/{session_id}/calculate-cost")
async def calculate_current_cost(
    session_id: UUID,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Calculate current cost for an active session"""

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

    # Create temporary session with current time as exit to calculate cost
    temp_session = ParkingSession(
        session_id=session.session_id,
        vehicle_id=session.vehicle_id,
        spot_id=session.spot_id,
        entry_time=session.entry_time,
        exit_time=datetime.utcnow(),
        booking_id=session.booking_id,
        status=session.status
    )

    cost = await calculate_session_cost(temp_session, db)
    duration = datetime.utcnow() - session.entry_time
    duration_minutes = int(duration.total_seconds() / 60)

    return {
        "session_id": session_id,
        "entry_time": session.entry_time,
        "current_time": datetime.utcnow(),
        "duration_minutes": duration_minutes,
        "estimated_cost": float(cost),
        "status": session.status
    }


@router.get("/history/all", response_model=List[ParkingSessionHistoryResponse])
async def get_session_history(
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed history of all parking sessions for current customer"""

    # Get customer's vehicle IDs
    vehicles_stmt = select(Vehicle.vehicle_id).where(Vehicle.customer_id == current_customer.customer_id)
    vehicles_result = await db.execute(vehicles_stmt)
    vehicle_ids = [row[0] for row in vehicles_result.all()]

    if not vehicle_ids:
        return []

    # Get all completed sessions
    stmt = select(ParkingSession).where(
        ParkingSession.vehicle_id.in_(vehicle_ids),
        ParkingSession.status == "completed"
    ).order_by(ParkingSession.entry_time.desc())

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # Build detailed response
    detailed_sessions = []
    for session in sessions:
        # Get spot
        spot_stmt = select(ParkingSpot).where(ParkingSpot.spot_id == session.spot_id)
        spot_result = await db.execute(spot_stmt)
        spot = spot_result.scalar_one_or_none()

        if not spot:
            continue

        # Get zone
        zone_stmt = select(ParkingZone).where(ParkingZone.zone_id == spot.zone_id)
        zone_result = await db.execute(zone_stmt)
        zone = zone_result.scalar_one_or_none()

        if not zone:
            continue

        # Get vehicle
        vehicle_stmt = select(Vehicle).where(Vehicle.vehicle_id == session.vehicle_id)
        vehicle_result = await db.execute(vehicle_stmt)
        vehicle = vehicle_result.scalar_one_or_none()

        if not vehicle:
            continue

        # Get payment (optional)
        payment_stmt = select(Payment).where(Payment.session_id == session.session_id)
        payment_result = await db.execute(payment_stmt)
        payment = payment_result.scalar_one_or_none()

        # Build detailed session
        detailed_session = ParkingSessionHistoryResponse(
            session_id=session.session_id,
            entry_time=session.entry_time,
            exit_time=session.exit_time,
            duration_minutes=session.duration_minutes,
            total_cost=session.total_cost,
            status=session.status,
            created_at=session.created_at,
            spot=SessionSpotDetail(
                spot_id=spot.spot_id,
                spot_number=spot.spot_number,
                spot_type=spot.spot_type
            ),
            zone=SessionZoneDetail(
                zone_id=zone.zone_id,
                name=zone.name,
                address=zone.address
            ),
            vehicle=SessionVehicleDetail(
                vehicle_id=vehicle.vehicle_id,
                license_plate=vehicle.license_plate,
                model=vehicle.model,
                color=vehicle.color
            ),
            payment=SessionPaymentDetail(
                payment_id=payment.payment_id,
                amount=payment.amount,
                status=payment.status,
                payment_method=payment.payment_method,
                created_at=payment.created_at
            ) if payment else None
        )

        detailed_sessions.append(detailed_session)

    return detailed_sessions


@router.get("/statistics/monthly")
async def get_monthly_statistics(
    current_customer: Customer = Depends(get_current_customer),
    months: int = 6,
    db: AsyncSession = Depends(get_db)
):
    """Get monthly parking statistics for charts"""
    from datetime import timedelta
    from collections import defaultdict

    # Get customer's vehicle IDs
    vehicles_stmt = select(Vehicle.vehicle_id).where(Vehicle.customer_id == current_customer.customer_id)
    vehicles_result = await db.execute(vehicles_stmt)
    vehicle_ids = [row[0] for row in vehicles_result.all()]

    if not vehicle_ids:
        return {"months": [], "sessions_count": [], "total_cost": [], "total_hours": []}

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=months * 30)

    # Get all completed sessions in range
    stmt = select(ParkingSession).where(
        ParkingSession.vehicle_id.in_(vehicle_ids),
        ParkingSession.status == "completed",
        ParkingSession.entry_time >= start_date
    ).order_by(ParkingSession.entry_time)

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # Group by month
    monthly_data = defaultdict(lambda: {"count": 0, "cost": 0, "hours": 0})

    for session in sessions:
        month_key = session.entry_time.strftime("%Y-%m")
        monthly_data[month_key]["count"] += 1
        monthly_data[month_key]["cost"] += float(session.total_cost or 0)
        monthly_data[month_key]["hours"] += (session.duration_minutes or 0) / 60

    # Format response
    sorted_months = sorted(monthly_data.keys())

    return {
        "months": sorted_months,
        "sessions_count": [monthly_data[m]["count"] for m in sorted_months],
        "total_cost": [round(monthly_data[m]["cost"], 2) for m in sorted_months],
        "total_hours": [round(monthly_data[m]["hours"], 1) for m in sorted_months]
    }
