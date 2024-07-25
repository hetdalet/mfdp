# Сервис оценки загородных домов RealEstateEva

[Схема сервиса](https://drive.google.com/file/d/1OmwaMffi-zOBy3ro58Of_Yv1D5tlpLiH/view?usp=sharing).

[Репозиторий](https://github.com/hetdalet/mfdp_mp) с реализацией пайплайна обучения модели.

Основные компоненты сервиса:

1. Воркер с моделью (models/real_estate)
2. REST бэкэнд (app)
3. Диспетчер очередей (RabbitMQ)
4. СУБД (PostgreSQL)
5. Хранилище для временных данных (Redis)
6. Реверс-прокси (nginx)
7. Телеграм-бот (tg_bot)
8. WebUI (Streamlit)

Компоненты разворачиваются в отдельных контейнерах. Оркестрацией занимается Docker Compose.

Для запуска сервиса нужно перейти в директорию с файлом `docker-compose.yml` и выполнить команду `docker compose up`.

При этом рядом с `docker-compose.yml` должен быть `.env` файл со значениями для следующих переменных:

```
POSTGRES_DB_FILE
POSTGRES_USER_FILE
POSTGRES_PASSWORD_FILE
DB_HOST
DB_PORT
RABBITMQ_USER
RABBITMQ_PASSWORD
RABBITMQ_HOST
RABBITMQ_PORT
RABBITMQ_UI_PORT
RABBITMQ_DISK_FREE_LIMIT
REDIS_HOST
REDIS_PORT
APP_HOST
APP_PORT
STREAMLIT_SERVER_PORT
ALEMBIC_CONFIG
SECRETS_DIR
COOKIE_NAME
TG_API_TOKEN_FILE
TG_BOT_POLL_TIMEOUT
TG_BOT_POLL_MAX_RETRIES
```

В директории `app` должен быть файл `auth_secret_key.secret` с секретным ключом для создания и проверки JWT-токенов.

В директории `postgres` должны быть следующие файлы:

1. `db.secret` (название базы данных сервиса)
2. `user.secret` (пользователь с правами на запись в БД)
3. `password.secret` (пароль пользователя из п. 2)

В директории `tg_bot` должен быть файл `api_token.secret` с API-ключом для телеграм бота.



