from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from .logger import logger
from pydantic import BaseModel
from aux.aux_functions import extract_fixture_points, scrape_page
import imghdr
from fastapi.responses import Response
from classes.footballer import Footballer
import time
import datetime
from aux.constants import FANTASY_PLAYER_URL, FOOTBALLER_POSITIONS, UPDATE_DB_INTERVAL, LINEUP_POSITIONS


router = APIRouter(prefix="/footballer", tags=["footballer"])


def get_last_updated_time(footballer_id: int):
    """Get the last updated time of a footballer from PostgreSQL."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COALESCE(last_updated, '1970-01-01 00:00:00'::timestamp)
            FROM footballer_data
            WHERE id = %s
            """,
            (footballer_id,)
        )

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return row[0]
        else:
            return None
    except Exception as e:
        logger.error(f"Error retrieving last updated time: {e}")
        return None


@router.get("/{footballer_id}")
def get_footballer_info(footballer_id: int):
    """Get information about a specific footballer."""
    try:
        conn = pg_connect()
        client = mongo_client()
        db = client["FantasyMDB"]

        if (datetime.datetime.now(tz=datetime.timezone.utc) - get_last_updated_time(footballer_id)).seconds > UPDATE_DB_INTERVAL:
            update_footballer_info(footballer_id)
        else:
            logger.info(f"Footballer {footballer_id} data is up-to-date; no update needed.")

        document = db.footballer.find_one({"id": footballer_id})
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                full_name
                , team
                , total_points
                , average_points
            FROM footballer_data
            WHERE id = %s
            """,
            (footballer_id,)
        )

        footballer_data = cursor.fetchone()

        cursor.close()
        conn.close()
        client.close()

        if document is None or footballer_data is None:
            return {"status": "error", "message": "Footballer not found."}

        return {
            "status": "success",
            "footballer_info": {
                "name": footballer_data[0],
                "team": footballer_data[1],
                "total_points": footballer_data[2],
                "average_points": footballer_data[3],
                "market_value": document['market_details'][-1]['value'],
                "market_details": document['market_details'],
                "fixture_breakdown": extract_fixture_points(document['fixture_breakdown']),
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving footballer info: {e}")
        return {"status": "error", "message": str(e)}
    

@router.get("/short_name/{footballer_id}")
def get_short_name(footballer_id: int):
    """Get the footballer's short name."""
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name
            FROM footballer_data
            WHERE id = %s
            """,
            (footballer_id,),
        )
        name = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        return {"status": "success", "name": name, "columns": ["name"]}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "footballers": []}


@router.get("/fixture_detail/{footballer_id}")
def get_fixture_detail(footballer_id: int, fixture: int):
    try:
        client = mongo_client()
        db = client["FantasyMDB"]

        document = db.footballer.find_one({"id": footballer_id})
        client.close()

        if document is None:
            return {"status": "error", "message": "Footballer not found."}
        
        return {
            "status": "success",
            "fixture_detail": next(
                (item for item in document['fixture_breakdown'] if item['fixture'] == fixture),
                {}
            )
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/fixture_points/{footballer_id}")
def get_fixture_points(footballer_id: int, fixture: int):
    try:
        client = mongo_client()
        db = client["FantasyMDB"]

        document = db.footballer.find_one({"id": footballer_id})
        client.close()

        if document is None:
            return {"status": "error", "message": "Footballer not found."}

        for fixture_dict in extract_fixture_points(document.get('fixture_breakdown', {})):
            if fixture_dict['fixture'] == fixture:
                points = fixture_dict.get('points', 0)
                break
        else:
            points = 0
        
        return {
            "status": "success",
            "points": points,
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("s")
def get_all_footballers(limit: int = 20, offset: int = 0, page: int | None = None, sort: str = 'name', invert: str = "false", search: str = ""):
    """Get all footballers with pagination and total count.

    Supports either `offset` or `page` (1-based). If `page` is provided it takes precedence and offset is computed as (page-1)*limit.
    Returns SQL tuples in `footballers` for backward compatibility and a `meta` object with `total`, `limit`, `offset`, and `page`.
    """
    # whitelist allowed sort columns
    sort_map = {
        'name': 'name',
        'points': 'total_points',
        'value': 'value'
    }
    if sort not in sort_map:
        sort = 'name'

    limit = max(1, min(int(limit), 100))
    if page is not None:
        page = max(1, int(page))
        offset = (page - 1) * limit
    else:
        offset = max(0, int(offset))

    sort_col = sort_map[sort]
    if sort_col in ['total_points', 'value']:
        direction = 'ASC' if invert == 'true' else 'DESC'
    elif sort_col == 'name':
        direction = 'DESC' if invert == 'true' else 'ASC'

    try:
        conn = pg_connect()
        cursor = conn.cursor()

        # total count for pagination meta (respect search filter)
        # Use unaccent() so searches are accent-insensitive (e -> é matches)
        cursor.execute("SELECT COUNT(*) FROM footballer_data")
        total = cursor.fetchone()[0]

        query = f"""
            SELECT
                f.id
                , fd.name
                , fd.value
                , p.name AS owner_name
                , NULL as on_market_since
                , NULL as bid_amount
                , fd.average_points
                , fd.total_points
            FROM footballer_data fd
            LEFT JOIN footballer f ON fd.id = f.id
            LEFT JOIN player p on f.owner_id = p.id
            WHERE unaccent(fd.full_name) ILIKE unaccent(%s)
            ORDER BY {sort_col} {direction}
            LIMIT %s
            OFFSET %s
            """

        cursor.execute(query, (f"%{search}%", limit, offset,))
        footballers = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "footballers": footballers,
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "page": page if page is not None else None
            },
            "columns": [
                "id",
                "name",
                "value",
                "owner_name",
                "on_market_since",
                "bid_amount",
                "average_points",
                "total_points"
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving footballer info: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/image/{footballer_id}")
def get_footballer_image(footballer_id: int):
    """Return the footballer's image as raw bytes (with proper Content-Type)."""
    try:
        client = mongo_client()
        db = client["FantasyMDB"]

        footballer = db.footballer.find_one({"id": footballer_id})
        if footballer is None:
            client.close()
            return {"status": "error", "message": "Footballer not found."}

        img_field = footballer.get("image_binary")
        if img_field is None:
            client.close()
            return {"status": "error", "message": "No image found for this footballer."}

        # Convert bson.Binary to raw bytes if necessary
        img_bytes = bytes(img_field)

        # Try to detect image type
        fmt = imghdr.what(None, img_bytes)
        content_type = f"image/{fmt}" if fmt else "application/octet-stream"

        client.close()
        return Response(content=img_bytes, media_type=content_type)

    except Exception as e:
        logger.error(f"Error retrieving footballer image: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/update/{footballer_id}")
