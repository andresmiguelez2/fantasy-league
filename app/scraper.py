from aux.constants import FANTASY_MAIN_URL, FOOTBALLER_NAME_DICT
from aux.server_requests import scrape_page
from classes.footballer import Footballer
import unicodedata
import logging
import re
from tqdm import tqdm


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