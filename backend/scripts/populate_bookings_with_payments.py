"""
Скрипт для заполнения бронирований с платежами на 3 недели вперёд
- Удаляет существующие бронирования и платежи
- Создает тестовых пользователей с автомобилями
- Распределяет бронирования на 3 недели:
  * Первые 1.5 недели: 50-80% заполненность
  * Остальные 1.5 недели: 30-50% заполненность
- Создает платежи для каждого бронирования
"""
import os
import re
from datetime import datetime, timedelta, timezone as dt_timezone
import random
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

# Database connection
database_url = os.getenv('DATABASE_URL', '')
if database_url:
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
            'password': 'parking_pass',
            'host': 'db',
            'port': '5432'
        }
else:
    DB_CONFIG = {
        'dbname': 'parking_db',
        'user': 'parking_user',
        'password': 'parking_pass',
        'host': 'db',
        'port': '5432'
    }


def hash_password(password: str) -> str:
    """Хеширование пароля (простое для тестовых данных)"""
    return hashlib.sha256(password.encode()).hexdigest()


def clear_data(cursor):
    """Удалить все бронирования и платежи"""
    cursor.execute("DELETE FROM payments WHERE booking_id IS NOT NULL")
    payments_deleted = cursor.rowcount

    cursor.execute("DELETE FROM bookings")
    bookings_deleted = cursor.rowcount

    return bookings_deleted, payments_deleted


def create_test_users(cursor):
    """Создать тестовых пользователей"""
    users_data = [
        {
            'email': 'ivan.petrov@test.com',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'phone': '+7 (911) 123-45-67',
            'password': 'password123'
        },
        {
            'email': 'maria.ivanova@test.com',
            'first_name': 'Мария',
            'last_name': 'Иванова',
            'phone': '+7 (922) 234-56-78',
            'password': 'password123'
        },
        {
            'email': 'sergey.smirnov@test.com',
            'first_name': 'Сергей',
            'last_name': 'Смирнов',
            'phone': '+7 (933) 345-67-89',
            'password': 'password123'
        },
        {
            'email': 'elena.kozlova@test.com',
            'first_name': 'Елена',
            'last_name': 'Козлова',
            'phone': '+7 (944) 456-78-90',
            'password': 'password123'
        },
        {
            'email': 'dmitry.novikov@test.com',
            'first_name': 'Дмитрий',
            'last_name': 'Новиков',
            'phone': '+7 (955) 567-89-01',
            'password': 'password123'
        }
    ]

    created_users = []

    for user_data in users_data:
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT customer_id FROM customers WHERE email = %s", (user_data['email'],))
        existing = cursor.fetchone()

        if existing:
            created_users.append(existing['customer_id'])
            continue

        # Создаем нового пользователя
        cursor.execute("""
            INSERT INTO customers (email, password_hash, first_name, last_name, phone, is_admin)
            VALUES (%s, %s, %s, %s, %s, false)
            RETURNING customer_id
        """, (
            user_data['email'],
            hash_password(user_data['password']),
            user_data['first_name'],
            user_data['last_name'],
            user_data['phone']
        ))

        customer_id = cursor.fetchone()['customer_id']
        created_users.append(customer_id)

    return created_users


