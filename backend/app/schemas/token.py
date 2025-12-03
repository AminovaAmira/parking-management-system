from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """JWT Token response schema"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None
    customer_id: Optional[str] = None
