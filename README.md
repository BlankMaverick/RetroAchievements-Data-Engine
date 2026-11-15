# RetroAchievements Data Engine

A learning project for building a data pipeline with Python and SQL, one small feature at a time. The long-term goal is a companion for achievement chasers: help a player explore their progress and decide what to finish next.

The current collection step retrieves a RetroAchievements user's profile and played-game completion progress, then saves the responses as local JSON. PostgreSQL, analysis, and recommendation logic are planned; they are not implemented yet.

## Current capabilities

- Fetch a user's profile with `API_GetUserProfile.php`.
- Fetch all pages of their played-game completion progress with `API_GetUserCompletionProgress.php`.
- Save both API responses as readable UTF-8 JSON files.

The completion-progress response includes game and console identifiers/names, the number of core achievements, the user's earned achievement counts, and award dates. The endpoint supports pagination up to 500 records per request, and the client retrieves every page.

## Requirements

- Python 3.13.7 (the documented development version)
- A RetroAchievements account and web API key
- The `requests` package

## Setup

Run these commands from the project root in **PowerShell**:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install requests
```

## Run

Set your API key in the same PowerShell session, then run the script:

```powershell
$env:RA_API_KEY = "YOUR_API_KEY"
python main.py
```

The target username is currently set to `Foolacetic` in `main.py`. Change the `username` value there to collect another player's data. Do not commit your API key or share request URLs containing it.

The API key is read from the environment; `.env` files are not loaded. If you use Command Prompt instead of PowerShell:

```bat
set RA_API_KEY=YOUR_API_KEY
.venv\Scripts\python.exe main.py
```

See the official documentation for [User Profile](https://api-docs.retroachievements.org/v1/get-user-profile.html) and [User Completion Progress](https://api-docs.retroachievements.org/v1/get-user-completion-progress.html).

## Project structure

```text
main.py                    Coordinates collection and output
ra_data_engine/api.py      RetroAchievements API client
ra_data_engine/storage.py  JSON persistence helper
```

`main.py` is the runnable entry point. The API client centralizes requests, authentication parameters, timeouts, and API response handling. The storage helper writes JSON files.

## Output

Run the script from the project root. It writes or overwrites:

- `user_profile.json` — the profile response.
- `user_completion_progress.json` — an object containing `Total` and `Results` for the user's played games.

The script prints a success message after both files are saved. These generated files are excluded from Git. If a request fails, the program stops before either output file is opened. File-write errors are not given a custom message, and the two files are not written atomically as a pair.

## Error handling and current limitations

- Stops with a clear message if `RA_API_KEY` is missing.
- Uses a 10-second request timeout and handles request/HTTP failures without printing the request URL, which contains the API key.
- Reports invalid JSON and unexpected API response formats.
- Checks the expected top-level fields for completion progress, but does not validate every game record or profile field.
- The target username is hardcoded; there is no command-line interface or interactive profile search yet.
- No database, transformations, analysis queries, recommendation algorithms, automated tests, logging, or scheduling are implemented yet.

## Validation status

The earlier single-profile version was manually checked for successful output, missing credentials, and an invalid key. The new API client and pagination flow have not yet been run against the API or tested automatically. A syntax check was attempted, but the environment reported that no Python installation was available. Invalid JSON and unexpected response cases also need verification.

## AI-assisted development

AI tools are used as collaborators for planning, API research, implementation scaffolding, and code explanations. Project scope and design decisions remain mine. I review suggested changes and verify them with documentation and local checks where available; AI-generated code is not treated as validated until it has been checked. Work sessions and meaningful decisions are summarized in `SESSION_LOG.md` rather than recording every prompt or minor edit.
