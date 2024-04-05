import os

import redis.asyncio as redis
import motor

MongoClient = motor.MotorClient  # Just alias
RedisClient = redis.Redis  # Just alias


async def get_db_session() -> MongoClient:

    client: MongoClient = motor.MotorClient(os.getenv("MONGODB_URI"))
    await client.server_info()  # PING
    return client


async def get_cache_session() -> RedisClient:

    client: RedisClient = redis.Redis.from_url(os.getenv("REDIS_URI"))
    await client.ping()  # PING
    return client
