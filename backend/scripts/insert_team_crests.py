from backend.app.db.database import mongo_client
from backend.app.core.constants import TEAM_NAME_DICT
import time
import requests
from bson.binary import Binary


def get_image_binary(image_url):
    for attempt in range(4):
        response = requests.get(
            image_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            },
            timeout=30,
        )
        if response.status_code == 429 or 500 <= response.status_code < 600:
            print(
                f"Rate limited while fetching image {image_url}; retrying in {2 ** attempt}s (attempt {attempt + 1}/4)"
            )
            time.sleep(2**attempt)
            continue

        if response.status_code == 200:
            img_binary = Binary(response.content)
            return img_binary

        break

    return None


if __name__ == "__main__":
    client = mongo_client()
    db = client["FantasyMDB"]

    for i in range(1, 60):
        try:
            url = f"https://static.futbolfantasy.com/uploads/images/cabecera/webp/{i}.webp"

            image_binary = get_image_binary(url)

            document = {"name": TEAM_NAME_DICT[i], "image_binary": image_binary}

            db.team.insert_one(document)
        except Exception as e:
            print(f"Error processing team {i}: {e}")
