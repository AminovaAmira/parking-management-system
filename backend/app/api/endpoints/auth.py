from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerLogin
from app.schemas.token import Token
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_current_customer
from datetime import timedelta
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def register(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new customer"""

    # Check if email already exists
    stmt = select(Customer).where(Customer.email == customer_data.email)
    result = await db.execute(stmt)
    existing_customer = result.scalar_one_or_none()

    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new customer
    hashed_password = get_password_hash(customer_data.password)

    new_customer = Customer(
        first_name=customer_data.first_name,
        last_name=customer_data.last_name,
        email=customer_data.email,
        phone=customer_data.phone,
        password_hash=hashed_password
    )

    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)

    return new_customer


@router.post("/login", response_model=Token)
async def login(
    login_data: CustomerLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login and get access token"""

    # Get customer by email
    stmt = select(Customer).where(Customer.email == login_data.email)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, customer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": customer.email, "customer_id": str(customer.customer_id)},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=CustomerResponse)
async def get_current_user(
    customer: Customer = Depends(get_current_customer)
):
    """Get current authenticated customer"""
    return customer
