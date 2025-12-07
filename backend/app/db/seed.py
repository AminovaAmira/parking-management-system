"""Seed script to populate database with initial test data."""
import asyncio
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.tariff_plan import TariffPlan
from app.models.parking_zone import ParkingZone
from app.models.parking_spot import ParkingSpot


async def seed_tariff_plans(db: AsyncSession):
    """Create initial tariff plans."""
    print("🎫 Seeding tariff plans...")

    # Check if tariffs already exist
    result = await db.execute(select(TariffPlan))
    existing = result.scalars().all()
    if existing:
        print(f"⚠️  {len(existing)} tariff plans already exist, skipping creation...")
        return existing

    tariffs = [
        TariffPlan(
            tariff_id=uuid.uuid4(),
            name="Стандартный",
            description="Обычный тариф для всех типов мест",
            price_per_hour=Decimal("100.00"),
            price_per_day=Decimal("800.00"),
            is_active=True
        ),
        TariffPlan(
            tariff_id=uuid.uuid4(),
            name="Премиум",
            description="Премиум тариф для VIP мест",
            price_per_hour=Decimal("200.00"),
            price_per_day=Decimal("1500.00"),
            is_active=True
        ),
        TariffPlan(
            tariff_id=uuid.uuid4(),
            name="Электромобили",
            description="Специальный тариф для электромобилей с зарядкой",
            price_per_hour=Decimal("150.00"),
            price_per_day=Decimal("1000.00"),
            is_active=True
        ),
    ]

    for tariff in tariffs:
        db.add(tariff)

    await db.commit()
    print(f"✅ Created {len(tariffs)} tariff plans")
    return tariffs


async def seed_parking_zones(db: AsyncSession, tariffs: list):
    """Create parking zones."""
    print("\n🏢 Seeding parking zones...")

    # Check if zones already exist
    result = await db.execute(select(ParkingZone))
    existing = result.scalars().all()
    if existing:
        print(f"⚠️  {len(existing)} parking zones already exist, skipping creation...")
        return existing

    zones = [
        ParkingZone(
            zone_id=uuid.uuid4(),
            name="Зона A - Центр",
            address="ул. Ленина, 1",
            total_spots=50,
            available_spots=50,
            tariff_id=tariffs[0].tariff_id,  # Стандартный
            is_active=True
        ),
        ParkingZone(
            zone_id=uuid.uuid4(),
            name="Зона B - Север",
            address="пр. Победы, 15",
            total_spots=40,
            available_spots=40,
            tariff_id=tariffs[0].tariff_id,  # Стандартный
            is_active=True
        ),
        ParkingZone(
            zone_id=uuid.uuid4(),
            name="Зона VIP - Премиум",
            address="ул. Пушкина, 10",
            total_spots=20,
            available_spots=20,
            tariff_id=tariffs[1].tariff_id,  # Премиум
            is_active=True
        ),
        ParkingZone(
            zone_id=uuid.uuid4(),
            name="Зона ECO - Электро",
            address="ул. Гагарина, 25",
            total_spots=30,
            available_spots=30,
            tariff_id=tariffs[2].tariff_id,  # Электромобили
            is_active=True
        ),
    ]

    for zone in zones:
        db.add(zone)

    await db.commit()
    print(f"✅ Created {len(zones)} parking zones")
    return zones


async def seed_parking_spots(db: AsyncSession, zones: list):
    """Create parking spots for each zone."""
    print("\n🅿️  Seeding parking spots...")

    # Check if spots already exist
    result = await db.execute(select(ParkingSpot))
    existing_count = len(result.scalars().all())
    if existing_count > 0:
        print(f"⚠️  {existing_count} parking spots already exist, skipping creation...")
        return

    spot_types_config = {
        "Зона A - Центр": {"standard": 40, "disabled": 10},
        "Зона B - Север": {"standard": 35, "disabled": 5},
        "Зона VIP - Премиум": {"vip": 20},
        "Зона ECO - Электро": {"electric": 30},
    }

    total_spots_created = 0

    for zone in zones:
        config = spot_types_config[zone.name]
        spot_num = 1

        for spot_type, count in config.items():
            for i in range(count):
                spot = ParkingSpot(
                    spot_id=uuid.uuid4(),
                    zone_id=zone.zone_id,
                    spot_number=f"{zone.name[5]}{spot_num:03d}",  # A001, B001, etc.
                    spot_type=spot_type,
                    is_occupied=False,
                    is_active=True
                )
                db.add(spot)
                spot_num += 1
                total_spots_created += 1

    await db.commit()
    print(f"✅ Created {total_spots_created} parking spots")


async def seed_all():
    """Run all seed functions."""
    print("🌱 Starting database seeding...\n")

    async with AsyncSessionLocal() as db:
        try:
            # Seed in order (respecting foreign keys)
            tariffs = await seed_tariff_plans(db)

            # Refresh tariffs to get their IDs
            for tariff in tariffs:
                await db.refresh(tariff)

            zones = await seed_parking_zones(db, tariffs)

            # Refresh zones to get their IDs
            for zone in zones:
                await db.refresh(zone)

            await seed_parking_spots(db, zones)

            print("\n✅ Database seeding completed successfully!")

        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_all())
