import logging
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Motor client placeholder
client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    """Return the initialized MongoDB client.

    Raises:
        RuntimeError: If the client has not been initialized.
    """
    if client is None:
        raise RuntimeError("MongoDB client not initialized. Call connect_to_mongo() first.")
    return client


def get_db():
    """Retrieve the specific database defined in settings."""
    return get_client()[settings.DATABASE_NAME]


async def connect_to_mongo() -> None:
    """Initialize the Motor client and ensure required indexes exist.

    This function is intended to be called on FastAPI startup.
    """
    global client
    if client is None:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        try:
            # Simple ping to verify connection
            await client.admin.command("ping")
            logger.info("Successfully connected to MongoDB.")
        except Exception as exc:
            logger.error(f"MongoDB connection failed: {exc}")
            raise
        # Create indexes
        db = get_db()
        await db["users"].create_index("email", unique=True)
        await db["screen_ad_mappings"].create_index("screen_id", unique=True)
        logger.info("MongoDB indexes ensured.")


async def close_mongo_connection() -> None:
    """Close the Motor client connection on application shutdown."""
    global client
    if client:
        client.close()
        client = None
        logger.info("MongoDB connection closed.")
