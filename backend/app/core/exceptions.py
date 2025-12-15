"""
Кастомная обработка исключений для API
Все сообщения об ошибках на русском языке
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError
from typing import Union


# Словарь с переводами стандартных HTTP статусов
HTTP_STATUS_MESSAGES = {
    400: "Неверный запрос",
    401: "Требуется авторизация",
    403: "Доступ запрещен",
    404: "Ресурс не найден",
    405: "Метод не разрешен",
    409: "Конфликт данных",
    422: "Ошибка валидации данных",
    500: "Внутренняя ошибка сервера",
    503: "Сервис недоступен",
}


# Перевод полей для ошибок валидации
FIELD_TRANSLATIONS = {
    "email": "Email",
    "password": "Пароль",
    "first_name": "Имя",
    "last_name": "Фамилия",
    "phone": "Телефон",
    "license_plate": "Номер автомобиля",
    "make": "Марка",
    "model": "Модель",
    "color": "Цвет",
    "vehicle_type": "Тип автомобиля",
    "spot_id": "ID парковочного места",
    "vehicle_id": "ID автомобиля",
    "zone_id": "ID зоны",
    "start_time": "Время начала",
    "end_time": "Время окончания",
    "amount": "Сумма",
    "payment_method": "Метод оплаты",
    "current_password": "Текущий пароль",
    "new_password": "Новый пароль",
}


# Перевод типов ошибок валидации
VALIDATION_ERROR_MESSAGES = {
    "value_error.missing": "Поле обязательно для заполнения",
    "value_error.email": "Неверный формат email адреса",
    "value_error.any_str.min_length": "Значение слишком короткое",
    "value_error.any_str.max_length": "Значение слишком длинное",
    "value_error.number.not_ge": "Значение должно быть больше или равно {limit_value}",
    "value_error.number.not_le": "Значение должно быть меньше или равно {limit_value}",
    "type_error.integer": "Должно быть целое число",
    "type_error.float": "Должно быть число",
    "type_error.string": "Должна быть строка",
    "type_error.boolean": "Должно быть булево значение",
    "type_error.none.not_allowed": "Значение не может быть пустым",
}


def translate_field_name(field: str) -> str:
    """Переводит название поля на русский"""
    return FIELD_TRANSLATIONS.get(field, field)


def translate_validation_error_type(error_type: str, ctx: dict = None) -> str:
    """Переводит тип ошибки валидации на русский"""
    message = VALIDATION_ERROR_MESSAGES.get(error_type, "Ошибка валидации")

    if ctx:
        try:
            message = message.format(**ctx)
        except (KeyError, ValueError):
            pass

    return message


def format_validation_errors(errors: list) -> list:
    """Форматирует ошибки валидации Pydantic на русский язык"""
    formatted_errors = []

    for error in errors:
        loc = error.get("loc", [])
        error_type = error.get("type", "")
        msg = error.get("msg", "")
        ctx = error.get("ctx", {})

        # Получаем имя поля (последний элемент в loc)
        field = loc[-1] if loc else "unknown"
        field_name = translate_field_name(str(field))

        # Формируем русское сообщение
        if "missing" in error_type:
            russian_msg = f"{field_name}: Поле обязательно для заполнения"
        elif "email" in error_type:
            russian_msg = f"{field_name}: Неверный формат email адреса"
        elif "min_length" in msg.lower():
            min_length = ctx.get("limit_value", "")
            russian_msg = f"{field_name}: Минимальная длина {min_length} символов"
        elif "max_length" in msg.lower():
            max_length = ctx.get("limit_value", "")
            russian_msg = f"{field_name}: Максимальная длина {max_length} символов"
        elif "string" in error_type:
            russian_msg = f"{field_name}: Должна быть строка"
        elif "integer" in error_type:
            russian_msg = f"{field_name}: Должно быть целое число"
        elif "not a valid" in msg.lower():
            russian_msg = f"{field_name}: Неверный формат данных"
        else:
            # Переводим через словарь или оставляем как есть
            translated = translate_validation_error_type(error_type, ctx)
            russian_msg = f"{field_name}: {translated}"

        formatted_errors.append({
            "field": field_name,
            "message": russian_msg,
            "type": error_type
        })

    return formatted_errors


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Обработчик HTTP исключений с русскими сообщениями"""

    status_code = exc.status_code
    detail = exc.detail

    # Если detail уже на русском (содержит кириллицу), оставляем как есть
    if isinstance(detail, str) and any('\u0400' <= c <= '\u04FF' for c in detail):
        russian_detail = detail
    else:
        # Иначе используем стандартное сообщение для статус-кода
        russian_detail = HTTP_STATUS_MESSAGES.get(status_code, detail)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": True,
            "message": russian_detail,
            "status_code": status_code
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Обработчик ошибок валидации Pydantic с русскими сообщениями"""

    errors = exc.errors() if hasattr(exc, 'errors') else []
    formatted_errors = format_validation_errors(errors)

    # Формируем основное сообщение
    if len(formatted_errors) == 1:
        main_message = formatted_errors[0]["message"]
    else:
        main_message = f"Обнаружено ошибок валидации: {len(formatted_errors)}"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": main_message,
            "errors": formatted_errors,
            "status_code": 422
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик всех остальных исключений"""

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Произошла внутренняя ошибка сервера. Попробуйте позже.",
            "status_code": 500
        }
    )
