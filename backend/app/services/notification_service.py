"""
Notification Service
Handles email and in-app notifications for parking events
"""
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications to users"""

    def __init__(self, email_enabled: bool = False):
        self.email_enabled = email_enabled
        logger.info(f"Notification service initialized (email_enabled={email_enabled})")

    async def send_booking_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        booking_id: str,
        zone_name: str,
        spot_number: str,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Send booking confirmation notification"""
        try:
            subject = "Подтверждение бронирования парковочного места"
            message = f"""
Здравствуйте, {customer_name}!

Ваше бронирование успешно создано.

Детали бронирования:
- Номер бронирования: {booking_id[:8]}
- Зона: {zone_name}
- Место: {spot_number}
- Начало: {start_time.strftime('%d.%m.%Y %H:%M')}
- Окончание: {end_time.strftime('%d.%m.%Y %H:%M')}

Спасибо, что выбрали нашу парковку!
"""
            await self._send_email(customer_email, subject, message)
            return True
        except Exception as e:
            logger.error(f"Failed to send booking confirmation: {e}")
            return False

    async def send_session_started(
        self,
        customer_email: str,
        customer_name: str,
        session_id: str,
        zone_name: str,
        spot_number: str,
        vehicle_plate: str,
        entry_time: datetime
    ) -> bool:
        """Send session started notification"""
        try:
            subject = "Парковочная сессия начата"
            message = f"""
Здравствуйте, {customer_name}!

Ваша парковочная сессия начата.

Детали:
- Номер сессии: {session_id[:8]}
- Зона: {zone_name}
- Место: {spot_number}
- Автомобиль: {vehicle_plate}
- Время въезда: {entry_time.strftime('%d.%m.%Y %H:%M')}

Удачной поездки!
"""
            await self._send_email(customer_email, subject, message)
            return True
        except Exception as e:
            logger.error(f"Failed to send session started notification: {e}")
            return False

    async def send_session_ended(
        self,
        customer_email: str,
        customer_name: str,
        session_id: str,
        zone_name: str,
        spot_number: str,
        vehicle_plate: str,
        entry_time: datetime,
        exit_time: datetime,
        duration_minutes: int,
        total_cost: float
    ) -> bool:
        """Send session ended notification"""
        try:
            hours = duration_minutes // 60
            minutes = duration_minutes % 60

            subject = "Парковочная сессия завершена"
            message = f"""
Здравствуйте, {customer_name}!

Ваша парковочная сессия завершена.

Детали:
- Номер сессии: {session_id[:8]}
- Зона: {zone_name}
- Место: {spot_number}
- Автомобиль: {vehicle_plate}
- Время въезда: {entry_time.strftime('%d.%m.%Y %H:%M')}
- Время выезда: {exit_time.strftime('%d.%m.%Y %H:%M')}
- Длительность: {hours}ч {minutes}мин
- Стоимость: {total_cost:.2f} ₽

Пожалуйста, оплатите парковку в личном кабинете.
"""
            await self._send_email(customer_email, subject, message)
            return True
        except Exception as e:
            logger.error(f"Failed to send session ended notification: {e}")
            return False

    async def send_payment_confirmation(
        self,
        customer_email: str,
        customer_name: str,
        payment_id: str,
        amount: float,
        payment_method: str,
        transaction_id: Optional[str] = None
    ) -> bool:
        """Send payment confirmation notification"""
        try:
            subject = "Платеж успешно обработан"
            message = f"""
Здравствуйте, {customer_name}!

Ваш платеж успешно обработан.

Детали платежа:
- Номер платежа: {payment_id[:8]}
- Сумма: {amount:.2f} ₽
- Способ оплаты: {payment_method}
"""
            if transaction_id:
                message += f"- ID транзакции: {transaction_id}\n"

            message += "\nСпасибо за оплату!"

            await self._send_email(customer_email, subject, message)
            return True
        except Exception as e:
            logger.error(f"Failed to send payment confirmation: {e}")
            return False

    async def send_booking_reminder(
        self,
        customer_email: str,
        customer_name: str,
        zone_name: str,
        spot_number: str,
        start_time: datetime
    ) -> bool:
        """Send booking reminder notification"""
        try:
            subject = "Напоминание о бронировании"
            message = f"""
Здравствуйте, {customer_name}!

Напоминаем, что у вас скоро начинается бронирование:

- Зона: {zone_name}
- Место: {spot_number}
- Начало: {start_time.strftime('%d.%m.%Y %H:%M')}

Не забудьте прибыть вовремя!
"""
            await self._send_email(customer_email, subject, message)
            return True
        except Exception as e:
            logger.error(f"Failed to send booking reminder: {e}")
            return False

    async def _send_email(self, to_email: str, subject: str, message: str) -> None:
        """Internal method to send email"""
        if self.email_enabled:
            # TODO: Implement actual email sending using fastapi-mail or smtplib
            # For production, integrate with services like SendGrid, AWS SES, etc.
            logger.info(f"Would send email to {to_email}: {subject}")
            # await actual_email_send(to_email, subject, message)
        else:
            # In development mode, just log the notification
            logger.info(
                f"\n{'='*60}\n"
                f"EMAIL NOTIFICATION\n"
                f"To: {to_email}\n"
                f"Subject: {subject}\n"
                f"Message:\n{message}\n"
                f"{'='*60}\n"
            )


# Global instance
notification_service = NotificationService(email_enabled=False)
