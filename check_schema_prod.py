import asyncio
import os
from sqlalchemy import create_engine, inspect

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mezhgorod"
).replace("postgresql+asyncpg://", "postgresql://")

from app.models.user import Base, User
from app.models.route import Route, RoutePrice
from app.models.trip import Trip
from app.models.booking import Booking
from app.models.driver_profile import DriverProfile
from app.models.agreement import Agreement
from app.models.rating import Rating
from app.models.fleet_profile import FleetProfile, FleetDriver
from app.models.payment import Payment
from app.models.trip_request import TripRequest, TripOffer
from app.models.settings import PlatformSettings


def main():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())

    missing_tables = []
    missing_columns = []

    for table_name, table in Base.metadata.tables.items():
        if table_name not in db_tables:
            missing_tables.append(table_name)
            continue
        db_columns = {c["name"] for c in inspector.get_columns(table_name)}
        for col in table.columns:
            if col.name not in db_columns:
                missing_columns.append((table_name, col.name, str(col.type)))

    if missing_tables:
        print("ОТСУТСТВУЮТ ТАБЛИЦЫ:")
        for t in missing_tables:
            print(f"  - {t}")
    else:
        print("Все таблицы на месте.")

    if missing_columns:
        print("\nОТСУТСТВУЮТ КОЛОНКИ:")
        for t, c, ty in missing_columns:
            print(f"  - {t}.{c} ({ty})")
    else:
        print("\nВсе колонки на месте.")


main()
