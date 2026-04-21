from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.scoring.player_score import LANES  # noqa: E402

ROLE_TEMPLATES = [
    ["TOP"],
    ["JUNGLE"],
    ["MID"],
    ["ADC"],
    ["SUPPORT"],
    ["TOP", "JUNGLE"],
    ["JUNGLE", "MID"],
    ["MID", "ADC"],
    ["ADC", "SUPPORT"],
    ["TOP", "MID"],
    ["JUNGLE", "SUPPORT"],
    ["TOP", "SUPPORT"],
    ["MID", "SUPPORT"],
    ["TOP", "ADC"],
    ["JUNGLE", "ADC"],
]

BASE_NAMES = [
    "Avery", "Blake", "Casey", "Drew", "Emerson", "Finley", "Gray", "Harper",
    "Indigo", "Jules", "Kai", "Logan", "Morgan", "Nova", "Oakley", "Parker",
    "Quinn", "Reese", "Sawyer", "Taylor", "Uma", "Vale", "Winter", "Xen",
    "Yael", "Zion", "Ash", "Briar", "Cove", "Dakota", "Echo", "Fable",
]


def build_players_table(metadata: sa.MetaData) -> sa.Table:
    return sa.Table(
        "players",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("discord_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("riot_id", sa.String(64)),
        sa.Column("puuid", sa.String(128)),
        sa.Column("summoner_id", sa.String(128)),
        sa.Column("roles", sa.JSON, nullable=False),
        sa.Column("role_preferences", sa.JSON, nullable=False),
        sa.Column("mmr", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def generate_sample_players(
    count: int = 20,
    *,
    seed: int = 7,
    min_mmr: int = 350,
    max_mmr: int = 850,
) -> list[dict[str, Any]]:
    if count < len(LANES) * 2:
        raise ValueError("At least 10 players are required to cover a full 5v5 lobby.")

    rng = random.Random(seed)
    players: list[dict[str, Any]] = []

    for idx in range(count):
        base_name = BASE_NAMES[idx % len(BASE_NAMES)]
        suffix = idx // len(BASE_NAMES) + 1
        name = base_name if suffix == 1 else f"{base_name}{suffix}"
        roles = list(ROLE_TEMPLATES[idx % len(ROLE_TEMPLATES)])
        mmr = rng.randint(min_mmr, max_mmr)

        players.append(
            {
                "discord_id": 10_000_000_000_000_000 + idx,
                "name": name,
                "riot_id": f"{name}#NA1",
                "puuid": f"sample-puuid-{idx:03d}",
                "summoner_id": f"sample-summoner-{idx:03d}",
                "roles": roles,
                "role_preferences": roles,
                "mmr": mmr,
            }
        )

    return players


def get_database_url() -> str:
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing in .env")
    return database_url


def seed_database(players: list[dict[str, Any]], *, reset: bool = False) -> tuple[int, int]:
    metadata = sa.MetaData()
    players_table = build_players_table(metadata)
    engine = sa.create_engine(get_database_url(), future=True)

    metadata.create_all(engine)

    inserted = 0
    skipped = 0

    with engine.begin() as connection:
        if reset:
            connection.execute(sa.delete(players_table))

        existing_ids = set(connection.execute(sa.select(players_table.c.discord_id)).scalars())
        new_rows = []

        for player in players:
            if player["discord_id"] in existing_ids:
                skipped += 1
                continue
            new_rows.append(player)

        if new_rows:
            connection.execute(sa.insert(players_table), new_rows)
            inserted = len(new_rows)

    return inserted, skipped


def load_players_from_db(limit: int | None = None) -> list[dict[str, Any]]:
    metadata = sa.MetaData()
    players_table = build_players_table(metadata)
    engine = sa.create_engine(get_database_url(), future=True)
    metadata.create_all(engine)

    stmt = sa.select(
        players_table.c.discord_id,
        players_table.c.name,
        players_table.c.riot_id,
        players_table.c.puuid,
        players_table.c.summoner_id,
        players_table.c.roles,
        players_table.c.role_preferences,
        players_table.c.mmr,
    ).order_by(players_table.c.id.asc())

    if limit is not None:
        stmt = stmt.limit(limit)

    with engine.begin() as connection:
        rows = connection.execute(stmt).mappings().all()

    players: list[dict[str, Any]] = []
    for row in rows:
        roles = list(row["role_preferences"] or row["roles"] or [])
        players.append(
            {
                "id": row["discord_id"],
                "discord_id": row["discord_id"],
                "name": row["name"],
                "riot_id": row["riot_id"],
                "puuid": row["puuid"],
                "summoner_id": row["summoner_id"],
                "roles": list(row["roles"] or roles),
                "role_preferences": roles,
                "mmr": int(row["mmr"]),
            }
        )

    return players


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed the local players table with sample inhouse players.")
    parser.add_argument("--count", type=int, default=20, help="How many sample players to generate.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for deterministic sample data.")
    parser.add_argument("--min-mmr", type=int, default=350, help="Minimum sample MMR.")
    parser.add_argument("--max-mmr", type=int, default=850, help="Maximum sample MMR.")
    parser.add_argument("--reset", action="store_true", help="Delete existing players before inserting samples.")
    parser.add_argument("--dry-run", action="store_true", help="Print generated players instead of writing to the DB.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    players = generate_sample_players(
        args.count,
        seed=args.seed,
        min_mmr=args.min_mmr,
        max_mmr=args.max_mmr,
    )

    if args.dry_run:
        print(json.dumps(players, indent=2))
        return 0

    inserted, skipped = seed_database(players, reset=args.reset)
    print(f"Inserted {inserted} players into the database.")
    print(f"Skipped {skipped} existing players.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
