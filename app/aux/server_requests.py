from fastapi import FastAPI
import logging
import psycopg2
import os


logger = logging.getLogger(__name__)

server_app = FastAPI()


@server_app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}


@server_app.get("/squads/{player_id}")
def squad(player_id: int):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres_db"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432"),
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM footballer WHERE owner_id = %s ORDER BY id
            """,
            (player_id,),
        )
        players = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"players": players}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"players": []}