"""
Тесты для эндпоинтов парковочных сессий
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.vehicle import Vehicle
from app.models.parking_zone import ParkingZone
from app.models.parking_spot import ParkingSpot
from app.models.parking_session import ParkingSession
from app.models.booking import Booking
from app.models.tariff_plan import TariffPlan
from app.models.payment import Payment


@pytest.fixture
async def test_tariff(db_session: AsyncSession):
    """Создание тестового тарифного плана"""
    tariff = TariffPlan(
        name="Стандартный тариф",
        description="Обычный тариф для всех",
        price_per_hour=Decimal("100.00"),
        price_per_day=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(tariff)
    await db_session.commit()
    await db_session.refresh(tariff)
    return tariff


@pytest.fixture
async def test_zone_with_tariff(db_session: AsyncSession, test_tariff):
    """Создание тестовой парковочной зоны с тарифом"""
    zone = ParkingZone(
        name="Тестовая зона",
        address="ул. Тестовая, 1",
        total_spots=10,
        available_spots=10,
        tariff_id=test_tariff.tariff_id,
        is_active=True
    )
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)
    return zone


@pytest.fixture
async def test_spot_with_zone(db_session: AsyncSession, test_zone_with_tariff):
    """Создание тестового парковочного места с зоной"""
    spot = ParkingSpot(
        zone_id=test_zone_with_tariff.zone_id,
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
async def test_vehicle_for_session(db_session: AsyncSession, test_customer):
    """Создание тестового автомобиля для сессий"""
    vehicle = Vehicle(
        customer_id=test_customer.customer_id,
        license_plate="С777РС777",
        make="BMW",
        model="X5",
        color="Черный",
        vehicle_type="suv"
    )
    db_session.add(vehicle)
    await db_session.commit()
    await db_session.refresh(vehicle)
    return vehicle


@pytest.mark.asyncio
async def test_start_session_success(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    db_session: AsyncSession
):
    """Тест успешного начала парковочной сессии"""
    response = await client.post(
        "/api/sessions/",
        headers=auth_headers,
        json={
            "vehicle_id": str(test_vehicle_for_session.vehicle_id),
            "spot_id": str(test_spot_with_zone.spot_id),
            "entry_time": datetime.utcnow().isoformat()
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "active"
    assert data["vehicle_id"] == str(test_vehicle_for_session.vehicle_id)
    assert data["spot_id"] == str(test_spot_with_zone.spot_id)

    # Проверяем, что место помечено как занятое
    await db_session.refresh(test_spot_with_zone)
    assert test_spot_with_zone.is_occupied is True


@pytest.mark.asyncio
async def test_start_session_spot_occupied(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    db_session: AsyncSession
):
    """Тест начала сессии на занятом месте"""
    # Занимаем место
    test_spot_with_zone.is_occupied = True
    await db_session.commit()

    response = await client.post(
        "/api/sessions/",
        headers=auth_headers,
        json={
            "vehicle_id": str(test_vehicle_for_session.vehicle_id),
            "spot_id": str(test_spot_with_zone.spot_id),
            "entry_time": datetime.utcnow().isoformat()
        }
    )

    assert response.status_code == 400
    assert "already occupied" in response.json()["detail"]


@pytest.mark.asyncio
async def test_start_session_with_booking(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    test_customer,
    db_session: AsyncSession
):
    """Тест начала сессии с бронированием"""
    # Создаем подтвержденное бронирование
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=2)

    booking = Booking(
        customer_id=test_customer.customer_id,
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        start_time=start_time,
        end_time=end_time,
        status="confirmed"
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    response = await client.post(
        "/api/sessions/",
        headers=auth_headers,
        json={
            "vehicle_id": str(test_vehicle_for_session.vehicle_id),
            "spot_id": str(test_spot_with_zone.spot_id),
            "entry_time": datetime.utcnow().isoformat(),
            "booking_id": str(booking.booking_id)
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["booking_id"] == str(booking.booking_id)


@pytest.mark.asyncio
async def test_start_session_invalid_booking(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone
):
    """Тест начала сессии с несуществующим бронированием"""
    response = await client.post(
        "/api/sessions/",
        headers=auth_headers,
        json={
            "vehicle_id": str(test_vehicle_for_session.vehicle_id),
            "spot_id": str(test_spot_with_zone.spot_id),
            "entry_time": datetime.utcnow().isoformat(),
            "booking_id": "00000000-0000-0000-0000-000000000000"
        }
    )

    assert response.status_code == 404
    assert "Booking not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_my_sessions(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    db_session: AsyncSession
):
    """Тест получения всех сессий пользователя"""
    # Создаем тестовую сессию
    session = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=datetime.utcnow() - timedelta(hours=2),
        status="active"
    )
    db_session.add(session)
    await db_session.commit()

    response = await client.get("/api/sessions/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_active_sessions(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    db_session: AsyncSession
):
    """Тест получения только активных сессий"""
    # Создаем активную сессию
    active_session = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=datetime.utcnow() - timedelta(hours=1),
        status="active"
    )

    # Создаем завершенную сессию
    completed_session = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=datetime.utcnow() - timedelta(days=1),
        exit_time=datetime.utcnow() - timedelta(days=1, hours=-2),
        duration_minutes=120,
        total_cost=Decimal("200.00"),
        status="completed"
    )

    db_session.add_all([active_session, completed_session])
    await db_session.commit()

    response = await client.get("/api/sessions/active", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert all(s["status"] == "active" for s in data)


@pytest.mark.asyncio
async def test_get_session_by_id(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    db_session: AsyncSession
):
    """Тест получения конкретной сессии"""
    session = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=datetime.utcnow() - timedelta(hours=1),
        status="active"
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    response = await client.get(
        f"/api/sessions/{session.session_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == str(session.session_id)


@pytest.mark.asyncio
async def test_end_session_success(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    db_session: AsyncSession
):
    """Тест успешного завершения сессии"""
    entry_time = datetime.utcnow() - timedelta(hours=2)
    session = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=entry_time,
        status="active"
    )

    # Помечаем место как занятое
    test_spot_with_zone.is_occupied = True

    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    exit_time = datetime.utcnow()
    response = await client.patch(
        f"/api/sessions/{session.session_id}/end",
        headers=auth_headers,
        json={"exit_time": exit_time.isoformat()}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["exit_time"] is not None
    assert data["duration_minutes"] is not None
    assert data["total_cost"] is not None

    # Проверяем, что место освободилось
    await db_session.refresh(test_spot_with_zone)
    assert test_spot_with_zone.is_occupied is False

    # Проверяем, что создан платеж
    payment_stmt = select(Payment).where(Payment.session_id == session.session_id)
    payment_result = await db_session.execute(payment_stmt)
    payment = payment_result.scalar_one_or_none()
    assert payment is not None


@pytest.mark.asyncio
async def test_end_session_invalid_exit_time(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    db_session: AsyncSession
):
    """Тест завершения сессии с некорректным временем выезда"""
    entry_time = datetime.utcnow()
    session = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=entry_time,
        status="active"
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    # Время выезда раньше времени въезда
    exit_time = entry_time - timedelta(hours=1)
    response = await client.patch(
        f"/api/sessions/{session.session_id}/end",
        headers=auth_headers,
        json={"exit_time": exit_time.isoformat()}
    )

    assert response.status_code == 400
    assert "after entry time" in response.json()["detail"]


@pytest.mark.asyncio
async def test_end_already_completed_session(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    db_session: AsyncSession
):
    """Тест завершения уже завершенной сессии"""
    entry_time = datetime.utcnow() - timedelta(hours=3)
    exit_time = datetime.utcnow() - timedelta(hours=1)

    session = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=entry_time,
        exit_time=exit_time,
        duration_minutes=120,
        total_cost=Decimal("200.00"),
        status="completed"
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    response = await client.patch(
        f"/api/sessions/{session.session_id}/end",
        headers=auth_headers,
        json={"exit_time": datetime.utcnow().isoformat()}
    )

    assert response.status_code == 400
    assert "not active" in response.json()["detail"]


@pytest.mark.asyncio
async def test_calculate_current_cost(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    db_session: AsyncSession
):
    """Тест расчета текущей стоимости активной сессии"""
    entry_time = datetime.utcnow() - timedelta(hours=2)
    session = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=entry_time,
        status="active"
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    response = await client.get(
        f"/api/sessions/{session.session_id}/calculate-cost",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "estimated_cost" in data
    assert "duration_minutes" in data
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_get_session_history(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    test_customer,
    db_session: AsyncSession
):
    """Тест получения истории парковочных сессий"""
    # Создаем завершенные сессии
    entry_time1 = datetime.utcnow() - timedelta(days=2)
    exit_time1 = entry_time1 + timedelta(hours=3)

    session1 = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=entry_time1,
        exit_time=exit_time1,
        duration_minutes=180,
        total_cost=Decimal("300.00"),
        status="completed"
    )

    entry_time2 = datetime.utcnow() - timedelta(days=1)
    exit_time2 = entry_time2 + timedelta(hours=1)

    session2 = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=entry_time2,
        exit_time=exit_time2,
        duration_minutes=60,
        total_cost=Decimal("100.00"),
        status="completed"
    )

    db_session.add_all([session1, session2])
    await db_session.commit()
    await db_session.refresh(session1)

    # Создаем платеж для первой сессии
    payment = Payment(
        session_id=session1.session_id,
        customer_id=test_customer.customer_id,
        amount=Decimal("300.00"),
        payment_method="card",
        status="completed"
    )
    db_session.add(payment)
    await db_session.commit()

    response = await client.get("/api/sessions/history/all", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # Проверяем детальную информацию
    assert all("spot" in s for s in data)
    assert all("zone" in s for s in data)
    assert all("vehicle" in s for s in data)


@pytest.mark.asyncio
async def test_get_monthly_statistics(
    client: AsyncClient,
    auth_headers,
    test_vehicle_for_session,
    test_spot_with_zone,
    db_session: AsyncSession
):
    """Тест получения месячной статистики"""
    # Создаем несколько завершенных сессий за последние месяцы
    sessions = []
    for i in range(5):
        entry_time = datetime.utcnow() - timedelta(days=i*7)
        exit_time = entry_time + timedelta(hours=2)

        session = ParkingSession(
            vehicle_id=test_vehicle_for_session.vehicle_id,
            spot_id=test_spot_with_zone.spot_id,
            entry_time=entry_time,
            exit_time=exit_time,
            duration_minutes=120,
            total_cost=Decimal("200.00"),
            status="completed"
        )
        sessions.append(session)

    db_session.add_all(sessions)
    await db_session.commit()

    response = await client.get("/api/sessions/statistics/monthly", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "months" in data
    assert "sessions_count" in data
    assert "total_cost" in data
    assert "total_hours" in data
    assert isinstance(data["months"], list)


@pytest.mark.asyncio
async def test_session_unauthorized(client: AsyncClient):
    """Тест доступа к сессиям без авторизации"""
    response = await client.get("/api/sessions/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_session_cost_calculation(
    db_session: AsyncSession,
    test_tariff,
    test_zone_with_tariff,
    test_spot_with_zone,
    test_vehicle_for_session
):
    """Тест расчета стоимости парковочной сессии"""
    from app.api.endpoints.sessions import calculate_session_cost

    # Создаем сессию длительностью 3 часа
    entry_time = datetime.utcnow() - timedelta(hours=3)
    exit_time = datetime.utcnow()

    session = ParkingSession(
        vehicle_id=test_vehicle_for_session.vehicle_id,
        spot_id=test_spot_with_zone.spot_id,
        entry_time=entry_time,
        exit_time=exit_time,
        status="completed"
    )

    cost = await calculate_session_cost(session, db_session)

    # Стоимость должна быть 3 часа * 100 руб/час = 300 руб
    assert cost == Decimal("300.00")
