import requests
from bs4 import BeautifulSoup


def scrape_page(url, logger):
    if logger:
        logger.debug(f"Fetching {url}")
    
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup