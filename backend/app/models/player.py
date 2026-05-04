import logging
from backend.app.db.database import pg_connect


logger = logging.getLogger(__name__)


def debit_player_value(player_id: int, amount: int):
    """Debit value from player's budget
    Args:
        player_id (int): The player ID
        amount (int): The amount to debit
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE player
            SET budget = budget - %s
            WHERE id = %s
            """,
            (amount, player_id),
        )

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Debited {amount:,.0f} from player {player_id}'s budget.")

        return True
    except Exception as e:
        logger.error(f"Error while debiting player budget: {e}")
        return False