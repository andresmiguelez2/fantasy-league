import datetime
import os
import logging
import psycopg2
import random

from aux.constants import N_NEW_FOOTBALLERS_INTO_MARKET
from pymongo import MongoClient
from aux.database import pg_connect, mongo_client


# Create logger for this module
logger = logging.getLogger(__name__)


class Market:
    """Market class to represent a certain market."""

    def __init__(self):
        self._id = None
        self._league_id = None
        self._closing_ts = None
        self._has_been_closed = None

    @property
    def id(self):
        """Get the market ID."""
        return self._id

    @id.setter
    def id(self, value):
        """Set the market ID."""
        self._id = value

    @property
    def closing_ts(self):
        """Get the market closing timestamp."""
        return self._closing_ts

    @closing_ts.setter
    def closing_ts(self, value):
        """Set the market closing timestamp."""
        if self._closing_ts is not None:
            logger.info("Market closing timestamp overridden")
        self._closing_ts = value

    @property
    def has_been_closed(self):
        """Get the market closed status."""
        return self._has_been_closed

    @has_been_closed.setter
    def has_been_closed(self, value):
        """Set the market closed status."""
        self._has_been_closed = value

    @property
    def league_id(self):
        """Get the league ID."""
        return self._league_id

    @league_id.setter
    def league_id(self, value):
        """Set the league ID."""
        self._league_id = value

    def _is_active(self):
        """Check if the market is still active based on the closing timestamp."""
        if self._closing_ts:
            return self._closing_ts > datetime.datetime.now(tz=datetime.timezone.utc)
        return False
    
    def _open_new_market(self, cursor):
        cursor.execute(
            """
            INSERT INTO market (id, closing_timestamp, has_been_closed, league_id)
            VALUES (default, '{}', FALSE, {})
            """.format(datetime.datetime.strftime(self._closing_ts + datetime.timedelta(days=1), "%Y-%m-%d %H:%M:%S"), self.league_id)
        )
        logger.info(f"New market opened. League {self.league_id}.")

    def _cleanup_market(self, cursor) -> list[int]:
        """Removes footballers without bids and owner from the market.
            
        returns:
            list[int]: List of footballer IDs removed from the market.
        """
        cursor.execute(
            """
            SELECT id
            FROM footballer
            WHERE 
                on_market = TRUE
                AND owner_id IS NULL
                AND league_id = %s
            """, (self.league_id,)
        )
        footballers_to_remove = cursor.fetchall()
        if footballers_to_remove:
            cursor.execute(
                """
                UPDATE footballer
                SET
                    on_market = FALSE,
                    on_market_since = NULL
                WHERE id IN %s AND league_id = %s
                """,
                (tuple([f[0] for f in footballers_to_remove]), self.league_id)
            )
            logger.info(f"Removed footballers without bids and owner from market: {footballers_to_remove}. League {self.league_id}.")

        return [f_[0] for f_ in footballers_to_remove]

    def _place_footballers_into_market(self, cursor, n_agents, just_removed):
        """Place free agents into the market."""
        cursor.execute(
            """
            SELECT footballer.id
            FROM footballer
            WHERE 
                footballer.owner_id IS NULL 
                AND footballer.on_market = FALSE
                AND footballer.id NOT IN %s
                AND footballer.league_id = %s
            """,
            (tuple(just_removed) if just_removed else (0,), self.league_id)
        )
        free_agents = cursor.fetchall()
        chosen_free_agents = random.sample(free_agents, min(n_agents, len(free_agents)))

        cursor.execute(
            """
            UPDATE footballer
            SET
                on_market = TRUE,
                on_market_since = now()
            WHERE 
                id in %s
                AND league_id = %s;
            """,
            (tuple([fa[0] for fa in chosen_free_agents]), self.league_id)
        )
        logger.info(f"Placed players {chosen_free_agents} into the market. League {self.league_id}.")

    def _assign_bids(self, cursor):
        """Assign bids placed on league players."""
        cursor.execute(
            """
            SELECT 
                bid.footballer_id
                , bid.bidder_id
                , bid.amount
            FROM bid JOIN footballer ON footballer.id = bid.footballer_id
            WHERE
                bid.league_id = %s
                AND footballer.owner_id IS NULL
                AND footballer.on_market = TRUE -- para mayor robustez
            ORDER BY 
                amount DESC
                , timestamp ASC
            """, (self.league_id, )
        )
        bid_data = cursor.fetchall()

        bid_players = dict()
        for bid in bid_data:
            footballer_id, bidder_id, amount = bid
            if footballer_id not in bid_players:
                bid_players[footballer_id] = (bidder_id, amount)
            elif amount > bid_players[footballer_id][1]:
                bid_players[footballer_id] = (bidder_id, amount)
            elif amount == bid_players[footballer_id][1]:
                logger.warning(f"Bid for footballer {footballer_id} by {bidder_id} with amount {amount} is equal to an existing bid. Skipping.")

        for footballer_id, (bidder_id, amount) in bid_players.items():
            cursor.execute(
                """
                UPDATE footballer
                SET 
                    on_market = FALSE,
                    owner_id = %s,
                    on_market_since = NULL
                WHERE id = %s AND league_id = %s;
                DELETE FROM bid
                WHERE footballer_id = %s AND league_id = %s;
                """,
                (bidder_id, footballer_id, self.league_id, footballer_id, self.league_id)
            )

            if bidder_id is not None:
                cursor.execute(
                    """
                    UPDATE player
                    SET budget = budget - %s
                    WHERE id = %s AND league_id = %s
                    """,
                    (amount, bidder_id, self.league_id)
                )

            logger.info(f"Footballer {footballer_id} assigned to bidder {bidder_id} with amount {amount}. League {self.league_id}.")
            
            
    def fulfill_market(self):
        """Fulfill the market if it has been closed."""
        if not self._is_active() and not self._has_been_closed:
            self._has_been_closed = True
            logger.info(f"Market {self._id} has been closed.")

            try:
                conn = pg_connect()
                cursor = conn.cursor()

                cursor.execute(
                    f"""
                    UPDATE market
                    SET has_been_closed = TRUE
                    WHERE id = {self._id}
                    """
                )
                logger.info(f"Database updated: Market {self._id} marked as closed")

                self._assign_bids(cursor)
                self._open_new_market(cursor)
                removed_from_market = self._cleanup_market(cursor)
                self._place_footballers_into_market(cursor, N_NEW_FOOTBALLERS_INTO_MARKET, removed_from_market)
                self._place_bid_on_footballers(cursor)

                conn.commit()
                cursor.close()
                conn.close()
                
            except psycopg2.Error as e:
                logger.error(f"Database error while fulfilling market {self._id}: {e}")
                self._has_been_closed = False# Rollback the local state change if database update failed

    def _place_bid_on_footballers(self, cursor):
        """Place bids on all footballers owned by someone on the market, by the league."""
        cursor.execute(
            """
            SELECT
                f.id
                , fd.value
            FROM footballer f LEFT JOIN footballer_data fd ON f.id = fd.id
            WHERE
                owner_id IS NOT NULL
                AND on_market = true
                AND f.league_id = %s
            """, (self.league_id,)
        )
        footballers_on_market = cursor.fetchall()

        cursor.execute(
            """
            DELETE FROM BID
            WHERE bidder_id IS NULL AND league_id = %s
            """, (self.league_id,)
        )

        for id, value in footballers_on_market:
            bid_amount = Market.get_random_bid(value)
            cursor.execute(
                """
                INSERT INTO bid (footballer_id, bidder_id, amount, timestamp, league_id)
                VALUES (%s, %s, %s, now(), %s)
                """,
                (id, None, bid_amount, self.league_id)
            )
            logger.info(f"League placed bid of amount {bid_amount} on footballer {id}. League {self.league_id}.")


    def shift_closing_ts(self):
        """Shift the market closing timestamp far into the future."""
        self.closing_ts += datetime.timedelta(days=9999)

    def __str__(self):
        return f"Market(id={self._id}, closing_ts={self._closing_ts}, has_been_closed={self._has_been_closed})"
    
    @classmethod
    def get_random_bid(cls, market_value):
        """Generate a random bid based on the market value."""
        bid_multiplier = random.uniform(0.9, 1.1)
        return int(market_value * bid_multiplier)
    

