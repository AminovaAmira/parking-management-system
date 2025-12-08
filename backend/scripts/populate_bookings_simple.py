"""
Простой скрипт для заполнения бронирований через psycopg2
"""
import os
import sys
from datetime import datetime, timedelta
import random
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
# Парсим DATABASE_URL из окружения или используем значения по умолчанию
import re
database_url = os.getenv('DATABASE_URL', '')
if database_url:
    # Парсим URL формата: postgresql+asyncpg://user:pass@host:port/dbname
    match = re.match(r'postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
    if match:
        DB_CONFIG = {
            'user': match.group(1),
            'password': match.group(2),
            'host': match.group(3),
            'port': match.group(4),
            'dbname': match.group(5)
        }
    else:
        DB_CONFIG = {
            'dbname': 'parking_db',
            'user': 'parking_user',
            'password': 'parking_pass_2024',
            'host': 'db',
            'port': '5432'
        }
else:
    DB_CONFIG = {
        'dbname': 'parking_db',
        'user': 'parking_user',
        'password': 'parking_pass_2024',
        'host': 'db',
        'port': '5432'
    }


def get_customers_with_vehicles(cursor):
    """Получить пользователей с автомобилями"""
    cursor.execute("""
        SELECT DISTINCT c.customer_id, v.vehicle_id
        FROM customers c
        INNER JOIN vehicles v ON c.customer_id = v.customer_id
    """)
    return cursor.fetchall()


def get_parking_spots(cursor):
    """Получить все активные парковочные места"""
    cursor.execute("""
        SELECT spot_id, spot_number
        FROM parking_spots
        WHERE is_active = true
    """)
    return cursor.fetchall()


def check_booking_conflict(cursor, spot_id, start_time, end_time):
    """Проверить конфликт бронирований"""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM bookings
        WHERE spot_id = %s
          AND status IN ('pending', 'confirmed')
          AND start_time < %s
          AND end_time > %s
    """, (spot_id, end_time, start_time))
    result = cursor.fetchone()
    return result['count'] > 0


def create_booking(cursor, customer_id, vehicle_id, spot_id, start_time, end_time):
    """Создать бронирование"""
    cursor.execute("""
        INSERT INTO bookings (customer_id, vehicle_id, spot_id, start_time, end_time, status)
        VALUES (%s, %s, %s, %s, %s, 'confirmed')
        RETURNING booking_id
    """, (customer_id, vehicle_id, spot_id, start_time, end_time))
    return cursor.fetchone()['booking_id']


def clear_future_bookings(cursor):
    """Удалить все будущие бронирования"""
    now = datetime.now()
    cursor.execute("""
        DELETE FROM bookings
        WHERE start_time > %s
    """, (now,))
    return cursor.rowcount


def main():
    print("="*60)
    print("Скрипт заполнения тестовых бронирований")
    print("="*60)

    # Подключение к базе данных
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("✓ Подключено к базе данных")
    except Exception as e:
        print(f"✗ Ошибка подключения к БД: {e}")
        return

    try:
        # Очистка существующих будущих бронирований
        print("\nОчистка существующих будущих бронирований...")
        deleted = clear_future_bookings(cursor)
        conn.commit()
        print(f"✓ Удалено {deleted} бронирований")

        # Получаем данные
        print("\nПолучение данных из БД...")
        customers = get_customers_with_vehicles(cursor)
        spots = get_parking_spots(cursor)

        if not customers:
            print("✗ Нет пользователей с автомобилями!")
            return

        if not spots:
            print("✗ Нет активных парковочных мест!")
            return

        print(f"✓ Найдено {len(customers)} пользователей с автомобилями")
        print(f"✓ Найдено {len(spots)} парковочных мест")

        # Параметры заполнения
        weeks = 3
        days = weeks * 7
        now = datetime.now()

        created_bookings = 0
        failed_attempts = 0

        print(f"\nГенерация бронирований на {days} дней...")
        print("-"*60)

        # Генерируем бронирования
        for day_offset in range(days):
            current_date = now + timedelta(days=day_offset)

            # Определяем процент заполненности
            if day_offset < 10.5:  # Первые 1.5 недели
                occupancy_rate = 0.75  # 75%
            else:
                occupancy_rate = 0.40  # 40%

            # Количество мест для бронирования в этот день
            spots_to_book = int(len(spots) * occupancy_rate)

            # Выбираем случайные места для этого дня
            day_spots = random.sample(spots, min(spots_to_book, len(spots)))

            day_bookings = 0

            # Для каждого места создаём бронирования
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
                end_time = start_time + timedelta(hours=duration)

                # Случайный пользователь
                customer = random.choice(customers)

                # Проверяем конфликт
                if check_booking_conflict(cursor, spot['spot_id'], start_time, end_time):
                    failed_attempts += 1
                    continue

                # Создаём бронирование
                try:
                    booking_id = create_booking(
                        cursor,
                        customer['customer_id'],
                        customer['vehicle_id'],
                        spot['spot_id'],
                        start_time,
                        end_time
                    )
                    created_bookings += 1
                    day_bookings += 1
                except Exception as e:
                    failed_attempts += 1
                    print(f"  ✗ Ошибка создания бронирования: {e}")

            # Промежуточный коммит каждый день
            conn.commit()

            occupancy_percent = int(occupancy_rate * 100)
            print(f"День {day_offset + 1:2d} ({current_date.strftime('%Y-%m-%d')}): "
                  f"заполненность {occupancy_percent}%, создано {day_bookings} бронирований")

        print("-"*60)
        print(f"\n✓ Всего создано бронирований: {created_bookings}")
        print(f"✗ Неудачных попыток: {failed_attempts}")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        print("\nСоединение закрыто.")


if __name__ == "__main__":
    main()
