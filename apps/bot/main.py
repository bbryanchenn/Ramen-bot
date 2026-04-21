import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from apps.bot.client import LeagueBot

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


async def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is missing in .env")

    bot = LeagueBot()
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())