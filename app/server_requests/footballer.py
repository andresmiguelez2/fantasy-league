from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from .logger import logger
from pydantic import BaseModel
from aux.aux_functions import extract_fixture_points, scrape_page
import imghdr
from fastapi.responses import Response
from classes.footballer import Footballer
import time
from aux.constants import FANTASY_PLAYER_URL, FOOTBALLER_POSITIONS


router = APIRouter(prefix="/footballer", tags=["footballer"])


@router.get("/{footballer_id}")
def get_footballer_info(footballer_id: int):
    """Get information about a specific footballer."""
    try:
        conn = pg_connect()
        client = mongo_client()
        db = client["FantasyMDB"]

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
    

@router.get("s")
def get_all_footballers(limit: int = 20, offset: int = 0, page: int | None = None, sort_by: str = 'name'):
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
    if sort_by not in sort_map:
        sort_by = 'name'

    limit = max(1, min(int(limit), 100))
    if page is not None:
        page = max(1, int(page))
        offset = (page - 1) * limit
    else:
        offset = max(0, int(offset))

    sort_col = sort_map[sort_by]
    direction = 'ASC' if sort_by == 'name' else 'DESC'

    try:
        conn = pg_connect()
        cursor = conn.cursor()

        # total count for pagination meta
        cursor.execute("SELECT COUNT(*) FROM footballer_data")
        total = cursor.fetchone()[0]

        query = f"""
            SELECT
                id
                , name
                , team
                , value
                , average_points
                , total_points AS points
            FROM footballer_data
            ORDER BY {sort_col} {direction}
            LIMIT %s
            OFFSET %s
            """

        cursor.execute(query, (limit, offset))
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
            }
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

        cursor.execute(
            """
            UPDATE footballer_data
            SET (last_updated, total_points, average_points, value) = (SELECT NOW(), %s, %s, %s)
            WHERE id = %s
            """,
            (fb.data['total_points'], fb.data['average_points'], fb.data['market_details'][-1]['value'], footballer_id)
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

        conn.commit()
        cursor.close()
        conn.close()
        client.close()

        elapsed_time = time.time() - init_time

        logger.info(f"Updated footballer {footballer_id}. Elapsed time: {elapsed_time:.4f} seconds.")
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
