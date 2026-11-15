"""Run the RetroAchievements profile data collection."""

import os

from ra_data_engine.api import RetroAchievementsClient
from ra_data_engine.storage import save_json


def main() -> None:
    """Fetch a player's profile and played-game progress."""
    api_key = os.getenv("RA_API_KEY")
    if not api_key:
        raise SystemExit("RA_API_KEY environment variable is not set.")

    username = "example_username"  # Replace with the desired username
    client = RetroAchievementsClient(api_key)

    try:
        profile = client.get_user_profile(username)
        progress = client.get_user_completion_progress(username)
    except Exception as error:
        raise SystemExit(str(error)) from None

    save_json(profile, "user_profile.json")
    save_json(progress, "user_completion_progress.json")
    print(f"Saved profile and game progress for {username}.")


if __name__ == "__main__":
    main()
