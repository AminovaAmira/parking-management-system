"""
Скрипт для заполнения БД реалистичными тестовыми данными
- Пользователи (15-20)
- Транспортные средства (25-30)
- Бронирования за последние 3 недели (с разной заполненностью)
- Платежи и парковочные сессии (завершённые и активные)
"""
import asyncio
import uuid
import random
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db.database import AsyncSessionLocal
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.models.parking_zone import ParkingZone
from app.models.parking_spot import ParkingSpot
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.parking_session import ParkingSession
from app.core.security import get_password_hash


# Данные для генерации реалистичных пользователей
FIRST_NAMES = [
    "Александр", "Дмитрий", "Михаил", "Сергей", "Андрей",
    "Алексей", "Артем", "Иван", "Максим", "Владимир",
    "Екатерина", "Анна", "Мария", "Ольга", "Елена",
    "Наталья", "Татьяна", "Ирина", "Светлана", "Юлия"
]

LAST_NAMES = [
    "Иванов", "Петров", "Сидоров", "Козлов", "Новikov",
    "Морозов", "Волков", "Соколов", "Лебедев", "Семенов",
    "Егоров", "Павлов", "Кузнецов", "Михайлов", "Федоров",
    "Смирнов", "Васильев", "Попов", "Соловьев", "Николаев"
]

# Марки и модели автомобилей
CAR_BRANDS = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Land Cruiser"],
    "BMW": ["3 Series", "5 Series", "X5", "X3"],
    "Mercedes": ["C-Class", "E-Class", "GLC", "S-Class"],
    "Audi": ["A4", "A6", "Q5", "Q7"],
    "Volkswagen": ["Polo", "Tiguan", "Passat", "Golf"],
    "Hyundai": ["Solaris", "Creta", "Tucson", "Elantra"],
    "Kia": ["Rio", "Sportage", "Optima", "Seltos"],
    "Lada": ["Vesta", "Granta", "Largus", "XRAY"],
    "Nissan": ["Qashqai", "X-Trail", "Juke", "Almera"],
    "Mazda": ["CX-5", "6", "3", "CX-9"]
}

COLORS = ["Черный", "Белый", "Серебристый", "Серый", "Синий", "Красный", "Зеленый"]

# Генераторы номеров
def generate_license_plate():
    """Генерация российского автомобильного номера"""
    letters = "АВЕКМНОРСТУХ"
    region = random.choice(["77", "99", "50", "78", "23", "16", "02", "01"])
    return f"{random.choice(letters)}{random.randint(100, 999)}{random.choice(letters)}{random.choice(letters)}{region}"

def generate_phone():
    """Генерация номера телефона"""
    return f"+7 ({random.randint(900, 999)}) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"


async def clear_test_data(db: AsyncSession):
    """Очистка тестовых данных (не трогая зоны, места и тарифы)"""
    print("🗑️  Очистка старых тестовых данных...")

    # Удаляем в правильном порядке (из-за foreign keys)
    await db.execute(delete(Payment))
    await db.execute(delete(ParkingSession))
    await db.execute(delete(Booking))
    await db.execute(delete(Vehicle))

    # Удаляем всех пользователей кроме админа
    await db.execute(delete(Customer).where(Customer.is_admin == False))

    await db.commit()
    print("✅ Старые данные очищены")


async def create_customers(db: AsyncSession, count: int = 18):
    """Создание тестовых пользователей (включая админа и Амиру)"""
    print(f"\n👥 Создание {count} пользователей...")

    customers = []
    used_emails = set()

    # 1. Создаём или находим админа
    admin_stmt = select(Customer).where(Customer.email == "admin@parking.com")
    admin_result = await db.execute(admin_stmt)
    admin = admin_result.scalar_one_or_none()

    if not admin:
        admin = Customer(
            customer_id=uuid.uuid4(),
            first_name="Admin",
            last_name="Parking",
            email="admin@parking.com",
            phone="+7 (999) 000-00-00",
            password_hash=get_password_hash("admin123"),
            is_admin=True,
            balance=Decimal("10000.00")  # У админа большой баланс
        )
        db.add(admin)
        await db.flush()
        print("✅ Создан админ: admin@parking.com / admin123")
    else:
        # Обновляем баланс существующего админа
        admin.balance = Decimal("10000.00")
        admin.is_admin = True  # На всякий случай
        await db.flush()
        print("✅ Обновлен админ: admin@parking.com (баланс установлен на 10000₽)")

    # 2. Создаём Амиру
    amira_stmt = select(Customer).where(Customer.email == "amira@test.com")
    amira_result = await db.execute(amira_stmt)
    amira = amira_result.scalar_one_or_none()

    if not amira:
        amira = Customer(
            customer_id=uuid.uuid4(),
            first_name="Амира",
            last_name="Аминова",
            email="amira@test.com",
            phone="+7 (999) 111-22-33",
            password_hash=get_password_hash("amira123"),
            is_admin=False,
            balance=Decimal("5000.00")  # Начальный баланс
        )
        db.add(amira)
        customers.append(amira)
        used_emails.add("amira@test.com")
        print("✅ Создана Амира: amira@test.com / amira123")
    else:
        # Обновляем баланс существующей Амиры
        amira.balance = Decimal("5000.00")
        await db.flush()
        customers.append(amira)
        used_emails.add("amira@test.com")
        print("✅ Обновлена Амира: amira@test.com (баланс установлен на 5000₽)")

    # 3. Создаём остальных пользователей
    for i in range(count - 1):  # -1 потому что Амира уже создана
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        # Генерируем уникальный email
        email_base = f"{first_name.lower()}.{last_name.lower()}{i}@test.com"
        email = email_base
        counter = 1
        while email in used_emails:
            email = f"{first_name.lower()}.{last_name.lower()}{i}_{counter}@test.com"
            counter += 1
        used_emails.add(email)

        # Случайный баланс от 0 до 3000 рублей
        balance = Decimal(str(random.randint(0, 3000)))

        customer = Customer(
            customer_id=uuid.uuid4(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=generate_phone(),
            password_hash=get_password_hash("password123"),
            is_admin=False,
            balance=balance
        )
        db.add(customer)
        customers.append(customer)

    await db.commit()

    # Обновляем объекты
    for customer in customers:
        await db.refresh(customer)

    print(f"✅ Создано {len(customers)} обычных пользователей (+ админ)")
    return customers


async def create_vehicles(db: AsyncSession, customers: list):
    """Создание транспортных средств"""
    print("\n🚗 Создание транспортных средств...")

    vehicles = []
    used_plates = set()

    # Некоторым пользователям даем по 2-3 машины
    for customer in customers:
        num_vehicles = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]

        for _ in range(num_vehicles):
            brand = random.choice(list(CAR_BRANDS.keys()))
            model = random.choice(CAR_BRANDS[brand])

            # Генерируем уникальный номер
            plate = generate_license_plate()
            while plate in used_plates:
                plate = generate_license_plate()
            used_plates.add(plate)

            vehicle = Vehicle(
                vehicle_id=uuid.uuid4(),
                customer_id=customer.customer_id,
                license_plate=plate,
                brand=brand,
                model=model,
                color=random.choice(COLORS),
                vehicle_type="passenger"
            )
            db.add(vehicle)
            vehicles.append(vehicle)

    await db.commit()

    for vehicle in vehicles:
        await db.refresh(vehicle)

    print(f"✅ Создано {len(vehicles)} транспортных средств")
    return vehicles


