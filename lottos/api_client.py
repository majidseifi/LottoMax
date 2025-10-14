"""
Canada Lottery API Client
Handles all API interactions with the Canada Lottery Results API
"""

import requests
import time
import threading
from typing import List, Dict, Any, Optional

class CanadaLotteryAPI:
    """Client for interacting with Canada Lottery Results API"""

    BASE_URL = "https://canada-lottery.p.rapidapi.com"
    HEADERS = {
        "x-rapidapi-key": "***REMOVED***",
        "x-rapidapi-host": "canada-lottery.p.rapidapi.com"
    }

    # API endpoint mappings
    LOTTERY_ENDPOINTS = {
        "lottomax": "lottomax",
        "6-49": "6-49",
        "daily-grand": "daily-grand"
    }

    # Rate limiting: 50 requests per minute
    RATE_LIMIT = 50  # requests
    RATE_WINDOW = 60  # seconds
    MIN_REQUEST_DELAY = (RATE_WINDOW / RATE_LIMIT) + 0.15  # 1.35 seconds (with safety margin)

    # Class-level rate limiting (shared across all instances)
    _last_request_time = 0
    _rate_lock = threading.Lock()

    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        Initialize API client

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries

    def _enforce_rate_limit(self):
        """
        Enforce rate limiting: max 50 requests per 60 seconds
        Simple approach: ensure exactly MIN_REQUEST_DELAY (1.2s) between requests
        Thread-safe with lock held during entire operation
        """
        with self._rate_lock:
            current_time = time.time()

            # Calculate time since last request
            if self._last_request_time > 0:
                time_since_last = current_time - self._last_request_time

                # If not enough time has passed, wait
                if time_since_last < self.MIN_REQUEST_DELAY:
                    wait_time = self.MIN_REQUEST_DELAY - time_since_last
                    time.sleep(wait_time)

            # Update last request time
            self._last_request_time = time.time()

    def _make_request(self, endpoint: str) -> Optional[Any]:
        """
        Make an API request with retry logic and rate limiting

        Args:
            endpoint: API endpoint path (e.g., "/lottomax/years")

        Returns:
            JSON response data or None on failure
        """
        # Enforce rate limit before making request
        self._enforce_rate_limit()

        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=self.HEADERS, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return None
            except requests.exceptions.RequestException as e:
                if response.status_code == 404:
                    return None
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None

        return None

    def fetch_years(self, lottery_type: str) -> Optional[List[int]]:
        """
        Fetch available years for a lottery

        Args:
            lottery_type: Type of lottery ("lottomax", "6-49", "daily-grand")

        Returns:
            List of available years or None on failure
        """
        endpoint = f"/{lottery_type}/years"
        return self._make_request(endpoint)

    def fetch_draws_for_year(self, lottery_type: str, year: int) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all draws for a specific year

        Args:
            lottery_type: Type of lottery ("lottomax", "6-49", "daily-grand")
            year: Year to fetch draws for

        Returns:
            List of draw data dictionaries or None on failure
        """
        endpoint = f"/{lottery_type}/years/{year}"
        return self._make_request(endpoint)

    def fetch_all_draws(self, lottery_type: str, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Fetch draws for a range of years

        Args:
            lottery_type: Type of lottery ("lottomax", "6-49", "daily-grand")
            start_year: Starting year (inclusive)
            end_year: Ending year (inclusive)

        Returns:
            List of all draw data dictionaries
        """
        all_draws = []

        for year in range(start_year, end_year + 1):
            draws = self.fetch_draws_for_year(lottery_type, year)
            if draws:
                all_draws.extend(draws)

        return all_draws

    def fetch_latest_draw(self, lottery_type: str, current_year: int) -> Optional[Dict[str, Any]]:
        """
        Fetch the most recent draw for a lottery

        Args:
            lottery_type: Type of lottery ("lottomax", "6-49", "daily-grand")
            current_year: Current year to check

        Returns:
            Most recent draw data or None on failure
        """
        draws = self.fetch_draws_for_year(lottery_type, current_year)
        if draws and len(draws) > 0:
            # Draws are typically returned in chronological order, get the most recent
            return draws[-1] if draws else None
        return None
