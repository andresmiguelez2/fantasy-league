import requests
from bs4 import BeautifulSoup


def scrape_page(url, logger):
    if logger:
        logger.debug(f"Fetching {url}")
    
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup

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