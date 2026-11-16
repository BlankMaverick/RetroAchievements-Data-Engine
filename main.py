"""Run the RetroAchievements profile data collection."""

import os

from ra_data_engine.api import RetroAchievementsClient
from ra_data_engine.recommendations import (
    balanced_point_opportunities,
    closest_to_completion,
    most_approachable_remaining_achievements,
    most_remaining_points,
)
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
        balanced_recommendations = balanced_point_opportunities(
            progress, point_summaries
        )
        game_details = {
            str(game["GameID"]): client.get_game_info_and_user_progress(
                username, game["GameID"]
            )
            for game in balanced_recommendations
        }
    except Exception as error:
        raise SystemExit(str(error)) from None

    save_json(profile, "user_profile.json")
    save_json(progress, "user_completion_progress.json")
    print(f"Saved profile and game progress for {username}.")

    recommendations = closest_to_completion(progress)
    if recommendations:
        print("Closest games to completion:")
        for game in recommendations:
            percentage = game["CompletionRate"] * 100
            remaining = game["RemainingAchievements"]
            print(f"- {game['Title']}: {percentage:.1f}% ({remaining} remaining)")
    else:
        print("No unfinished games with valid achievement counts were found.")

    point_recommendations = most_remaining_points(progress, point_summaries)
    if point_recommendations:
        print("Games with the most achievement points remaining:")
        for game in point_recommendations:
            print(f"- {game['Title']}: {game['RemainingPoints']} points remaining")
    else:
        print("No unfinished games with valid point totals were found.")

    if balanced_recommendations:
        print("Balanced opportunities (remaining points × progress):")
        for game in balanced_recommendations:
            score = game["BalancedOpportunityScore"]
            rate = game["PointProgressRate"] * 100
            remaining = game["RemainingPoints"]
            print(
                f"- {game['Title']}: score {score:.1f} "
                f"({remaining} points remaining, {rate:.1f}% earned)"
            )
    else:
        print("No partially progressed games with valid point totals were found.")

    approachable_recommendations = most_approachable_remaining_achievements(
        balanced_recommendations, game_details
    )
    if approachable_recommendations:
        print("Most approachable remaining achievements (community average):")
        for game in approachable_recommendations:
            percentage = game["AverageCommunityUnlockRate"] * 100
            remaining = game["RemainingAchievementCount"]
            print(
                f"- {game['Title']}: {percentage:.1f}% average community unlock "
                f"rate across {remaining} remaining achievements"
            )
    else:
        print("No community unlock rates were available for balanced opportunities.")


if __name__ == "__main__":
    main()
