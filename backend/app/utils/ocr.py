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


def upscale_image(image: np.ndarray, scale_factor: float = 2.0) -> np.ndarray:
    """
    Увеличение изображения для лучшего распознавания мелких символов
    """
    height, width = image.shape[:2]
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # Используем INTER_CUBIC для лучшего качества при увеличении
    upscaled = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    return upscaled


def preprocess_image_for_ocr(image: np.ndarray, upscale: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Продвинутая предобработка изображения для улучшения OCR

    Возвращает четыре варианта предобработанного изображения для повышения точности
    """
    # Конвертация в grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Увеличение изображения для лучшего распознавания мелких символов (код региона)
    if upscale and min(gray.shape) < 100:
        scale = 100.0 / min(gray.shape)
        gray = upscale_image(gray, scale_factor=max(2.0, scale))
    elif upscale:
        gray = upscale_image(gray, scale_factor=2.0)

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

    # Вариант 4: Увеличенное изображение с контрастом (для мелких символов)
    sharp_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, sharp_kernel)
    _, binary4 = cv2.threshold(
        sharpened, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return binary1, binary2, binary3, binary4


def detect_license_plate_region(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Попытка выделить регион номерного знака на изображении
    """
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # Применение билатерального фильтра для сохранения краев
        bilateral = cv2.bilateralFilter(gray, 11, 17, 17)

        # Обнаружение краев с более строгими порогами
        edged = cv2.Canny(bilateral, 50, 150)

        # Морфологические операции для объединения краёв
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

        # Поиск контуров
        contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]

        candidates = []

        # Поиск прямоугольных контуров (номерной знак обычно прямоугольный)
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            # Прямоугольник может иметь 4-6 вершин из-за шума
            if 4 <= len(approx) <= 6:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / float(h)
                area = w * h

                # Российские номера: соотношение 2.0:1 - 5.0:1
                # Минимальный размер - чтобы отфильтровать мелкие контуры
                min_area = (image.shape[0] * image.shape[1]) * 0.01  # минимум 1% от площади

                if 2.0 < aspect_ratio < 5.0 and area > min_area:
                    # Проверяем, что контур не слишком большой (не весь бампер)
                    max_area = (image.shape[0] * image.shape[1]) * 0.3  # максимум 30% от площади

                    if area < max_area:
                        candidates.append((x, y, w, h, area, aspect_ratio))

        # Если нашли кандидатов, выбираем лучший
        if candidates:
            # Сортируем по площади (предпочитаем средние размеры)
            # Идеальная площадь номера - около 5-15% от изображения
            ideal_area = (image.shape[0] * image.shape[1]) * 0.10

            def score_candidate(candidate):
                x, y, w, h, area, aspect_ratio = candidate
                # Штраф за отклонение от идеальной площади
                area_diff = abs(area - ideal_area) / ideal_area
                # Штраф за отклонение от идеального aspect ratio (3.5:1)
                aspect_diff = abs(aspect_ratio - 3.5) / 3.5
                # Меньше - лучше
                return area_diff + aspect_diff

            best_candidate = min(candidates, key=score_candidate)
            x, y, w, h, _, _ = best_candidate

            # Добавляем небольшой отступ
            margin = 5
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = min(image.shape[1] - x, w + 2 * margin)
            h = min(image.shape[0] - y, h + 2 * margin)

            plate_region = gray[y:y+h, x:x+w]
            logger.info(f"Detected plate region: {w}x{h}, aspect={w/float(h):.2f}")
            return plate_region

        logger.info("No suitable plate region found")
        return None
    except Exception as e:
        logger.warning(f"Failed to detect plate region: {str(e)}")
        return None


