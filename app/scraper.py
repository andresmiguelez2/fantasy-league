from aux.constants import FANTASY_MAIN_URL, FANTASY_PLAYER_URL
import requests
from bs4 import BeautifulSoup
import logging
import pandas as pd
import re


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def scrape_page(url):
    logger.debug(f"Fetching {url}")
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


def parse_stat_text(stat_text):
    # Try to match: [value] [stat_name] [points] p
    match = re.match(r"(\d+)\s+([^\d]+?)\s+(-?\d+)\s*p", stat_text)
    if match:
        value = int(match.group(1))
        stat_name = match.group(2).strip()
        points = int(match.group(3))
        return stat_name, {'value': value, 'points': points}
    # Try to match: [stat_name] [points] p (no value)
    match = re.match(r"([^\d]+?)\s+(-?\d+)\s*p", stat_text)
    if match:
        stat_name = match.group(1).strip()
        points = int(match.group(2))
        return stat_name, {'value': None, 'points': points}
    return None, None


def get_fixture_breakdown(soup):
    breakdowns = []
    # Find all fixture rows
    for fixture_td in soup.find_all("td", class_="bold jorn-td"):
        fixture_str = fixture_td.get_text(strip=True)
        # Extract the integer before the first non-numeric character
        match = re.match(r"(\d+)", fixture_str)
        fixture_number = int(match.group(1)) if match else fixture_str
        # The fixture row's parent is a <tr>, so find the next <tr class="desglose">
        desglose_tr = fixture_td.find_parent("tr").find_next_sibling("tr", class_="desglose")
        if desglose_tr:
            # Find all statistics divs inside this breakdown
            stats_dict = {}
            for stat_div in desglose_tr.find_all("div", class_="estadistica"):
                stat_text = stat_div.get_text(separator=" ", strip=True)
                stat_name, stat_entry = parse_stat_text(stat_text)
                if stat_name:
                    stats_dict[stat_name] = stat_entry
                if stat_name in ['Puntos DAZN', 'Puntos Relevo']: break
            breakdowns.append({
                "fixture": fixture_number,
                "breakdown": stats_dict
            })
    return breakdowns


def get_player_data(player_name):
    search_url = FANTASY_PLAYER_URL + player_name.replace(" ", "-")
    soup = scrape_page(search_url)

    total_points = get_total_points(soup)
    average_points = get_average_points(soup)
    fixture_breakdown = get_fixture_breakdown(soup)
    image_url = get_player_image_url(soup)
    player_id = int(image_url.split('/')[-1].split('.')[0]) if image_url else None
    market_details = get_market_details(player_id) if player_id else None

    return None


def get_market_details(player_id):
    """
    Fetches market details for a player by scraping the chart data from the analytics page.
    Returns a list of dicts with 'date' and 'value'.
    """
    url = f"https://www.futbolfantasy.com/analytics/laliga-fantasy/mercado/detalle/{player_id}"
    soup = scrape_page(url)
    # Find all script tags and search for player_chartjs.push({...})
    chart_data = []
    script_tags = soup.find_all("script")
    pattern = re.compile(r'player_chartjs\.push\(\{date:"([^"]+)",value:(\d+)\}\)')
    for script in script_tags:
        if script.string:
            for match in pattern.finditer(script.string):
                date = match.group(1)
                value = int(match.group(2))
                chart_data.append({"date": date, "value": value})
    logger.debug(f"Found {len(chart_data)} market data points for player {player_id}")
    return chart_data


def get_player_image_url(soup):
    # Find the modal div by id
    modal_div = soup.find("div", id="player-polygon")
    if modal_div:
        # Find the <img> inside the <h5 class="modal-title">
        h5 = modal_div.find("h5", class_="modal-title")
        if h5:
            img = h5.find("img")
            if img and img.has_attr("src"):
                return img["src"]
    logger.warning("Player image URL not found.")
    return None


if __name__ == "__main__":
    # soup = scrape_page(FANTASY_MAIN_URL)
    # player_data_df = pd.DataFrame(get_all_players(soup), columns=["name", "full_name", "displayable_name"])

    get_player_data('arda gler')
