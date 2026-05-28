from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


class Database:
    client: AsyncIOMotorClient | None = None
    db = None


db = Database()


async def connect_to_mongo():
    mongo_uri = settings.MONGODB_URL
    db.client = AsyncIOMotorClient(mongo_uri)
    db.db = db.client[settings.DATABASE_NAME]
    await db.db["users"].create_index("email", unique=True)


async def close_mongo_connection():
    if db.client:
        db.client.close()
        db.client = None
        db.db = None


def get_db():
    return db.db
