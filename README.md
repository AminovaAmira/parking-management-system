# Parking Management System

Система управления парковкой с функциями бронирования, оплаты и автоматического распознавания номерных знаков.

## Технологический стек

### Backend
- **FastAPI** 0.104+ - веб-фреймворк
- **Python** 3.11+
- **PostgreSQL** 15+ - основная база данных
- **SQLAlchemy** 2.0 - ORM
- **Alembic** - миграции БД
- **JWT** - аутентификация

### Frontend
- **React** 18+
- **Material-UI** v5
- **Axios** - HTTP клиент
- **React Router** v6

### Infrastructure
- **Docker** & **Docker Compose**
- **PostgreSQL** в контейнере

## Быстрый старт

### Предварительные требования
- Docker и Docker Compose
- Git

### Запуск проекта

1. **Клонируйте репозиторий:**
```bash
git clone git@github.com:AminovaAmira/parking-management-system.git
cd parking-management-system
```

2. **Настройте переменные окружения (опционально):**
Файл `.env` уже создан с базовыми настройками. При необходимости отредактируйте его.

3. **Запустите все сервисы:**
```bash
docker-compose up --build
```

4. **Доступ к приложению:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432

### Остановка проекта

```bash
docker-compose down
```

Для полного удаления (включая volumes с данными БД):
```bash
docker-compose down -v
```

## Структура проекта

```
parking-management-system/
├── backend/                 # FastAPI приложение
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Конфигурация, безопасность
│   │   ├── db/             # Подключение к БД
│   │   ├── models/         # SQLAlchemy модели
│   │   ├── schemas/        # Pydantic схемы
│   │   ├── services/       # Бизнес-логика
│   │   └── utils/          # Утилиты
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # React приложение
│   ├── public/
│   ├── src/
│   │   ├── components/    # React компоненты
│   │   ├── pages/         # Страницы
│   │   ├── services/      # API сервисы
│   │   └── utils/         # Утилиты
│   ├── Dockerfile
│   └── package.json
├── database/              # Скрипты БД
│   ├── scripts/          # SQL скрипты инициализации
│   └── migrations/       # Alembic миграции
├── docker-compose.yml    # Оркестрация Docker
└── .env                  # Переменные окружения
```

## API Endpoints (планируемые)

### Аутентификация
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход
- `POST /api/auth/refresh` - Обновление токена

### Клиенты
- `GET /api/customers/me` - Профиль текущего пользователя
- `PUT /api/customers/me` - Обновление профиля

### Автомобили
- `GET /api/vehicles` - Список автомобилей
- `POST /api/vehicles` - Добавить автомобиль
- `DELETE /api/vehicles/{id}` - Удалить автомобиль

### Парковочные зоны
- `GET /api/zones` - Список зон
- `GET /api/zones/{id}/availability` - Доступные места

### Бронирования
- `POST /api/bookings` - Создать бронирование
- `GET /api/bookings` - Мои бронирования
- `DELETE /api/bookings/{id}` - Отменить бронирование

### Парковочные сессии
- `POST /api/sessions/start` - Начать сессию
- `POST /api/sessions/end` - Завершить сессию
- `GET /api/sessions/active` - Активные сессии

### Платежи
- `POST /api/payments` - Создать платеж
- `GET /api/payments` - История платежей

## Разработка

### Backend development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend development

```bash
cd frontend
npm install
npm start
```

## База данных

### Схема БД
- **customers** - Клиенты
- **vehicles** - Автомобили
- **parking_zones** - Парковочные зоны
- **parking_spots** - Парковочные места
- **tariff_plans** - Тарифные планы
- **bookings** - Бронирования
- **parking_sessions** - Парковочные сессии
- **payments** - Платежи

### Миграции (Alembic)

```bash
# Создать миграцию
docker-compose exec backend alembic revision --autogenerate -m "description"

# Применить миграции
docker-compose exec backend alembic upgrade head
```

## Тестирование

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test
```

## Дополнительная информация

- Документация API доступна по адресу: http://localhost:8000/docs
- Используется JWT для аутентификации
- OCR для распознавания номерных знаков (pytesseract)
- Асинхронная работа с БД через asyncpg

## Авторы

Курсовой проект по дисциплине "Программная инженерия"