async def create_bookings_and_payments(db: AsyncSession, vehicles: list, zones: list, spots: list):
    """Создание бронирований и платежей: 3 недели назад + 1 неделя вперёд"""
    print("\n📅 Создание бронирований (3 недели назад + 1 неделя вперёд)...")

    total_spots = len(spots)
    now = datetime.utcnow()

    # Распределяем места по зонам
    spots_by_zone = {}
    for spot in spots:
        if spot.zone_id not in spots_by_zone:
            spots_by_zone[spot.zone_id] = []
        spots_by_zone[spot.zone_id].append(spot)

    # Тарифы по зонам
    zone_tariffs = {}
    for zone in zones:
        if "VIP" in zone.name or "Премиум" in zone.name:
            zone_tariffs[zone.zone_id] = Decimal("200.00")  # Премиум
        elif "ECO" in zone.name or "Электро" in zone.name:
            zone_tariffs[zone.zone_id] = Decimal("150.00")  # Электро
        else:
            zone_tariffs[zone.zone_id] = Decimal("100.00")  # Стандарт

    bookings = []
    payments = []

    # Бронирования: от -20 дней (прошлое) до +7 дней (будущее)
    for day_offset in range(-20, 8):  # -20 to 7 (20 дней назад до 7 дней вперёд)
        day_date = now + timedelta(days=day_offset)

        # Определяем заполненность:
        # - Прошлое (первые 1.5 недели): 75%
        # - Прошлое (остальное): 45%
        # - Будущее (неделя вперёд): 55%
        if day_offset < -9:  # дни от -20 до -10
            occupancy_rate = 0.75
        elif day_offset <= 0:  # дни от -9 до 0
            occupancy_rate = 0.45
        else:  # дни от 1 до 7 (будущее)
            occupancy_rate = 0.55

        bookings_today = int(total_spots * occupancy_rate)

        # Создаем бронирования на этот день
        selected_spots = random.sample(spots, min(bookings_today, len(spots)))

        for spot in selected_spots:
            vehicle = random.choice(vehicles)

            # Случайное время начала (6:00 - 20:00)
            start_hour = random.randint(6, 20)
            start_time = day_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)

            # Длительность парковки: 1-8 часов
            duration_hours = random.randint(1, 8)
            end_time = start_time + timedelta(hours=duration_hours)

            # Статус: текущие и будущие - confirmed (80%) или pending (20%)
            booking_status = random.choices(["confirmed", "pending"], weights=[0.8, 0.2])[0]

            # Рассчитываем стоимость
            booking_cost = zone_tariffs[spot.zone_id] * duration_hours

            booking = Booking(
                booking_id=uuid.uuid4(),
                customer_id=vehicle.customer_id,
                spot_id=spot.spot_id,
                vehicle_id=vehicle.vehicle_id,
                start_time=start_time,
                end_time=end_time,
                status=booking_status
            )
            db.add(booking)
            bookings.append(booking)

            # Создаем платеж для confirmed бронирований
            if booking_status == "confirmed":
                # Для прошлых бронирований - все платежи completed
                # Для текущих - 90% completed, 10% pending
                # Для будущих - все платежи pending (оплачены заранее)
                if end_time < now:
                    # Прошлые бронирования - все оплачены
                    payment_status = "completed"
                    create_payment = True
                elif start_time <= now < end_time:
                    # Текущие активные бронирования - 90% оплачены
                    payment_status = random.choices(["completed", "pending"], weights=[0.9, 0.1])[0]
                    create_payment = True
                else:
                    # Будущие бронирования - все pending (оплата прошла, но сессия ещё не началась)
                    create_payment = True
                    payment_status = "pending"

                if create_payment:
                    # Дата платежа - день бронирования плюс случайное время
                    payment_time = start_time + timedelta(hours=random.randint(-2, 1), minutes=random.randint(0, 59))

                    payment = Payment(
                        payment_id=uuid.uuid4(),
                        customer_id=vehicle.customer_id,
                        booking_id=booking.booking_id,
                        amount=booking_cost,
                        payment_method=random.choice(["card", "cash", "online"]),
                        status=payment_status,
                        transaction_id=f"TXN{uuid.uuid4().hex[:12].upper()}",
                        created_at=payment_time  # Устанавливаем дату платежа
                    )
                    db.add(payment)
                    payments.append(payment)

        # Статистика каждые 7 дней
        if (day_offset + 21) % 7 == 0:
            week_num = (day_offset + 21) // 7
            week_start = now + timedelta(days=max(day_offset-6, -20))
            week_bookings = len([b for b in bookings if b.start_time.date() >= week_start.date() and b.start_time.date() <= day_date.date()])
            print(f"  📊 Неделя {week_num}: создано {week_bookings} бронирований")

    await db.commit()

    print(f"✅ Создано {len(bookings)} бронирований")
    print(f"✅ Создано {len(payments)} платежей")

    return bookings, payments


