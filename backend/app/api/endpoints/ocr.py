from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import Optional

from app.utils.ocr import extract_license_plate_from_image, format_license_plate

router = APIRouter()


@router.post("/recognize")
async def recognize_license_plate(
    file: UploadFile = File(..., description="Image file containing license plate")
):
    """
    Recognize license plate from uploaded image

    Accepts image formats: JPG, JPEG, PNG
    Returns recognized license plate number
    """

    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    # Read file
    try:
        image_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading file: {str(e)}"
        )

    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(image_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum size is 10MB"
        )

    # Extract license plate
    license_plate = extract_license_plate_from_image(image_bytes)

    if not license_plate:
        return {
            "success": False,
            "message": "Could not recognize license plate from image",
            "license_plate": None
        }

    # Format license plate
    formatted_plate = format_license_plate(license_plate)

    return {
        "success": True,
        "message": "License plate recognized successfully",
        "license_plate": formatted_plate,
        "raw_text": license_plate
    }


@router.post("/validate")
async def validate_license_plate_format(
    license_plate: str
):
    """
    Validate license plate format

    Checks if the license plate matches Russian format
    """
    from app.utils.ocr import validate_russian_license_plate

    is_valid = validate_russian_license_plate(license_plate.upper())

    return {
        "license_plate": license_plate.upper(),
        "is_valid": is_valid,
        "format": "Russian standard" if is_valid else "Unknown/Invalid"
    }
