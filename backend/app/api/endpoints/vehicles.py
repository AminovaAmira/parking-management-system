from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from app.core.dependencies import get_current_customer

router = APIRouter()


@router.get("/", response_model=List[VehicleResponse])
async def get_my_vehicles(
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Get all vehicles for current customer"""
    stmt = select(Vehicle).where(Vehicle.customer_id == current_customer.customer_id)
    result = await db.execute(stmt)
    vehicles = result.scalars().all()
    return vehicles


@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Create a new vehicle for current customer"""

    # Check if license plate already exists
    stmt = select(Vehicle).where(Vehicle.license_plate == vehicle_data.license_plate)
    result = await db.execute(stmt)
    existing_vehicle = result.scalar_one_or_none()

    if existing_vehicle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle with this license plate already exists"
        )

    # Create new vehicle
    new_vehicle = Vehicle(
        customer_id=current_customer.customer_id,
        **vehicle_data.model_dump()
    )

    db.add(new_vehicle)
    await db.commit()
    await db.refresh(new_vehicle)

    return new_vehicle


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific vehicle by ID"""
    stmt = select(Vehicle).where(
        Vehicle.vehicle_id == vehicle_id,
        Vehicle.customer_id == current_customer.customer_id
    )
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )

    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    vehicle_data: VehicleUpdate,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Update a vehicle"""
    stmt = select(Vehicle).where(
        Vehicle.vehicle_id == vehicle_id,
        Vehicle.customer_id == current_customer.customer_id
    )
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )

    # Update vehicle fields
    update_data = vehicle_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    await db.commit()
    await db.refresh(vehicle)

    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: UUID,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Delete a vehicle"""
    stmt = select(Vehicle).where(
        Vehicle.vehicle_id == vehicle_id,
        Vehicle.customer_id == current_customer.customer_id
    )
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )

    await db.delete(vehicle)
    await db.commit()

    return None