def create_vehicles_for_users(cursor, user_ids):
    """Создать автомобили для пользователей"""
    vehicle_data = [
        {'brand': 'Toyota', 'model': 'Camry', 'color': 'Белый', 'vehicle_type': 'sedan', 'plates': ['А123ВС777', 'В456ЕК777']},
        {'brand': 'Honda', 'model': 'Accord', 'color': 'Черный', 'vehicle_type': 'sedan', 'plates': ['С789МН777', 'Е012ОР777']},
        {'brand': 'Nissan', 'model': 'Qashqai', 'color': 'Серый', 'vehicle_type': 'suv', 'plates': ['К345ТУ777', 'М678ХЦ777']},
        {'brand': 'Mazda', 'model': 'CX-5', 'color': 'Синий', 'vehicle_type': 'suv', 'plates': ['Н901ЧШ777', 'О234АВ777']},
        {'brand': 'BMW', 'model': 'X5', 'color': 'Красный', 'vehicle_type': 'suv', 'plates': ['Р567СД777', 'Т890ЕК777', 'У123МН777']},
    ]

    vehicles_by_user = {}

    for i, user_id in enumerate(user_ids):
        vehicles_by_user[user_id] = []
        user_vehicles = vehicle_data[i % len(vehicle_data)]

        for plate in user_vehicles['plates']:
            # Проверяем, существует ли автомобиль
            cursor.execute("""
                SELECT vehicle_id FROM vehicles
                WHERE license_plate = %s AND customer_id = %s
            """, (plate, user_id))

            existing = cursor.fetchone()

            if existing:
                vehicles_by_user[user_id].append(existing['vehicle_id'])
                continue

            # Проверяем, не занят ли номер
            cursor.execute("SELECT vehicle_id FROM vehicles WHERE license_plate = %s", (plate,))

            if cursor.fetchone():
                # Генерируем новый номер
                base_plate = plate[:-2]
                for suffix in range(10, 100):
                    new_plate = base_plate + str(suffix)
                    cursor.execute("SELECT vehicle_id FROM vehicles WHERE license_plate = %s", (new_plate,))
                    if not cursor.fetchone():
                        plate = new_plate
                        break

            # Создаем автомобиль
            cursor.execute("""
                INSERT INTO vehicles (customer_id, license_plate, brand, model, color, vehicle_type)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING vehicle_id
            """, (
                user_id,
                plate,
                user_vehicles['brand'],
                user_vehicles['model'],
                user_vehicles['color'],
                user_vehicles['vehicle_type']
            ))

            vehicle_id = cursor.fetchone()['vehicle_id']
            vehicles_by_user[user_id].append(vehicle_id)

    return vehicles_by_user


