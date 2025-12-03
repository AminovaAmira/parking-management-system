from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class ParkingSession(Base):
    """Parking Session model - парковочные сессии"""
    __tablename__ = "parking_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id"))
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    spot_id = Column(UUID(as_uuid=True), ForeignKey("parking_spots.spot_id"), nullable=False)
    entry_time = Column(DateTime(timezone=True), nullable=False)
    exit_time = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False, default="active", index=True)  # active, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    booking = relationship("Booking", back_populates="parking_sessions")
    vehicle = relationship("Vehicle", back_populates="parking_sessions")
    spot = relationship("ParkingSpot", back_populates="parking_sessions")
    payments = relationship("Payment", back_populates="session")

    def __repr__(self):
        return f"<ParkingSession {self.session_id} - {self.status}>"
