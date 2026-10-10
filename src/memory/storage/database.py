from common.core.env import env
from psycopg_pool import ConnectionPool



def get_database_url() -> str:

    database_url = env.DATABASE_URL

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. Configure it in the project root .env file."
        )

    return database_url


_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:

    global _pool

    if _pool is None:
        _pool = ConnectionPool(
            conninfo=get_database_url(),
            min_size=1,
            max_size=5,
            open=False,
        )
        _pool.open()

    return _pool


def close_pool() -> None:

    global _pool

    if _pool is not None:
        _pool.close()
        _pool = None


def check_database_connection() -> dict[str, str]:

    pool = get_pool()

    with pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_user, current_database(), version()"
            )
            user, database, version = cursor.fetchone()

    return {
        "user": user,
        "database": database,
        "version": version,
    }