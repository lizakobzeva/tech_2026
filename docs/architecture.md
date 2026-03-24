# Architecture

## High-Level Design

Telegram Bot → Webhook (/webhook) → FastAPI Application

Слои приложения:

- Presentation: handlers, routers, keyboards, states
- Application: services, use cases, business logic
- Domain: models, schemas, entities
- Infrastructure: repositories, database, external clients

## Текущая структура

- `backend/app/` — FastAPI + бизнес-логика
- `bot/app/` — Aiogram бот (handlers, FSM, keyboards)
