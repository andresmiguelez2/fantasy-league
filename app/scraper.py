from aux.constants import FANTASY_MAIN_URL, FOOTBALLER_NAME_DICT
from classes.footballer import Footballer
from aux.aux_functions import scrape_page
import logging
import re
from tqdm import tqdm
import pandas as pd


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
        nombre = FOOTBALLER_NAME_DICT.get(el["data-nombre"], el["data-nombre"])
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


def normalise_name(name):
    return_name = name[:]
    if 'alvarez' in return_name:
        return_name = return_name.replace('alvarez', 'lvarez')
    if 'toni ' in return_name:
        return_name = return_name.replace('toni ', 'antonio ')
    if return_name == 'yeray lvarez':
        return_name = 'yeray alvarez'
        
    return return_name


if __name__ == "__main__":
    soup = scrape_page(FANTASY_MAIN_URL, logger)
    player_data_df = pd.DataFrame(get_all_players(soup), columns=["name", "full_name", "displayable_name"])

    for _, row in player_data_df.iterrows():
        try:
            footballer = Footballer(obtain_data=True, name=row['name'])
            footballer.name = row['displayable_name'] if row['displayable_name'] else row['name']
        except Exception as e:
            print(f"Error processing {row['name']}: {e}")
