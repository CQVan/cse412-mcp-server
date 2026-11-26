import os
import re
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import requests
from psycopg import sql

STORE_DELAY = 1.6      # seconds between appdetails calls (~200 requests / 5 min limit)
REVIEW_DELAY = 0.5     # appreviews is much more lenient
MAX_DLC_PER_GAME = None  # set to an int to cap DLC lookups per game (some games have 100+)
MCP_USER = "mcp"
_mcp_password: str | None = None


def _database_params() -> dict[str, str | int]:
    env_vars = {
        "host": "DATABASE_HOST",
        "port": "DATABASE_PORT",
        "dbname": "DATABASE_NAME",
        "user": "DATABASE_USER",
        "password": "DATABASE_PASSWORD",
    }
    missing = [env_var for env_var in env_vars.values() if not os.getenv(env_var)]
    if missing:
        raise ValueError(f"{', '.join(missing)} must be set in .env")

    values = {key: os.environ[env_var] for key, env_var in env_vars.items()}
    try:
        port = int(values["port"])
    except ValueError as exc:
        raise ValueError("DATABASE_PORT must be an integer") from exc

    return {
        "host": values["host"],
        "port": port,
        "dbname": values["dbname"],
        "user": values["user"],
        "password": values["password"],
    }


def execute_sql(query: str):
    if _mcp_password is None:
        raise RuntimeError("MCP database user has not been initialized")

    db_params = _database_params()
    db_params["user"] = MCP_USER
    db_params["password"] = _mcp_password

    with psycopg.connect(**db_params) as conn:
        with conn.cursor() as cur:
            cur.execute(query)


def _configure_mcp_user(conn, database_name: str, password: str):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (MCP_USER,))
        user_exists = cur.fetchone() is not None
        if user_exists:
            cur.execute(
                sql.SQL("REVOKE CONNECT ON DATABASE {} FROM {}").format(
                    sql.Identifier(database_name),
                    sql.Identifier(MCP_USER),
                )
            )
            cur.execute(
                sql.SQL("REVOKE USAGE ON SCHEMA public FROM {}").format(
                    sql.Identifier(MCP_USER)
                )
            )
            cur.execute(
                sql.SQL("REVOKE SELECT ON ALL TABLES IN SCHEMA public FROM {}").format(
                    sql.Identifier(MCP_USER)
                )
            )
            cur.execute(
                sql.SQL("ALTER DEFAULT PRIVILEGES REVOKE SELECT ON TABLES FROM {}").format(
                    sql.Identifier(MCP_USER)
                )
            )
            cur.execute(
                sql.SQL("DROP USER {}").format(sql.Identifier(MCP_USER))
            )
        cur.execute(
            sql.SQL("CREATE USER {} WITH PASSWORD {}").format(
                sql.Identifier(MCP_USER),
                sql.Literal(password),
            )
        )
        cur.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(database_name),
                sql.Identifier(MCP_USER),
            )
        )
        cur.execute(
            sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(MCP_USER))
        )
        cur.execute(
            sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(
                sql.Identifier(MCP_USER)
            )
        )
        cur.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES GRANT SELECT ON TABLES TO {}").format(
                sql.Identifier(MCP_USER)
            )
        )


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_json(url: str, params: dict | None = None, delay: float = 0.0, retries: int = 5):
    """GET a URL and return parsed JSON, or None on failure. Backs off on 429."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue

        if resp.status_code == 429:
            time.sleep(30 * (attempt + 1))
            continue

        if delay:
            time.sleep(delay)

        if resp.status_code != 200:
            return None
        try:
            return resp.json()
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Steam API wrappers
# ---------------------------------------------------------------------------

def resolve_steam_id(api_key: str, user: str) -> str:
    """TARGET_USER can be a 17-digit SteamID64 or a vanity URL name."""
    if re.fullmatch(r"\d{17}", user):
        return user
    data = _get_json(
        "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
        {"key": api_key, "vanityurl": user},
    )
    response = (data or {}).get("response", {})
    if response.get("success") != 1:
        raise ValueError(f"Could not resolve Steam user '{user}'")
    return response["steamid"]


def fetch_owned_games(api_key: str, steam_id: str) -> list[dict]:
    data = _get_json(
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/",
        {
            "key": api_key,
            "steamid": steam_id,
            "include_appinfo": 1,
            "include_played_free_games": 1,
            "format": "json",
        },
    )
    games = (data or {}).get("response", {}).get("games")
    if games is None:
        raise RuntimeError(
            "GetOwnedGames returned no games. Check the API key and that the "
            "profile's 'Game details' privacy setting is Public."
        )
    return games


def fetch_app_details(appid: int) -> dict | None:
    data = _get_json(
        "https://store.steampowered.com/api/appdetails",
        {"appids": appid, "l": "english"},
        delay=STORE_DELAY,
    )
    entry = (data or {}).get(str(appid))
    if not entry or not entry.get("success"):
        return None
    return entry["data"]


def fetch_review_score(appid: int) -> int | None:
    """Steam's 1-9 review_score (Overwhelmingly Negative .. Overwhelmingly Positive)."""
    data = _get_json(
        f"https://store.steampowered.com/appreviews/{appid}",
        {"json": 1, "language": "all", "purchase_type": "all", "num_per_page": 0},
        delay=REVIEW_DELAY,
    )
    summary = (data or {}).get("query_summary")
    if not summary or summary.get("total_reviews", 0) == 0:
        return None
    return summary.get("review_score")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_languages(raw: str | None) -> list[str]:
    """supported_languages looks like: 'English<strong>*</strong>, French, ...<br><strong>*</strong>languages with full audio support'"""
    if not raw:
        return []
    raw = raw.split("<br>")[0]
    raw = re.sub(r"<[^>]+>", "", raw).replace("*", "")
    return [lang.strip()[:25] for lang in raw.split(",") if lang.strip()]


