from __future__ import annotations

import asyncio

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.recap.service import (
    MIN_SHARED_PUUIDS,
    attach_recap_to_history,
    collect_team_puuids,
    find_inhouse_match,
    is_custom,
    summarize_match,
)
from apps.bot.utils.storage import load_players
from core.riot.api import get_match_by_id


INITIAL_DELAY_S = 90
POLL_INTERVAL_S = 60
MAX_POLLS = 10


def _champion_icon(champion_id: int | None) -> str | None:
    if not champion_id:
        return None
    return (
        "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/"
        f"default/v1/champion-icons/{int(champion_id)}.png"
    )


def _format_kda(p: dict) -> str:
    return f"{p['kills']}/{p['deaths']}/{p['assists']}"


def _resolve_name(guild: discord.Guild | None, row: dict) -> str:
    user_id = row.get("user_id")
    if user_id and guild is not None:
        member = guild.get_member(int(user_id))
        if member:
            return member.display_name
    if user_id:
        return f"<@{user_id}>"
    puuid = row.get("puuid") or ""
    return f"unlinked ({puuid[:6]})" if puuid else "unlinked"


def _format_side_block(rows: list[dict], guild: discord.Guild | None) -> str:
    if not rows:
        return "*no data*"
    rows_sorted = sorted(rows, key=lambda r: r["score"], reverse=True)
    lines = []
    for r in rows_sorted:
        champ = (r.get("champion") or "?")[:11]
        name = _resolve_name(guild, r)
        lines.append(
            f"`{champ:<11}` {_format_kda(r):>8} · {r['damage']:>6} dmg · ⭐{r['score']:>5} — {name}"
        )
    return "\n".join(lines)


def build_recap_embed(summary: dict, guild: discord.Guild | None) -> discord.Embed:
    winner = (summary.get("winner") or "").lower()
    color = discord.Color.blue() if winner == "blue" else discord.Color.red()

    duration = int(summary.get("duration_s", 0) or 0)
    duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "?"

    embed = discord.Embed(
        title=f"📜 Postgame Recap — {winner.title() or '?'} wins ({duration_str})",
        color=color,
    )

    blue_rows = [r for r in summary["participants"] if r["side"] == "blue"]
    red_rows = [r for r in summary["participants"] if r["side"] == "red"]

    embed.add_field(name="🔵 Blue", value=_format_side_block(blue_rows, guild), inline=False)
    embed.add_field(name="🔴 Red", value=_format_side_block(red_rows, guild), inline=False)

    mvp_id = summary.get("mvp_user_id")
    diff_id = summary.get("diff_user_id")
    mvp_row = next((r for r in summary["participants"] if r.get("user_id") == mvp_id), None)
    diff_row = next((r for r in summary["participants"] if r.get("user_id") == diff_id), None)

    mvp_label = _resolve_name(guild, mvp_row) if mvp_row else "—"
    diff_label = _resolve_name(guild, diff_row) if diff_row else "—"

    if mvp_row:
        mvp_label += f" ({mvp_row.get('champion', '?')})"
    if diff_row:
        diff_label += f" ({diff_row.get('champion', '?')})"

    embed.add_field(name="🏆 MVP", value=mvp_label, inline=True)
    embed.add_field(name="💩 Diff", value=diff_label, inline=True)

    if mvp_row and mvp_row.get("champion_id"):
        icon = _champion_icon(mvp_row["champion_id"])
        if icon:
            embed.set_thumbnail(url=icon)

    riot_match_id = summary.get("match_id")
    if riot_match_id:
        embed.set_footer(text=f"Riot match {riot_match_id}")

    return embed


def _apply_side_effects(summary: dict) -> None:
    try:
        attach_recap_to_history(summary)
    except Exception:
        pass

    try:
        from apps.bot.features.diffs.service import add_diff, add_mvp

        if summary.get("mvp_user_id"):
            add_mvp(int(summary["mvp_user_id"]))
        if summary.get("diff_user_id"):
            add_diff(int(summary["diff_user_id"]))
    except Exception:
        pass


