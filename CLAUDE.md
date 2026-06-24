# ZHOLAUSHY — Бэкенд (taxi-backend)

## Что это
FastAPI бэкенд для платформы ZHOLAUSHY — межгородские поездки, Актобе, Казахстан.
Два режима: InDriver-стиль (заявки пассажиров → отклики водителей) и готовые поездки.

## Стек
- FastAPI + asyncpg + AsyncSession
- PostgreSQL (БД: mezhgorod)
- JWT (python-jose, HS256), bcrypt (import bcrypt напрямую, НЕ passlib)
- Firebase FCM (push), MinIO (файлы)
- Venv: `venv\Scripts\activate` (cmd, не PowerShell)

## Критические детали
- `current_user` — dict → используй `.get("role")`, `.get("user_id")`
- CORS: `allow_origins=["*"]`, `allow_credentials=False` в main.py
- trip-requests роутер: prefix `/trip-requests` (ДЕФИС, не underscore)
- `payment_type` — Column(String), НЕ PostgreSQL Enum
- `extra_pickups` / `extra_destinations` — Column(Text), хранятся как JSON-строка
- register возвращает `{"message": "..."}`, НЕ токен — логин отдельно
- `TripOffer.trip_id` — nullable (Trip создаётся автоматически при accept_offer)

## Адресная модель
Все адреса хранятся как объекты `{address: str, entrance: str | None}`.

Поля в `trip_requests` и `bookings`:
```
pickup_address       VARCHAR
entrance             VARCHAR
extra_pickups        TEXT  ← JSON: [{address, entrance?}, ...]
destination_address  VARCHAR
destination_entrance VARCHAR
extra_destinations   TEXT  ← JSON: [{address, entrance?}, ...]
```

Pydantic: `ExtraAddress` в `app/schemas/trip_request.py`.
`field_validator` — backward-compat: обрабатывает и старые строки, и новые объекты.

## API эндпоинты

### Auth
- POST /api/v1/auth/register — {name, phone, password}
- POST /api/v1/auth/login — {phone, password} → {access_token}
- POST /api/v1/auth/admin/login?email=&password= → {access_token}

### Trip Requests (ДЕФИС в URL!)
- POST /api/v1/trip-requests/ — создать заявку (passenger)
- GET  /api/v1/trip-requests/ — открытые заявки (driver, ?route_id=)
- GET  /api/v1/trip-requests/my — мои заявки (passenger)
- PATCH /api/v1/trip-requests/{id} — редактировать заявку
- DELETE /api/v1/trip-requests/{id} — отменить заявку
- POST /api/v1/trip-requests/offers — откликнуться с ценой (driver)
- GET  /api/v1/trip-requests/{id}/offers — офферы на заявку (passenger)
- POST /api/v1/trip-requests/{id}/accept/{offer_id} — принять оффер (passenger)

### Trips
- GET  /api/v1/trips/ — список поездок (?my=true, ?route_id=)
- POST /api/v1/trips/ — создать поездку (driver, query params)
- GET  /api/v1/trips/my-offers — мои отклики с данными пассажира (driver)
- PATCH /api/v1/trips/{id}/complete — завершить поездку

### Bookings
- POST /api/v1/bookings/ — забронировать (passenger)
- GET  /api/v1/bookings/my — мои брони (passenger)
- GET  /api/v1/bookings/for-driver — пассажиры по моим поездкам (driver)
- DELETE /api/v1/bookings/{id} — отменить бронь

### Прочее
- GET/POST /api/v1/routes/
- GET /api/v1/admin/stats, GET /api/v1/admin/trips
- GET /api/v1/drivers/unverified, PATCH /api/v1/drivers/{id}/verify|reject
- GET /api/v1/settings/, PATCH /api/v1/settings/{key}

## Структура файлов
```
taxi-backend/
├── app/
│   ├── main.py                     # CORS: allow_origins=["*"], allow_credentials=False
│   ├── api/v1/
│   │   ├── auth.py
│   │   ├── trip_requests.py        # prefix /trip-requests (ДЕФИС!)
│   │   ├── trips.py                # my-offers возвращает все адреса пассажира
│   │   ├── bookings.py             # for-driver, my — все поля адресов
│   │   ├── admin.py, drivers.py, routes.py, ratings.py, settings.py
│   ├── models/
│   │   ├── trip_request.py         # TripRequest + TripOffer, все адресные поля
│   │   └── booking.py              # Booking, все адресные поля
│   ├── schemas/
│   │   └── trip_request.py         # ExtraAddress, TripRequestCreate, TripRequestOut
│   └── db/database.py              # НЕ трогать — только движок + get_db
├── add_destination_and_extra_pickups.py          # ✅ выполнена
├── add_destination_entrance_and_extra_destinations.py  # ✅ выполнена
└── docker-compose.yml
```

## Что сделать дальше (план)
- [ ] Push-уведомления: когда водитель откликается → уведомить пассажира
- [ ] Push-уведомления: когда пассажир принял оффер → уведомить водителя
- [ ] Экран активной поездки: пассажир видит данные водителя после accept
- [ ] История поездок: детали по тапу
- [ ] Рейтинг: пассажир оценивает водителя после завершения
- [ ] WebSocket: real-time обновления офферов
