from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, select, func as sql_func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
import uuid

from app.db.database import Base


class ParkingZone(Base):
    """Parking Zone model - парковочные зоны"""
    __tablename__ = "parking_zones"

    zone_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    total_spots = Column(Integer, nullable=False)
    tariff_id = Column(UUID(as_uuid=True), ForeignKey("tariff_plans.tariff_id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tariff = relationship("TariffPlan", back_populates="parking_zones")
    parking_spots = relationship("ParkingSpot", back_populates="zone", cascade="all, delete-orphan")

    @property
    def available_spots(self):
        """Динамически вычисляем количество свободных мест"""
        if not self.parking_spots:
            return 0
        return sum(1 for spot in self.parking_spots if spot.is_active and not spot.is_occupied)

    def __repr__(self):
        return f"<ParkingZone {self.name}>"
