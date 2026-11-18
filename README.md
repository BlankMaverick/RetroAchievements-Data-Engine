# RetroAchievements Data Engine

A learning project for building a data pipeline with Python and SQL, one small feature at a time. The long-term goal is a companion for achievement chasers: help a player explore their progress and decide what to finish next.

The collection step retrieves a RetroAchievements user's profile and played-game completion progress, point summaries, and detailed achievement progress for the top five balanced opportunities. It saves normalized fields and source responses in PostgreSQL, keeps profile and completion progress as local JSON exports, and runs its displayed rankings against the saved PostgreSQL snapshot.

## Current capabilities

- Fetch a user's profile with `API_GetUserProfile.php`.
- Fetch all pages of their played-game completion progress with `API_GetUserCompletionProgress.php`.
- Fetch per-game possible and earned points with `API_GetUserProgress.php` in batches.
- Fetch detailed community achievement rates for the top five balanced opportunities.
- Save profile and completion progress as readable UTF-8 JSON files.
- Store collection snapshots, normalized progress, and raw API responses in PostgreSQL.

The completion-progress response includes game and console identifiers/names, the number of core achievements, the user's earned achievement counts, and award dates. The endpoint supports pagination up to 500 records per request, and the client retrieves every page.

SQL calculates four rankings of up to five unfinished games. Closest to completion uses the fraction of core achievements earned (`NumAwarded / MaxPossible`), with fewer remaining achievements and title as tie-breakers. Most remaining points ranks by unearned points for players who want the largest score backlog. Balanced opportunities multiply unearned points by the fraction of possible points already earned. The script uses that SQL ranking to choose which games need detailed achievement data, then saves those API responses and reruns the SQL rankings. The community ranking averages unlock rates across the player's remaining achievements in those games; higher rates suggest those achievements are more approachable to the community. This community measure is an estimate, not a completion probability, and uses one API request per candidate game. None of these signals estimate playtime or personal preference.

## Requirements

- Python 3.13.7 (the documented development version)
- A RetroAchievements account and web API key
- Docker Desktop or another Docker Compose installation
- The Python packages in `requirements.txt`

## Setup

Run these commands from the project root in **PowerShell**:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the local PostgreSQL database from the project root:

```powershell
docker compose up -d
```

The Compose setup uses a local development database named `ra_data_engine` and persists its data in a Docker volume. Its default local credentials are `ra_user` / `ra_local_password`; change them in `docker-compose.yml` and set a matching `DATABASE_URL` if you use this database beyond local development.

## Run

Set your API key in the same PowerShell session, then run the script:

```powershell
$env:RA_API_KEY = "YOUR_API_KEY"
$env:DATABASE_URL = "postgresql://ra_user:ra_local_password@localhost:5432/ra_data_engine"
python main.py
```

The target username is currently set to `Foolacetic` in `main.py`. Change the `username` value there to collect another player's data. Do not commit your API key or share request URLs containing it.

The API key is read from the environment; `.env` files are not loaded. If you use Command Prompt instead of PowerShell:

```bat
set RA_API_KEY=YOUR_API_KEY
set DATABASE_URL=postgresql://ra_user:ra_local_password@localhost:5432/ra_data_engine
.venv\Scripts\python.exe main.py
```

See the official documentation for [User Profile](https://api-docs.retroachievements.org/v1/get-user-profile.html) and [User Completion Progress](https://api-docs.retroachievements.org/v1/get-user-completion-progress.html).
The community-rate ranking uses [User Game Progress](https://api-docs.retroachievements.org/v1/get-game-info-and-user-progress.html).

## Project structure

```text
main.py                    Coordinates collection and output
ra_data_engine/api.py      RetroAchievements API client
ra_data_engine/storage.py  JSON persistence helper
ra_data_engine/database.py PostgreSQL persistence for normalized and raw data
ra_data_engine/schema.sql  PostgreSQL table definitions
sql/analysis_queries.sql   SQL rankings for manual inspection
docker-compose.yml         Local PostgreSQL service
```

`main.py` is the runnable entry point. The API client centralizes requests, authentication parameters, timeouts, and API response handling. The database module stores snapshots and executes the analysis queries; the storage helper writes local JSON exports.

## Output

Run the script from the project root. It writes or overwrites:

- `user_profile.json` — the profile response.
- `user_completion_progress.json` — an object containing `Total` and `Results` for the user's played games.

The script prints the PostgreSQL collection run ID after saving. The JSON files are convenience exports; SQL reads normalized rows from the database for the displayed rankings. The JSON files and database snapshot are not written atomically as one unit. If API collection or database persistence fails, the JSON files are not opened.

## Query the collected data

The SQL in `sql/analysis_queries.sql` contains the four rankings calculated from normalized PostgreSQL tables. `main.py` runs equivalent parameterized queries automatically after each collection. To inspect the SQL manually, note the printed run ID and, in PowerShell, stream the queries into the database container, replacing `1` with that run ID:

```powershell
Get-Content .\sql\analysis_queries.sql | docker compose exec -T postgres psql -U ra_user -d ra_data_engine -v run_id=1
```

The community unlock query only covers games whose detailed achievement data was collected for that snapshot (currently the top five balanced opportunities). It averages the community unlock rate across achievements the player has not earned in either mode.

## Error handling and current limitations

- Stops with a clear message if `RA_API_KEY` is missing.
- Uses a 10-second request timeout and handles request/HTTP failures without printing the request URL, which contains the API key.
- Reports invalid JSON and unexpected API response formats.
- Checks the expected top-level fields for completion progress, but does not validate every game record or profile field.
- The target username is hardcoded; there is no command-line interface or interactive profile search yet.
- Recommendation rankings are heuristic; logging and scheduling are not implemented.

## Validation status

The collection, point-summary request, and rankings have been run manually against the target profile, including live community-rate responses. PostgreSQL persistence is now part of the collection flow and requires the local Compose database to be running. There is no automated test suite; malformed JSON and unexpected response cases still need verification.

## AI-assisted development

AI tools are used as collaborators for planning, API research, implementation scaffolding, and code explanations. Project scope and design decisions remain mine. I review suggested changes and verify them with documentation and local checks where available; AI-generated code is not treated as validated until it has been checked. Work sessions and meaningful decisions are summarized in `SESSION_LOG.md` rather than recording every prompt or minor edit.
