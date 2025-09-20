import datetime
import os
import logging
import psycopg2
import random

from aux.constants import N_NEW_FOOTBALLERS_INTO_MARKET

# Create logger for this module
logger = logging.getLogger(__name__)


class Market:
    """Market class to represent a certain market."""

    def __init__(self):
        self._id = None
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
        self._closing_ts = value

    @property
    def has_been_closed(self):
        """Get the market closed status."""
        return self._has_been_closed

    @has_been_closed.setter
    def has_been_closed(self, value):
        """Set the market closed status."""
        self._has_been_closed = value

    def _is_active(self):
        """Check if the market is still active based on the closing timestamp."""
        if self._closing_ts:
            return self._closing_ts > datetime.datetime.now(tz=datetime.timezone.utc)
        return False
    
    def _open_new_market(self, cursor):
        cursor.execute(
            """
            INSERT INTO market (id, closing_timestamp, has_been_closed)
            VALUES (default, '{}', FALSE)
            """.format(datetime.datetime.strftime(self._closing_ts + datetime.timedelta(days=1), "%Y-%m-%d %H:%M:%S"))
        )
        logger.info("New market opened.")

    def _cleanup_market(self, cursor):
        """Removes players without bids and owner from the market.
            
        returns:
            list[int]: List of footballer IDs removed from the market.
        """
        cursor.execute(
            """
            SELECT id
            FROM public.footballer
            WHERE 
                on_market = TRUE
                AND owner_id IS NULL
            """
        )
        footballers_to_remove = cursor.fetchall()
        if footballers_to_remove:
            cursor.execute(
                """
                DELETE FROM public.footballer
                WHERE id IN %s
                """,
                (tuple([f[0] for f in footballers_to_remove]),)
            )
            logger.info(f"Removed footballers without bids and owner from market: {footballers_to_remove}")

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
            """,
            (tuple(just_removed) if just_removed else (0,),)
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
                ID in %s;
            """,
            (tuple([fa[0] for fa in chosen_free_agents]),)
        )
        logger.info(f"Placed players {chosen_free_agents} into the market.")

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
                footballer.owner_id IS NULL
                AND footballer.on_market = TRUE -- para mayor robustez
                AND bid.amount >= footballer.price -- para mayor robustez
            ORDER BY 
                amount DESC
                , timestamp ASC
            """,
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
                SET on_market = FALSE, owner_id = %s
                WHERE id = %s;
                DELETE FROM bid
                WHERE footballer_id = %s;
                """,
                (bidder_id, footballer_id, footballer_id)
            )
            logger.info(f"Footballer {footballer_id} assigned to bidder {bidder_id} with amount {amount}.")
            
            
    def fulfill_market(self):
        """Fulfill the market if it has been closed."""
        if not self._is_active() and not self._has_been_closed:
            self._has_been_closed = True
            logger.info(f"Market {self._id} has been closed.")

            try:
                conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "postgres_db"),
                    database=os.getenv("DB_NAME", "postgres"),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", "password"),
                    port=os.getenv("DB_PORT", "5432"),
                )
                cursor = conn.cursor()

                # Use parameterized query to prevent SQL injection
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

                conn.commit()
                cursor.close()
                conn.close()
                
            except psycopg2.Error as e:
                logger.error(f"Database error while fulfilling market {self._id}: {e}")
                self._has_been_closed = False# Rollback the local state change if database update failed


    def __str__(self):
        return f"Market(id={self._id}, closing_ts={self._closing_ts}, has_been_closed={self._has_been_closed})"
    

def load_market():
    """Load the active market from the database."""
    try:
        logger.info("Loading market data...")
        logger.info("Connecting to database...")
        # Connect to PostgreSQL database using environment variables
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres_db"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432"),
        )

        cursor = conn.cursor()

        logger.info("Executing market query...")
        # Example query to load market data
        cursor.execute(
            """
            SELECT *
            FROM market
            WHERE closing_timestamp > now() AND has_been_closed = FALSE
        """
        )
        market_data = cursor.fetchall()

        if len(market_data) > 1:
            logger.error("Several concurrent markets found in the database.")
            raise ValueError("Several concurrent markets found in the database.")
        if len(market_data) == 0:
            logger.warning("No active market found in the database.")
            raise ValueError("No active market found in the database.")

        market = Market()
        market.id = market_data[0][0]
        market.closing_ts = market_data[0][1]
        market.has_been_closed = market_data[0][2]
        logger.info(f"Found market {market}")

        cursor.close()
        conn.close()
        logger.info("Database connection closed successfully")

        return market

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return []
