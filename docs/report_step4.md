# Отчёт по проекту DatingBot (этапы 1–4)

## 1. Краткое описание проекта

Telegram-бот для знакомств с backend на FastAPI и PostgreSQL.  
Пользователь регистрируется, заполняет анкету, ищет пару, ставит лайки/пропуски. Рейтинг формируется по трёхуровневой модели и влияет на ранжирование анкет в поиске.

---

## 2. Этапы разработки

| Этап | Что реализовано |
|------|-----------------|
| **1** | Каркас проекта: Docker Compose, PostgreSQL, модели БД, базовый FastAPI backend, Telegram-бот |
| **2** | Регистрация через FSM, заполнение профиля и предпочтений, API пользователей |
| **3** | Поиск пары, лайки/пропуски, ранжирование кандидатов по рейтингу, пересчёт рейтинга |
| **4** | Фоновый пересчёт рейтингов, детальная разбивка рейтинга, уведомления о match, отчёт |

---

## 3. Система оценивания рейтинга (3 уровня)

Реализация: `backend/app/rating_service.py`, вызов из `backend/app/repositories.py`.

### Уровень 1 — первичный рейтинг
- Заполненность анкеты (8 полей: профиль + предпочтения).
- Формула: `primary_score = (заполненные_поля / 8) * 100`.

### Уровень 2 — поведенческий рейтинг
- Соотношение лайков и пропусков: `like_skip_ratio = likes / (likes + skips)`.
- Доля взаимных лайков (match): `mutual_ratio = mutual_likes / outgoing_likes`.
- Временной фактор активности по `last_activity` (штраф при долгом отсутствии).
- Формула: `behavior_score = (like_skip_ratio * 0.5 + mutual_ratio * 0.5) * 100 * activity_factor`.

### Уровень 3 — комбинированный рейтинг
- Взвешенная сумма: `combined = primary * 0.4 + behavior * 0.5 + referral_bonus`.
- Реферальный бонус: `min(кол-во_приглашённых * 5, 20)`.

Итог сохраняется в таблицу `user_ratings`.

---

## 4. Этап 4 — что добавлено

| Компонент | Файл | Назначение |
|-----------|------|------------|
| Сервис расчёта рейтинга | `backend/app/rating_service.py` | Единая логика 3 уровней + структура `RatingBreakdown` |
| Фоновый пересчёт | `backend/app/rating_updater.py` | Периодический пересчёт рейтингов всех пользователей (каждые 5 мин) |
| Запуск updater | `backend/app/main.py` | Старт/остановка фоновой задачи в `lifespan` FastAPI |
| Детали рейтинга API | `backend/app/router.py` | `GET /api/users/{id}/rating/details` |
| Match при лайке | `backend/app/repositories.py`, `router.py` | Поле `is_match` в ответе interaction |
| Уведомления в боте | `bot/app/handlers.py` | Сообщение о match обоим пользователям |
| Разбивка в боте | `bot/app/handlers.py` | Кнопка «Мой рейтинг» показывает все уровни |

---

## 5. Технологии из системы оценивания: где и как применены

### Python 3.11
- Весь backend и bot.
- Файлы: `backend/app/*`, `bot/app/*`.

### FastAPI
- REST API для бота.
- Файлы: `backend/app/main.py`, `backend/app/router.py`.
- Эндпоинты: регистрация, профиль, interactions, рейтинг, поиск кандидата.

### PostgreSQL
- Хранение пользователей, взаимодействий, рейтингов.
- Подключение через `asyncpg`.
- Файлы: `backend/app/database.py`, `docker-compose.yml`.

### SQLAlchemy 2.0 (async ORM)
- Модели и запросы к БД.
- Файлы: `backend/app/models.py`, `backend/app/repositories.py`, `backend/app/rating_service.py`.

### Alembic
- Миграции схемы БД.
- Файлы: `backend/app/migrations/versions/001_initial.py`, `backend/app/migrations/env.py`.

### Pydantic / pydantic-settings
- Валидация запросов и ответов API.
- Конфигурация из `.env`.
- Файлы: `backend/app/schemas.py`, `backend/app/config.py`, `bot/app/config.py`.

### Docker + Docker Compose
- Контейнеризация postgres, backend, bot.
- Файлы: `docker-compose.yml`, `backend/Dockerfile`, `bot/Dockerfile`.

### Aiogram 3.x
- Telegram-интерфейс, обработчики, клавиатуры.
- Файлы: `bot/app/main.py`, `bot/app/handlers.py`, `bot/app/keyboards.py`.

### FSM (Finite State Machine)
- Пошаговая регистрация и сценарий поиска.
- Файлы: `bot/app/states.py`, `bot/app/handlers.py`.

### aiohttp
- HTTP-клиент бота к backend.
- Файл: `bot/app/http_requests.py`.

### asyncio (фоновые задачи)
- Периодический пересчёт рейтингов без блокировки API.
- Файлы: `backend/app/rating_updater.py`, `backend/app/main.py`.

### REST / клиент-серверная архитектура
- Бот не ходит в БД напрямую, только через backend API.
- Разделение: `bot/` (UI) ↔ `backend/` (бизнес-логика).

### Repository pattern
- CRUD и бизнес-операции вынесены из роутеров.
- Файл: `backend/app/repositories.py`.

---

## 6. Дополнительный функционал (сверх базовых требований)

1. **Реферальная система** — ссылка `t.me/bot?start=<id>`, учёт в рейтинге (`bot/app/handlers.py`, `repositories.py`).
2. **Детальная разбивка рейтинга** — API и вывод в боте по уровням 1–3.
3. **Match-уведомления** — при взаимном лайке оба пользователя получают сообщение.
4. **Фоновый rating updater** — автоматический пересчёт всех рейтингов каждые 5 минут.
5. **Фильтрация кандидатов** — по возрасту, полу, городу, интересам при поиске.
6. **Middleware логирования** — `bot/app/middlewares.py`.
7. **Health-check** — `GET /health` в backend.

---

## 7. Структура API (основное)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/users/register` | Регистрация (+ referal_id) |
| GET | `/api/users/{id}` | Профиль |
| PATCH | `/api/users/{id}` | Обновление анкеты |
| POST | `/api/interactions` | Лайк/пропуск (+ `is_match`) |
| GET | `/api/users/{id}/rating` | Итоговый рейтинг |
| GET | `/api/users/{id}/rating/details` | Разбивка по уровням |
| GET | `/api/users/{id}/search-candidate` | Следующая анкета для поиска |

---

## 8. Запуск

```bash
docker compose up --build
```

Backend: `http://localhost:8000`  
Документация API: `http://localhost:8000/docs`

---

## 9. Итог

Проект покрывает все 4 этапа: от инфраструктуры и регистрации до ранжирования, фонового обновления рейтинга и пользовательских уведомлений о match.  
Трёхуровневая модель рейтинга реализована с учётом минимум одного критерия из каждого уровня: первичный (анкета), поведенческий (лайки/пропуски/матчи/активность), комбинированный (весовая модель + рефералы).
