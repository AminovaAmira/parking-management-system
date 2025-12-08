"""
Скрипт для заполнения тестовых бронирований на 3 недели вперёд
Первые 1.5 недели - 75% заполненность
Оставшиеся 1.5 недели - 40% заполненность
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_session_maker
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.models.parking_spot import ParkingSpot
from app.models.booking import Booking


async def get_customer_with_vehicle(db: AsyncSession):
    """Получить случайного пользователя с автомобилем"""
    # Получаем всех пользователей с автомобилями
    stmt = select(Customer).join(Vehicle)
    result = await db.execute(stmt)
    customers = result.scalars().unique().all()

    if not customers:
        print("Нет пользователей с автомобилями!")
        return None, None

    customer = random.choice(customers)

    # Получаем автомобиль этого пользователя
    vehicle_stmt = select(Vehicle).where(Vehicle.customer_id == customer.customer_id)
    vehicle_result = await db.execute(vehicle_stmt)
    vehicle = vehicle_result.scalars().first()

    return customer, vehicle


async def get_available_spot(db: AsyncSession):
    """Получить случайное свободное место"""
    stmt = select(ParkingSpot).where(ParkingSpot.is_active == True)
    result = await db.execute(stmt)
    spots = result.scalars().all()

    if not spots:
        print("Нет доступных парковочных мест!")
        return None

    return random.choice(spots)


async def create_booking(
    db: AsyncSession,
    customer: Customer,
    vehicle: Vehicle,
    spot: ParkingSpot,
    start_time: datetime,
    duration_hours: int
):
    """Создать бронирование"""
    end_time = start_time + timedelta(hours=duration_hours)

    # Проверяем, нет ли конфликтующих бронирований
    check_stmt = select(Booking).where(
        Booking.spot_id == spot.spot_id,
        Booking.status.in_(['pending', 'confirmed']),
        Booking.start_time < end_time,
        Booking.end_time > start_time
    )
    check_result = await db.execute(check_stmt)
    existing_booking = check_result.scalar_one_or_none()

    if existing_booking:
        return None  # Есть конфликт, не создаём бронирование

    # Создаём бронирование
    booking = Booking(
        customer_id=customer.customer_id,
        vehicle_id=vehicle.vehicle_id,
        spot_id=spot.spot_id,
        start_time=start_time,
        end_time=end_time,
        status='confirmed'
    )

    db.add(booking)
    return booking


async def populate_bookings():
    """Заполнить базу тестовыми бронированиями"""
    async with async_session_maker() as db:
        try:
            # Получаем все парковочные места
            spots_stmt = select(ParkingSpot).where(ParkingSpot.is_active == True)
            spots_result = await db.execute(spots_stmt)
            all_spots = spots_result.scalars().all()

            if not all_spots:
                print("Нет активных парковочных мест!")
                return

            total_spots = len(all_spots)
            print(f"Всего доступных мест: {total_spots}")

            # Параметры заполнения
            weeks = 3
            days = weeks * 7  # 21 день

            created_bookings = 0
            failed_attempts = 0

            # Генерируем бронирования на каждый день
            now = datetime.now()

            for day_offset in range(days):
                current_date = now + timedelta(days=day_offset)

                # Определяем процент заполненности
                if day_offset < 10.5:  # Первые 1.5 недели (10.5 дней)
                    occupancy_rate = 0.75  # 75%
                else:
                    occupancy_rate = 0.40  # 40%

                # Количество мест для бронирования в этот день
                spots_to_book = int(total_spots * occupancy_rate)

                print(f"\nДень {day_offset + 1} ({current_date.strftime('%Y-%m-%d')}): "
                      f"заполненность {occupancy_rate * 100}%, бронируем {spots_to_book} мест")

                # Выбираем случайные места для этого дня
                day_spots = random.sample(all_spots, min(spots_to_book, len(all_spots)))

                # Для каждого места создаём бронирования в разное время
                for spot in day_spots:
                    # Случайное время начала (от 6:00 до 20:00)
                    start_hour = random.randint(6, 20)
                    start_minute = random.choice([0, 15, 30, 45])

                    start_time = current_date.replace(
                        hour=start_hour,
                        minute=start_minute,
                        second=0,
                        microsecond=0
                    )

                    # Случайная длительность (1-8 часов)
                    duration = random.randint(1, 8)

                    # Получаем случайного пользователя с автомобилем
                    customer, vehicle = await get_customer_with_vehicle(db)

                    if not customer or not vehicle:
                        failed_attempts += 1
                        continue

                    # Создаём бронирование
                    booking = await create_booking(
                        db, customer, vehicle, spot,
                        start_time, duration
                    )

                    if booking:
                        created_bookings += 1
                    else:
                        failed_attempts += 1

            # Сохраняем все бронирования
            await db.commit()

            print(f"\n{'='*60}")
            print(f"Создано бронирований: {created_bookings}")
            print(f"Неудачных попыток: {failed_attempts}")
            print(f"{'='*60}")

        except Exception as e:
            print(f"Ошибка при заполнении бронирований: {e}")
            await db.rollback()
            raise


async def clear_future_bookings():
    """Удалить все будущие бронирования (для повторного запуска скрипта)"""
    async with async_session_maker() as db:
        try:
            now = datetime.now()

            # Удаляем все будущие бронирования
            stmt = select(Booking).where(Booking.start_time > now)
            result = await db.execute(stmt)
            bookings = result.scalars().all()

            for booking in bookings:
                await db.delete(booking)

            await db.commit()
            print(f"Удалено {len(bookings)} будущих бронирований")

        except Exception as e:
            print(f"Ошибка при удалении бронирований: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Заполнение тестовых бронирований')
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Удалить все будущие бронирования перед заполнением'
    )

    args = parser.parse_args()

    print("Скрипт заполнения тестовых бронирований")
    print("=" * 60)

    if args.clear:
        print("Удаляем существующие будущие бронирования...")
        asyncio.run(clear_future_bookings())
        print()

    print("Начинаем заполнение...")
    asyncio.run(populate_bookings())
    print("\nГотово!")