def load_market(league_id: int):
    """Load the active market from the database."""
    try:
        logger.debug("Loading market data...")
        logger.debug("Connecting to database...")
        
        conn = pg_connect()
        cursor = conn.cursor()

        logger.debug("Executing market query...")
        
        cursor.execute(
            """
            SELECT *
            FROM market
            WHERE closing_timestamp > now() AND has_been_closed = FALSE AND league_id = %s
            """, 
            (league_id,)
        )
        market_data = cursor.fetchall()

        if len(market_data) > 1:
            logger.error("Several concurrent markets found in the database.")
            raise ValueError("Several concurrent markets found in the database.")
        if len(market_data) == 0:
            logger.warning(f"No active market found in the database for league {league_id}.")
            return None

        market = Market()
        market.id = market_data[0][0]
        market.closing_ts = market_data[0][1]
        market.has_been_closed = market_data[0][2]
        market.league_id = market_data[0][3]
        logger.info(f"Found market {market}")

        cursor.close()
        conn.close()
        logger.debug("Database connection closed successfully")

        return market

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return []

def load_last_market(league_id: int):
    try:
        logger.debug("Loading last unfulfilled market...")
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM market
            WHERE closing_timestamp < now() AND has_been_closed = FALSE AND league_id = %s
        """,
            (league_id,)
        )
        market_data = cursor.fetchall()

        if len(market_data) > 1:
            logger.error(f"Several non closed markets found in the database for league {league_id}.")
            raise ValueError(f"Several non closed markets found in the database for league {league_id}.")
        if len(market_data) == 0:
            logger.error(f"No non closed market found in the database for league {league_id}.")
            raise ValueError(f"No non closed market found in the database for league {league_id}.")

        market = Market()
        market.id = market_data[0][0]
        market.closing_ts = market_data[0][1]
        market.has_been_closed = market_data[0][2]
        market.league_id = market_data[0][3]
        logger.info(f"Found non closed market {market}")

        cursor.close()
        conn.close()

        return market
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return None