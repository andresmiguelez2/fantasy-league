from aux.constants import FANTASY_MAIN_URL
from aux.server_requests import scrape_page
from classes.footballer import Footballer
import unicodedata
import logging
import pandas as pd
import re


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


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


def normalise_string(s):
    """
    Lowercase the string and remove any character that is not a-z, whitespace,
    or a lowercase accented vowel (á, é, í, ó, ú).
    If the original letter is uppercase and contains an accent, remove it.
    """
    result = []
    for c in s:
        # If uppercase accented vowel, skip it
        if c in "ÁÉÍÓÚ":
            continue
        # Keep lowercase a-z, whitespace, and lowercase accented vowels
        if re.match(r"[a-z]", c):
            result.append(c)
        elif c in "áéíóú":
            result.append(chr(int(unicodedata.decomposition(c).split()[0], 16)))
        # Lowercase and check again (for uppercase unaccented letters)
        elif c.lower() in "abcdefghijklmnopqrstuvwxyz " and not re.match(r"[ÁÉÍÓÚ]", c):
            result.append(c.lower())
    return ''.join(result)


if __name__ == "__main__":
    soup = scrape_page(FANTASY_MAIN_URL)
    player_data_df = pd.DataFrame(get_all_players(soup), columns=["name", "full_name", "displayable_name"])

    for _, row in player_data_df.iterrows():
        footballer = Footballer()
        footballer.name = row['displayable_name'] if row['displayable_name'] else row['name']
        footballer_data = footballer.get_player_data(row['name'])

        pass