"""Simple recommendation rankings based on collected game progress."""


def closest_to_completion(progress: dict, limit: int = 5) -> list[dict]:
    """Return unfinished games ranked by completion percentage.

    Games with missing or invalid achievement counts are ignored. Ties are
    broken by fewer remaining achievements, then by title for stable output.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    results = progress.get("Results")
    if not isinstance(results, list):
        raise ValueError("progress must contain a Results list")

    recommendations = []
    for game in results:
        if not isinstance(game, dict):
            continue

        maximum = game.get("MaxPossible")
        awarded = game.get("NumAwarded")
        if (
            not isinstance(maximum, int)
            or isinstance(maximum, bool)
            or not isinstance(awarded, int)
            or isinstance(awarded, bool)
            or maximum <= 0
            or awarded < 0
            or awarded >= maximum
        ):
            continue

        remaining = maximum - awarded
        recommendation = dict(game)
        recommendation["CompletionRate"] = awarded / maximum
        recommendation["RemainingAchievements"] = remaining
        recommendations.append(recommendation)

    recommendations.sort(
        key=lambda game: (
            -game["CompletionRate"],
            game["RemainingAchievements"],
            game.get("Title", ""),
        )
    )
    return recommendations[:limit]


def most_remaining_points(progress: dict, point_summaries: dict, limit: int = 5) -> list[dict]:
    """Return unfinished games ranked by unearned achievement points."""
    if limit < 1:
        raise ValueError("limit must be at least 1")

    results = progress.get("Results")
    if not isinstance(results, list):
        raise ValueError("progress must contain a Results list")

    recommendations = []
    for game in results:
        if not isinstance(game, dict):
            continue

        game_id = game.get("GameID")
        if not isinstance(game_id, int) or isinstance(game_id, bool):
            continue
        summary = point_summaries.get(str(game_id))
        if not isinstance(summary, dict):
            continue

        possible = summary.get("PossibleScore")
        achieved = summary.get("ScoreAchieved")
        if (
            not isinstance(possible, int)
            or isinstance(possible, bool)
            or not isinstance(achieved, int)
            or isinstance(achieved, bool)
            or possible <= 0
            or achieved < 0
            or achieved >= possible
        ):
            continue

        recommendation = dict(game)
        recommendation["RemainingPoints"] = possible - achieved
        recommendations.append(recommendation)

    recommendations.sort(
        key=lambda game: (-game["RemainingPoints"], game.get("Title", ""))
    )
    return recommendations[:limit]


def balanced_point_opportunities(
    progress: dict, point_summaries: dict, limit: int = 5
) -> list[dict]:
    """Balance unearned points against the player's existing progress.

    The score is remaining points multiplied by the fraction of possible
    points already earned. This favors substantial, partially progressed
    games over untouched backlogs and tiny cleanup tasks.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    results = progress.get("Results")
    if not isinstance(results, list):
        raise ValueError("progress must contain a Results list")

    opportunities = []
    for game in results:
        if not isinstance(game, dict):
            continue

        game_id = game.get("GameID")
        if not isinstance(game_id, int) or isinstance(game_id, bool):
            continue
        summary = point_summaries.get(str(game_id))
        if not isinstance(summary, dict):
            continue

        possible = summary.get("PossibleScore")
        achieved = summary.get("ScoreAchieved")
        if (
            not isinstance(possible, int)
            or isinstance(possible, bool)
            or not isinstance(achieved, int)
            or isinstance(achieved, bool)
            or possible <= 0
            or achieved <= 0
            or achieved >= possible
        ):
            continue

        remaining = possible - achieved
        progress_fraction = achieved / possible
        opportunity = dict(game)
        opportunity["RemainingPoints"] = remaining
        opportunity["PointProgressRate"] = progress_fraction
        opportunity["BalancedOpportunityScore"] = remaining * progress_fraction
        opportunities.append(opportunity)

    opportunities.sort(
        key=lambda game: (
            -game["BalancedOpportunityScore"],
            game["Title"],
        )
    )
    return opportunities[:limit]


def most_approachable_remaining_achievements(
    candidates: list[dict], game_details: dict[str, dict], limit: int = 5
) -> list[dict]:
    """Rank candidate games by average community unlock rate of missing awards."""
    if limit < 1:
        raise ValueError("limit must be at least 1")

    recommendations = []
    for game in candidates:
        game_id = game.get("GameID")
        if not isinstance(game_id, int) or isinstance(game_id, bool):
            continue

        details = game_details.get(str(game_id))
        if not isinstance(details, dict):
            continue
        achievements = details.get("Achievements")
        player_count = details.get("NumDistinctPlayersCasual")
        if (
            not isinstance(achievements, dict)
            or not isinstance(player_count, int)
            or isinstance(player_count, bool)
            or player_count <= 0
        ):
            continue

        unlock_rates = []
        for achievement in achievements.values():
            if not isinstance(achievement, dict):
                continue
            if achievement.get("DateEarned") or achievement.get("DateEarnedHardcore"):
                continue

            awarded = achievement.get("NumAwarded")
            if (
                not isinstance(awarded, int)
                or isinstance(awarded, bool)
                or awarded < 0
                or awarded > player_count
            ):
                continue
            unlock_rates.append(awarded / player_count)

        if not unlock_rates:
            continue

        recommendation = dict(game)
        recommendation["RemainingAchievementCount"] = len(unlock_rates)
        recommendation["AverageCommunityUnlockRate"] = sum(unlock_rates) / len(
            unlock_rates
        )
        recommendations.append(recommendation)

    recommendations.sort(
        key=lambda game: (
            -game["AverageCommunityUnlockRate"],
            game["Title"],
        )
    )
    return recommendations[:limit]
