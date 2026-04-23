# Ramen Bot

Ramen Bot is a Discord bot for running League of Legends inhouses/customs.
It supports lobby management, team generation, Riot linking, ready checks, and extra community features like betting, bounties, and leaderboards.

## Features

- Slash-command based workflow for customs
- Lobby join/leave and live lobby view
- Automatic team generation using role + MMR balancing
- Riot account linking and ranked profile lookup
- Ready check + optional auto-move into Blue/Red voice channels
- Optional feature modules (betting, bounties, events, titles, and more)

## Requirements

- Python 3.10+
- A Discord bot application with the proper bot permissions

## Quick Start

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Create a `.env` file in the project root.
5. Run the bot.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m apps.bot.main
```

### Windows (cmd)

```bat
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python -m apps.bot.main
```

## Environment Variables

Create `.env` in the repository root:

```env
DISCORD_TOKEN=your_discord_bot_token

# Riot API (required for /linkriot and rank lookups)
RIOT_API_KEY=your_riot_api_key
RIOT_REGION=americas
RIOT_PLATFORM=na1

# Optional: used by /readymove
BLUE_VC_ID=123456789012345678
RED_VC_ID=987654321098765432
```

Notes:

- `DISCORD_TOKEN` is required to start the bot.
- `RIOT_API_KEY` is required for Riot account/rank features.
- `BLUE_VC_ID` and `RED_VC_ID` are optional, but needed for reliable voice auto-move.

## Customs Match Flow (Recommended)

Use these slash commands in order:

1. `/join` for all players entering lobby
2. `/lobby` to confirm who is in
3. Optional: `/linkriot riot_id:gameName#tagLine`
4. Optional: `/setmmr user:@player mmr:number` for manual MMR correction
5. `/teams` to generate Blue/Red teams
6. `/readycheck` to start readiness confirmation
7. `/readystatus` to monitor progress
8. `/readymove` to move ready players into Blue/Red voice channels

Useful reset commands:

- `/leave` for an individual player
- `/endreadycheck` to cancel active ready check
- `/clearlobby` to reset the lobby for a new game

## Help Command

- `/help` shows all available commands
- `/help topic:customs_setup` shows the step-by-step customs setup guide

## Project Layout

- `apps/bot/commands`: Core slash commands
- `apps/bot/features`: Feature modules and feature-specific commands
- `core/builder`: Team builder and balancing logic
- `core/riot`: Riot API integration
- `data`: JSON data storage files

## Notes

- Keep `.env` private and never commit it.
- `.venv` and `__pycache__` should stay gitignored.
- This bot currently stores some state in JSON files under `data/`.