from asyncpg import Connection, connect
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config_reader import config


engine = create_async_engine(url=config.SQLALCHEMY_DATABASE_URI, echo=True)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


async def check_connection() -> None:
    try:
        conn: Connection = await connect(
            host=config.POSTGRES_HOST,
            password=config.POSTGRES_PASSWORD,
            user=config.POSTGRES_USER,
            database=config.POSTGRES_DB,
        )
        await conn.execute("SELECT 1;")
        await conn.close()
    except Exception as exc:
        raise ConnectionError(
            f"\n\n\033[101mNo connection to PostgreSQL!\n{exc}\033[0m"
        )

    return None
