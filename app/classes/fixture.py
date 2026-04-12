from datetime import datetime, timezone
import logging
from aux.database import pg_connect
from aux.constants import DANGLING_FIXTURE_THRESHOLD, FANTASY_FIXTURE_URL, CLOSING_TIME_FIXTURE, COINS_PER_POINT
from bs4 import BeautifulSoup
from server_requests.footballer import get_fixture_points
from server_requests.leaderboard import leaderboard
from server_requests.player import get_footballers_on_lineup, get_player_lineup
from aux.aux_functions import scrape_page


logger = logging.getLogger(__name__)


class Fixture:
    def __init__(self, **kwargs):
        self._id: int = None
        self._n: int = None
        self._start_dt: datetime = None
        self._end_dt: datetime = None
        self._finished: bool = None
        self._dangling: bool = None # incicates if fixture is somewhat abnormal

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def id(self) -> int:
        return self._id 
    
    @id.setter
    def id(self, value: int):
        self._id = value
    
    @property
    def n(self) -> str:
        return self._n  
    
    @n.setter
    def n(self, value: str):
        self._n = value
    
    @property
    def start_dt(self) -> datetime:
        return self._start_dt
    
    @start_dt.setter
    def start_dt(self, value: datetime):
        self._start_dt = value

    @property
    def end_dt(self) -> datetime:
        return self._end_dt
    
    @end_dt.setter
    def end_dt(self, value: datetime):
        self._end_dt = value

    @property
    def finished(self) -> bool:
        return self._finished
    
    @finished.setter
    def finished(self, value: bool):
        self._finished = value

    @property
    def dangling(self) -> bool:
        return self._dangling
    
    @dangling.setter
    def dangling(self, value: bool):
        self._dangling = value

    def _fix_lineups(self):
        """Fix lineups for all players in the fixture
        """
        players = [row_[0] for row_ in leaderboard()["leaderboard"]]

        for player_id in players:
            footballers_on_lineup = [element for sublist in get_footballers_on_lineup(player_id)['lineup_footballers'] for element in sublist]
            lineup = get_player_lineup(player_id)['lineup']

            conn = pg_connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO fixture_details (fixture_n, player_id, footballers_on_lineup, lineup)
                VALUES (%s, %s, %s, %s)
                """,
                (self.n, player_id, footballers_on_lineup, lineup),
            )
            conn.commit()
            cursor.close()
            conn.close()

    def open_fixture(self):
        """Open the fixture in the database and fix lineups in time
        """
        logger.info(f"Opening fixture {self.n}.")

        _, closing_ts, _ = get_earliest_fixture_dates(scrape_page(FANTASY_FIXTURE_URL + str(self.n), logger))

        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE FIXTURE
            SET
                opened = true
                , end_ts = %s + INTERVAL '%s minutes'
            WHERE id = %s
            """,
            (closing_ts, CLOSING_TIME_FIXTURE, self.id),
        )
        conn.commit()
        cursor.close()
        conn.close()

        self._fix_lineups()

    def _close_fixture(self):
        """Close the fixture in the database
        """
        logger.info(f"Closing fixture {self.n}.")

        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE FIXTURE
            SET finished = true
            WHERE id = %s
            """,
            (self.id,),
        )
        conn.commit()
        cursor.close()
        conn.close()

    def _set_closing_time(self, time_diff: float = 0) -> None:
        """Set the closing time of a fixture in the database.
        
        Args:
            time_diff (float): Time difference in minutes to set the closing time.
        """
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE FIXTURE
            SET end_ts = now() + INTERVAL '%s minutes'
            WHERE n = %s
            """,
            (time_diff, self.n),
        )

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"fixture {self.n} will be closed in {time_diff} minutes.")

    def _assign_fixture_prizes(self):
        """Assign prizes to players based on their performance in the fixture.
        """
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                player_id
                , footballers_on_lineup
                , valid
            FROM fixture_details
            WHERE fixture_n = %s
            """,
            (self.n,),
        )

        valid_players = cursor.fetchall()

        for player_id, footballers_on_lineup, valid in valid_players:
            fixture_points = 0
            if valid:
                for fid in footballers_on_lineup:
                    points = get_fixture_points(fid, self.n)['points']
                    fixture_points += points
                    
            cursor.execute(
                """
                UPDATE fixture_details
                SET points = %s
                WHERE 
                    fixture_n = %s
                    AND player_id = %s
                """,
                (fixture_points, self.n, player_id),
            )
            logger.info(f"Player {player_id} scored {fixture_points} points in fixture {self.n}.")

            cursor.execute(
                """
                UPDATE player
                SET 
                    points = points + %s
                    , budget = budget + %s
                WHERE id = %s
                """,
                (fixture_points, fixture_points*COINS_PER_POINT, player_id),
            )
            logger.info(f"Player {player_id} awarded {fixture_points*COINS_PER_POINT:,.0f} € for fixture {self.n}.")

        conn.commit()
        cursor.close()
        conn.close()


    def fulfill_fixture(self) -> bool:
        """Fulfills the fixture. It first checks if it should be closed.

        Returns:
            bool: True if the fixture was closed, False otherwise.
        """
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT end_ts
            FROM FIXTURE
            WHERE n = %s
            """,
            (self.n,),
        )

        end_ts = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        if end_ts and end_ts <= datetime.now(tz=timezone.utc):
            self._close_fixture()
            self._assign_fixture_prizes()
            closed = True
        elif end_ts:
            logger.info(f"fixture {self.n} will be closed at {end_ts}.")
            closed = False
        else:
            self._set_closing_time(time_diff=CLOSING_TIME_FIXTURE)
            closed = False

        return closed

    def __repr__(self):
        return f"Fixture(n={self.n}, start_dt={self.start_dt}, end_dt={self.end_dt}, finished={self.finished})"
    

def get_current_fixture(handle_dangling: bool = True) -> Fixture | None:
    """
    Retrieve the current open fixture from the database.

    Args:
        handle_dangling (bool): Whether to handle dangling fixtures.
    
    Returns:
        Fixture: The current open fixture object, or None if no open fixture is found.
    """
    conn = pg_connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id
            , n
            , start_ts
            , now() - start_ts AS time_open
            , opened
        FROM FIXTURE
        WHERE
            start_ts < now()
            AND finished = false
        ORDER BY start_ts ASC
        """
    )

    open_fixtures = cursor.fetchall()

    cursor.close()
    conn.close()

    logger.info(f"Open fixtures found: {len(open_fixtures)}")

    for id, n, start_ts, time_open, opened in open_fixtures:
        if time_open.days >= DANGLING_FIXTURE_THRESHOLD:
            logger.warning(f"Dangling fixture detected: Fixture {n} has been open for {time_open}")
            if handle_dangling and ckeck_all_matches_finished(n):
                fixture = Fixture(id=id, n=n, start_dt=start_ts, finished=False, dangling=True)
                fixture.fulfill_fixture()

            continue

        fixture = Fixture(id=id, n=n, start_dt=start_ts, finished=False, dangling=False)
        logger.info(f"Current fixture found: {fixture}")

        if not opened:
            fixture.open_fixture()

        return fixture
    else:
        logger.info("No open fixture found.")
        return None
    

def ckeck_all_matches_finished(fixture_n: int) -> bool:
    """Check if all matches in a fixture have finished.
    
    Args:
        fixture_n (int): The fixture number.
        
    Returns:
        bool: True if all matches have finished, False otherwise.
    """
    match_urls = get_fixture_matches(fixture_n)
    
    if len(match_urls) != 10:
        logger.warning(f"Expected 10 match URLs for fixture {fixture_n}, but found {len(match_urls)}.")
        return False
    
    for url in match_urls:
        soup = scrape_page(url, logger)
        if "El árbitro pita el final del partido" not in soup.get_text():
            return False
    
    return True


def get_fixture_matches(fixture_n: int) -> list[str]:
    """Get match URLs for a given fixture number.
    
    Args:
        fixture_n (int): The fixture number.

    Returns:
        list: List of match URLs for the fixture.
    """
    fixture_url = FANTASY_FIXTURE_URL + str(fixture_n)

    soup = scrape_page(fixture_url, logger)
    
    fixture_matches_url = soup.find_all('a', href=True)
    
    # Filter links that start with the specified URL pattern
    match_urls = []
    for link in fixture_matches_url:
        href = link['href']
        if href.startswith("https://www.futbolfantasy.com/partidos/"):
            match_urls.append(href)
            if len(match_urls) == 10:
                break
    
    return match_urls


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


def update_fixture_times():
    """Updates fixture starting time in databsae
    """
    conn = pg_connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT n
        FROM fixture
        WHERE finished = false AND COALESCE(opened, false) != true
        ORDER BY n ASC
        """
    )

    fixtures_to_update = cursor.fetchall()

    for fixture in fixtures_to_update:
        url = FANTASY_FIXTURE_URL + str(fixture[0])
        page_content = scrape_page(url, None)
        start_date, end_date, closed = get_earliest_fixture_dates(page_content)

        cursor.execute(
            """
            UPDATE fixture 
            SET start_ts = %s, finished = %s
            WHERE n = %s
            """,
            (f'{start_date} Europe/Madrid', closed, fixture[0])
        )

    conn.commit()
    cursor.close()
    conn.close()