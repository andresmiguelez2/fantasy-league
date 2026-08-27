import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.app.api.routers.general import app_config
from backend.app.core.constants import BID_EXPIRATION_DAYS


class GeneralRouterTests(unittest.TestCase):
    def test_app_config_returns_bid_expiration_days(self):
        config = app_config()
        self.assertEqual(config["bid_expiration_days"], BID_EXPIRATION_DAYS)


if __name__ == "__main__":
    unittest.main()
