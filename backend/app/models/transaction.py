from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Transaction(Base):
    """Transaction model - транзакции с балансом клиента"""
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False, index=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.booking_id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("parking_sessions.session_id"), nullable=True)

    amount = Column(Numeric(10, 2), nullable=False)  # Положительное - пополнение, отрицательное - списание
    type = Column(String(50), nullable=False, index=True)  # topup, booking_charge, refund, penalty
    description = Column(Text)
    balance_before = Column(Numeric(10, 2), nullable=False)
    balance_after = Column(Numeric(10, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer = relationship("Customer")
    booking = relationship("Booking")
    session = relationship("ParkingSession")

    def __repr__(self):
        return f"<Transaction {self.transaction_id} - {self.type}: {self.amount}>"