async def _auto_recap_task(
    bot: commands.Bot,
    channel_id: int,
    blue_team: list[int],
    red_team: list[int],
    declared_winner: str,
) -> None:
    await asyncio.sleep(INITIAL_DELAY_S)

    channel = bot.get_channel(int(channel_id))
    if channel is None:
        return

    blue_puuids, red_puuids = collect_team_puuids(blue_team, red_team)
    inhouse_puuids = set(blue_puuids.keys()) | set(red_puuids.keys())

    if len(inhouse_puuids) < MIN_SHARED_PUUIDS:
        try:
            await channel.send(
                f"📜 Skipped postgame recap: only {len(inhouse_puuids)} linked Riot accounts "
                f"(need ≥{MIN_SHARED_PUUIDS}). Use `/recap match_id:<id>` to fetch manually."
            )
        except Exception:
            pass
        return

    last_error: str | None = None
    summary: dict | None = None

    for attempt in range(MAX_POLLS):
        try:
            match, error = await find_inhouse_match(list(inhouse_puuids), inhouse_puuids)
            if match is not None:
                summary = summarize_match(match, blue_puuids, red_puuids, declared_winner)
                break
            last_error = error
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"

        if attempt < MAX_POLLS - 1:
            await asyncio.sleep(POLL_INTERVAL_S)

    if summary is None:
        try:
            await channel.send(
                f"📜 Could not auto-fetch the postgame recap ({last_error or 'no match found'}). "
                "Use `/recap match_id:<id>` if you have the Riot match ID."
            )
        except Exception:
            pass
        return

    _apply_side_effects(summary)

    try:
        guild = getattr(channel, "guild", None)
        embed = build_recap_embed(summary, guild)
        await channel.send(embed=embed)
    except Exception:
        pass


def schedule_auto_recap(
    bot: commands.Bot,
    channel_id: int,
    blue_team: list[int],
    red_team: list[int],
    declared_winner: str,
) -> None:
    """Fire-and-forget auto recap. Safe to call from /winner."""
    blue_copy = [int(x) for x in blue_team]
    red_copy = [int(x) for x in red_team]
    asyncio.create_task(
        _auto_recap_task(bot, int(channel_id), blue_copy, red_copy, str(declared_winner))
    )


class Recap(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="recap", description="Fetch postgame recap from a Riot match ID")
    @app_commands.describe(match_id="Riot match ID, e.g. NA1_5012345678")
    async def recap(self, interaction: Interaction, match_id: str) -> None:
        await interaction.response.defer()

        match, error = await get_match_by_id(match_id.strip())
        if error or not match:
            await interaction.followup.send(
                f"Couldn't fetch match: {error or 'no data'}",
                ephemeral=True,
            )
            return

        if not is_custom(match):
            await interaction.followup.send(
                "That match isn't a custom game.",
                ephemeral=True,
            )
            return

        from apps.bot.features.betting.service import load_bets

        state = load_bets()
        cm = state.get("current_match", {}) or {}
        blue_puuids, red_puuids = collect_team_puuids(
            cm.get("blue_team", []) or [],
            cm.get("red_team", []) or [],
        )

        if not blue_puuids and not red_puuids:
            participants = (match.get("info", {}) or {}).get("participants", []) or []
            players = load_players()
            puuid_to_user = {
                str(p["puuid"]): int(uid)
                for uid, p in players.items()
                if p.get("puuid")
            }
            for part in participants:
                puuid = str(part.get("puuid", ""))
                if puuid not in puuid_to_user:
                    continue
                tid = int(part.get("teamId", 0))
                if tid == 100:
                    blue_puuids[puuid] = puuid_to_user[puuid]
                elif tid == 200:
                    red_puuids[puuid] = puuid_to_user[puuid]

        summary = summarize_match(match, blue_puuids, red_puuids)
        _apply_side_effects(summary)

        embed = build_recap_embed(summary, interaction.guild)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Recap(bot))
