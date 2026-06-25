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
- POST /api/v1/auth/send-otp?phone= — отправить код (Flutter использует OTP, не password)
- POST /api/v1/auth/verify-otp?phone=&code=&name=&role= — войти/зарегистрировать
  - Новый пользователь без name → 400 "Новый пользователь — укажите имя"
  - `role` обновляет роль пользователя в БД при каждом входе (passenger/driver)
- GET  /api/v1/auth/me — данные текущего пользователя
- PATCH /api/v1/auth/me — обновить имя
- POST /api/v1/auth/admin/login?email=&password= → {access_token}

### Trip Requests (ДЕФИС в URL!)
- POST /api/v1/trip-requests/ — создать заявку (passenger)
- GET  /api/v1/trip-requests/ — открытые заявки (driver, ?route_id=)
- GET  /api/v1/trip-requests/my — мои заявки (passenger)
- PATCH /api/v1/trip-requests/{id} — редактировать заявку
- DELETE /api/v1/trip-requests/{id} — отменить заявку
- POST /api/v1/trip-requests/offers — откликнуться с ценой (driver, role='driver' required)
- GET  /api/v1/trip-requests/{id}/offers — офферы на заявку (passenger)
- POST /api/v1/trip-requests/{id}/accept/{offer_id} — принять оффер (passenger)
- DELETE /api/v1/trip-requests/offers/{offer_id} — отозвать отклик (driver)

### Trips
- GET  /api/v1/trips/ — список поездок (?my=true, ?route_id=)
- POST /api/v1/trips/ — создать поездку (driver, role='driver' required, query params)
- GET  /api/v1/trips/my-offers — мои отклики с данными пассажира (driver)
- PATCH /api/v1/trips/{id}/complete — завершить поездку → push пассажиру
- PATCH /api/v1/trips/{id}/cancel — отменить поездку → push пассажиру
- PATCH /api/v1/trips/{id}/departing — водитель выехал → push пассажиру
- PATCH /api/v1/trips/{id}/arrived — водитель подъехал → push пассажиру

### Bookings
- POST /api/v1/bookings/ — забронировать (passenger)
- GET  /api/v1/bookings/my — мои брони (passenger)
- GET  /api/v1/bookings/for-driver — пассажиры по моим поездкам (driver)
- DELETE /api/v1/bookings/{id} — отменить бронь

### Drivers (верификация)
- POST   /api/v1/drivers/profile — создать профиль водителя (query params, без проверки role)
- GET    /api/v1/drivers/profile — профиль текущего водителя
- PATCH  /api/v1/drivers/profile/vehicle — сменить машину (сбрасывает is_verified=False)
- GET    /api/v1/drivers/all — все водители (admin)
- GET    /api/v1/drivers/unverified — только неверифицированные (admin)
- PATCH  /api/v1/drivers/{id}/verify — одобрить (admin)
- PATCH  /api/v1/drivers/{id}/reject?reason=... — отклонить (admin)

### Прочее
- GET/POST /api/v1/routes/
- GET /api/v1/admin/stats, GET /api/v1/admin/trips
- GET /api/v1/settings/, PATCH /api/v1/settings/{key}

## DriverProfile модель
```
driver_profiles:
  user_id        FK → users.id
  car_brand      VARCHAR  (марка: Toyota)
  car_model      VARCHAR  (модель: Camry)
  car_year       INTEGER  (год)
  car_color      VARCHAR  (цвет)
  car_number     VARCHAR  (госномер: 123 ABC 02)
  is_verified    BOOLEAN  (false по умолчанию)
  rejection_reason VARCHAR nullable
  rating         FLOAT    (default 5.0)
  license_doc_url  VARCHAR nullable
  car_doc_url      VARCHAR nullable
```

## Утилиты
- `create_admin.py` — создаёт/обновляет admin-пользователя (email: admin@zholaushy.kz, пароль: Admin1234)

## Структура файлов
```
taxi-backend/
├── app/
│   ├── main.py                     # CORS: allow_origins=["*"], allow_credentials=False
│   ├── api/v1/
│   │   ├── auth.py                 # verify-otp принимает role, обновляет роль в БД
│   │   ├── trip_requests.py        # prefix /trip-requests (ДЕФИС!); push во всех ключевых событиях
│   │   ├── trips.py                # departing/arrived эндпоинты; push во всех событиях
│   │   ├── drivers.py              # GET /all, PATCH /profile/vehicle; без role-check на create
│   │   ├── bookings.py, admin.py, routes.py, ratings.py, settings.py
│   ├── models/
│   │   ├── driver_profile.py       # DriverProfile с is_verified, rejection_reason
│   │   ├── trip_request.py         # TripRequest + TripOffer
│   │   └── booking.py
│   ├── schemas/
│   │   ├── user.py                 # UserRegister принимает role (Optional)
│   │   └── trip_request.py         # ExtraAddress, TripRequestCreate, TripRequestOut
│   └── db/database.py
├── create_admin.py                 # upsert admin-пользователя
└── docker-compose.yml
```

## Push-уведомления ✅ (реализовано полностью)
- Водитель откликнулся → пассажиру
- Пассажир принял оффер → водителю
- Пассажир отклонил оффер → водителю
- Водитель отозвал отклик (до/после принятия) → пассажиру
- Пассажир отменил заявку → всем водителям с откликами
- Водитель отменил поездку → пассажиру
- Поездка завершена → пассажиру "Оцените поездку"
- Водитель нажал Выезжаю → пассажиру
- Водитель нажал Подъехал → пассажиру

## Что сделать дальше (план)
- [ ] Рейтинг: пассажир оценивает водителя после завершения (POST /api/v1/ratings/)
- [ ] Foreground push: FirebaseMessaging.onMessage → SnackBar в приложении
- [ ] Экран активной поездки (отдельный экран после принятия оффера)
- [ ] WebSocket: real-time обновления офферов
