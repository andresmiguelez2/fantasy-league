from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from .logger import logger
from pydantic import BaseModel
from aux.aux_functions import extract_fixture_points
import imghdr
from fastapi.responses import Response



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