-- Test Data for Parking Management System
-- This script will run automatically when database is initialized

-- Insert Parking Zones
INSERT INTO parking_zones (zone_id, name, address, total_spots, available_spots, tariff_id, is_active)
VALUES
    (gen_random_uuid(), 'Центральная парковка', 'ул. Ленина, 15', 50, 50,
     (SELECT tariff_id FROM tariff_plans WHERE name = 'Почасовая' LIMIT 1), TRUE),
    (gen_random_uuid(), 'Торговый центр "Мега"', 'Московское шоссе, 23', 100, 100,
     (SELECT tariff_id FROM tariff_plans WHERE name = 'Дневная' LIMIT 1), TRUE),
    (gen_random_uuid(), 'Бизнес-центр "Плаза"', 'ул. Пушкина, 44', 30, 30,
     (SELECT tariff_id FROM tariff_plans WHERE name = 'VIP' LIMIT 1), TRUE),
    (gen_random_uuid(), 'Парковка у метро', 'пр. Победы, 89', 75, 75,
     (SELECT tariff_id FROM tariff_plans WHERE name = 'Почасовая' LIMIT 1), TRUE)
ON CONFLICT DO NOTHING;

-- Insert Parking Spots for Zone 1 (Центральная парковка)
DO $$
DECLARE
    zone_id_central UUID;
    i INTEGER;
BEGIN
    SELECT zone_id INTO zone_id_central FROM parking_zones WHERE name = 'Центральная парковка' LIMIT 1;

    -- Standard spots (A1-A40)
    FOR i IN 1..40 LOOP
        INSERT INTO parking_spots (zone_id, spot_number, spot_type, is_occupied, is_active)
        VALUES (zone_id_central, 'A' || i, 'standard', FALSE, TRUE)
        ON CONFLICT DO NOTHING;
    END LOOP;

    -- Disabled spots (D1-D5)
    FOR i IN 1..5 LOOP
        INSERT INTO parking_spots (zone_id, spot_number, spot_type, is_occupied, is_active)
        VALUES (zone_id_central, 'D' || i, 'disabled', FALSE, TRUE)
        ON CONFLICT DO NOTHING;
    END LOOP;

    -- Electric spots (E1-E5)
    FOR i IN 1..5 LOOP
        INSERT INTO parking_spots (zone_id, spot_number, spot_type, is_occupied, is_active)
        VALUES (zone_id_central, 'E' || i, 'electric', FALSE, TRUE)
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- Insert Parking Spots for Zone 2 (Торговый центр)
DO $$
DECLARE
    zone_id_mega UUID;
    i INTEGER;
BEGIN
    SELECT zone_id INTO zone_id_mega FROM parking_zones WHERE name = 'Торговый центр "Мега"' LIMIT 1;

    -- Standard spots (1-90)
    FOR i IN 1..90 LOOP
        INSERT INTO parking_spots (zone_id, spot_number, spot_type, is_occupied, is_active)
        VALUES (zone_id_mega, 'P' || i, 'standard', FALSE, TRUE)
        ON CONFLICT DO NOTHING;
    END LOOP;

    -- Disabled spots (D1-D10)
    FOR i IN 1..10 LOOP
        INSERT INTO parking_spots (zone_id, spot_number, spot_type, is_occupied, is_active)
        VALUES (zone_id_mega, 'D' || i, 'disabled', FALSE, TRUE)
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- Insert Parking Spots for Zone 3 (Бизнес-центр VIP)
DO $$
DECLARE
    zone_id_plaza UUID;
    i INTEGER;
BEGIN
    SELECT zone_id INTO zone_id_plaza FROM parking_zones WHERE name = 'Бизнес-центр "Плаза"' LIMIT 1;

    -- VIP spots (V1-V30)
    FOR i IN 1..30 LOOP
        INSERT INTO parking_spots (zone_id, spot_number, spot_type, is_occupied, is_active)
        VALUES (zone_id_plaza, 'V' || i, 'vip', FALSE, TRUE)
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- Insert Parking Spots for Zone 4 (У метро)
DO $$
DECLARE
    zone_id_metro UUID;
    i INTEGER;
BEGIN
    SELECT zone_id INTO zone_id_metro FROM parking_zones WHERE name = 'Парковка у метро' LIMIT 1;

    -- Standard spots (M1-M70)
    FOR i IN 1..70 LOOP
        INSERT INTO parking_spots (zone_id, spot_number, spot_type, is_occupied, is_active)
        VALUES (zone_id_metro, 'M' || i, 'standard', FALSE, TRUE)
        ON CONFLICT DO NOTHING;
    END LOOP;

    -- Disabled spots (MD1-MD5)
    FOR i IN 1..5 LOOP
        INSERT INTO parking_spots (zone_id, spot_number, spot_type, is_occupied, is_active)
        VALUES (zone_id_metro, 'MD' || i, 'disabled', FALSE, TRUE)
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- Create a test customer (password: test123)
INSERT INTO customers (customer_id, first_name, last_name, email, phone, password_hash)
VALUES
    (gen_random_uuid(), 'Тестовый', 'Пользователь', 'test@example.com', '+79991234567',
     '$2b$12$CazzPhzbxW0DXBjlE2E8A.4fVc8ZncfXggPAsy8bvCPJmSpN.JXci')
ON CONFLICT (email) DO NOTHING;

-- Create test vehicles for test customer
DO $$
DECLARE
    customer_id_test UUID;
BEGIN
    SELECT customer_id INTO customer_id_test FROM customers WHERE email = 'test@example.com' LIMIT 1;

    IF customer_id_test IS NOT NULL THEN
        INSERT INTO vehicles (customer_id, license_plate, vehicle_type, brand, model, color)
        VALUES
            (customer_id_test, 'А123БВ77', 'sedan', 'Toyota', 'Camry', 'Белый'),
            (customer_id_test, 'М456КУ77', 'suv', 'BMW', 'X5', 'Черный')
        ON CONFLICT (license_plate) DO NOTHING;
    END IF;
END $$;

-- Output summary
DO $$
DECLARE
    zones_count INTEGER;
    spots_count INTEGER;
    tariffs_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO zones_count FROM parking_zones;
    SELECT COUNT(*) INTO spots_count FROM parking_spots;
    SELECT COUNT(*) INTO tariffs_count FROM tariff_plans;

    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Test Data Loaded Successfully!';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Tariff Plans: %', tariffs_count;
    RAISE NOTICE 'Parking Zones: %', zones_count;
    RAISE NOTICE 'Parking Spots: %', spots_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Test User Credentials:';
    RAISE NOTICE 'Email: test@example.com';
    RAISE NOTICE 'Password: test123';
    RAISE NOTICE '==============================================';
END $$;
