from datetime import datetime
import logging
from aux.database import pg_connect
from aux.constants import DANGLING_FIXTURE_THRESHOLD
from server_requests.leaderboard import leaderboard
from server_requests.player import get_footballers_on_lineup


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
            lineup = [element for sublist in get_footballers_on_lineup(player_id)['lineup_footballers'] for element in sublist]

            conn = pg_connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO fixture_details (fixture_n, player_id, lineup)
                VALUES (%s, %s, %s)
                """,
                (self.n, player_id, lineup),
            )
            conn.commit()
            cursor.close()
            conn.close()


    def open_fixture(self):
        """Open the fixture in the database and fix lineups
        """
        logger.info(f"Opening fixture {self.n}.")

        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE FIXTURE
            SET opened = true
            WHERE id = %s
            """,
            (self.id,),
        )
        conn.commit()
        cursor.close()
        conn.close()

        self._fix_lineups()



    def __repr__(self):
        return f"Fixture(n={self.n}, start_dt={self.start_dt}, end_dt={self.end_dt}, finished={self.finished})"
    

def get_current_fixture():
    """
    Retrieve the current open fixture from the database.
    
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
            continue

        fixture = Fixture(id=id, n=n, start_dt=start_ts, finished=False, dangling=False)
        logger.info(f"Current fixture found: {fixture}")

        if not opened:
            fixture.open_fixture()

        return fixture
    else:
        logger.info("No open fixture found.")
        return None