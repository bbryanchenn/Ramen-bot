# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Ramen Bot is a Discord bot (discord.py) for running League of Legends inhouses. It handles lobby management, role/MMR-balanced team generation, Riot account linking, ready checks, and a suite of opt-in feature modules (betting, bounties, events, history, leaderboard, salt, titles, voting, etc.). State persists to JSON files under `data/`. There is also a stub FastAPI app at `apps/api/` referenced by `docker-compose.yml`, but the bot is the active surface.

## Commands

Run the bot (Windows, project root):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m apps.bot.main
```

`run.bat` is a shortcut that activates `.venv` and runs `python -m apps.bot.main`.

Tests use `unittest` (not pytest). The only test currently is the team builder smoke suite:

```powershell
python -m unittest scripts.test_team_builder -v
# single test:
python -m unittest scripts.test_team_builder.TeamBuilderSmokeTests.test_build_two_teams_returns_unique_players -v
```

Docker (runs bot + stub API + Postgres + Redis): `docker-compose up`. The bot service runs `python -m apps.bot.main`; only `DISCORD_TOKEN` and `RIOT_API_KEY` are required in `.env` for the bot itself.

## Architecture

### Extension auto-discovery (`apps/bot/client.py`)

`LeagueBot.setup_hook` loads cogs by scanning the filesystem on startup — there is no central registry. To add a new command surface:

- A top-level command: drop a `.py` in `apps/bot/commands/` exposing `async def setup(bot)`.
- A feature module: create `apps/bot/features/<name>/commands.py` with `async def setup(bot)`. The discovery rule is "directory under `features/` containing a `commands.py`."
- A fun/social command: drop a `.py` in `apps/bot/fun/`.

If `DISCORD_GUILD_ID` is set, slash commands are copied to that guild and synced immediately (instant on dev servers). Without it, they sync globally (~1 hour propagation).

### Lobby is the source of truth for players

`apps/bot/commands/lobby.py` (the `Lobby` cog) holds the in-memory `players: dict[int, dict]` keyed by Discord user ID. Other cogs reach into it via `self.bot.get_cog("Lobby").players` rather than re-reading storage — `apps/bot/commands/teams.py` is the canonical example. When adding features that need lobby roster data, follow that pattern instead of loading `data/players.json` directly.

Player dicts carry: `id`, `name`, `roles` (League lanes), `mmr`, `riot_id`, `puuid`, `summoner_id`, `ranked_entry`, `manual_rank`, `in_lobby`. Persistence goes through `apps/bot/utils/storage.py` (`load_players`/`save_players`), which coerces keys to `int` on load and back to `str` on save (JSON limitation).

### Team building

Two parallel scoring/lane modules exist. The active one is `core/scoring/` — `player_score.py` defines `LANES = ("TOP", "JUNGLE", "MID", "ADC", "SUPPORT")`, role normalization, and lane-fit penalties; `team_score.py` produces the `matchup_summary` weighted score (total MMR diff × 4 + lane gap sum × 1.25 + max lane diff × 2 + assignment penalty × 3). `apps/bot/utils/team_builder.py` is the entry point used by commands: `build_two_teams(players, tries=3000)` does randomized sampling + permutation search per side.

`core/builder/` exists in parallel (similar `LANES` constant, similar role utilities) and is imported by `apps/bot/commands/teams.py`. Treat `core/scoring/` as authoritative for new work; `core/builder/` is legacy still wired into the `/teams` command.

The `FILL` Discord role is expanded to all five lanes by `apps/bot/utils/roles.py:extract_player_roles`. Don't push `FILL` into player dicts — expand it at the boundary.

### Feature module conventions

Feature modules under `apps/bot/features/` follow a consistent shape: `commands.py` (the cog with `async def setup`), `service.py` (state mutation + JSON persistence), and optionally `views.py` (discord.py UI views). Each feature owns its own JSON file under `data/` (e.g. `bets.json`, `bounties.json`, `history.json`). State files are loaded/saved on every mutation — there is no in-memory cache layer, so don't introduce one without changing the read-modify-write pattern across all callers.

Cross-feature coupling does happen and is intentional: `Lobby` calls into `betting.service` so that joining/leaving a side updates `current_match` atomically. When a player leaves, `leave_sides(state, user_id)` must be called or betting state will reference ghost players.

Note the duplicate data directories: `data/` (root, the live one) and `apps/bot/features/data/` (older copies of bounties/events/history). The features read/write from `data/` at the project root — `apps/bot/features/data/` is stale and should not be the target of new writes.

### Riot integration

`core/riot/api.py` wraps Riot endpoints with `httpx.AsyncClient`. All Riot calls return `(payload, error_message)` tuples — the convention is to surface `error_message` to Discord ephemerally rather than raising. `fetch_rank_profile` chains the three calls (puuid → summoner → ranked entries) and returns a single dict with `ok`/`error`/`rank_unavailable` flags; prefer it over the lower-level functions.

`core/riot/mmr.py:entry_to_mmr` converts a ranked entry to the integer MMR stored on player dicts (tier base + division offset + clamped LP). The default for unranked is 500 and is hardcoded across multiple files (`player_score.DEFAULT_MMR`, `lobby.py`, `settings.py`); change all of them together if you change it.

### Environment variables

Read via `apps/bot/utils/env.py:get_env`, which falls back through `GITHUB_<NAME>`, `SECRET_<NAME>`, `GH_<NAME>` aliases (so the same code works in CI). Required: `DISCORD_TOKEN`, `RIOT_API_KEY`. Optional: `DISCORD_GUILD_ID` (instant slash-command sync), `RIOT_REGION` (default `americas`), `RIOT_PLATFORM` (default `na1`), `BLUE_VC_ID`/`RED_VC_ID` (auto-move targets).

### Hardcoded IDs to watch

`apps/bot/commands/teams.py` has hardcoded Blue/Red voice channel IDs (lines ~112). `apps/bot/features/banner_commit/commands.py` has a hardcoded `TARGET_CHANNEL_ID` and a `TRIGGER_KEY`. These are guild-specific and will need to be parameterized before deploying to a second server.
