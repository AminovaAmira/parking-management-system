"""
Admin endpoints - управление системой (только для администраторов)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, cast, Date
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.customer import Customer
from app.models.parking_zone import ParkingZone
from app.models.parking_spot import ParkingSpot
from app.models.booking import Booking
from app.models.parking_session import ParkingSession
from app.models.payment import Payment
from app.models.tariff_plan import TariffPlan
from app.core.dependencies import get_current_admin
from app.schemas.parking import ParkingZoneCreate, ParkingZoneResponse, ParkingSpotCreate, ParkingSpotResponse

router = APIRouter()


# ========== СТАТИСТИКА ДЛЯ АДМИНА ==========

@router.get("/stats/overview")
async def get_admin_stats_overview(
    admin: Customer = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Общая статистика системы для админа"""

    # Количество пользователей
    users_count_stmt = select(func.count(Customer.customer_id))
    users_count = (await db.execute(users_count_stmt)).scalar()

    # Количество активных парковочных сессий
    active_sessions_stmt = select(func.count(ParkingSession.session_id)).where(
        ParkingSession.status == "active"
    )
    active_sessions = (await db.execute(active_sessions_stmt)).scalar()

    # Общая выручка
    total_revenue_stmt = select(func.sum(Payment.amount)).where(
        Payment.status == "completed"
    )
    total_revenue = (await db.execute(total_revenue_stmt)).scalar() or 0

    # Количество зон и мест
    zones_count_stmt = select(func.count(ParkingZone.zone_id))
    zones_count = (await db.execute(zones_count_stmt)).scalar()

    spots_count_stmt = select(func.count(ParkingSpot.spot_id))
    spots_count = (await db.execute(spots_count_stmt)).scalar()

    # Занятость мест
    occupied_spots_stmt = select(func.count(ParkingSpot.spot_id)).where(
        ParkingSpot.is_occupied == True
    )
    occupied_spots = (await db.execute(occupied_spots_stmt)).scalar()

    # Количество бронирований по статусам
    bookings_by_status_stmt = select(
        Booking.status,
        func.count(Booking.booking_id)
    ).group_by(Booking.status)
    bookings_by_status = (await db.execute(bookings_by_status_stmt)).all()

    return {
        "users_count": users_count,
        "active_sessions": active_sessions,
        "total_revenue": float(total_revenue),
        "parking_zones": zones_count,
        "parking_spots": {
            "total": spots_count,
            "occupied": occupied_spots,
            "available": spots_count - occupied_spots,
            "occupancy_rate": round((occupied_spots / spots_count * 100) if spots_count > 0 else 0, 2)
        },
        "bookings_by_status": {row[0]: row[1] for row in bookings_by_status}
    }


@router.get("/stats/daily")
async def get_daily_statistics(
    days: int = Query(21, ge=7, le=90, description="Количество дней для отображения"),
    admin: Customer = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Статистика по дням для графиков (выручка, бронирования, заполненность)"""

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    # Выручка по дням
    revenue_stmt = select(
        cast(Payment.created_at, Date).label('date'),
        func.sum(Payment.amount).label('revenue')
    ).where(
        and_(
            Payment.status == 'completed',
            cast(Payment.created_at, Date) >= start_date,
            cast(Payment.created_at, Date) <= end_date
        )
    ).group_by(cast(Payment.created_at, Date)).order_by(cast(Payment.created_at, Date))

    revenue_result = await db.execute(revenue_stmt)
    revenue_by_date = {str(row.date): float(row.revenue) for row in revenue_result}

    # Бронирования по дням (по времени начала)
    bookings_stmt = select(
        cast(Booking.start_time, Date).label('date'),
        func.count(Booking.booking_id).label('count')
    ).where(
        and_(
            cast(Booking.start_time, Date) >= start_date,
            cast(Booking.start_time, Date) <= end_date,
            Booking.status == 'confirmed'
        )
    ).group_by(cast(Booking.start_time, Date)).order_by(cast(Booking.start_time, Date))

    bookings_result = await db.execute(bookings_stmt)
    bookings_by_date = {str(row.date): row.count for row in bookings_result}

    # Формируем данные для всех дней в диапазоне
    daily_stats = []
    current_date = start_date

    while current_date <= end_date:
        date_str = str(current_date)
        daily_stats.append({
            "date": date_str,
            "revenue": revenue_by_date.get(date_str, 0),
            "bookings": bookings_by_date.get(date_str, 0)
        })
        current_date += timedelta(days=1)

    return {
        "daily_stats": daily_stats,
        "period": {
            "start_date": str(start_date),
            "end_date": str(end_date),
            "days": days
        }
    }


# ========== УПРАВЛЕНИЕ ЗОНАМИ ==========

@router.post("/zones", response_model=ParkingZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_parking_zone(
    zone_data: ParkingZoneCreate,
    admin: Customer = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Создание новой парковочной зоны (только админ)"""

    new_zone = ParkingZone(**zone_data.model_dump())
    db.add(new_zone)
    await db.commit()
    await db.refresh(new_zone)

    return new_zone


@router.put("/zones/{zone_id}", response_model=ParkingZoneResponse)
async def update_parking_zone(
    zone_id: UUID,
    zone_data: ParkingZoneCreate,
    admin: Customer = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Обновление парковочной зоны (только админ)"""

    stmt = select(ParkingZone).where(ParkingZone.zone_id == zone_id)
    result = await db.execute(stmt)
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking zone not found"
        )

    for key, value in zone_data.model_dump(exclude_unset=True).items():
        setattr(zone, key, value)

    await db.commit()
    await db.refresh(zone)

    return zone


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parking_zone(
    zone_id: UUID,
    admin: Customer = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Удаление парковочной зоны (только админ)"""

    stmt = select(ParkingZone).where(ParkingZone.zone_id == zone_id)
    result = await db.execute(stmt)
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking zone not found"
        )

    # Проверяем, есть ли активные места
    spots_stmt = select(func.count(ParkingSpot.spot_id)).where(
        ParkingSpot.zone_id == zone_id,
        ParkingSpot.is_active == True
    )
    active_spots = (await db.execute(spots_stmt)).scalar()

    if active_spots > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete zone with {active_spots} active parking spots. Deactivate spots first."
        )

    await db.delete(zone)
    await db.commit()

    return None


