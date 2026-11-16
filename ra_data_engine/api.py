"""Small client for the RetroAchievements web API."""

import requests


class RetroAchievementsAPIError(Exception):
    """Raised when an API request fails or returns unusable data."""


class RetroAchievementsClient:
    """Retrieve data from RetroAchievements for a target user."""

    BASE_URL = "https://retroachievements.org/API"

    def __init__(self, api_key: str, timeout: int = 10) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def _get(self, endpoint: str, params: dict[str, str]) -> object:
        request_params = {**params, "y": self.api_key}
        try:
            response = requests.get(
                f"{self.BASE_URL}/{endpoint}",
                params=request_params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            raise RetroAchievementsAPIError(
                "The API returned a response that is not valid JSON."
            ) from None
        except requests.exceptions.RequestException:
            raise RetroAchievementsAPIError(
                "Could not retrieve data. Check your connection and API settings."
            ) from None

        if not isinstance(data, (dict, list)):
            raise RetroAchievementsAPIError("The API returned an unexpected response format.")
        return data

    def get_user_profile(self, username: str) -> dict:
        """Return a user's profile."""
        data = self._get("API_GetUserProfile.php", {"u": username})
        if not isinstance(data, dict):
            raise RetroAchievementsAPIError("The profile response was not an object.")
        return data

    def get_user_completion_progress(self, username: str) -> dict:
        """Return all pages of a user's played-game completion progress."""
        page_size = 500
        offset = 0
        all_results = []

        while True:
            page = self._get(
                "API_GetUserCompletionProgress.php",
                {"u": username, "c": str(page_size), "o": str(offset)},
            )
            if not isinstance(page, dict):
                raise RetroAchievementsAPIError(
                    "The completion progress response was not an object."
                )

            results = page.get("Results")
            total = page.get("Total")
            if not isinstance(results, list) or not isinstance(total, int):
                raise RetroAchievementsAPIError(
                    "The completion progress response is missing expected fields."
                )

            all_results.extend(results)
            offset += len(results)
            if not results or offset >= total:
                break

        return {"Total": len(all_results), "Results": all_results}

    def get_user_progress(self, username: str, game_ids: list[int]) -> dict[str, dict]:
        """Return point and achievement summaries for the requested games."""
        summaries = {}
        batch_size = 100

        for start in range(0, len(game_ids), batch_size):
            batch = game_ids[start : start + batch_size]
            response = self._get(
                "API_GetUserProgress.php",
                {"u": username, "i": ",".join(str(game_id) for game_id in batch)},
            )
            if not isinstance(response, dict):
                raise RetroAchievementsAPIError(
                    "The user progress response was not an object."
                )
            summaries.update(response)

        return summaries

    def get_game_info_and_user_progress(self, username: str, game_id: int) -> dict:
        """Return game metadata, community stats, and the user's earned achievements."""
        data = self._get(
            "API_GetGameInfoAndUserProgress.php",
            {"u": username, "g": str(game_id), "a": "1"},
        )
        if not isinstance(data, dict):
            raise RetroAchievementsAPIError(
                "The game info and user progress response was not an object."
            )
        if not isinstance(data.get("Achievements"), dict):
            raise RetroAchievementsAPIError(
                "The game response is missing achievement details."
            )
        return data
