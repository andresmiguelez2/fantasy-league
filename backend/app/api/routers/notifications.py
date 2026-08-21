import json
import os
import threading
import time

from fastapi import APIRouter
from pydantic import BaseModel
from pywebpush import WebPushException, webpush

from .logger import logger
from backend.app.db.database import pg_connect


router = APIRouter(prefix="/notifications", tags=["notifications"])

PUSH_SEND_DELAY_SECONDS = 1.0


def _vapid_config() -> tuple[str | None, str | None, str]:
    return (
        os.getenv("VAPID_PUBLIC_KEY"),
        os.getenv("VAPID_PRIVATE_KEY"),
        os.getenv("VAPID_SUBJECT", "mailto:admin@fantasytato.mooo.com"),
    )


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


def ensure_push_subscriptions_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS push_subscription (
            id SERIAL PRIMARY KEY,
            player_id INT NOT NULL,
            league_id INT NOT NULL,
            endpoint TEXT NOT NULL UNIQUE,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )


def send_push_to_player(
    player_id: int,
    league_id: int,
    notification_type: str,
    title: str,
    message: str,
) -> None:
    """Send a Web Push for every subscription of a player. Best-effort only:
    failures (including expired subscriptions) are logged and never raised.
    """
    public_key, private_key, subject = _vapid_config()
    if not public_key or not private_key:
        return

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        ensure_push_subscriptions_table(cursor)
        cursor.execute(
            """
            SELECT endpoint, p256dh, auth
            FROM push_subscription
            WHERE player_id = %s AND league_id = %s
            """,
            (player_id, league_id),
        )
        subscriptions = cursor.fetchall()
        cursor.close()

        payload = json.dumps({
            "type": notification_type,
            "title": title,
            "message": message,
        })

        dead_endpoints = []
        for endpoint, p256dh, auth in subscriptions:
            try:
                webpush(
                    subscription_info={
                        "endpoint": endpoint,
                        "keys": {"p256dh": p256dh, "auth": auth},
                    },
                    data=payload,
                    vapid_private_key=private_key,
                    vapid_claims={"sub": subject},
                )
            except WebPushException as e:
                status_code = getattr(getattr(e, "response", None), "status_code", None)
                if status_code in (404, 410):
                    dead_endpoints.append(endpoint)
                else:
                    logger.error(f"Push to {endpoint} failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error pushing to {endpoint}: {e}")

        if dead_endpoints:
            cursor.execute(
                "DELETE FROM push_subscription WHERE endpoint = ANY(%s)",
                (dead_endpoints,),
            )

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error sending web pushes: {e}")


def queue_push_notification(
    player_id: int,
    league_id: int,
    notification_type: str,
    title: str,
    message: str,
) -> None:
    """Queue a Web Push in the background so it never blocks or fails requests.

    The short delay gives callers time to commit their transaction before the
    push goes out.
    """

    public_key, private_key, _ = _vapid_config()
    if not public_key or not private_key:
        return

    def worker() -> None:
        time.sleep(PUSH_SEND_DELAY_SECONDS)
        send_push_to_player(player_id, league_id, notification_type, title, message)

    threading.Thread(target=worker, daemon=True).start()


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
    queue_push_notification(player_id, league_id, notification_type, title, message)


@router.get("/vapid-public-key")
def get_vapid_public_key():
    public_key, _, _ = _vapid_config()
    if not public_key:
        logger.error("VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY are not configured")
        return {"status": "error", "public_key": None}
    return {"status": "success", "public_key": public_key}


class PushSubscriptionRequest(BaseModel):
    player_id: int
    league_id: int
    endpoint: str
    keys: dict[str, str]


@router.post("/subscribe")
def subscribe_push(request: PushSubscriptionRequest):
    p256dh = request.keys.get("p256dh")
    auth = request.keys.get("auth")
    if not p256dh or not auth or not request.endpoint.startswith("https://"):
        return {"status": "error", "message": "Invalid push subscription."}

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        ensure_push_subscriptions_table(cursor)
        cursor.execute(
            """
            INSERT INTO push_subscription (player_id, league_id, endpoint, p256dh, auth)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (endpoint) DO UPDATE
            SET player_id = EXCLUDED.player_id,
                league_id = EXCLUDED.league_id,
                p256dh = EXCLUDED.p256dh,
                auth = EXCLUDED.auth
            """,
            (request.player_id, request.league_id, request.endpoint, p256dh, auth),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error subscribing to push: {e}")
        return {"status": "error", "message": str(e)}


class UnsubscribeRequest(BaseModel):
    endpoint: str


@router.post("/unsubscribe")
def unsubscribe_push(request: UnsubscribeRequest):
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        ensure_push_subscriptions_table(cursor)
        cursor.execute("DELETE FROM push_subscription WHERE endpoint = %s", (request.endpoint,))
        deleted = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "deleted": deleted}
    except Exception as e:
        logger.error(f"Error unsubscribing from push: {e}")
        return {"status": "error", "deleted": 0}


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
