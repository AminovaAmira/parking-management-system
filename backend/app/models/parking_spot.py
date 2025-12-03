from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class ParkingSpot(Base):
    """Parking Spot model - парковочные места"""
    __tablename__ = "parking_spots"
    __table_args__ = (
        UniqueConstraint('zone_id', 'spot_number', name='uq_zone_spot'),
    )

    spot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("parking_zones.zone_id", ondelete="CASCADE"), nullable=False)
    spot_number = Column(String(20), nullable=False)
    spot_type = Column(String(50), nullable=False)  # standard, disabled, electric, vip
    is_occupied = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    zone = relationship("ParkingZone", back_populates="parking_spots")
    bookings = relationship("Booking", back_populates="spot")
    parking_sessions = relationship("ParkingSession", back_populates="spot")

    def __repr__(self):
        return f"<ParkingSpot {self.spot_number}>"
