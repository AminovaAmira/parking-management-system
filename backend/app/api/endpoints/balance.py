from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from decimal import Decimal

from app.db.database import get_db
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.core.dependencies import get_current_customer

router = APIRouter()


@router.post("/topup", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def topup_balance(
    transaction_data: TransactionCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Пополнить баланс"""

    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сумма пополнения должна быть больше нуля"
        )

    # Get current balance
    balance_before = current_customer.balance
    balance_after = balance_before + transaction_data.amount

    # Create transaction
    new_transaction = Transaction(
        customer_id=current_customer.customer_id,
        amount=transaction_data.amount,
        type="topup",
        description=f"Пополнение баланса на {transaction_data.amount} ₽",
        balance_before=balance_before,
        balance_after=balance_after
    )

    # Update customer balance
    current_customer.balance = balance_after

    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)

    return new_transaction


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Получить историю транзакций"""

    stmt = select(Transaction).where(
        Transaction.customer_id == current_customer.customer_id
    ).order_by(Transaction.created_at.desc())

    result = await db.execute(stmt)
    transactions = result.scalars().all()

    return transactions


@router.get("/balance", response_model=dict)
async def get_balance(
    current_customer: Customer = Depends(get_current_customer)
):
    """Получить текущий баланс"""

    return {
        "balance": float(current_customer.balance),
        "currency": "RUB"
    }
