import logging
import requests
import os
from tabulate import tabulate
from aux.constants import FOOTBALLER_COLUMNS, PLAYER_MARKET_COLUMNS


logger = logging.getLogger(__name__)

class Session():
    def __init__(self):
        self._user = None
        self._player_id = None
        self._active = False

    def _load_users(self):
        users = set()
        user_id = dict()
        try:
            with open("/secrets/users.env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:
                        username, password, player_id = line.split(':')
                        users.add((username.strip(), password.strip()))
                        user_id[username.strip()] = int(player_id.strip())
        except FileNotFoundError:
            logger.error("User secrets file not found.")
        return users, user_id

    def login(self):
        username = input("Enter username: ")
        password = input("Enter password: ")
        users, users_id = self._load_users()

        if (username, password) in users:
            logger.info("Login successful!")
            self._user = username
            self._player_id = users_id[username]
            if self._ping_backend():
                self._active = True
                return True
            else:
                logger.error("Backend is not reachable.")
                return False
        else:
            logger.warning("Invalid username or password.")
            return False
        
    def main_menu(self):
        if not self.active:
            logger.warning("Session is not active. Please log in first.")
            return

        print("\nMain Menu:")
        print("\t1. Squad")
        print("\t2. Market")
        print("\t3. Leaderboard")
        print("\t4. Other players' squad")
        print("\t5. Logout")
        choice = input("Select an option: ")

        if choice == "1":
            self._squad_main()
        elif choice == "2":
            self._market_main()
        elif choice == "3":
            self._leaderboard_main()
        elif choice == "4":
            self._other_players_squad()
        elif choice == "5":
            self.logout()
        else:
            logger.info("Invalid choice.")

    def _squad_main(self):
        print("\nSquad menu:")
        print("\t1. View Squad")
        print("\t2. Edit player status")
        choice = input("Select an option: ")

        if choice == "1":
            self._view_squad(self.player_id)
        elif choice == "2":
            self._edit_player_status()
        else:
            logger.info("Invalid choice.")

    def _other_players_squad(self):
        choice = input("Select a player ID: ")
        self._view_squad(int(choice))

    def _market_main(self):
        print("\nMarket menu:")
        print("\t1. View Market")
        print("\t2. Place bid")
        choice = input("Select an option: ")

        if choice == "1":
            self._view_market()
        elif choice == "2":
            self._place_bid()
        else:
            logger.info("Invalid choice.")

    def _leaderboard_main(self):
        url=f"{os.environ['BACKEND_URL']}/leaderboard"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                players = data.get("leaderboard", [])
                if players:
                    print("\nLeaderboard:")
                    print(tabulate(players, headers=["Position", "Name", "Score", "Squad value"], tablefmt="grid"))
                else:
                    print("No players found in the leaderboard.")
            else:
                logger.error(f"Failed to fetch leaderboard: {response.status_code}")
        except Exception as e:
            logger.error(f"Error while fetching leaderboard: {e}")

    @property
    def user(self):
        return self._user

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        self._active = value
    
    @property
    def player_id(self):
        return self._player_id
    
    def logout(self):
        self.active = False
        logger.info("Logged out successfully.")

    def _ping_backend(self):
        try:
            url = f"{os.environ['BACKEND_URL']}/ping"
            response = requests.get(url)
            if response.status_code == 200:
                logger.info("Backend is reachable.")
                return True
            else:
                logger.error(f"Backend returned error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to reach backend: {e}")
            return False

    def _view_squad(self, player_id: int):
        try:
            url = f"{os.environ['BACKEND_URL']}/squad/{player_id}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                players = data.get("players", [])
                if players:
                    print("\nYour Squad:")
                    print(tabulate(players, headers=FOOTBALLER_COLUMNS, tablefmt="grid"))
                else:
                    print("No players found.")
            else:
                logger.error(f"Failed to fetch squad: {response.status_code}")
        except Exception as e:
            logger.error(f"Error while fetching squad: {e}")

    def _view_market(self):
        try:
            url = f"{os.environ['BACKEND_URL']}/market/{self.player_id}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                players = data.get("players", [])
                if players:
                    print("\nMarket:")
                    print(tabulate(players, headers=PLAYER_MARKET_COLUMNS, tablefmt="grid"))
                else:
                    print("No players found on the market.")
            else:
                logger.error(f"Failed to fetch market: {response.status_code}")
        except Exception as e:
            logger.error(f"Error while fetching market: {e}")


    def _place_bid(self):
        footballer_id = input("Enter the ID of the player you want to bid on: ")
        bid_amount = input("Enter your bid amount: ")

        try:
            url = f"{os.environ['BACKEND_URL']}/market/bids"
            response = requests.post(url, json={"footballer_id": footballer_id, "player_id": self.player_id, "bid_amount": bid_amount})
            if response.status_code == 200:
                logger.info(response.json()['message'])
            else:
                logger.error(f"Failed to request bid: {response.status_code}")
        except Exception as e:
            logger.error(f"Error while placing bid: {e}")

    def _edit_player_status(self):
        footballer_id = input("Enter the ID of the player you want to edit status for: ")
        status_input = input("Enter '1' to place on market or '0' to remove from market: ")
        if status_input not in ['0', '1']:
            logger.error("Invalid input. Please enter '1' or '0'.")
            return
        on_market = status_input == '1'

        try:
            url = f"{os.environ['BACKEND_URL']}/edit_player"
            response = requests.post(url, json={"footballer_id": int(footballer_id), "player_id": self.player_id, "on_market": on_market})
            if response.status_code == 200:
                logger.info(response.json()['message'])
            else:
                logger.error(f"Failed to edit player status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error while editing player status: {e}")