# CSE412 MCP Server

## Configuration

Copy `.env.example` to `.env` and fill in the values below.

```dotenv
DATABASE_HOST=
DATABASE_PORT=5432
DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
STEAM_API_KEY=
TARGET_USER=

TRANSPORT_PROTOCOL=http

HTTP_HOST=localhost
HTTP_PORT=8000

SSE_HOST=localhost
SSE_PORT=8000
```

### Required

| Variable | Description |
|---|---|
| `DATABASE_HOST`, `DATABASE_PORT` | PostgreSQL server host and port (typically `5432`). |
| `DATABASE_NAME` | Name of the existing PostgreSQL database. |
| `DATABASE_USER`, `DATABASE_PASSWORD` | Credentials used to connect to PostgreSQL. |
| `STEAM_API_KEY` | Your Steam Web API key. You can get one at https://steamcommunity.com/dev/apikey. |
| `TARGET_USER` | The Steam account whose library is loaded. Accepts a 17-digit SteamID64 or a vanity URL name. |

The target account's **Game details** privacy setting must be set to **Public** (Steam profile > Edit Profile > Privacy Settings). Otherwise Steam returns no owned games and the database will not be populated.

### Transport

| Variable | Description |
|---|---|
| `TRANSPORT_PROTOCOL` | One of `http`, `sse`, or `stdio`. Defaults to `http`. |
| `HTTP_HOST`, `HTTP_PORT` | Bind address for the HTTP listener. Only used when `TRANSPORT_PROTOCOL=http`. |
| `SSE_HOST`, `SSE_PORT` | Bind address for the SSE listener. Only used when `TRANSPORT_PROTOCOL=sse`. |

With `stdio`, the host and port variables are ignored. The HTTP and SSE ports default to the same value, so change one if you ever run both at once.

## Database initialization

Initializing the database **drops and recreates all tables** (`drop_tables.sql`, `create_tables.sql`, `add_relationships.sql`) and then reloads data from Steam. Any existing data in those tables is lost.

The Steam crawl is rate limited, so a large library can take several minutes to load (roughly 15 minutes for a few hundred games, plus extra time for DLC lookups).