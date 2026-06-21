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

## Текущий статус

### Бэкенд ✅ (полностью готов)
- [x] FastAPI + PostgreSQL + Alembic
- [x] Auth: регистрация, JWT, admin/login
- [x] Все модели и эндпоинты
- [x] MinIO, Firebase, Docker-compose
- [x] admin.py: /admin/stats и /admin/trips

### Веб-панель (taxi-admin) ✅ (полностью готова)
- [x] Логин: app/login/page.tsx
- [x] Дашборд: app/dashboard/page.tsx (реальная статистика)
- [x] Водители: app/dashboard/drivers/page.tsx (верификация)
- [x] Маршруты: app/dashboard/routes/page.tsx
- [x] Поездки: app/dashboard/trips/page.tsx
- [x] Настройки: app/dashboard/settings/page.tsx

### Flutter — приложение пассажира (zholaushy_passenger)
- [x] Проект создан: C:\Users\KhazezB\zholaushy_passenger
- [x] Пакеты: dio 5.9.2, go_router 17.3.0
- [x] main.dart — GoRouter, dart:html localStorage для токена
- [x] screens/login_screen.dart — логин через /auth/login
- [x] screens/register_screen.dart — регистрация + автологин
- [x] screens/home_screen.dart — два таба: Попутки + Поездки
- [x] Создать заявку: выпадающий список маршрутов + дата + время ✅
- [x] GET /api/v1/trip-requests/ — работает (route_id теперь необязательный)
- [ ] Экран деталей поездки + бронирование
- [ ] Профиль пользователя
- [ ] История поездок
- [ ] Уведомления об офферах от водителей

### Важные исправления (сессия 2026-06-21)
- **trip_requests.py**: current_user — dict, использовать .get("user_id") и .get("role")
- **GET /trip-requests/**: route_id сделан необязательным параметром
- **CORS**: allow_origins=["*"], allow_credentials=False (Flutter работает на другом порту)
- **Маршруты в БД**: добавлены тестовые маршруты (Актобе → Актау, Уральск, Алматы, Астана, Атырау)

### Flutter — приложение водителя
- [ ] Не начато

## Структура файлов

```
taxi-backend/                 # https://github.com/Khazez/taxi
├── app/
│   ├── main.py               # CORS: allow_origins=["*"], allow_credentials=False
│   ├── api/v1/
│   │   ├── auth.py           # register возвращает message, НЕ токен
│   │   ├── trip_requests.py  # роутер с prefix /trip-requests (дефис!)
│   │   ├── admin.py          # создан вручную
│   │   └── settings.py       # current_user.get("role")
│   └── db/database.py        # НЕ трогать, только движок + get_db
├── insert_setting.py         # psycopg2 seed настроек
└── docker-compose.yml

taxi-admin/                   # https://github.com/Khazez/taxi_admin
└── app/dashboard/            # все страницы готовы

zholaushy_passenger/          # Flutter пассажир
└── lib/
    ├── main.dart
    └── screens/
        ├── login_screen.dart
        ├── register_screen.dart
        └── home_screen.dart
```

## Как использовать этот файл

При каждом новом чате с Claude — прикрепляй этот файл.
Это даёт Claude полный контекст без повторных объяснений.
