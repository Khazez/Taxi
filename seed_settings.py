import asyncio
from app.db.database import AsyncSessionLocal
from app.models.settings import PlatformSettings

async def seed():
    async with AsyncSessionLocal() as db:
        setting = PlatformSettings(key="cancellation_fee_percent", value="20")
        db.add(setting)
        await db.commit()
        print("Done!")

asyncio.run(seed())