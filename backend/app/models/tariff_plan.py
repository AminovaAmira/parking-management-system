from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class TariffPlan(Base):
    """Tariff Plan model - тарифные планы"""
    __tablename__ = "tariff_plans"

    tariff_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price_per_hour = Column(Numeric(10, 2), nullable=False)
    price_per_day = Column(Numeric(10, 2))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    parking_zones = relationship("ParkingZone", back_populates="tariff")

    def __repr__(self):
        return f"<TariffPlan {self.name}>"
