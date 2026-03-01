from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from .logger import logger
import imghdr
from fastapi.responses import Response

router = APIRouter(prefix="/team", tags=["team"])


@router.get("/image/{team_name}")
def get_team_image(team_name: str):
    try:
        client = mongo_client()
        db = client["FantasyMDB"]

        team = db.team.find_one({"name": team_name})
        if team is None:
            client.close()
            return {"status": "error", "message": "Team not found."}

        img_field = team.get("image_binary")
        if img_field is None:
            client.close()
            return {"status": "error", "message": "No image found for this team."}

        # Convert bson.Binary to raw bytes if necessary
        img_bytes = bytes(img_field)

        # Try to detect image type
        fmt = imghdr.what(None, img_bytes)
        content_type = f"image/{fmt}" if fmt else "application/octet-stream"

        client.close()
        return Response(content=img_bytes, media_type=content_type)

    except Exception as e:
        logger.error(f"Error retrieving team image: {e}")
        return {"status": "error", "message": str(e)}