def update_footballer_info(footballer_id: int):
    """Update footballer information in the database.
    The method will fetch the source for the footballer and update relevant fields in both PostgreSQL and MongoDB."""
    init_time = time.time()

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        client = None

        cursor.execute(
            """
            SELECT url_name
            FROM footballer
            WHERE id = %s
            """,
            (footballer_id,)
        )

        row = cursor.fetchone()

        if not row or not row[0]:
            return {"status": "error", "message": "url_name not found for footballer"}

        url_name = row[0]

        fb = Footballer(obtain_data=False)
        fb.id = footballer_id
        fb.url_name = url_name
        fb.get_player_data()

        if fb.data['market_details']:
            cursor.execute(
                """
                UPDATE footballer_data
                SET (last_updated, total_points, average_points, value, availability) = (SELECT NOW(), %s, %s, %s, CAST(%s AS AVAILABILITY_TYPE))
                WHERE id = %s
                """,
                (fb.data['total_points'], fb.data['average_points'], fb.data['market_details'][-1]['value'], fb.availability, footballer_id)
            )

            client = mongo_client()
            db = client["FantasyMDB"]

            update_fields = {}
            if fb.data is not None:
                if fb.data.get("market_details") is not None:
                    update_fields["market_details"] = fb.data["market_details"]
                if fb.data.get("fixture_breakdown") is not None:
                    update_fields["fixture_breakdown"] = fb.data["fixture_breakdown"]
                # if fb.data.get("image_binary") is not None:
                #     update_fields["image_binary"] = fb.data["image_binary"]

            if update_fields:
                db.footballer.update_one({"id": footballer_id}, {"$set": update_fields}, upsert=True)
        else:
            logger.warning(f"No market details found for footballer {footballer_id}; skipping update. Consider removing from database")

        conn.commit()
        cursor.close()
        conn.close()
        if client:
            client.close()

        elapsed_time = time.time() - init_time

        logger.debug(f"Updated footballer {footballer_id}. Elapsed time: {elapsed_time:.4f} seconds.")
        return {"status": "success", "elapsed_time": round(elapsed_time, 4)}
    except Exception as e:
        logger.error(f"Error updating footballer data: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/update_field/{footballer_id}")
