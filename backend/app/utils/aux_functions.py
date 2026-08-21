import time

import requests
from bs4 import BeautifulSoup


REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def scrape_page(url, logger):
    if logger:
        logger.debug(f"Fetching {url}")

    last_error = None
    for attempt in range(2):
        try:
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
            if response.status_code == 429 or 500 <= response.status_code < 600:
                last_error = requests.HTTPError(
                    f"{response.status_code} Client Error: {response.reason} for url: {url}",
                    response=response,
                )
                if logger:
                    logger.warning(
                        f"Rate limited while fetching {url}; retrying in {2 ** attempt}s (attempt {attempt + 1}/4)"
                    )
                time.sleep(2 ** attempt)
                continue

            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as error:
            last_error = error
            if attempt == 3:
                break
            if logger:
                logger.warning(
                    f"Request failed for {url}; retrying in {2 ** attempt}s (attempt {attempt + 1}/4): {error}"
                )
            time.sleep(2 ** attempt)

    raise last_error

def extract_fixture_points(fixture_breakdown: list) -> dict:
    """Extracts total points per fixture from the fixture breakdown.
    Args:
        fixture_breakdown (list): List of fixture breakdowns with points details.

    Returns:
        dict[str, int]: {fixture, points}
    """
    fixture_points = list()
    for fixture_info in fixture_breakdown:
        points = 0
        for point_item, point_info in fixture_info['breakdown'].items():
            points += point_info.get("points", 0)

        fixture_points.append(
            {
                'fixture': fixture_info['fixture'],
                'points': points
            }
        )

    return fixture_points