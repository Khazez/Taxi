# ZHOLAUSHY — Project Context for Claude

## Что это за проект

Мобильная платформа для заказа межгородских поездок (аналог Яндекс.Межгород / InDriver).
Запуск: западный Казахстан, город Актобе.
Название: **ZHOLAUSHY** (может измениться).

## Роли пользователей

- **passenger** — пассажир
- **driver** — водитель
- **fleet** — таксопарк (может добавлять водителей под собой)
- **admin** — диспетчер / администратор

## Стек технологий

| Слой | Технология |
|------|-----------|
| Мобильное приложение | Flutter (iOS + Android) |
| Веб-панель (диспетчер) | Next.js / React |
| Бэкенд API | FastAPI (Python) |
| База данных | PostgreSQL |
| Кэш / real-time | Redis |
| Хранилище файлов | MinIO |
| Аутентификация | JWT (access + refresh tokens) |
| Push-уведомления | Firebase Cloud Messaging |

## Архитектура

```
Flutter (Пассажир)   Flutter (Водитель)   Next.js (Диспетчер)
        └──────────────────┬──────────────────────┘
                      REST API + WebSocket
                           │
                    FastAPI Backend
               ┌───────────┼────────────┐
           PostgreSQL     Redis        MinIO
           (основная БД)  (кэш,сессии) (файлы)
```

## Бизнес-логика (два режима для пассажира и водителя)

### Режим 1 — Попутки (InDriver-стиль):
- Пассажир создаёт заявку: откуда → куда, дата, кол-во мест
- Водители видят заявки и откликаются с ценой (TripOffer)
- Пассажир выбирает водителя → поездка подтверждена

### Режим 2 — Готовые поездки:
- Водитель создаёт поездку: маршрут, дата, цена, места
- Пассажир видит список и бронирует место (Booking)

### Пассажир (полный флоу):
1. Регистрируется (POST /api/v1/auth/register → {name, phone, password})
2. Логинится (POST /api/v1/auth/login → {phone, password} → access_token)
3. Видит два таба: "Попутки" и "Поездки"
4. Создаёт заявку или бронирует готовую поездку
5. Оплачивает (Kaspi / карта / наличные)
6. Получает push-уведомление
7. Если отменяет за < 1 часа — штраф (% из PlatformSettings)

### Водитель:
1. Регистрируется → загружает документы → верификация у admin
2. Создаёт поездку (Trip) или откликается на заявки пассажиров (TripOffer)
3. Отмечает поездку завершённой
4. Получает рейтинг

### Диспетчер (веб-панель):
1. Входит по email + пароль (POST /api/v1/auth/admin/login?email=...&password=...)
2. Верифицирует водителей
3. Управляет маршрутами и ценами
4. Управляет настройками платформы

## Важные технические детали

- **bcrypt**: используем `import bcrypt` напрямую, НЕ через passlib
- **Async**: create_async_engine + AsyncSession + asyncpg
- **JWT**: python-jose, алгоритм HS256
- **Venv активация**: venv\Scripts\activate (cmd, не PowerShell)
- **CORS**: allow_origins=["*"], allow_credentials=False в main.py
- **settings.py**: current_user — dict, проверять через current_user.get("role")
- **database.py**: НЕ класть seed-скрипты сюда — только движок и get_db
- **register endpoint**: возвращает {"message": "Пользователь создан"} — НЕ токен!
  После регистрации нужно отдельно вызвать /auth/login чтобы получить токен.
- **trip-requests**: эндпоинт пишется через ДЕФИС: /api/v1/trip-requests/ (не trip_requests)
- **Flutter Web**: использовать dart:html window.localStorage вместо shared_preferences
  (shared_preferences вызывает MissingPluginException на Flutter Web)
- **Dio на Flutter Web**: всегда указывать явно Content-Type: application/json в Options

## API эндпоинты (проверено в Swagger)

### Auth
- POST /api/v1/auth/register — {name, phone, password} → {"message": "Пользователь создан"}
- POST /api/v1/auth/login — {phone, password} → {"access_token": "..."}
- POST /api/v1/auth/admin/login?email=...&password=... → {"access_token": "..."}

### Routes
- GET /api/v1/routes/ — список маршрутов
- POST /api/v1/routes/ — создать маршрут (admin)

### Trips
- GET /api/v1/trips/ — список поездок (требует auth, возможно query params)
- POST /api/v1/trips/ — создать поездку (driver)

### Trip Requests (InDriver-стиль) — ДЕФИС!
- POST /api/v1/trip-requests/ — создать заявку пассажира
- GET /api/v1/trip-requests/ — получить открытые заявки
- POST /api/v1/trip-requests/offers — водитель откликается
- GET /api/v1/trip-requests/{request_id}/offers — офферы на заявку
- POST /api/v1/trip-requests/{request_id}/accept/{offer_id} — принять оффер

### Bookings
- POST /api/v1/bookings/ — забронировать место в поездке
- DELETE /api/v1/bookings/{booking_id} — отменить бронь

### Drivers
- GET /api/v1/drivers/unverified — неверифицированные водители
- PATCH /api/v1/drivers/{id}/verify — верифицировать
- PATCH /api/v1/drivers/{id}/reject — отклонить

