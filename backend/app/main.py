from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Create FastAPI application
app = FastAPI(
    title="Parking Management System API",
    description="API для системы управления парковкой",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Parking Management System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected"
    }


# TODO: Import and include routers
# from app.api.endpoints import auth, customers, vehicles, zones, bookings, sessions, payments

# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
# app.include_router(vehicles.router, prefix="/api/vehicles", tags=["Vehicles"])
# app.include_router(zones.router, prefix="/api/zones", tags=["Parking Zones"])
# app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
# app.include_router(sessions.router, prefix="/api/sessions", tags=["Parking Sessions"])
# app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
