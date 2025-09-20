import logging
import requests

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
            with open("secrets/users.env", "r") as f:
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
            self._active = True
            return True
        else:
            logger.warning("Invalid username or password.")
            return False
        
    def main_menu(self):
        if not self.active:
            logger.warning("Session is not active. Please log in first.")
            return

        logger.info("\nMain Menu:")
        logger.info("\t1. Squad")
        logger.info("\t2. Market")
        logger.info("\t3. Leaderboard")
        logger.info("\t4. Logout")
        choice = input("Select an option: ")

        if choice == "1":
            self._squad_main()
        elif choice == "2":
            self._market_main()
        elif choice == "3":
            self._leaderboard_main()
        elif choice == "4":
            self.logout()
        else:
            logger.info("Invalid choice.")

    def _squad_main(self):
        logger.info("Squad management is not implemented yet.")

    def _market_main(self):
        logger.info("Market interaction is not implemented yet.")

    def _leaderboard_main(self):
        logger.info("Leaderboard viewing is not implemented yet.")

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
        
    def ping_backend(self):
        try:
            # Use the service name and port as defined in docker-compose.yml
            url = "http://backend_app:8000/ping"
            response = requests.get(url)
            if response.status_code == 200:
                logger.info("Backend is reachable:", response.text)
            else:
                logger.error("Backend returned error:", response.status_code)
        except Exception as e:
            logger.error("Failed to reach backend:", e)