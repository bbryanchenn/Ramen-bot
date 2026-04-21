import asyncio
from pathlib import Path

from dotenv import load_dotenv

from apps.bot.client import LeagueBot
from apps.bot.utils.env import get_env

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


async def main() -> None:
    token = get_env("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is missing (set DISCORD_TOKEN or a supported secret alias)")

    bot = LeagueBot()
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())