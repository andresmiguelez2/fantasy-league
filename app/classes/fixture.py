from datetime import datetime
import logging
from aux.database import pg_connect
from aux.constants import DANGLING_FIXTURE_THRESHOLD


logger = logging.getLogger(__name__)


class Fixture:
    def __init__(self, **kwargs):
        self._n: str = None
        self._start_dt: datetime = None
        self._end_dt: datetime = None
        self._finished: bool = None
        self._dangling: bool = None # incicates if fixture is somewhat abnormal

        for key, value in kwargs.items():
            setattr(self, key, value)
    
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

    def __repr__(self):
        return f"Fixture(n={self.n}, start_dt={self.start_dt}, end_dt={self.end_dt}, finished={self.finished})"
    

def get_current_fixture():
    conn = pg_connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            n
            , start_ts
            , now() - start_ts AS time_open
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

    for n, start_ts, time_open in open_fixtures:
        if time_open.days >= DANGLING_FIXTURE_THRESHOLD:
            logger.warning(f"Dangling fixture detected: Fixture {n} has been open for {time_open}")
            continue

        return Fixture(n=n, start_dt=start_ts, finished=False, dangling=False)
    else:
        logger.info("No open fixture found.")
        return None