from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Vehicle(Base):
    """Vehicle model - автомобили клиентов"""
    __tablename__ = "vehicles"

    vehicle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    license_plate = Column(String(20), unique=True, nullable=False, index=True)
    vehicle_type = Column(String(50), nullable=False)  # sedan, suv, truck, motorcycle
    brand = Column(String(100))
    model = Column(String(100))
    color = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="vehicles")
    bookings = relationship("Booking", back_populates="vehicle")
    parking_sessions = relationship("ParkingSession", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle {self.license_plate}>"
