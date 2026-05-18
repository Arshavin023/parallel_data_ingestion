import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=6432, 
        database="lamisplus_staging_dwh",
        user="lamisplus",
        password="FmALa9PYGQUfyjq"
    )
    result = await conn.fetch("SELECT NOW();")
    print(result)
    await conn.close()

asyncio.run(main())
