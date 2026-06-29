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
- `POST /auth/verify-otp` принимает `role` (passenger/driver) и обновляет роль пользователя в БД
- `TripOffer.trip_id` — nullable (Trip создаётся автоматически при accept_offer)
- `POST /trips/` проверяет `role == 'driver'` → роль обязательно должна быть выставлена правильно
- Docker контейнер БД: `taxi-backend-db-1` (НЕ `mezhgorod-db`)

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
- POST /api/v1/auth/register — {name, phone, password, role?} → {message, access_token}
- POST /api/v1/auth/send-otp?phone= — отправить код
- POST /api/v1/auth/verify-otp?phone=&code=&name=&role= — войти/зарегистрировать
- GET  /api/v1/auth/me — данные текущего пользователя
- PATCH /api/v1/auth/me — обновить имя
- POST /api/v1/auth/admin/login?email=&password= → {access_token}

### Trip Requests (ДЕФИС в URL!)
- POST /api/v1/trip-requests/ — создать заявку (passenger)
- GET  /api/v1/trip-requests/ — открытые заявки (driver, ?route_id=)
- GET  /api/v1/trip-requests/my — мои заявки (passenger); возвращает is_departed, is_arrived, booking_id
- PATCH /api/v1/trip-requests/{id} — редактировать заявку
- DELETE /api/v1/trip-requests/{id} — отменить (open И accepted статусы)
- POST /api/v1/trip-requests/offers — откликнуться (driver); списывает OFFER_PRICE (50₸) с баланса; 402 если нехватка
- GET  /api/v1/trip-requests/{id}/offers — офферы на заявку (passenger)
- POST /api/v1/trip-requests/{id}/accept/{offer_id} — принять оффер (passenger)
- DELETE /api/v1/trip-requests/{request_id}/offers/{offer_id} — пассажир отклоняет оффер
- DELETE /api/v1/trip-requests/offers/{offer_id} — водитель отзывает отклик

### Trips
- GET  /api/v1/trips/ — список поездок (?my=true, ?route_id=); возвращает is_departed, is_arrived
- POST /api/v1/trips/ — создать поездку (driver)
- GET  /api/v1/trips/my-offers — мои отклики с данными пассажира (driver)
- PATCH /api/v1/trips/{id}/complete — завершить поездку
- PATCH /api/v1/trips/{id}/cancel — отменить поездку
- PATCH /api/v1/trips/{id}/departing — водитель выехал → is_departed=True + push
- PATCH /api/v1/trips/{id}/arrived — водитель подъехал → is_arrived=True + push

### Bookings
- POST /api/v1/bookings/ — забронировать (passenger)
- GET  /api/v1/bookings/my — мои брони (passenger)
- GET  /api/v1/bookings/for-driver — пассажиры по моим поездкам (driver)
- DELETE /api/v1/bookings/{id} — отменить бронь

### Drivers
- POST   /api/v1/drivers/profile — создать профиль водителя (query params)
- GET    /api/v1/drivers/profile — профиль текущего водителя
- PATCH  /api/v1/drivers/profile/vehicle — сменить машину (сбрасывает is_verified=False)
- GET    /api/v1/drivers/balance — текущий баланс + цена оффера {balance, offer_price}
- POST   /api/v1/drivers/balance/topup?amount=&driver_id= — пополнить (только admin)
- GET    /api/v1/drivers/all — все водители (admin)
- GET    /api/v1/drivers/unverified — неверифицированные (admin)
- PATCH  /api/v1/drivers/{id}/verify — одобрить (admin)
- PATCH  /api/v1/drivers/{id}/reject?reason= — отклонить (admin)

### Прочее
- GET/POST /api/v1/routes/
- GET /api/v1/admin/stats, GET /api/v1/admin/trips
- GET /api/v1/settings/, PATCH /api/v1/settings/{key}
- POST /api/v1/ratings/ — оценить (passenger→driver или driver→passenger)
- GET  /api/v1/ratings/received — полученные оценки

## Модели БД

### DriverProfile (driver_profiles)
```
user_id        FK → users.id (unique)
car_brand/model/year/color/number  VARCHAR/INTEGER
is_verified    BOOLEAN (default False)
rejection_reason VARCHAR nullable
rating         FLOAT (default 5.0)
balance        NUMERIC(10,2) (default 0) ← добавлено для монетизации
created_at     DATETIME
```

### Trip (trips)
```
driver_id, route_id, departure_time, seats_total, seats_available
price_per_seat  NUMERIC(10,2)
status          ENUM (active/completed/cancelled)
is_departed     BOOLEAN (default False) ← водитель выехал
is_arrived      BOOLEAN (default False) ← водитель подъехал
created_at
```

### TripOffer (trip_offers)
```
request_id  FK → trip_requests.id
trip_id     FK → trips.id (nullable)
driver_id   FK → users.id
price_per_seat NUMERIC(10,2)
```

## Монетизация
- `OFFER_PRICE = 50` (₸) — константа в `app/models/driver_profile.py`
- При каждом отклике (POST /trip-requests/offers) списывается OFFER_PRICE с баланса водителя
- 402 ошибка если баланс < OFFER_PRICE
- Пополнение только через admin: POST /drivers/balance/topup

## Push-уведомления ✅
Все события покрыты: новый отклик, принятие/отклонение оффера, отзыв оффера,
отмена заявки пассажиром, отмена/завершение поездки, Выехал, Подъехал.
- `firebase-key.json` — НЕ в git
- VAPID: `BPm0kWEEazAULngzb2ysuswI0QVl_H2Y3DTJ-dOSRL0tzp_EV1y87vn5UReefU5ideVvYd6IiMQ9BT3GDkjX0Wk`

## Структура файлов
```
taxi-backend/
├── app/
│   ├── main.py
│   ├── api/v1/
│   │   ├── auth.py
│   │   ├── trip_requests.py   # /trip-requests (ДЕФИС); списание баланса при оффере
│   │   ├── trips.py           # departing/arrived → is_departed/is_arrived в БД
│   │   ├── drivers.py         # balance + topup эндпоинты
│   │   ├── bookings.py, admin.py, routes.py, ratings.py, settings.py
│   ├── models/
│   │   ├── driver_profile.py  # balance NUMERIC + OFFER_PRICE=50 константа
│   │   ├── trip.py            # is_departed, is_arrived Boolean колонки
│   │   ├── trip_request.py    # TripRequest + TripOffer
│   │   └── booking.py
│   └── db/database.py
├── create_admin.py            # admin@zholaushy.kz / Admin1234
└── docker-compose.yml
```

## Утилиты
- `create_admin.py` — создаёт/обновляет admin-пользователя (email: admin@zholaushy.kz, пароль: Admin1234)

## Что НЕ сделано (после МВП)
- [ ] WebSocket — real-time обновления вместо поллинга
- [ ] Возврат баланса при отзыве оффера водителем
- [ ] Реальная интеграция с Kaspi/картой для пополнения баланса
- [ ] Admin-панель: фильтры, экспорт CSV, детальная страница водителя
- [ ] Настраиваемая цена оффера через settings (сейчас hardcoded 50₸)