def unix_to_timestamp(ts: int | None) -> datetime | None:
    if not ts:  # 0 / missing means never played
        return None
    return datetime.fromtimestamp(ts, timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Crawl: build every table's rows in memory
# ---------------------------------------------------------------------------

def fetch_steam_data(api_key: str, user: str) -> dict:
    steam_id = resolve_steam_id(api_key, user)
    owned = fetch_owned_games(api_key, steam_id)
    print(f"Found {len(owned)} owned games")

    games = []
    genres: dict[int, str] = {}
    genre_for: set[tuple[int, int]] = set()
    creator_ids: dict[str, int] = {}   # name -> surrogate id
    developers: set[int] = set()
    publishers: set[int] = set()
    made: set[tuple[int, int]] = set()
    published: set[tuple[int, int]] = set()
    dlcs: dict[int, tuple] = {}

    def creator_id(name: str) -> int:
        return creator_ids.setdefault(name, len(creator_ids) + 1)

    for i, owned_game in enumerate(owned, 1):
        appid = owned_game["appid"]
        print(f"[{i}/{len(owned)}] {owned_game.get('name', appid)}")

        details = fetch_app_details(appid)
        review_score = fetch_review_score(appid)

        name = (details or {}).get("name") or owned_game.get("name") or str(appid)
        oslist = None
        languages = None

        if details:
            oslist = [p for p, supported in (details.get("platforms") or {}).items() if supported]
            languages = parse_languages(details.get("supported_languages"))

            for genre in details.get("genres", []):
                genre_id = int(genre["id"])
                genres[genre_id] = genre["description"][:100]
                genre_for.add((genre_id, appid))

            for dev in details.get("developers", []):
                cid = creator_id(dev.strip()[:100])
                developers.add(cid)
                made.add((cid, appid))

            for pub in details.get("publishers", []):
                cid = creator_id(pub.strip()[:100])
                publishers.add(cid)
                published.add((cid, appid))

            dlc_list = details.get("dlc", [])
            if MAX_DLC_PER_GAME is not None:
                dlc_list = dlc_list[:MAX_DLC_PER_GAME]
            for dlc_id in dlc_list:
                if dlc_id in dlcs:
                    continue
                dlc_details = fetch_app_details(dlc_id)
                if dlc_details:
                    dlcs[dlc_id] = (dlc_id, dlc_details["name"][:100], appid)

        games.append((
            appid,
            name[:100],
            oslist,
            languages,
            unix_to_timestamp(owned_game.get("rtime_last_played")),
            round(owned_game.get("playtime_forever", 0) / 60, 2),
            review_score,
        ))

    return {
        "games": games,
        "genres": sorted(genres.items()),
        "genre_for": sorted(genre_for),
        "creators": sorted((cid, name) for name, cid in creator_ids.items()),
        "developers": [(cid,) for cid in sorted(developers)],
        "publishers": [(cid,) for cid in sorted(publishers)],
        "made": sorted(made),
        "published": sorted(published),
        "dlcs": list(dlcs.values()),
    }


# ---------------------------------------------------------------------------
# Load: insert in foreign-key-safe order
# ---------------------------------------------------------------------------

def insert_data(database_params: dict[str, str | int], data: dict):
    with psycopg.connect(**database_params) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO GAME (G_GID, G_NAME, G_OSLIST, G_LANGUAGES, G_LASTPLAYED, G_HOURSPLAYED, G_REVIEWSCORE) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                data["games"],
            )
            cur.executemany("INSERT INTO GENRE (GN_ID, GN_NAME) VALUES (%s, %s)", data["genres"])
            cur.executemany("INSERT INTO GENREFOR (GF_ID, GF_GID) VALUES (%s, %s)", data["genre_for"])
            cur.executemany("INSERT INTO CREATOR (C_CID, C_NAME) VALUES (%s, %s)", data["creators"])
            cur.executemany("INSERT INTO DEVELOPER (D_CID) VALUES (%s)", data["developers"])
            cur.executemany("INSERT INTO PUBLISHER (P_CID) VALUES (%s)", data["publishers"])
            cur.executemany("INSERT INTO MADE (M_CID, M_GID) VALUES (%s, %s)", data["made"])
            cur.executemany("INSERT INTO PUBLISHED (PB_CID, PB_GID) VALUES (%s, %s)", data["published"])
            cur.executemany("INSERT INTO DLC (DLC_ID, DLC_NAME, DLC_GID) VALUES (%s, %s, %s)", data["dlcs"])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def init_database(steam_api_key: str, user: str):
    global _mcp_password

    database_params = _database_params()
    steam_api_key = os.getenv("STEAM_API_KEY")
    user = os.getenv("TARGET_USER")

    if(steam_api_key == None):
        raise ValueError("STEAM_API_KEY is not set in .env")

    if(user == None):
        raise ValueError("TARGET_USER is not set in .env")

    print("Initializing Database")

    sql_dir = Path(__file__).resolve().parents[2] / "sql"
    sql_files = ("drop_tables.sql", "create_tables.sql", "add_relationships.sql")
    mcp_password = secrets.token_urlsafe(32)

    with psycopg.connect(**database_params) as conn:
        with conn.cursor() as cur:
            for sql_file in sql_files:
                cur.execute((sql_dir / sql_file).read_text(encoding="utf-8"))
        _configure_mcp_user(conn, database_params["dbname"], mcp_password)
    _mcp_password = mcp_password

    print("Database is fully structured")
    print(f"Loading data about {user}'s library")

    # Crawl Steam first (slow, rate limited), then load everything in one transaction.
    data = fetch_steam_data(steam_api_key, user)
    insert_data(database_params, data)

    print(
        f"Loaded {len(data['games'])} games, {len(data['dlcs'])} DLC, "
        f"{len(data['creators'])} creators, {len(data['genres'])} genres"
    )