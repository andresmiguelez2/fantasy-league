from aux.constants import FANTASY_MAIN_URL, FANTASY_PLAYER_URL
import requests
from bs4 import BeautifulSoup
import logging
import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def scrape_page(url):
    logger.info(f"Fetching {url}")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def get_total_points(soup):
    # Find the main info div
    info_div = soup.find("div", class_="info laliga-fantasy d-none border-none")
    if info_div:
        # Find the right-side div with the points
        points_div = info_div.find("div", class_="info-right rachita")
        if points_div:
            points_text = points_div.get_text(strip=True)
            logger.debug(f"Found total points: {points_text}")
            return int(points_text)
    logger.warning("Total points not found.")
    return None


def get_average_points(soup):
    # Find all <span> tags and check if their text contains "Media puntos"
    media_spans = soup.find_all("span", class_="racha-box columna_puntos point mx-auto")
    for span in media_spans:
        if "Media puntos" in span.get_text():
            # Go up to the parent <td>
            td = span.find_parent("td")
            if td:
                # Find the next <td> with the desired class
                next_td = td.find_next_sibling("td", class_="data points bold d-flex rachita")
                if next_td:
                    points_str = next_td.text.strip('\n').strip(' ')
                    first_break = points_str.find('\n')
                    fantasy_points = points_str[:first_break]
                    try:
                        return float(fantasy_points)
                    except ValueError:
                        return fantasy_points
    logger.warning("Average points not found.")
    return None


def get_all_players(soup):
    results = []
    elements = soup.find_all(attrs={"data-nombre": True})
    for el in elements:
        nombre = el["data-nombre"]
        a_tag = el.find_next("a", class_="jugador mt-auto mb-1")
        if a_tag:
            spans = a_tag.find_all("span")
            span_texts = [span.get_text(strip=True) for span in spans]
            if len(span_texts) == 2:
                results.append((nombre, span_texts[0], span_texts[1]))
            else:
                results.append((nombre, None, None))
        else:
            results.append((nombre, None, None))
    logger.info(f"Found {len(results)} player entries.")
    return results


def get_player_data(player_name):
    search_url = FANTASY_PLAYER_URL + player_name.replace(" ", "-")
    soup = scrape_page(search_url)

    total_points = get_total_points(soup)
    average_points = get_average_points(soup)

    return None


if __name__ == "__main__":
    # soup = scrape_page(FANTASY_MAIN_URL)
    # player_data_df = pd.DataFrame(get_all_players(soup), columns=["name", "full_name", "displayable_name"])

    get_player_data('arda gler')