# ========== УПРАВЛЕНИЕ МЕСТАМИ ==========

@router.put("/spots/{spot_id}", response_model=ParkingSpotResponse)
async def update_parking_spot(
    spot_id: UUID,
    spot_data: ParkingSpotCreate,
    admin: Customer = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Обновление парковочного места (только админ)"""

    stmt = select(ParkingSpot).where(ParkingSpot.spot_id == spot_id)
    result = await db.execute(stmt)
    spot = result.scalar_one_or_none()

    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking spot not found"
        )

    for key, value in spot_data.model_dump(exclude_unset=True).items():
        setattr(spot, key, value)

    await db.commit()
    await db.refresh(spot)

    return spot


@router.delete("/spots/{spot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parking_spot(
    spot_id: UUID,
    admin: Customer = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Удаление парковочного места (только админ)"""

    stmt = select(ParkingSpot).where(ParkingSpot.spot_id == spot_id)
    result = await db.execute(stmt)
    spot = result.scalar_one_or_none()

    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking spot not found"
        )

    if spot.is_occupied:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete occupied parking spot"
        )

    await db.delete(spot)
    await db.commit()

    return None


# ========== ПРОСМОТР ВСЕХ БРОНИРОВАНИЙ ==========

@router.get("/bookings")
async def get_all_bookings(
    admin: Customer = Depends(get_current_admin),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех бронирований в системе (только админ)"""

    stmt = select(Booking)

    if status:
        stmt = stmt.where(Booking.status == status)

    stmt = stmt.order_by(Booking.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    bookings = result.scalars().all()

    # Получить общее количество
    count_stmt = select(func.count(Booking.booking_id))
    if status:
        count_stmt = count_stmt.where(Booking.status == status)
    total = (await db.execute(count_stmt)).scalar()

    # Получить информацию о клиентах и местах для каждого бронирования
    bookings_with_details = []
    for booking in bookings:
        # Получить клиента
        customer_stmt = select(Customer).where(Customer.customer_id == booking.customer_id)
        customer_result = await db.execute(customer_stmt)
        customer = customer_result.scalar_one_or_none()

        # Получить место
        spot_stmt = select(ParkingSpot).where(ParkingSpot.spot_id == booking.spot_id)
        spot_result = await db.execute(spot_stmt)
        spot = spot_result.scalar_one_or_none()

        bookings_with_details.append({
            "booking_id": str(booking.booking_id),
            "customer_id": str(booking.customer_id),
            "customer_name": f"{customer.first_name} {customer.last_name}" if customer else "Неизвестно",
            "spot_id": str(booking.spot_id),
            "spot_number": spot.spot_number if spot else "Неизвестно",
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "status": booking.status,
            "estimated_cost": float(booking.estimated_cost) if booking.estimated_cost else None,
            "created_at": booking.created_at
        })

    return {
        "bookings": bookings_with_details,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ========== ПРОСМОТР ВСЕХ СЕССИЙ ==========

@router.get("/sessions")
async def get_all_sessions(
    admin: Customer = Depends(get_current_admin),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех парковочных сессий (только админ)"""

    stmt = select(ParkingSession)

    if status:
        stmt = stmt.where(ParkingSession.status == status)

    stmt = stmt.order_by(ParkingSession.entry_time.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    count_stmt = select(func.count(ParkingSession.session_id))
    if status:
        count_stmt = count_stmt.where(ParkingSession.status == status)
    total = (await db.execute(count_stmt)).scalar()

    return {
        "sessions": sessions,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ========== ПРОСМОТР ВСЕХ ПЛАТЕЖЕЙ ==========

@router.get("/payments")
async def get_all_payments(
    admin: Customer = Depends(get_current_admin),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех платежей в системе (только админ)"""

    stmt = select(Payment)

    if status:
        stmt = stmt.where(Payment.status == status)

    stmt = stmt.order_by(Payment.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    payments = result.scalars().all()

    count_stmt = select(func.count(Payment.payment_id))
    if status:
        count_stmt = count_stmt.where(Payment.status == status)
    total = (await db.execute(count_stmt)).scalar()

    return {
        "payments": payments,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ========== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ==========

@router.get("/users")
async def get_all_users(
    admin: Customer = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка всех пользователей (только админ)"""

    stmt = select(Customer).order_by(Customer.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    users = result.scalars().all()

    count_stmt = select(func.count(Customer.customer_id))
    total = (await db.execute(count_stmt)).scalar()

    return {
        "users": [
            {
                "customer_id": str(user.customer_id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "is_admin": user.is_admin,
                "created_at": user.created_at
            }
            for user in users
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }
