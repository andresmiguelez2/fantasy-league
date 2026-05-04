import sys
sys.path.insert(0, '/workspace')

from datetime import datetime
import time
from backend.app.utils.aux_functions import scrape_page
from backend.app.db.database import pg_connect
from bs4 import BeautifulSoup


def get_earliest_fixture_dates(soup: BeautifulSoup) -> tuple[datetime | None, datetime | None, bool]:
    """
    Extracts the earliest fixture start and latest fixture end dates from the provided BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the HTML content.

    Returns:
        tuple[datetime.datetime | None, datetime.datetime | None, bool]: A tuple containing the earliest start date,
        latest end date, and a boolean indicating if all fixtures are closed.
    """
   # Find all time tags with itemprop="startDate"
    start_time_tags = soup.find_all('time', {'itemprop': 'startDate'})
    end_time_tags = soup.find_all('time', {'itemprop': 'endDate'})
    
    if not start_time_tags:
        return None
    
    dates = []
    for tag in start_time_tags:
        content = tag.get('content')
        if content:
            try:
                date_obj = datetime.strptime(content, '%Y-%m-%d %H:%M:%S')
                dates.append(date_obj)
            except ValueError:
                continue

    end_dates = []
    for tag in end_time_tags:
        content = tag.get('content')
        if content:
            try:
                date_obj = datetime.strptime(content, '%Y-%m-%d %H:%M:%S')
                end_dates.append(date_obj)
            except ValueError:
                continue

    if dates:
        earliest_start = min(dates)
    else:
        earliest_start = None

    if end_dates:
        latest_end = max(end_dates)
        if datetime.now() > latest_end:
            closed = True
        else:
            closed = False
    else:
        closed = False
        latest_end = None
    
    return earliest_start, latest_end, closed


if __name__ == "__main__":
    conn = pg_connect()
    cursor = conn.cursor()
    
    for fixture in range(1, 39):
        fixtures_URL = 'https://www.futbolfantasy.com/laliga/posibles-alineaciones/'
        url = fixtures_URL + str(fixture)
        page_content = scrape_page(url, None)
        start_date, end_date, closed = get_earliest_fixture_dates(page_content)

        cursor.execute(
            """
            INSERT INTO fixture (n, start_ts, finished)
            VALUES (%s, %s, %s)
            """,
            (fixture, f'{start_date} Europe/Madrid', closed)
        )

        conn.commit()
        time.sleep(1)

    cursor.close()
    conn.close()