import re
from typing import Optional
from PIL import Image
import pytesseract
import io


def preprocess_license_plate_text(text: str) -> str:
    """
    Preprocess OCR output to extract license plate number

    Removes spaces, special characters, and normalizes the text
    """
    # Remove spaces and convert to uppercase
    text = text.upper().strip()

    # Remove special characters except letters and numbers
    text = re.sub(r'[^A-Z0-9]', '', text)

    return text


def validate_russian_license_plate(plate: str) -> bool:
    """
    Validate Russian license plate format

    Common formats:
    - А123БВ77 (private cars) - 1 letter, 3 digits, 2 letters, 2-3 digits
    - А123БВ777 (private cars with 3-digit region)
    - М123КУ77 (Moscow region specific)
    """
    # Pattern for standard Russian license plates
    patterns = [
        r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',  # Standard format
        r'^[АВЕКМНОРСТУХ]{2}\d{4}\d{2,3}$',  # Alternative format
    ]

    for pattern in patterns:
        if re.match(pattern, plate):
            return True

    return False


def extract_license_plate_from_image(image_bytes: bytes, lang: str = 'rus+eng') -> Optional[str]:
    """
    Extract license plate number from image using OCR

    Args:
        image_bytes: Image file bytes
        lang: Tesseract language (default: 'rus+eng' for Russian and English)

    Returns:
        License plate number or None if not detected
    """
    try:
        # Open image
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to grayscale for better OCR
        image = image.convert('L')

        # Perform OCR with custom configuration
        # --psm 7: Treat image as single text line (good for license plates)
        # --oem 3: Use default OCR Engine Mode
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZАВЕКМНОРСТУХ0123456789'

        text = pytesseract.image_to_string(image, lang=lang, config=custom_config)

        # Preprocess text
        plate = preprocess_license_plate_text(text)

        if not plate:
            return None

        # Validate format (optional - return even if not valid for flexibility)
        # if not validate_russian_license_plate(plate):
        #     return None

        return plate

    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return None


def format_license_plate(plate: str) -> str:
    """
    Format license plate to standard view

    Example: А123БВ77 -> А123БВ77 (with proper spacing if needed)
    """
    plate = plate.upper().strip()

    # For Russian plates: А123БВ77
    # Format: Letter + 3digits + 2letters + 2-3digits
    match = re.match(r'^([АВЕКМНОРСТУХ])(\d{3})([АВЕКМНОРСТУХ]{2})(\d{2,3})$', plate)
    if match:
        return f"{match.group(1)}{match.group(2)}{match.group(3)}{match.group(4)}"

    return plate
