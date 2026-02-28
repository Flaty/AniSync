# AniSync

REST API для трекинга аниме. Синхронизация с MyAnimeList через Jikan, персональные списки, каталог с фильтрами, рекомендации на основе жанровых предпочтений.

## Stack

Python 3.14 · FastAPI · SQLAlchemy async · Pydantic v2 · Alembic · Taskiq (ListQueueBroker) · Redis · PostgreSQL · httpx · tenacity · uv

## Features

**Auth** — JWT access-токен (15 мин) + refresh (7 дней). При логауте `jti` access-токена пишется в Redis blacklist с TTL на остаток жизни. Refresh-токены одноразовые — при каждом использовании ротируются.

**Tracker** — CRUD для списка аниме пользователя. Статусы: watching, completed, plan_to_watch, dropped, on_hold. Фильтрация по статусу из коробки.

**Catalog** — `GET /anime/` с фильтрами по жанру, статусу, сезону, году, минимальной оценке и поиску по названию. Пагинация offset/limit.

**Recommendations** — берёт топ-5 жанров из списка пользователя, находит аниме с этими жанрами которых ещё нет в списке, сортирует по score.

**Sync Engine** — cache-aside: сначала проверяем локальную БД, при промахе тянем из Jikan и сохраняем. Фоновая синхронизация через Taskiq — можно запустить синк одного тайтла или целого топа.

## Project structure

```
app/
├── api/            роуты (тонкие, без бизнес-логики)
├── services/       бизнес-логика
├── repositories/   доступ к данным (только SQLAlchemy запросы)
├── models/         ORM-модели
├── schemas/        Pydantic v2 request/response схемы
├── tasks/          Taskiq фоновые задачи
├── external/       HTTP-клиенты (Jikan)
└── utils/          jwt, security
```

## Getting started

```bash
# поднять всё
docker-compose -f docker-compose.dev.yml up

# накатить миграции (в отдельном терминале)
docker exec -it anisync_dev uv run alembic upgrade head
```

Worker для фоновых задач поднимается автоматически как отдельный сервис в docker-compose.

После `docker-compose down -v` миграции нужно накатить заново.

## Environment

Два `.env` файла: корневой (для Docker, hostnames `postgres`/`redis`, порты 5432/6379) и `app/.env` (для локальной разработки вне Docker, порты 5433/6380).

| Переменная | Обязательна | Описание |
|---|---|---|
| `DATABASE_URL` | да | PostgreSQL connection string |
| `REDIS_URL` | да | Redis connection string |
| `JWT_SECRET` | да | Секрет для подписи JWT. Без неё приложение упадёт при старте — это намеренно |

## API overview

### Auth — `/auth`

| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/register` | Регистрация |
| POST | `/auth/login` | Логин, возвращает access + refresh |
| POST | `/auth/logout` | Логаут, blacklist access-токена |
| POST | `/auth/refresh` | Ротация refresh-токена |

### Users — `/users`

| Метод | Путь | Описание |
|---|---|---|
| GET | `/users/me` | Текущий пользователь |
| GET | `/users/me/list` | Список аниме (фильтр `?status=watching`) |
| POST | `/users/me/list` | Добавить аниме в список |
| PATCH | `/users/me/list/{anime_id}` | Обновить запись |
| DELETE | `/users/me/list/{anime_id}` | Удалить из списка |
| GET | `/users/me/recommendations` | Рекомендации по жанрам |

### Anime — `/anime`

| Метод | Путь | Описание |
|---|---|---|
| GET | `/anime/` | Каталог с фильтрами |
| GET | `/anime/{anime_id}` | По внутреннему ID |
| GET | `/anime/mal/{mal_id}` | По MAL ID (cache-aside) |
| POST | `/anime/` | Создать вручную |

### Jikan proxy — `/anime/jikan`

| Метод | Путь | Описание |
|---|---|---|
| GET | `/anime/jikan/top` | Топ аниме из Jikan |
| GET | `/anime/jikan/search` | Поиск через Jikan |
| GET | `/anime/jikan/{mal_id}` | Детали из Jikan |

### Sync — `/anime/sync`

| Метод | Путь | Описание |
|---|---|---|
| POST | `/anime/sync/{mal_id}` | Фоновый синк одного тайтла |
| POST | `/anime/sync/top` | Фоновый синк топа |

## Implementation details

**Genres sync** атомарный: при обновлении аниме из Jikan удаляются все связи жанров и вставляются заново. Грубо, но надёжно.

**Refresh-токены** одноразовые. Хранятся в Redis как `refresh_token:{user_id}`. При каждом использовании старый удаляется и выпускается новый.

**Jikan rate limiter** — 3 запроса в секунду через `aiolimiter`. Retry на HTTP-ошибки через `tenacity` (5 попыток, exponential backoff).
