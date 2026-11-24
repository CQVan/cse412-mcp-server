import json

from fastmcp import FastMCP

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
    with open ("../config.json", "r", encoding="utf-8") as file:
            config = json.load(file)
    
    match config["transport"]:
        case "http":
            host = config["http_settings"]["host"]
            port = config["http_settings"]["port"]
            mcp.run(transport="http", host=host, port=port);
        case "http":
            host = config["sse_settings"]["host"]
            port = config["sse_settings"]["port"]
            mcp.run(transport="sse", host=host, port=port);
        case "stdio":
            mcp.run()

if __name__ == "__main__":

    
    
    run_mcp()
