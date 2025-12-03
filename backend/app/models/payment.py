from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Payment(Base):
    """Payment model - платежи"""
    __tablename__ = "payments"

    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("parking_sessions.session_id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # card, cash, online
    status = Column(String(50), nullable=False, default="pending")  # pending, completed, failed, refunded
    transaction_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    session = relationship("ParkingSession", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.payment_id} - {self.amount} - {self.status}>"
