Архитектура проекта DatingBot
Проект построен как монолит с чётким разделением ответственности:

Backend (backend/) — FastAPI-приложение, отвечает за всю бизнес-логику, работу с базой данных и API.
Telegram Bot (bot/) — Aiogram 3.x бот, отвечает только за интерфейс общения с пользователем.

1. Backend (FastAPI)
   Папка: backend/app/
   Основные компоненты:

main.py — точка входа FastAPI. Создаёт приложение, подключает роутеры, middleware, lifespan.
router.py — регистрация всех API-эндпоинтов.
models.py — SQLAlchemy ORM-модели (User, UserInteraction, UserRating).
schemas.py — Pydantic-модели для запросов и ответов API.
repositories.py — слой доступа к данным (CRUD-операции над моделями).
database.py — настройка асинхронного подключения к PostgreSQL, создание сессий (AsyncSession).
rating_updater.py — сервис фонового обновления рейтингов пользователей.
config.py — загрузка настроек (токены, DATABASE_URL, DEBUG и т.д.).
migrations/ — Alembic-миграции базы данных.

Слой доступа к данным:
Handlers/Routers → Services (пока частично в router) → Repositories → Database 2. Telegram Bot (Aiogram 3.x)
Папка: bot/app/
Основные компоненты:

main.py — запуск бота, создание Bot и Dispatcher, регистрация middleware и handlers.
handlers.py — все обработчики сообщений, команд и callback-запросов.
states.py — все состояния Finite State Machine (FSM)
fsm.py — реализация и переходы между состояниями FSM
keyboards.py — генерация всех клавиатур (reply и inline).
middlewares.py — промежуточные обработчики (логирование, проверка пользователя, throttling и т.д.).
http_requests.py — HTTP-клиент для общения бота с Backend
config.py — конфигурация бота (BOT_TOKEN и т.д.).
utils.py — вспомогательные функции.
