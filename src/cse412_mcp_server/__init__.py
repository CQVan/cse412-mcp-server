import os
from pathlib import Path

from fastmcp import FastMCP
from dotenv import load_dotenv

mcp = FastMCP("Steam Library Inspector")


@mcp.tool
def get_database_scheme():
    return "Tool not Implemented!"


@mcp.tool
def execute_sql(query: str):
    return "Tool not Implemented!"


@mcp.tool
def get_games_by_creator(
    creator: str,
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"


@mcp.tool
def get_dlc_of_games(
    game: str,
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def get_games_by_genre(
    genre: str,
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"


@mcp.tool
def get_games_by_developer(
    developer: str,
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def get_games_by_publisher(
    publisher: str,
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def get_games_by_review_score(
    minimum_score: float = 0,
    maximum_score: float = 100,
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def get_unplayed_games(
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def get_games_by_playtime(
    minimum_hours: float = 0,
    maximum_hours: float | None = None,
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def get_games_not_played_since(
    date: str,
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def get_recently_played_games(
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def get_most_played_games(
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def search_games_by_name(
    name: str,
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def get_game_info(game: str):
    return "Tool not Implemented!"

@mcp.tool
def get_game_playtime(game: str):
    return "Tool not Implemented!"

@mcp.tool
def get_last_played(game: str):
    return "Tool not Implemented!"

@mcp.tool
def get_total_playtime():
    return "Tool not Implemented!"

@mcp.tool
def get_game_count():
    return "Tool not Implemented!"

@mcp.tool
def get_unplayed_game_count():
    return "Tool not Implemented!"


@mcp.tool
def get_owned_dlc_count():
    return "Tool not Implemented!"

@mcp.tool
def get_games_with_dlc(
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

@mcp.tool
def get_games_without_dlc(
    limit: int = 0,
    offset: int = 0
):
    return "Tool not Implemented!"

def run_mcp():
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")

    match os.getenv("TRANSPORT_PROTOCOL", "http"):
        case "http":
            host = os.getenv("HTTP_HOST", "localhost")
            port = int(os.getenv("HTTP_PORT", "8000"))
            mcp.run(transport="http", host=host, port=port)
        case "sse":
            host = os.getenv("SSE_HOST", "localhost")
            port = int(os.getenv("SSE_PORT", "8000"))
            mcp.run(transport="sse", host=host, port=port)
        case "stdio":
            mcp.run()
        case protocol:
            raise ValueError(
                f"Unsupported transport protocol {protocol!r}. "
                "Expected 'http', 'sse', or 'stdio'."
            )


def main():
    run_mcp()


if __name__ == "__main__":
    main()
