from fastapi import APIRouter
from pydantic import BaseModel

from .logger import logger
from backend.app.db.database import pg_connect


router = APIRouter(prefix="/notifications", tags=["notifications"])


def ensure_notifications_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS app_notification (
            id SERIAL PRIMARY KEY,
            player_id INT NOT NULL,
            league_id INT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            read_at TIMESTAMPTZ NULL
        );
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS app_notification_unread_idx
        ON app_notification (player_id, league_id, read_at, created_at DESC);
        """
    )


def create_player_notification(
    cursor,
    player_id: int,
    league_id: int,
    notification_type: str,
    title: str,
    message: str,
) -> None:
    ensure_notifications_table(cursor)
    cursor.execute(
        """
        INSERT INTO app_notification (player_id, league_id, type, title, message)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (player_id, league_id, notification_type, title, message),
    )


@router.get("/{player_id}")
def get_notifications(player_id: int, league_id: int, unread_only: bool = True, limit: int = 20):
    bounded_limit = max(1, min(limit, 100))

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        ensure_notifications_table(cursor)

        if unread_only:
            cursor.execute(
                """
                SELECT id, type, title, message, created_at, read_at
                FROM app_notification
                WHERE player_id = %s AND league_id = %s AND read_at IS NULL
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (player_id, league_id, bounded_limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, type, title, message, created_at, read_at
                FROM app_notification
                WHERE player_id = %s AND league_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (player_id, league_id, bounded_limit),
            )

        notifications = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "notifications": [
                {
                    "id": row[0],
                    "type": row[1],
                    "title": row[2],
                    "message": row[3],
                    "created_at": row[4],
                    "read_at": row[5],
                }
                for row in notifications
            ],
        }
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        return {"status": "error", "notifications": []}


class MarkReadRequest(BaseModel):
    player_id: int
    league_id: int
    notification_ids: list[int] = []
    mark_all: bool = False


@router.post("/mark-read")
def mark_notifications_read(request: MarkReadRequest):
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        ensure_notifications_table(cursor)

        if request.mark_all:
            cursor.execute(
                """
                UPDATE app_notification
                SET read_at = now()
                WHERE player_id = %s AND league_id = %s AND read_at IS NULL
                """,
                (request.player_id, request.league_id),
            )
        elif request.notification_ids:
            cursor.execute(
                """
                UPDATE app_notification
                SET read_at = now()
                WHERE
                    player_id = %s
                    AND league_id = %s
                    AND read_at IS NULL
                    AND id = ANY(%s)
                """,
                (request.player_id, request.league_id, request.notification_ids),
            )
        else:
            cursor.close()
            conn.close()
            return {"status": "success", "updated": 0}

        updated = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "updated": updated}
    except Exception as e:
        logger.error(f"Error marking notifications as read: {e}")
        return {"status": "error", "updated": 0}