def fix_region_code(text: str) -> str:
    """
    Попытка исправить код региона в конце номера

    Российские коды регионов: 01-99, 102-199, 702, 750, 777, 799 и др.
    """
    russian_letters = 'АВЕКМНОРСТУХ'

    # Паттерн: буква + 3 цифры + 2 буквы + что-то в конце
    match = re.match(f'^([{russian_letters}])(\\d{{3}})([{russian_letters}]{{2}})(.+)$', text)

    if match:
        letter1 = match.group(1)
        digits = match.group(2)
        letters = match.group(3)
        region_part = match.group(4)

        # Очищаем код региона от букв (иногда OCR добавляет буквы)
        region_cleaned = re.sub(r'[^0-9]', '', region_part)

        # Если получилось 1-3 цифры, используем
        if 1 <= len(region_cleaned) <= 3:
            # Дополняем до 2 цифр нулем спереди, если нужно
            if len(region_cleaned) == 1:
                region_cleaned = '0' + region_cleaned
            return f"{letter1}{digits}{letters}{region_cleaned}"

    return text


def preprocess_license_plate_text(text: str, try_fix_region: bool = True) -> str:
    """
    Предобработка текста OCR для извлечения номерного знака

    Удаляет пробелы, спецсимволы и нормализует текст
    """
    # Удаление пробелов и конвертация в верхний регистр
    text = text.upper().strip()

    # Удаление спецсимволов, оставляем только буквы и цифры
    text = re.sub(r'[^A-ZА-Я0-9]', '', text)

    # ВАЖНО: Российский номер не может быть длиннее 9 символов (А123БВ777)
    # Если получилось больше - это мусор, отбрасываем
    if len(text) > 10:
        logger.warning(f"Text too long ({len(text)} chars), likely not a plate: {text[:20]}...")
        return ""

    # Попытка исправить код региона
    if try_fix_region and len(text) >= 6:
        text = fix_region_code(text)

    return text


def validate_russian_license_plate(plate: str, strict: bool = True) -> bool:
    """
    Валидация формата российского номерного знака

    Общие форматы:
    - А123БВ77 (легковые) - 1 буква, 3 цифры, 2 буквы, 2-3 цифры
    - А123БВ777 (легковые с 3-значным регионом)
    - М123КУ77 (Московский регион)
    """
    # Базовая проверка длины
    if len(plate) < 6 or len(plate) > 9:
        return False

    # Российские буквы, разрешенные на номерах (совпадают с латинскими)
    russian_letters = 'АВЕКМНОРСТУХ'

    # Строгая проверка формата
    if strict:
        patterns = [
            # Стандартный формат: 1 буква + 3 цифры + 2 буквы + 2-3 цифры
            f'^[{russian_letters}]\\d{{3}}[{russian_letters}]{{2}}\\d{{2,3}}$',
            # Альтернативный формат: 2 буквы + 4 цифры + 2-3 цифры
            f'^[{russian_letters}]{{2}}\\d{{4}}\\d{{2,3}}$',
        ]

        for pattern in patterns:
            if re.match(pattern, plate):
                return True
    else:
        # Нестрогая проверка: минимум 3 буквы и минимум 5 цифр
        letter_count = sum(1 for c in plate if c in russian_letters)
        digit_count = sum(1 for c in plate if c.isdigit())

        if letter_count >= 3 and digit_count >= 5:
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


