import re
import io
import logging
from typing import Optional, Tuple
from PIL import Image
import cv2
import numpy as np
import pytesseract

# EasyOCR будет инициализирован лениво при первом использовании
_easyocr_reader = None

logger = logging.getLogger(__name__)


def get_easyocr_reader():
    """Ленивая инициализация EasyOCR reader"""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(['ru', 'en'], gpu=False)
            logger.info("EasyOCR reader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {str(e)}")
            _easyocr_reader = None
    return _easyocr_reader


def preprocess_image_for_ocr(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Продвинутая предобработка изображения для улучшения OCR

    Возвращает три варианта предобработанного изображения для повышения точности
    """
    # Конвертация в grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Вариант 1: Увеличение контраста с адаптивной бинаризацией
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    binary1 = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Вариант 2: Удаление шума + бинаризация Otsu
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, binary2 = cv2.threshold(
        denoised, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Вариант 3: Морфологические операции для улучшения текста
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morphed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel)
    _, binary3 = cv2.threshold(
        morphed, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return binary1, binary2, binary3


def detect_license_plate_region(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Попытка выделить регион номерного знака на изображении
    """
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # Применение билатерального фильтра для сохранения краев
        bilateral = cv2.bilateralFilter(gray, 11, 17, 17)

        # Обнаружение краев
        edged = cv2.Canny(bilateral, 30, 200)

        # Поиск контуров
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        # Поиск прямоугольного контура (номерной знак обычно прямоугольный)
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.018 * peri, True)

            if len(approx) == 4:  # Прямоугольник
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / float(h)

                # Российские номера обычно имеют соотношение сторон около 2.5:1 - 4:1
                if 2.0 < aspect_ratio < 5.0:
                    # Добавляем небольшой отступ
                    margin = 5
                    x = max(0, x - margin)
                    y = max(0, y - margin)
                    w = min(image.shape[1] - x, w + 2 * margin)
                    h = min(image.shape[0] - y, h + 2 * margin)

                    return gray[y:y+h, x:x+w]

        return None
    except Exception as e:
        logger.warning(f"Failed to detect plate region: {str(e)}")
        return None


def preprocess_license_plate_text(text: str) -> str:
    """
    Предобработка текста OCR для извлечения номерного знака

    Удаляет пробелы, спецсимволы и нормализует текст
    """
    # Удаление пробелов и конвертация в верхний регистр
    text = text.upper().strip()

    # Замена похожих символов (часто OCR путает)
    replacements = {
        'O': '0',  # O -> 0
        'I': '1',  # I -> 1
        'Z': '2',  # Z -> 2
        'S': '5',  # S -> 5
        'G': '6',  # G -> 6
        'B': '8',  # B -> 8
        'Q': '0',  # Q -> 0
    }

    # Применяем замены только для цифр (не для букв в номере)
    # Сначала извлекаем возможные буквы и цифры отдельно

    # Удаление спецсимволов, оставляем только буквы и цифры
    text = re.sub(r'[^A-ZА-Я0-9]', '', text)

    return text


def validate_russian_license_plate(plate: str) -> bool:
    """
    Валидация формата российского номерного знака

    Общие форматы:
    - А123БВ77 (легковые) - 1 буква, 3 цифры, 2 буквы, 2-3 цифры
    - А123БВ777 (легковые с 3-значным регионом)
    - М123КУ77 (Московский регион)
    """
    # Российские буквы, разрешенные на номерах (совпадают с латинскими)
    russian_letters = 'АВЕКМНОРСТУХ'

    patterns = [
        # Стандартный формат: 1 буква + 3 цифры + 2 буквы + 2-3 цифры
        f'^[{russian_letters}]\\d{{3}}[{russian_letters}]{{2}}\\d{{2,3}}$',
        # Альтернативный формат: 2 буквы + 4 цифры + 2-3 цифры
        f'^[{russian_letters}]{{2}}\\d{{4}}\\d{{2,3}}$',
    ]

    for pattern in patterns:
        if re.match(pattern, plate):
            return True

    return False


def extract_with_easyocr(image: np.ndarray) -> Optional[str]:
    """
    Распознавание номера с помощью EasyOCR
    """
    try:
        reader = get_easyocr_reader()
        if reader is None:
            return None

        # EasyOCR работает лучше с оригинальным изображением
        results = reader.readtext(image, detail=0, paragraph=False)

        if not results:
            return None

        # Объединяем все распознанные тексты
        text = ''.join(results)
        plate = preprocess_license_plate_text(text)

        if plate and len(plate) >= 6:
            return plate

        return None
    except Exception as e:
        logger.error(f"EasyOCR error: {str(e)}")
        return None