def get_parking_spots_with_zones(cursor):
    """Получить все активные парковочные места с информацией о зонах"""
    cursor.execute("""
        SELECT ps.spot_id, ps.spot_number, pz.zone_id, pz.tariff_id, tp.price_per_hour
        FROM parking_spots ps
        JOIN parking_zones pz ON ps.zone_id = pz.zone_id
        LEFT JOIN tariff_plans tp ON pz.tariff_id = tp.tariff_id
        WHERE ps.is_active = true AND pz.is_active = true
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


def create_booking(cursor, customer_id, vehicle_id, spot_id, start_time, end_time, status='pending'):
    """Создать бронирование"""
    cursor.execute("""
        INSERT INTO bookings (customer_id, vehicle_id, spot_id, start_time, end_time, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING booking_id
    """, (customer_id, vehicle_id, spot_id, start_time, end_time, status))
    return cursor.fetchone()['booking_id']


def create_payment(cursor, booking_id, customer_id, amount, status='pending'):
    """Создать платеж для бронирования"""
    # Случайный способ оплаты для completed платежей
    payment_methods = ['card', 'cash', 'online']
    payment_method = random.choice(payment_methods) if status == 'completed' else 'pending'

    # Генерируем transaction_id для completed платежей
    transaction_id = None
    if status == 'completed':
        transaction_id = f"TXN-{random.randint(100000, 999999)}"

    cursor.execute("""
        INSERT INTO payments (booking_id, customer_id, amount, status, payment_method, transaction_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING payment_id
    """, (booking_id, customer_id, amount, status, payment_method, transaction_id))

    return cursor.fetchone()['payment_id']


def main():
    print("=" * 70)
    print("Скрипт заполнения бронирований с платежами на 3 недели")
    print("=" * 70)

    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("✓ Подключено к базе данных")
    except Exception as e:
        print(f"✗ Ошибка подключения к БД: {e}")
        return

    try:
        # Шаг 1: Очистка
        print("\n" + "=" * 70)
        print("ШАГ 1: Очистка существующих данных")
        print("=" * 70)

        deleted_bookings, deleted_payments = clear_data(cursor)
        print(f"✓ Удалено бронирований: {deleted_bookings}")
        print(f"✓ Удалено платежей: {deleted_payments}")
        conn.commit()

        # Шаг 2: Пользователи
        print("\n" + "=" * 70)
        print("ШАГ 2: Создание тестовых пользователей")
        print("=" * 70)

        user_ids = create_test_users(cursor)
        conn.commit()
        print(f"✓ Создано/найдено пользователей: {len(user_ids)}")

        # Шаг 3: Автомобили
        print("\n" + "=" * 70)
        print("ШАГ 3: Создание автомобилей")
        print("=" * 70)

        vehicles_by_user = create_vehicles_for_users(cursor, user_ids)
        conn.commit()

        total_vehicles = sum(len(v) for v in vehicles_by_user.values())
        print(f"✓ Создано/найдено автомобилей: {total_vehicles}")

        # Шаг 4: Парковочные места
        print("\n" + "=" * 70)
        print("ШАГ 4: Загрузка парковочных мест")
        print("=" * 70)

        spots = get_parking_spots_with_zones(cursor)
        print(f"✓ Найдено активных мест: {len(spots)}")

        if not spots:
            print("✗ Нет активных парковочных мест!")
            return

        # Шаг 5: Создание бронирований
        print("\n" + "=" * 70)
        print("ШАГ 5: Генерация бронирований на 3 недели")
        print("=" * 70)

        weeks = 3
        days = weeks * 7
        now = datetime.now(dt_timezone.utc)

        created_bookings = 0
        created_payments = 0
        failed_attempts = 0

        # Создаем список пользователей с автомобилями
        user_vehicle_pairs = []
        for user_id, vehicle_ids in vehicles_by_user.items():
            for vehicle_id in vehicle_ids:
                user_vehicle_pairs.append((user_id, vehicle_id))

        print(f"\nГенерация бронирований на {days} дней...")
        print("-" * 70)

        for day_offset in range(days):
            current_date = now + timedelta(days=day_offset)

            # Определяем процент заполненности
            if day_offset < 10.5:  # Первые 1.5 недели
                occupancy_rate = random.uniform(0.50, 0.80)
            else:  # Остальные 1.5 недели
                occupancy_rate = random.uniform(0.30, 0.50)

            spots_to_book = int(len(spots) * occupancy_rate)
            day_spots = random.sample(spots, min(spots_to_book, len(spots)))

            day_bookings = 0
            day_payments = 0

            for spot in day_spots:
                # Случайное время начала
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

                # Случайный пользователь с автомобилем
                customer_id, vehicle_id = random.choice(user_vehicle_pairs)

                # Проверяем конфликт
                if check_booking_conflict(cursor, spot['spot_id'], start_time, end_time):
                    failed_attempts += 1
                    continue

                # Определяем статусы (80% confirmed, 20% pending)
                booking_status = 'confirmed' if random.random() < 0.8 else 'pending'
                payment_status = 'completed' if booking_status == 'confirmed' else 'pending'

                try:
                    # Создаем бронирование
                    booking_id = create_booking(
                        cursor,
                        customer_id,
                        vehicle_id,
                        spot['spot_id'],
                        start_time,
                        end_time,
                        booking_status
                    )
                    created_bookings += 1
                    day_bookings += 1

                    # Рассчитываем стоимость
                    hourly_rate = float(spot['price_per_hour']) if spot['price_per_hour'] else 50.0
                    amount = round(hourly_rate * duration, 2)

                    # Создаем платеж
                    payment_id = create_payment(
                        cursor,
                        booking_id,
                        customer_id,
                        amount,
                        payment_status
                    )
                    created_payments += 1
                    day_payments += 1

                except Exception as e:
                    failed_attempts += 1
                    print(f"  ✗ Ошибка: {e}")

            # Коммит каждый день
            conn.commit()

            occupancy_percent = int(occupancy_rate * 100)
            print(f"День {day_offset + 1:2d} ({current_date.strftime('%Y-%m-%d')}): "
                  f"{occupancy_percent}% заполненность, "
                  f"создано {day_bookings} бронирований и {day_payments} платежей")

        print("-" * 70)
        print(f"\n{'=' * 70}")
        print("ИТОГИ:")
        print(f"✓ Всего создано бронирований: {created_bookings}")
        print(f"✓ Всего создано платежей: {created_payments}")
        print(f"✗ Неудачных попыток: {failed_attempts}")
        print(f"✓ Пользователей: {len(user_ids)}")
        print(f"✓ Автомобилей: {total_vehicles}")
        print(f"{'=' * 70}")

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        print("\nСоединение закрыто.")


if __name__ == "__main__":
    main()