def try_segment_and_recognize(image: np.ndarray, lang: str = 'rus+eng') -> Optional[str]:
    """
    Попытка сегментировать номер на основную часть и код региона
    и распознать их отдельно
    """
    try:
        height, width = image.shape[:2]

        # Российский номер примерно: 75% основная часть, 25% код региона
        split_point = int(width * 0.72)

        # Основная часть (А123БВ)
        main_part = image[:, :split_point]

        # Код региона (77 или 777)
        region_part = image[:, split_point:]

        # Увеличиваем код региона сильнее, так как он меньше
        region_upscaled = upscale_image(region_part, scale_factor=3.0)

        # Распознаём основную часть
        russian_letters = 'АВЕКМНОРСТУХ'
        main_config = f'--oem 3 --psm 7 -c tessedit_char_whitelist={russian_letters}0123456789'

        main_variants = preprocess_image_for_ocr(main_part, upscale=True)
        main_text = None

        for variant in main_variants[:2]:  # Только первые 2 варианта для скорости
            pil_image = Image.fromarray(variant)
            text = pytesseract.image_to_string(pil_image, lang=lang, config=main_config)
            text = re.sub(r'[^A-ZА-Я0-9]', '', text.upper().strip())

            if len(text) >= 6:
                main_text = text
                break

        # Распознаём код региона (только цифры)
        region_config = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'

        region_variants = preprocess_image_for_ocr(region_upscaled, upscale=False)
        region_text = None

        for variant in region_variants:
            pil_image = Image.fromarray(variant)
            text = pytesseract.image_to_string(pil_image, lang='eng', config=region_config)
            text = re.sub(r'[^0-9]', '', text.strip())

            if 1 <= len(text) <= 3:
                # Дополняем до 2 цифр если 1 цифра
                if len(text) == 1:
                    text = '0' + text
                region_text = text
                break

        # Объединяем результаты
        if main_text and region_text:
            combined = main_text + region_text
            logger.info(f"Segmented recognition: main={main_text}, region={region_text}, combined={combined}")
            return combined

        return None
    except Exception as e:
        logger.debug(f"Segmentation failed: {str(e)}")
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
            for psm in [7, 8, 6, 13]:  # 7=single line, 8=single word, 6=single block, 13=raw line
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

        # Если не получилось, пробуем сегментацию
        if not best_result or not validate_russian_license_plate(best_result):
            segmented_result = try_segment_and_recognize(image, lang)
            if segmented_result:
                segmented_plate = preprocess_license_plate_text(segmented_result)
                if segmented_plate and len(segmented_plate) >= 8:
                    confidence = len(segmented_plate)
                    if validate_russian_license_plate(segmented_plate):
                        confidence += 10

                    if confidence > max_confidence:
                        best_result = segmented_plate

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

        results = []

        # Если регион найден, пробуем его распознать
        if plate_region is not None:
            logger.info("Plate region detected, processing it")

            # 1. Попытка с EasyOCR на выделенном регионе
            easyocr_result = extract_with_easyocr(plate_region)
            if easyocr_result and len(easyocr_result) <= 10:
                results.append(('easyocr_region', easyocr_result))
                logger.info(f"EasyOCR (region) result: {easyocr_result}")

            # 2. Попытка с Tesseract на выделенном регионе
            tesseract_result = extract_with_tesseract(plate_region, lang)
            if tesseract_result and len(tesseract_result) <= 10:
                results.append(('tesseract_region', tesseract_result))
                logger.info(f"Tesseract (region) result: {tesseract_result}")

        # Если регион не найден или результаты плохие, пробуем на всём изображении
        # НО только если изображение не слишком большое (иначе будет мусор)
        if not results or not any(validate_russian_license_plate(r[1]) for r in results):
            logger.info("No valid results from region, trying full image (if small enough)")

            gray_full = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
            image_area = gray_full.shape[0] * gray_full.shape[1]

            # Только если изображение достаточно мало (вероятно, это просто номер)
            if image_area < 500000:  # < 500K пикселей
                tesseract_full = extract_with_tesseract(gray_full, lang)
                if tesseract_full and len(tesseract_full) <= 10:
                    results.append(('tesseract_full', tesseract_full))
                    logger.info(f"Tesseract (full) result: {tesseract_full}")
            else:
                logger.info("Image too large to process fully, skipping")

        # Выбор лучшего результата
        if not results:
            logger.warning("No license plate detected by any method")
            return None

        # Фильтруем результаты: только те, что похожи на номер
        valid_results = []
        for method, plate in results:
            # Проверяем с нестрогой валидацией
            if validate_russian_license_plate(plate, strict=False):
                valid_results.append((method, plate))
            else:
                logger.debug(f"Filtered out invalid result: {plate}")

        if not valid_results:
            logger.warning("No valid results after filtering")
            return None

        # Приоритет: валидный формат > длина > регион > EasyOCR
        best_result = None
        best_score = -1

        for method, plate in valid_results:
            score = 0

            # +15 за строго валидный формат
            if validate_russian_license_plate(plate, strict=True):
                score += 15
            # +5 за нестрого валидный
            else:
                score += 5

            # +1 за каждый символ (оптимум 8-9 символов)
            score += min(len(plate), 9)

            # +3 за распознавание на выделенном регионе
            if 'region' in method:
                score += 3

            # +2 за EasyOCR (обычно точнее)
            if 'easyocr' in method:
                score += 2

            logger.debug(f"Score for {method} '{plate}': {score}")

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