async def create_parking_sessions(db: AsyncSession, bookings: list, spots: list):
    """Создание парковочных сессий (активных и завершённых) и обновление занятости мест"""
    print("\n🅿️  Создание парковочных сессий...")

    now = datetime.utcnow()
    sessions = []
    active_count = 0
    completed_count = 0

    # Сначала сбрасываем все места как свободные
    for spot in spots:
        spot.is_occupied = False

    for booking in bookings:
        if booking.status != "confirmed":
            continue

        # Для прошлых бронирований создаём завершённые сессии
        if booking.end_time < now:
            # Прошлое бронирование - создаём completed сессию
            if random.random() < 0.95:  # 95% прошлых бронирований состоялись
                actual_entry = booking.start_time + timedelta(minutes=random.randint(-15, 15))
                actual_exit = booking.end_time + timedelta(minutes=random.randint(-10, 30))

                session = ParkingSession(
                    session_id=uuid.uuid4(),
                    booking_id=booking.booking_id,
                    spot_id=booking.spot_id,
                    vehicle_id=booking.vehicle_id,
                    entry_time=actual_entry,
                    exit_time=actual_exit,
                    status="completed"
                )
                db.add(session)
                sessions.append(session)
                completed_count += 1

        # Создаем только активные сессии (которые сейчас идут)
        elif booking.start_time <= now < booking.end_time:
            # Текущее бронирование - создаем active сессию
            if random.random() < 0.90:  # 90% текущих бронирований активны
                actual_entry = booking.start_time + timedelta(minutes=random.randint(-15, 15))

                session = ParkingSession(
                    session_id=uuid.uuid4(),
                    booking_id=booking.booking_id,
                    spot_id=booking.spot_id,
                    vehicle_id=booking.vehicle_id,
                    entry_time=actual_entry,
                    exit_time=None,  # Активная сессия не завершена
                    status="active"
                )
                db.add(session)
                sessions.append(session)
                active_count += 1

                # Помечаем место как занятое
                for spot in spots:
                    if spot.spot_id == booking.spot_id:
                        spot.is_occupied = True
                        break

    await db.commit()

    print(f"✅ Создано {completed_count} завершённых парковочных сессий")
    print(f"✅ Создано {active_count} активных парковочных сессий")
    print(f"✅ Занято {sum(1 for s in spots if s.is_occupied)} парковочных мест")
    return sessions


async def seed_realistic_data():
    """Главная функция для заполнения БД реалистичными данными за последние 3 недели"""
    print("🌱 Начинаем заполнение БД реалистичными данными за последние 3 недели...\n")

    async with AsyncSessionLocal() as db:
        try:
            # 1. Очищаем старые данные
            await clear_test_data(db)

            # 2. Получаем существующие зоны и места
            zones_result = await db.execute(select(ParkingZone))
            zones = list(zones_result.scalars().all())
            print(f"ℹ️  Найдено {len(zones)} парковочных зон")

            spots_result = await db.execute(select(ParkingSpot))
            spots = list(spots_result.scalars().all())
            print(f"ℹ️  Найдено {len(spots)} парковочных мест")

            if not zones or not spots:
                print("❌ Ошибка: Сначала запустите базовый seed для создания зон и мест!")
                return

            # 3. Создаем пользователей
            customers = await create_customers(db, count=18)

            # 4. Создаем транспортные средства
            vehicles = await create_vehicles(db, customers)

            # 5. Создаем бронирования и платежи
            bookings, payments = await create_bookings_and_payments(db, vehicles, zones, spots)

            # 6. Создаем активные парковочные сессии и обновляем занятость мест
            sessions = await create_parking_sessions(db, bookings, spots)

            # Статистика
            print("\n" + "="*60)
            print("📊 ИТОГОВАЯ СТАТИСТИКА:")
            print("="*60)
            print(f"👥 Пользователей: {len(customers)}")
            print(f"🚗 Транспортных средств: {len(vehicles)}")
            print(f"📅 Бронирований: {len(bookings)}")
            print(f"💳 Платежей: {len(payments)}")
            print(f"🅿️  Парковочных сессий: {len(sessions)}")

            total_revenue = sum(p.amount for p in payments if p.status == "completed")
            print(f"💰 Общая выручка: {total_revenue:.2f} ₽")
            print("="*60)
            print("\n✅ База данных успешно заполнена реалистичными данными!")

        except Exception as e:
            print(f"\n❌ Ошибка при заполнении БД: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_realistic_data())
