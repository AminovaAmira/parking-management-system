from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.customer import Customer
from app.schemas.token import TokenData

security = HTTPBearer()


async def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Customer:
    """Get current authenticated customer from JWT token"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    token_data = TokenData(email=email)

    # Get customer from database
    stmt = select(Customer).where(Customer.email == token_data.email)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()

    if customer is None:
        raise credentials_exception

    return customer


async def get_current_admin(
    current_customer: Customer = Depends(get_current_customer)
) -> Customer:
    """Check if current customer is admin"""
    if not current_customer.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_customer
