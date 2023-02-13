from psycopg_pool import AsyncConnectionPool
from settings import settings


conninfo = f"dbname=docker user=docker password=docker host={settings.DB_HOST} port={settings.DB_PORT}"

pool = AsyncConnectionPool(conninfo, open=False)