def update_footballer_field(footballer_id: int, field: str = None):
    """Update a specific field of footballer data in the database."""
    init_time = time.time()

    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT url_name
            FROM footballer
            WHERE id = %s
            """,
            (footballer_id,)
        )

        row = cursor.fetchone()

        if not row or not row[0]:
            return {"status": "error", "message": "url_name not found for footballer"}

        url_name = row[0]

        fb = Footballer(obtain_data=False)
        search_url = FANTASY_PLAYER_URL + url_name
        soup = scrape_page(search_url, logger)
        
        if field == 'total_points':
            value = fb._get_total_points(soup)
        elif field == 'average_points':
            value = fb._get_average_points(soup)
        elif field == 'team':
            value = fb._get_team(soup)
        elif field == 'position':
            value = FOOTBALLER_POSITIONS[fb._get_position(soup)]
        else:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Invalid field specified"}

        cursor.execute(
            f"""
            UPDATE footballer_data
            SET {field} = %s
            WHERE id = %s
            """,
            (value, footballer_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        elapsed_time = time.time() - init_time

        logger.info(f"Updated field {field} for footballer {footballer_id}. Elapsed time: {elapsed_time:.4f} seconds.")
        return {"status": "success", "field": field, "elapsed_time": round(elapsed_time, 4)}
    except Exception as e:
        logger.error(f"Error updating footballer data: {e}")
        return {"status": "error", "message": str(e)}


def count_footballers_per_position(player_id: int):
    """Count the number of footballers per position in a player's lineup."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                footballer_data.position
                , COUNT(footballer.id)
            FROM footballer JOIN footballer_data ON footballer.id = footballer_data.id
            WHERE
                footballer.owner_id = %s
                AND footballer.on_lineup = TRUE
            GROUP BY footballer_data.position
            """,
            (player_id,)
        )

        counts = dict(cursor.fetchall())

        cursor.close()
        conn.close()

        return counts
    except Exception as e:
        logger.error(f"Error counting footballers per position: {e}")
        return {}
    

class LineUpFotballer(BaseModel):
    player_id: int
    footballer_id: int
    on_lineup: bool
@router.post("/set_lineup/")
def set_footballer_on_lineup(data: LineUpFotballer):
    """Set or unset a footballer in a player's lineup."""
    try:
        update_footballer_field(data.footballer_id, 'position')

        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT lineup
            FROM player join footballer
            ON player.id = footballer.owner_id
            WHERE
                player.id = %s
                AND footballer.id = %s
            """
        , (data.player_id, data.footballer_id))

        lineup = cursor.fetchone()

        if not lineup:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Footballer not owned by player."}
        else:
            lineup = lineup[0]
        
        cursor.execute(
            """
            UPDATE footballer
            SET on_lineup = %s
            WHERE id = %s
            """,
            (data.on_lineup, data.footballer_id)
        )

        footballers_per_position = count_footballers_per_position(data.player_id)
        logger.info(footballers_per_position)

        for n_spots, pos_name in zip([1] + lineup, LINEUP_POSITIONS):
            if n_spots < footballers_per_position.get(pos_name, 0):
                conn.rollback()
                cursor.close()
                conn.close()
                return {"status": "error", "message": f"Too many {pos_name} in lineup."}
        else:
            conn.commit()
            cursor.close()
            conn.close()

        return {"status": "success", "message": f"Footballer {'added to' if data.on_lineup else 'removed from'} lineup."}
    except Exception as e:
        logger.error(f"Error setting footballer lineup: {e}")
        return {"status": "error", "message": str(e)}
    

@router.post("/change_market_status/{footballer_id}")
def change_market_status(footballer_id: int, on_market: bool):
    """Change the market status of a footballer."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE footballer
            SET
                on_market = %s
                , on_market_since = CASE WHEN %s THEN NOW() ELSE NULL END
            WHERE id = %s
            """,
            (on_market, on_market, footballer_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Footballer {footballer_id} market status changed to {'on market' if on_market else 'off market'}.")
        return {"status": "success", "footballer_id": footballer_id, "on_market": on_market}
    except Exception as e:
        logger.error(f"Error changing footballer market status: {e}")
        return {"status": "error", "message": str(e)}