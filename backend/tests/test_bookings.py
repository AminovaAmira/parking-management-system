"""
Tests for booking endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from app.models.vehicle import Vehicle
from app.models.parking_zone import ParkingZone
from app.models.parking_spot import ParkingSpot
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.transaction import Transaction
from app.models.customer import Customer


@pytest.fixture
async def test_zone(db_session: AsyncSession):
    """Create a test parking zone"""
    zone = ParkingZone(
        name="Тестовая зона",
        address="ул. Тестовая, 1",
        total_spots=10,
        available_spots=10,
        is_active=True
    )
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)
    return zone


@pytest.fixture
async def test_spot(db_session: AsyncSession, test_zone: ParkingZone):
    """Create a test parking spot"""
    spot = ParkingSpot(
        zone_id=test_zone.zone_id,
        spot_number="A-101",
        spot_type="standard",
        is_occupied=False,
        is_active=True
    )
    db_session.add(spot)
    await db_session.commit()
    await db_session.refresh(spot)
    return spot


@pytest.fixture
async def test_vehicle(db_session: AsyncSession, test_customer):
    """Create a test vehicle"""
    vehicle = Vehicle(
        customer_id=test_customer.customer_id,
        license_plate="Т123ЕС777",
        make="Toyota",
        model="Camry",
        color="Белый",
        vehicle_type="sedan"
    )
    db_session.add(vehicle)
    await db_session.commit()
    await db_session.refresh(vehicle)
    return vehicle


@pytest.mark.asyncio
async def test_create_booking_success(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot,
    db_session: AsyncSession,
    test_customer
):
    """Test creating a booking successfully with balance deduction"""
    # Set initial balance
    test_customer.balance = Decimal("1000.00")
    await db_session.commit()

    start_time = datetime.now(dt_timezone.utc) + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    response = await client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "vehicle_id": str(test_vehicle.vehicle_id),
            "spot_id": str(test_spot.spot_id),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["vehicle_id"] == str(test_vehicle.vehicle_id)
    assert data["spot_id"] == str(test_spot.spot_id)
    assert "estimated_cost" in data

    # Check balance was deducted
    await db_session.refresh(test_customer)
    assert test_customer.balance < Decimal("1000.00")

    # Check payment was created
    payment_stmt = select(Payment).where(Payment.booking_id == data["booking_id"])
    payment_result = await db_session.execute(payment_stmt)
    payment = payment_result.scalar_one()
    assert payment.status == "completed"
    assert payment.payment_method == "balance"

    # Check transaction was created
    transaction_stmt = select(Transaction).where(Transaction.booking_id == data["booking_id"])
    transaction_result = await db_session.execute(transaction_stmt)
    transaction = transaction_result.scalar_one()
    assert transaction.type == "booking_charge"
    assert transaction.amount == data["estimated_cost"]


@pytest.mark.asyncio
async def test_create_booking_invalid_vehicle(
    client: AsyncClient,
    auth_headers,
    test_spot
):
    """Test creating a booking with non-existent vehicle"""
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    response = await client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "vehicle_id": "00000000-0000-0000-0000-000000000000",
            "spot_id": str(test_spot.spot_id),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

    assert response.status_code == 404
    assert "Vehicle not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_booking_invalid_spot(
    client: AsyncClient,
    auth_headers,
    test_vehicle
):
    """Test creating a booking with non-existent spot"""
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    response = await client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "vehicle_id": str(test_vehicle.vehicle_id),
            "spot_id": "00000000-0000-0000-0000-000000000000",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

    assert response.status_code == 404
    assert "Parking spot not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_booking_past_time(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot
):
    """Test creating a booking with past start time"""
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    response = await client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "vehicle_id": str(test_vehicle.vehicle_id),
            "spot_id": str(test_spot.spot_id),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

    assert response.status_code == 400
    assert "must be in the future" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_booking_invalid_time_range(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot
):
    """Test creating a booking with end time before start time"""
    start_time = datetime.utcnow() + timedelta(hours=2)
    end_time = datetime.utcnow() + timedelta(hours=1)

    response = await client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "vehicle_id": str(test_vehicle.vehicle_id),
            "spot_id": str(test_spot.spot_id),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

    assert response.status_code == 400
    assert "after start time" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_booking_conflict(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot,
    db_session: AsyncSession,
    test_customer
):
    """Test creating a booking when spot is already booked"""
    # Create an existing booking
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=3)

    existing_booking = Booking(
        customer_id=test_customer.customer_id,
        vehicle_id=test_vehicle.vehicle_id,
        spot_id=test_spot.spot_id,
        start_time=start_time,
        end_time=end_time,
        status="confirmed"
    )
    db_session.add(existing_booking)
    await db_session.commit()

    # Try to create overlapping booking
    new_start = start_time + timedelta(hours=1)
    new_end = new_start + timedelta(hours=2)

    response = await client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "vehicle_id": str(test_vehicle.vehicle_id),
            "spot_id": str(test_spot.spot_id),
            "start_time": new_start.isoformat(),
            "end_time": new_end.isoformat()
        }
    )

    assert response.status_code == 400
    assert "already booked" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_my_bookings(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot,
    db_session: AsyncSession,
    test_customer
):
    """Test getting all bookings for current user"""
    # Create test bookings
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    booking = Booking(
        customer_id=test_customer.customer_id,
        vehicle_id=test_vehicle.vehicle_id,
        spot_id=test_spot.spot_id,
        start_time=start_time,
        end_time=end_time,
        status="pending"
    )
    db_session.add(booking)
    await db_session.commit()

    response = await client.get("/api/bookings/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_get_my_bookings_filter_by_status(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot,
    db_session: AsyncSession,
    test_customer
):
    """Test filtering bookings by status"""
    # Create bookings with different statuses
    start_time = datetime.utcnow() + timedelta(hours=1)

    booking1 = Booking(
        customer_id=test_customer.customer_id,
        vehicle_id=test_vehicle.vehicle_id,
        spot_id=test_spot.spot_id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=2),
        status="pending"
    )
    booking2 = Booking(
        customer_id=test_customer.customer_id,
        vehicle_id=test_vehicle.vehicle_id,
        spot_id=test_spot.spot_id,
        start_time=start_time + timedelta(days=1),
        end_time=start_time + timedelta(days=1, hours=2),
        status="confirmed"
    )

    db_session.add_all([booking1, booking2])
    await db_session.commit()

    response = await client.get("/api/bookings/?status=pending", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert all(b["status"] == "pending" for b in data)


@pytest.mark.asyncio
async def test_get_booking_by_id(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot,
    db_session: AsyncSession,
    test_customer
):
    """Test getting a specific booking"""
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    booking = Booking(
        customer_id=test_customer.customer_id,
        vehicle_id=test_vehicle.vehicle_id,
        spot_id=test_spot.spot_id,
        start_time=start_time,
        end_time=end_time,
        status="pending"
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    response = await client.get(
        f"/api/bookings/{booking.booking_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["booking_id"] == str(booking.booking_id)


@pytest.mark.asyncio
async def test_update_booking_status(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot,
    db_session: AsyncSession,
    test_customer
):
    """Test updating booking status"""
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    booking = Booking(
        customer_id=test_customer.customer_id,
        vehicle_id=test_vehicle.vehicle_id,
        spot_id=test_spot.spot_id,
        start_time=start_time,
        end_time=end_time,
        status="pending"
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    response = await client.patch(
        f"/api/bookings/{booking.booking_id}/status",
        headers=auth_headers,
        json={"status": "confirmed"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_cancel_booking(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot,
    db_session: AsyncSession,
    test_customer
):
    """Test cancelling a booking with refund"""
    # Set initial balance and estimated cost
    initial_balance = Decimal("500.00")
    estimated_cost = Decimal("100.00")
    test_customer.balance = initial_balance - estimated_cost  # 400.00
    await db_session.commit()

    start_time = datetime.now(dt_timezone.utc) + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    booking = Booking(
        customer_id=test_customer.customer_id,
        vehicle_id=test_vehicle.vehicle_id,
        spot_id=test_spot.spot_id,
        start_time=start_time,
        end_time=end_time,
        estimated_cost=estimated_cost,
        status="pending"
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    response = await client.delete(
        f"/api/bookings/{booking.booking_id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Check balance was refunded
    await db_session.refresh(test_customer)
    assert test_customer.balance == initial_balance  # 500.00

    # Check refund transaction was created
    refund_stmt = select(Transaction).where(
        Transaction.booking_id == booking.booking_id,
        Transaction.type == "refund"
    )
    refund_result = await db_session.execute(refund_stmt)
    refund = refund_result.scalar_one()
    assert refund.amount == estimated_cost


@pytest.mark.asyncio
async def test_cancel_completed_booking(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot,
    db_session: AsyncSession,
    test_customer
):
    """Test that completed bookings cannot be cancelled"""
    start_time = datetime.utcnow() - timedelta(hours=3)
    end_time = start_time + timedelta(hours=2)

    booking = Booking(
        customer_id=test_customer.customer_id,
        vehicle_id=test_vehicle.vehicle_id,
        spot_id=test_spot.spot_id,
        start_time=start_time,
        end_time=end_time,
        status="completed"
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    response = await client.delete(
        f"/api/bookings/{booking.booking_id}",
        headers=auth_headers
    )

    assert response.status_code == 400
    assert "Cannot cancel completed booking" in response.json()["detail"]


@pytest.mark.asyncio
async def test_booking_unauthorized(client: AsyncClient):
    """Test booking endpoints without authentication"""
    response = await client.get("/api/bookings/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_booking_insufficient_balance(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot,
    db_session: AsyncSession,
    test_customer
):
    """Test creating a booking with insufficient balance"""
    # Set low balance
    test_customer.balance = Decimal("10.00")
    await db_session.commit()

    start_time = datetime.now(dt_timezone.utc) + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)  # 2 hours - will cost more than 10

    response = await client.post(
        "/api/bookings/",
        headers=auth_headers,
        json={
            "vehicle_id": str(test_vehicle.vehicle_id),
            "spot_id": str(test_spot.spot_id),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

    assert response.status_code == 400
    assert "Недостаточно средств" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_already_cancelled_booking(
    client: AsyncClient,
    auth_headers,
    test_vehicle,
    test_spot,
    db_session: AsyncSession,
    test_customer
):
    """Test that already cancelled bookings cannot be cancelled again"""
    start_time = datetime.now(dt_timezone.utc) + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    booking = Booking(
        customer_id=test_customer.customer_id,
        vehicle_id=test_vehicle.vehicle_id,
        spot_id=test_spot.spot_id,
        start_time=start_time,
        end_time=end_time,
        estimated_cost=Decimal("100.00"),
        status="cancelled"
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    response = await client.delete(
        f"/api/bookings/{booking.booking_id}",
        headers=auth_headers
    )

    assert response.status_code == 400
    assert "already cancelled" in response.json()["detail"]
