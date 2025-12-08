from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class CustomerBase(BaseModel):
    """Base customer schema"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)


class CustomerCreate(CustomerBase):
    """Schema for creating a customer"""
    password: str = Field(..., min_length=6, max_length=100)


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)


class CustomerResponse(CustomerBase):
    """Schema for customer response"""
    customer_id: UUID
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerLogin(BaseModel):
    """Schema for customer login"""
    email: EmailStr
    password: str


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6, max_length=100)
