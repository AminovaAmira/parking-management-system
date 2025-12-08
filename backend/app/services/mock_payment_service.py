"""
Mock Payment Service
Симуляция платежного шлюза для демонстрации
"""
import random
import string
from datetime import datetime
from typing import Dict, Any


class MockPaymentService:
    """Мок-сервис для обработки платежей"""

    def __init__(self):
        """Инициализация сервиса"""
        self.transactions = {}

    def generate_transaction_id(self) -> str:
        """Генерация ID транзакции"""
        return 'TXN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

    async def process_payment(
        self,
        amount: float,
        payment_method: str,
        customer_email: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Обработка платежа (мок)

        Args:
            amount: Сумма платежа
            payment_method: Способ оплаты (card, cash, online)
            customer_email: Email клиента
            description: Описание платежа

        Returns:
            Результат обработки платежа
        """
        transaction_id = self.generate_transaction_id()

        # Симуляция: 95% платежей успешны, 5% - отклонены
        success = random.random() < 0.95

        result = {
            "transaction_id": transaction_id,
            "status": "completed" if success else "failed",
            "amount": amount,
            "currency": "RUB",
            "payment_method": payment_method,
            "customer_email": customer_email,
            "description": description,
            "processed_at": datetime.utcnow().isoformat(),
            "message": "Оплата успешно обработана" if success else "Платеж отклонен банком"
        }

        # Сохраняем транзакцию
        self.transactions[transaction_id] = result

        return result

    async def refund_payment(
        self,
        transaction_id: str,
        amount: float = None
    ) -> Dict[str, Any]:
        """
        Возврат платежа (мок)

        Args:
            transaction_id: ID оригинальной транзакции
            amount: Сумма возврата (None = полный возврат)

        Returns:
            Результат возврата
        """
        if transaction_id not in self.transactions:
            return {
                "status": "failed",
                "message": "Транзакция не найдена"
            }

        original = self.transactions[transaction_id]
        refund_amount = amount or original["amount"]

        if refund_amount > original["amount"]:
            return {
                "status": "failed",
                "message": "Сумма возврата превышает сумму платежа"
            }

        refund_transaction_id = self.generate_transaction_id()

        result = {
            "transaction_id": refund_transaction_id,
            "original_transaction_id": transaction_id,
            "status": "refunded",
            "amount": refund_amount,
            "currency": "RUB",
            "processed_at": datetime.utcnow().isoformat(),
            "message": "Возврат успешно обработан"
        }

        self.transactions[refund_transaction_id] = result

        return result

    async def check_payment_status(
        self,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Проверка статуса платежа

        Args:
            transaction_id: ID транзакции

        Returns:
            Статус платежа
        """
        if transaction_id not in self.transactions:
            return {
                "status": "not_found",
                "message": "Транзакция не найдена"
            }

        return self.transactions[transaction_id]


# Глобальный экземпляр
mock_payment_service = MockPaymentService()
