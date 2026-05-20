import asyncio
import asyncpg
import os


db_host = os.environ.get("DB_HOST", "localhost")
db_user = os.environ.get("DB_USER", "lamisplus")
db_password = os.environ.get("DB_PASSWORD", "your_default_password")
db_port = os.environ.get("DB_PORT", "6432")

async def main():
    conn = await asyncpg.connect(
        host=db_host,
        port=db_port, 
        database="lamisplus_staging_dwh",
        user=db_user,
        password=db_password
    )
    result = await conn.fetch("SELECT NOW();")
    print(result)
    await conn.close()

asyncio.run(main())
