from aux.constants import FANTASY_MAIN_URL
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

def get_all_players(soup):
    results = []
    elements = soup.find_all(attrs={"data-nombre": True})
    for el in elements:
        nombre = el["data-nombre"]
        # Find the next <a> with the desired class
        a_tag = el.find_next("a", class_="jugador mt-auto mb-1")
        if a_tag:
            spans = a_tag.find_all("span")
            span_texts = [span.get_text(strip=True) for span in spans]
            # If there are exactly two spans, save both
            if len(span_texts) == 2:
                results.append((nombre, span_texts[0], span_texts[1]))
            else:
                results.append((nombre, None, None))
        else:
            results.append((nombre, None, None))
    logger.info(f"Found {len(results)} player entries.")
    return results

if __name__ == "__main__":
    soup = scrape_page(FANTASY_MAIN_URL)
    player_data_df = pd.DataFrame(get_all_players(soup), columns=["name", "full_name", "displayable_name"])

    print(player_data_df)
