"""Persist normalized collection data and source responses in PostgreSQL."""

import os
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


DEFAULT_DATABASE_URL = (
    "postgresql://ra_user:ra_local_password@localhost:5432/ra_data_engine"
)

ANALYSIS_QUERIES = {
    "closest_to_completion": """
        SELECT g.game_id, g.title,
               gp.num_awarded,
               gp.max_possible - gp.num_awarded AS remaining_achievements,
               gp.num_awarded::numeric / gp.max_possible * 100 AS completion_percent
        FROM game_progress AS gp
        JOIN games AS g USING (game_id)
        WHERE gp.run_id = %s
          AND gp.max_possible > 0
          AND gp.num_awarded >= 0
          AND gp.num_awarded < gp.max_possible
        ORDER BY gp.num_awarded::numeric / gp.max_possible DESC,
                 gp.max_possible - gp.num_awarded, g.title
        LIMIT 5
    """,
    "most_remaining_points": """
        SELECT g.game_id, g.title,
               gpp.possible_score - gpp.score_achieved AS remaining_points
        FROM game_point_progress AS gpp
        JOIN games AS g USING (game_id)
        WHERE gpp.run_id = %s
          AND gpp.possible_score > 0
          AND gpp.score_achieved >= 0
          AND gpp.score_achieved < gpp.possible_score
        ORDER BY remaining_points DESC, g.title
        LIMIT 5
    """,
    "balanced_opportunities": """
        SELECT g.game_id, g.title,
               gpp.possible_score - gpp.score_achieved AS remaining_points,
               gpp.score_achieved::numeric / gpp.possible_score * 100
                   AS point_progress_percent,
               (gpp.possible_score - gpp.score_achieved)::numeric
                   * gpp.score_achieved / gpp.possible_score
                   AS balanced_opportunity_score
        FROM game_point_progress AS gpp
        JOIN games AS g USING (game_id)
        WHERE gpp.run_id = %s
          AND gpp.possible_score > 0
          AND gpp.score_achieved > 0
          AND gpp.score_achieved < gpp.possible_score
        ORDER BY balanced_opportunity_score DESC, g.title
        LIMIT 5
    """,
    "most_approachable_remaining_achievements": """
        SELECT g.game_id, g.title,
               COUNT(*) AS remaining_achievement_count,
               AVG(ap.community_awarded_count::numeric
                   / NULLIF(ap.community_player_count, 0)) * 100
                   AS average_community_unlock_percent
        FROM achievement_progress AS ap
        JOIN games AS g USING (game_id)
        WHERE ap.run_id = %s
          AND ap.date_earned IS NULL
          AND ap.date_earned_hardcore IS NULL
          AND ap.community_awarded_count >= 0
          AND ap.community_awarded_count <= ap.community_player_count
          AND ap.community_player_count > 0
        GROUP BY g.game_id, g.title
        ORDER BY average_community_unlock_percent DESC, g.title
        LIMIT 5
    """,
}


def save_collection(
    username: str,
    profile: dict,
    progress: dict,
    point_summaries: dict[str, dict],
) -> int:
    """Save one collection snapshot and return its run ID."""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            for statement in schema.split(";"):
                if statement.strip():
                    cursor.execute(statement)

            cursor.execute(
                "INSERT INTO collection_runs (username, profile) VALUES (%s, %s) "
                "RETURNING run_id",
                (username, Jsonb(profile)),
            )
            run_id = cursor.fetchone()[0]

            _save_raw_response(cursor, run_id, "user_profile", "", profile)
            _save_raw_response(cursor, run_id, "completion_progress", "", progress)
            _save_raw_response(cursor, run_id, "user_progress", "", point_summaries)

            for game in progress.get("Results", []):
                game_id = game["GameID"]
                cursor.execute(
                    """INSERT INTO games (game_id, title, console_id, console_name)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (game_id) DO UPDATE SET
                           title = EXCLUDED.title,
                           console_id = EXCLUDED.console_id,
                           console_name = EXCLUDED.console_name""",
                    (
                        game_id,
                        game.get("Title", "Unknown"),
                        game.get("ConsoleID"),
                        game.get("ConsoleName"),
                    ),
                )
                cursor.execute(
                    """INSERT INTO game_progress
                       (run_id, game_id, max_possible, num_awarded,
                        num_awarded_hardcore, most_recent_awarded_at)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        run_id,
                        game_id,
                        game.get("MaxPossible"),
                        game.get("NumAwarded"),
                        game.get("NumAwardedHardcore"),
                        _parse_timestamp(game.get("MostRecentAwardedDate")),
                    ),
                )

                point_summary = point_summaries.get(str(game_id))
                if point_summary:
                    cursor.execute(
                        """INSERT INTO game_point_progress
                           (run_id, game_id, possible_score, score_achieved)
                           VALUES (%s, %s, %s, %s)""",
                        (
                            run_id,
                            game_id,
                            point_summary.get("PossibleScore"),
                            point_summary.get("ScoreAchieved"),
                        ),
                    )

    return run_id


def save_game_details(run_id: int, game_details: dict[str, dict]) -> None:
    """Save detailed achievement responses for selected games in a run."""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            for game_id_text, details in game_details.items():
                game_id = int(game_id_text)
                _save_raw_response(
                    cursor, run_id, "game_info_and_user_progress", game_id_text, details
                )
                player_count = details.get("NumDistinctPlayersCasual")
                for achievement_id, achievement in details["Achievements"].items():
                    cursor.execute(
                        """INSERT INTO achievement_progress
                           (run_id, game_id, achievement_id, title, points,
                            community_awarded_count, community_player_count,
                            date_earned, date_earned_hardcore)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            run_id,
                            game_id,
                            int(achievement_id),
                            achievement.get("Title", "Unknown"),
                            achievement.get("Points"),
                            achievement.get("NumAwarded"),
                            player_count,
                            _parse_timestamp(achievement.get("DateEarned")),
                            _parse_timestamp(achievement.get("DateEarnedHardcore")),
                        ),
                    )


def get_rankings(run_id: int) -> dict[str, list[dict]]:
    """Calculate the displayed recommendations from one saved SQL snapshot."""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    rankings = {}

    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            for name, query in ANALYSIS_QUERIES.items():
                cursor.execute(query, (run_id,))
                rankings[name] = cursor.fetchall()

    return rankings


def _parse_timestamp(value: str | None) -> datetime | None:
    """Convert API ISO timestamps to values psycopg can adapt safely."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _save_raw_response(
    cursor, run_id: int, name: str, source_key: str, payload: object
) -> None:
    cursor.execute(
        """INSERT INTO raw_api_responses (run_id, response_name, source_key, payload)
           VALUES (%s, %s, %s, %s)""",
        (run_id, name, source_key, Jsonb(payload)),
    )
