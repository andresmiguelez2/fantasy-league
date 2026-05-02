import logging
from server_requests.server_requests import server_app  # noqa: F401


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s",
    handlers=[logging.StreamHandler()],
)
