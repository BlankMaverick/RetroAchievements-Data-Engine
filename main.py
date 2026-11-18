"""Run the RetroAchievements profile data collection."""

import os

from ra_data_engine.api import RetroAchievementsClient
from ra_data_engine.database import get_rankings, save_collection, save_game_details
from ra_data_engine.storage import save_json


def main() -> None:
    """Fetch a player's profile and played-game progress."""
    api_key = os.getenv("RA_API_KEY")
    if not api_key:
        raise SystemExit("RA_API_KEY environment variable is not set.")

    username = "Foolacetic"  # Replace with the desired username
    client = RetroAchievementsClient(api_key)

    try:
        profile = client.get_user_profile(username)
        progress = client.get_user_completion_progress(username)
        game_ids = [game["GameID"] for game in progress["Results"]]
        point_summaries = client.get_user_progress(username, game_ids)
    except Exception as error:
        raise SystemExit(str(error)) from None

    try:
        run_id = save_collection(username, profile, progress, point_summaries)
    except Exception:
        raise SystemExit(
            "Could not save collection to PostgreSQL. "
            "Check DATABASE_URL and database availability."
        ) from None

    try:
        candidate_rankings = get_rankings(run_id)
        game_details = {
            str(game["game_id"]): client.get_game_info_and_user_progress(
                username, game["game_id"]
            )
            for game in candidate_rankings["balanced_opportunities"]
        }
        save_game_details(run_id, game_details)
    except Exception:
        raise SystemExit(
            "The collection snapshot was saved, but detailed achievement data "
            "could not be collected or stored. Check API settings and database availability."
        ) from None

    save_json(profile, "user_profile.json")
    save_json(progress, "user_completion_progress.json")
    print(f"Saved profile and game progress for {username} (collection run {run_id}).")

    try:
        rankings = get_rankings(run_id)
    except Exception:
        raise SystemExit(
            "Collection was saved, but SQL rankings could not be retrieved. "
            "Check DATABASE_URL and database availability."
        ) from None

    recommendations = rankings["closest_to_completion"]
    if recommendations:
        print("Closest games to completion:")
        for game in recommendations:
            percentage = game["completion_percent"]
            remaining = game["remaining_achievements"]
            print(f"- {game['title']}: {percentage:.1f}% ({remaining} remaining)")
    else:
        print("No unfinished games with valid achievement counts were found.")

    point_recommendations = rankings["most_remaining_points"]
    if point_recommendations:
        print("Games with the most achievement points remaining:")
        for game in point_recommendations:
            print(f"- {game['title']}: {game['remaining_points']} points remaining")
    else:
        print("No unfinished games with valid point totals were found.")

    balanced_recommendations = rankings["balanced_opportunities"]
    if balanced_recommendations:
        print("Balanced opportunities (remaining points × progress):")
        for game in balanced_recommendations:
            score = game["balanced_opportunity_score"]
            rate = game["point_progress_percent"]
            remaining = game["remaining_points"]
            print(
                f"- {game['title']}: score {score:.1f} "
                f"({remaining} points remaining, {rate:.1f}% earned)"
            )
    else:
        print("No partially progressed games with valid point totals were found.")

    approachable_recommendations = rankings[
        "most_approachable_remaining_achievements"
    ]
    if approachable_recommendations:
        print("Most approachable remaining achievements (community average):")
        for game in approachable_recommendations:
            percentage = game["average_community_unlock_percent"]
            remaining = game["remaining_achievement_count"]
            print(
                f"- {game['title']}: {percentage:.1f}% average community unlock "
                f"rate across {remaining} remaining achievements"
            )
    else:
        print("No community unlock rates were available for balanced opportunities.")


if __name__ == "__main__":
    main()
