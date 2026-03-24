# Database Schema

## Используемые модели (SQLAlchemy 2.0)

### 1. users

- **telegram_id** — BIGINT, PRIMARY KEY
- **age** — INT
- **gender** — String
- **interests** — String
- **city** — String
- **age_preferences** — INT
- **gender_preferences** — String
- **interests_preferences** — String
- **city_preferences** — String
- **last_activity** — DateTime
- **referal_id** — BIGINT, FOREIGN KEY → users.telegram_id (nullable)

### 2. user_interactions

- **id** — UUID, PRIMARY KEY (генерируется `uuid_generate_v4()`)
- **requester_telegram_id** — BIGINT, FOREIGN KEY → users.telegram_id
- **responser_telegram_id** — BIGINT, FOREIGN KEY → users.telegram_id
- **is_like** — BOOLEAN
- **is_checked** — BOOLEAN (nullable, используется только для лайков)
- **UniqueConstraint** на (`requester_telegram_id`, `responser_telegram_id`)

### 3. user_ratings

- **telegram_id** — BIGINT, PRIMARY KEY, FOREIGN KEY → users.telegram_id
- **rating** — FLOAT, по умолчанию 0

## Особенности схемы

- Основной ключ пользователей — `telegram_id` (BIGINT)
- Взаимодействия (лайки/дизлайки) хранятся в одной таблице `user_interactions`
- Один пользователь может взаимодействовать с другим только один раз (UniqueConstraint)
- Рейтинг пользователя вынесен в отдельную таблицу `user_ratings`
