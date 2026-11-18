-- Set this to a collection run ID from collection_runs before running a query.
-- Example in psql: \set run_id 1

-- Closest to completion, based on core achievements.
SELECT
    g.game_id,
    g.title,
    gp.num_awarded,
    gp.max_possible,
    gp.max_possible - gp.num_awarded AS remaining_achievements,
    ROUND(gp.num_awarded::numeric / gp.max_possible * 100, 1) AS completion_percent
FROM game_progress AS gp
JOIN games AS g USING (game_id)
WHERE gp.run_id = :run_id
  AND gp.max_possible > 0
  AND gp.num_awarded >= 0
  AND gp.num_awarded < gp.max_possible
ORDER BY
    gp.num_awarded::numeric / gp.max_possible DESC,
    gp.max_possible - gp.num_awarded,
    g.title
LIMIT 5;

-- Largest unearned point totals.
SELECT
    g.game_id,
    g.title,
    gpp.possible_score,
    gpp.score_achieved,
    gpp.possible_score - gpp.score_achieved AS remaining_points
FROM game_point_progress AS gpp
JOIN games AS g USING (game_id)
WHERE gpp.run_id = :run_id
  AND gpp.possible_score > 0
  AND gpp.score_achieved >= 0
  AND gpp.score_achieved < gpp.possible_score
ORDER BY remaining_points DESC, g.title
LIMIT 5;

-- Balanced opportunities: remaining points weighted by points already earned.
SELECT
    g.game_id,
    g.title,
    gpp.possible_score - gpp.score_achieved AS remaining_points,
    ROUND(gpp.score_achieved::numeric / gpp.possible_score * 100, 1)
        AS point_progress_percent,
    ROUND(
        (gpp.possible_score - gpp.score_achieved)::numeric
        * gpp.score_achieved / gpp.possible_score,
        1
    ) AS balanced_opportunity_score
FROM game_point_progress AS gpp
JOIN games AS g USING (game_id)
WHERE gpp.run_id = :run_id
  AND gpp.possible_score > 0
  AND gpp.score_achieved > 0
  AND gpp.score_achieved < gpp.possible_score
ORDER BY balanced_opportunity_score DESC, g.title
LIMIT 5;

-- Average community unlock rate among remaining achievements for games whose
-- details were collected (currently the top five balanced opportunities).
SELECT
    g.game_id,
    g.title,
    COUNT(*) AS remaining_achievement_count,
    ROUND(AVG(ap.community_awarded_count::numeric
              / NULLIF(ap.community_player_count, 0)) * 100, 1)
        AS average_community_unlock_percent
FROM achievement_progress AS ap
JOIN games AS g USING (game_id)
WHERE ap.run_id = :run_id
  AND ap.date_earned IS NULL
  AND ap.date_earned_hardcore IS NULL
  AND ap.community_awarded_count >= 0
  AND ap.community_awarded_count <= ap.community_player_count
  AND ap.community_player_count > 0
GROUP BY g.game_id, g.title
ORDER BY average_community_unlock_percent DESC, g.title
LIMIT 5;