def extract_with_tesseract(image: np.ndarray, lang: str = 'rus+eng') -> Optional[str]:
    """
    Распознавание номера с помощью Tesseract OCR
    """
    try:
        # Пробуем разные варианты предобработки
        variants = preprocess_image_for_ocr(image)

        # Конфигурация Tesseract для номерных знаков
        russian_letters = 'АВЕКМНОРСТУХ'
        config = f'--oem 3 --psm 7 -c tessedit_char_whitelist={russian_letters}0123456789'

        best_result = None
        max_confidence = 0

        for variant in variants:
            # Конвертация numpy array в PIL Image
            pil_image = Image.fromarray(variant)

            # OCR с разными PSM режимами
            for psm in [7, 8, 6]:  # 7=single line, 8=single word, 6=single block
                try:
                    custom_config = config.replace('--psm 7', f'--psm {psm}')
                    text = pytesseract.image_to_string(pil_image, lang=lang, config=custom_config)

                    plate = preprocess_license_plate_text(text)

                    if plate and len(plate) >= 6:
                        # Простая оценка "уверенности" по длине и валидности
                        confidence = len(plate)
                        if validate_russian_license_plate(plate):
                            confidence += 10

                        if confidence > max_confidence:
                            max_confidence = confidence
                            best_result = plate
                except Exception as e:
                    logger.debug(f"Tesseract PSM {psm} failed: {str(e)}")
                    continue

        return best_result if best_result else None
    except Exception as e:
        logger.error(f"Tesseract error: {str(e)}")
        return None


def extract_license_plate_from_image(image_bytes: bytes, lang: str = 'rus+eng') -> Optional[str]:
    """
    Извлечение номерного знака из изображения с использованием гибридного подхода

    Использует комбинацию EasyOCR и Tesseract для повышения точности

    Args:
        image_bytes: Байты изображения
        lang: Языки для Tesseract (по умолчанию: 'rus+eng')

    Returns:
        Распознанный номерной знак или None
    """
    try:
        # Открытие изображения
        image = Image.open(io.BytesIO(image_bytes))

        # Конвертация PIL -> OpenCV
        image_np = np.array(image)
        if len(image_np.shape) == 2:  # Grayscale
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
        elif image_np.shape[2] == 4:  # RGBA
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)

        # Попытка выделить регион номерного знака
        plate_region = detect_license_plate_region(image_np)

        # Если регион найден, используем его, иначе - все изображение
        target_image = plate_region if plate_region is not None else (
            cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        )

        logger.info(f"Processing image, plate region detected: {plate_region is not None}")

        # Гибридный подход: пробуем оба метода
        results = []

        # 1. Попытка с EasyOCR (обычно лучше для сложных случаев)
        easyocr_result = extract_with_easyocr(target_image)
        if easyocr_result:
            results.append(('easyocr', easyocr_result))
            logger.info(f"EasyOCR result: {easyocr_result}")

        # 2. Попытка с Tesseract (быстрее, хорош для четких изображений)
        tesseract_result = extract_with_tesseract(target_image, lang)
        if tesseract_result:
            results.append(('tesseract', tesseract_result))
            logger.info(f"Tesseract result: {tesseract_result}")

        # Выбор лучшего результата
        if not results:
            logger.warning("No license plate detected by any method")
            return None

        # Приоритет: валидный формат > длина > EasyOCR > Tesseract
        best_result = None
        best_score = -1

        for method, plate in results:
            score = 0

            # +10 за валидный формат
            if validate_russian_license_plate(plate):
                score += 10

            # +1 за каждый символ (оптимум 8-9 символов)
            score += min(len(plate), 9)

            # +5 за EasyOCR (обычно точнее)
            if method == 'easyocr':
                score += 5

            if score > best_score:
                best_score = score
                best_result = plate

        logger.info(f"Best result selected: {best_result} (score: {best_score})")
        return best_result

    except Exception as e:
        logger.error(f"OCR Error: {str(e)}", exc_info=True)
        return None


def format_license_plate(plate: str) -> str:
    """
    Форматирование номерного знака в стандартный вид

    Пример: А123БВ77 -> А123БВ77 (с правильными пробелами если нужно)
    """
    plate = plate.upper().strip()

    russian_letters = 'АВЕКМНОРСТУХ'

    # Для российских номеров: Буква + 3 цифры + 2 буквы + 2-3 цифры
    match = re.match(f'^([{russian_letters}])(\\d{{3}})([{russian_letters}]{{2}})(\\d{{2,3}})$', plate)
    if match:
        return f"{match.group(1)}{match.group(2)}{match.group(3)}{match.group(4)}"

    return plate
