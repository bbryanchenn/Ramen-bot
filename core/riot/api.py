from __future__ import annotations

from urllib.parse import quote

import httpx

from apps.bot.utils.env import get_env


def _get_env() -> tuple[str, str, str]:
    api_key = get_env("RIOT_API_KEY")
    region = get_env("RIOT_REGION", "americas") or "americas"
    platform = get_env("RIOT_PLATFORM", "na1") or "na1"

    if not api_key:
        raise RuntimeError("RIOT_API_KEY is missing (set RIOT_API_KEY or a supported secret alias)")

    return api_key, region, platform


def _headers() -> dict[str, str]:
    api_key, _, _ = _get_env()
    return {"X-Riot-Token": api_key}


async def _request_json(label: str, url: str) -> tuple[dict | list | None, str | None]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=_headers())
    except httpx.HTTPError as exc:
        return None, f"Could not reach Riot: {exc}"

    if response.status_code == 200:
        try:
            return response.json(), None
        except ValueError:
            return None, "Riot returned invalid JSON."

    if response.status_code == 401:
        return None, "Riot API key is invalid."
    if response.status_code == 403:
        return None, "Riot API key is expired or not allowed for this endpoint."
    if response.status_code == 404:
        return None, "not_found"
    if response.status_code == 429:
        return None, "Riot rate limit exceeded. Please try again in a moment."

    return None, f"Riot request failed with status {response.status_code}."


async def get_puuid(game_name: str, tag_line: str) -> tuple[str | None, str | None]:
    _, region, _ = _get_env()
    safe_game_name = quote(game_name.strip(), safe="")
    safe_tag_line = quote(tag_line.strip(), safe="")
    url = (
        f"https://{region}.api.riotgames.com/riot/account/v1/accounts/"
        f"by-riot-id/{safe_game_name}/{safe_tag_line}"
    )

    payload, error = await _request_json("get_puuid", url)
    if error:
        if error == "not_found":
            return None, "Could not find a Riot account for that Riot ID."
        return None, error

    if not isinstance(payload, dict):
        return None, "Riot account lookup returned an unexpected payload."

    puuid = payload.get("puuid")
    if not puuid:
        return None, "Riot account lookup succeeded, but no PUUID was returned."

    return str(puuid), None


async def get_summoner_by_puuid(puuid: str) -> tuple[dict | None, str | None]:
    _, _, platform = _get_env()
    url = f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"

    payload, error = await _request_json("get_summoner_by_puuid", url)
    if error:
        if error == "not_found":
            return None, (
                f"Riot account exists, but no League summoner profile was found on platform "
                f"{platform}."
            )
        return None, error

    if not isinstance(payload, dict):
        return None, "Summoner lookup returned an unexpected payload."

    return payload, None


async def get_ranked_entries_by_summoner_id(summoner_id: str) -> tuple[list[dict] | None, str | None]:
    _, _, platform = _get_env()
    url = f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"

    payload, error = await _request_json("get_ranked_entries_by_summoner_id", url)
    if error:
        if error == "not_found":
            return [], None
        return None, error

    if not isinstance(payload, list):
        return None, "Ranked lookup returned an unexpected payload."

    return payload, None


async def fetch_rank_profile(game_name: str, tag_line: str) -> dict:
    puuid, error = await get_puuid(game_name, tag_line)
    if error:
        return {
            "ok": False,
            "error": error,
            "rank_unavailable": False,
            "puuid": None,
            "summoner_id": None,
            "summoner_name": None,
            "solo": None,
            "flex": None,
            "best": None,
        }

    if not puuid:
        return {
            "ok": False,
            "error": "Could not find Riot account for that Riot ID.",
            "rank_unavailable": False,
            "puuid": None,
            "summoner_id": None,
            "summoner_name": None,
            "solo": None,
            "flex": None,
            "best": None,
        }

    summoner, error = await get_summoner_by_puuid(puuid)
    if error:
        return {
            "ok": False,
            "error": error,
            "rank_unavailable": False,
            "puuid": puuid,
            "summoner_id": None,
            "summoner_name": None,
            "solo": None,
            "flex": None,
            "best": None,
        }

    if not summoner:
        return {
            "ok": False,
            "error": "Could not fetch summoner data from Riot.",
            "rank_unavailable": False,
            "puuid": puuid,
            "summoner_id": None,
            "summoner_name": None,
            "solo": None,
            "flex": None,
            "best": None,
        }

    summoner_id = summoner.get("id") or summoner.get("summonerId")
    summoner_name = summoner.get("name")

    if not summoner_id:
        return {
            "ok": True,
            "error": None,
            "rank_unavailable": True,
            "puuid": puuid,
            "summoner_id": None,
            "summoner_name": summoner_name,
            "solo": None,
            "flex": None,
            "best": None,
        }

    ranked_entries, error = await get_ranked_entries_by_summoner_id(str(summoner_id))
    if error:
        return {
            "ok": False,
            "error": error,
            "rank_unavailable": False,
            "puuid": puuid,
            "summoner_id": str(summoner_id),
            "summoner_name": summoner_name,
            "solo": None,
            "flex": None,
            "best": None,
        }

    if ranked_entries is None:
        return {
            "ok": False,
            "error": "Could not fetch ranked entries from Riot.",
            "rank_unavailable": False,
            "puuid": puuid,
            "summoner_id": str(summoner_id),
            "summoner_name": summoner_name,
            "solo": None,
            "flex": None,
            "best": None,
        }

    solo = next((x for x in ranked_entries if x.get("queueType") == "RANKED_SOLO_5x5"), None)
    flex = next((x for x in ranked_entries if x.get("queueType") == "RANKED_FLEX_SR"), None)
    best = solo or flex

    return {
        "ok": True,
        "error": None,
        "rank_unavailable": best is None,
        "puuid": puuid,
        "summoner_id": str(summoner_id),
        "summoner_name": summoner_name,
        "solo": solo,
        "flex": flex,
        "best": best,
    }