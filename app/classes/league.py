from aux.database import pg_connect


def get_leagues() -> list[int]:
    """Get all the leagues that are currently active in the database.
    """
    conn = pg_connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT league.id
        FROM league JOIN player ON league.id = player.league_id
        GROUP BY league.id
        HAVING COUNT(player.id) > 0
        """
    )

    leagues = [row[0] for row in cursor.fetchall()]
    return leagues