### Admin
- GET /api/v1/admin/stats — статистика
- GET /api/v1/admin/trips — все поездки

### Settings
- GET /api/v1/settings/ — настройки платформы
- PATCH /api/v1/settings/{key} — изменить настройку

## Переменные окружения (.env)

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mezhgorod
REDIS_URL=redis://localhost:6379
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
FIREBASE_CREDENTIALS_PATH=./firebase-key.json
CANCELLATION_FEE_PERCENT=20
```

## Адресная модель (важно!)

Все адреса хранятся в виде объектов `{address: str, entrance: str | None}`.
Поля в `trip_requests` и `bookings`:
- `pickup_address` / `entrance` — главный адрес подачи
- `extra_pickups` — TEXT (JSON): `[{address, entrance?}, ...]`
- `destination_address` / `destination_entrance` — адрес назначения
- `extra_destinations` — TEXT (JSON): `[{address, entrance?}, ...]`

Pydantic: класс `ExtraAddress` в `app/schemas/trip_request.py`.
Backward-compat: field_validator обрабатывает как старые строки, так и новые объекты.

## Текущий статус

### Бэкенд ✅
- [x] FastAPI + PostgreSQL + asyncpg
- [x] Auth: регистрация, JWT, OTP, admin/login
- [x] Models: User, Trip, TripRequest, TripOffer, Booking, Route, Payment, Rating
- [x] Полные адреса: pickup/destination + entrance + extra_pickups/extra_destinations
- [x] trip_requests.py: create, list, my, update, cancel, offer, accept_offer
- [x] bookings.py: create, my, for-driver (все поля адресов)
- [x] trips.py: my-offers (все адреса пассажира + passenger_name)
- [x] MinIO, Firebase, Docker-compose
- [x] admin.py, settings.py, ratings.py

### Веб-панель (taxi-admin) ✅
- [x] Логин, дашборд, водители (верификация), маршруты, поездки, настройки

### Flutter — пассажир (zholaushy_passenger) ✅
- [x] GoRouter, dart:html localStorage, token = 'token'
- [x] Таб Поездки: создать заявку, список активных заявок/броней, экран офферов
- [x] Таб Попутки: поиск поездок водителей, бронирование
- [x] Форма заявки/брони: адрес А + подъезд, доп. адреса подачи (_AddrPair), адрес Б + подъезд, доп. точки назначения
- [x] _AddrPair класс: пара контроллеров {address, entrance} для списков адресов
- [x] Принятие оффера: bottom sheet подтверждения адреса перед accept
- [x] История поездок, профиль, поддержка, настройки

### Flutter — водитель (zholaushy_driver) ✅
- [x] GoRouter, dart:html localStorage, token = 'driver_token'
- [x] Таб Заявки: открытые заявки пассажиров, фильтр по маршруту, откликнуться с ценой
  - Развёрнутая карточка: все адреса А/Б с метками и подъездами
- [x] Таб Мои поездки: создание поездки, список своих поездок
  - _PassengerRow: все адреса пассажира (подача + назначение + доп.)
- [x] Таб Отклики: _OfferCard с данными пассажира и всеми адресами
  - Фильтрация: отменённые заявки (request_status=cancelled) не показываются

### Важные детали Flutter
- token ключи: `token` (пассажир), `driver_token` (водитель)
- Dio: всегда Content-Type: application/json в Options для POST/PATCH
- extra_pickups/extra_destinations: list of `{address, entrance?}` — НЕ plain strings
- _addrLine() — top-level функция в driver/home_screen.dart для форматирования адреса из Map

## Структура файлов

```
taxi-backend/                 # C:\Users\KhazezB\taxi-backend
├── app/
│   ├── main.py               # CORS: allow_origins=["*"], allow_credentials=False
│   ├── api/v1/
│   │   ├── auth.py           # register → message, login → token, OTP
│   │   ├── trip_requests.py  # prefix /trip-requests (ДЕФИС!)
│   │   ├── trips.py          # /trips/my-offers возвращает все адреса
│   │   ├── bookings.py       # /bookings/for-driver, /bookings/my
│   │   ├── admin.py, ratings.py, drivers.py, routes.py, settings.py
│   ├── models/               # booking.py, trip_request.py — все адресные поля
│   ├── schemas/trip_request.py  # ExtraAddress, TripRequestOut, field_validator
│   └── db/database.py
├── add_destination_and_extra_pickups.py       # миграция (выполнена)
├── add_destination_entrance_and_extra_destinations.py  # миграция (выполнена)
└── docker-compose.yml

zholaushy_passenger/          # C:\Users\KhazezB\zholaushy_passenger
└── lib/screens/home_screen.dart  # _AddrPair, все формы, _OffersScreen

zholaushy_driver/             # C:\Users\KhazezB\zholaushy_driver
└── lib/screens/home_screen.dart  # _addrLine(), _PassengerRow, _OfferCard, _PassengerRequestCard
```

## Как использовать этот файл

При каждом новом чате с Claude — прикрепляй этот файл.
Это даёт Claude полный контекст без повторных объяснений.
