import datetime
import logging
import re
import requests
from bson import Binary
from aux.server_requests import scrape_page

from aux.constants import FANTASY_PLAYER_URL, FANTASY_PLAYER_MARKET_URL, COMPETITION_NAME


logger = logging.getLogger(__name__)


class Footballer():
    def __init__(self, obtain_data=False, name=None, full_name=None):
        self._id: int = None
        self._name: str = None
        self._full_name: str = None
        self._url_name: str = None
        self._price: int = None
        self._on_market: bool = None
        self._owner_id: int = None
        self._data: dict = None
        self._team: str = None
        
        if obtain_data and name:
            self._name = name
            self._full_name = full_name
            self._url_name = name.replace(" ", "-")
            self._get_player_data()

    @property
    def id(self):
        """Get the footballer ID."""
        return self._id
    
    @id.setter
    def id(self, value):
        """Set the footballer ID."""
        self._id = value

    @property
    def name(self):
        """Get the footballer name."""
        return self._name
    
    @name.setter
    def name(self, value):
        """Set the footballer name."""
        self._name = value
    
    @property
    def full_name(self):
        """Get the footballer full name."""
        return self._full_name

    @full_name.setter
    def full_name(self, value):
        """Set the footballer full name."""
        if '-1' in value:
            logger.warning(f"Full name not found in API: {value}")
        self._full_name = value

    @property
    def url_name(self):
        """Get the footballer URL name."""
        return self._url_name

    @url_name.setter
    def url_name(self, value):
        """Set the footballer URL name."""
        self._url_name = value

    @property
    def price(self):
        """Get the footballer price."""
        return self._price
    
    @price.setter
    def price(self, value):
        """Set the footballer price."""
        self._price = value

    @property
    def on_market(self):
        """Check if the footballer is on the market."""
        return self._on_market
    
    @on_market.setter
    def on_market(self, value):
        """Set the footballer on market status."""
        self._on_market = value

    @property
    def owner_id(self):
        """Get the footballer owner_id ID."""
        return self._owner_id
    
    @owner_id.setter
    def owner_id(self, value):
        """Set the footballer owner ID."""
        self._owner_id = value

    @property
    def data(self):
        """Get the footballer data."""
        return self._data

    @data.setter
    def data(self, value):
        """Set the footballer data."""
        self._data = value

    @property
    def team(self):
        """Get the footballer team."""
        return self._team

    @team.setter
    def team(self, value):
        """Set the footballer team."""
        self._team = value

    def __str__(self):
        attrs = [attr for attr in dir(self) if attr.startswith('_') and not attr.startswith('__')]
        attr_strs = []
        for attr in attrs:
            attr_strs.append(f"{attr[1:]}={getattr(self, attr)}")
        return f"Footballer({', '.join(attr_strs)})"


    def _get_total_points(self, soup):
        """Extracts the total points from the player's page soup."""
        # Find the main info div
        info_div = soup.find("div", class_="info laliga-fantasy d-none border-none")
        if info_div:
            # Find the right-side div with the points
            points_div = info_div.find("div", class_="info-right rachita")
            if points_div:
                points_text = points_div.get_text(strip=True)
                logger.debug(f"Found total points: {points_text}")
                return int(points_text if points_text else 0)

        logger.warning("Total points not found.")
        return 0


    def _get_average_points(self, soup):
        """Extracts the average points from the player's page soup."""
        # Find all <span> tags and check if their text contains "Media puntos"
        media_spans = soup.find_all("span", class_="racha-box columna_puntos point mx-auto")
        for span in media_spans:
            if "Media puntos" in span.get_text():
                # Go up to the parent <td>
                td = span.find_parent("td")
                if td:
                    # Find the next <td> with the desired class
                    next_td = td.find_next_sibling("td", class_="data points bold d-flex rachita")
                    if next_td:
                        points_str = next_td.text.strip('\n').strip(' ')
                        first_break = points_str.find('\n')
                        fantasy_points = points_str[:first_break]
                        try:
                            return float(fantasy_points)
                        except ValueError:
                            return fantasy_points
        logger.warning("Average points not found.")
        return None

    def _parse_stat_text(self, stat_text):
        """Parses a statistic text and returns the stat name, value, and points.
        Handles formats like:
        - [value] [stat_name] [points] p
        - [stat_name] [points] p
        """
        # Try to match: [value] [stat_name] [points] p
        match = re.match(r"(\d+)\s+([^\d]+?)\s+(-?\d+)\s*p", stat_text)
        if match:
            value = int(match.group(1))
            stat_name = match.group(2).strip()
            points = int(match.group(3))
            return stat_name, {'value': value, 'points': points}
        # Try to match: [stat_name] [points] p (no value)
        match = re.match(r"([^\d]+?)\s+(-?\d+)\s*p", stat_text)
        if match:
            stat_name = match.group(1).strip()
            points = int(match.group(2))
            return stat_name, {'value': None, 'points': points}
        return None, None

    def _get_fixture_breakdown(self, soup):
        """Extracts the fixture breakdown from the player's page soup."""
        breakdowns = []
        # Find all fixture rows
        for fixture_td in soup.find_all("td", class_="bold jorn-td"):
            fixture_str = fixture_td.get_text(strip=True)
            # Extract the integer before the first non-numeric character
            match = re.match(r"(\d+)", fixture_str)
            fixture_number = int(match.group(1)) if match else fixture_str
            # The fixture row's parent is a <tr>, so find the next <tr class="desglose">
            desglose_tr = fixture_td.find_parent("tr").find_next_sibling("tr", class_="desglose")
            if desglose_tr:
                # Find all statistics divs inside this breakdown
                stats_dict = {}
                for stat_div in desglose_tr.find_all("div", class_="estadistica"):
                    stat_text = stat_div.get_text(separator=" ", strip=True)
                    stat_name, stat_entry = self._parse_stat_text(stat_text)
                    if stat_name:
                        stats_dict[stat_name] = stat_entry
                    if stat_name in ['Puntos DAZN', 'Puntos Relevo']: break
                breakdowns.append({
                    "fixture": fixture_number,
                    "breakdown": stats_dict
                })
        return breakdowns

    def _get_player_data(self):
        """Fetches and parses player data from the fantasy football website."""
        search_url = FANTASY_PLAYER_URL + self.url_name
        soup = scrape_page(search_url)

        if COMPETITION_NAME not in soup.text:
            if '-1' not in self.url_name:
                self.url_name += '-1'
                self._get_player_data()
            logger.debug(f"Player {self.url_name} does not belong to {COMPETITION_NAME}.")
            return

        total_points = self._get_total_points(soup)
        average_points = self._get_average_points(soup)
        fixture_breakdown = self._get_fixture_breakdown(soup)
        image_url = self._get_player_image_url(soup)
        image_binary = self._get_image_binary(image_url) if image_url else None
        player_id = int(image_url.split('/')[-1].split('.')[0]) if image_url else None
        market_details = self._get_market_details(player_id) if player_id else None
        self.team = self._get_team(soup)

        self.data = {
            "player_source_id": player_id,
            "team": self.team,
            "total_points": total_points,
            "average_points": average_points,
            "fixture_breakdown": fixture_breakdown,
            "image_binary": image_binary,
            "market_details": market_details
        }

    def get_player_data(self):
        """Public method to get player data, fetching it if not already done.
        url_name must be set first."""
        self._get_player_data()

    def _get_market_details(self, player_id):
        """
        Fetches market details for a player by scraping the chart data from the analytics page.
        Returns a list of dicts with 'date' and 'value'.
        """
        url = FANTASY_PLAYER_MARKET_URL + str(player_id)
        soup = scrape_page(url)
        # Find all script tags and search for player_chartjs.push({...})
        chart_data = []
        script_tags = soup.find_all("script")
        pattern = re.compile(r'player_chartjs\.push\(\{date:"([^"]+)",value:(\d+)\}\)')
        for script in script_tags:
            if script.string:
                for match in pattern.finditer(script.string):
                    date = match.group(1)
                    value = int(match.group(2))
                    chart_data.append({"date": date, "value": value})
        logger.debug(f"Found {len(chart_data)} market data points for player {player_id}")
        return list(reversed(chart_data))

    def _get_player_image_url(self, soup):
        """Extracts the player's image URL from the player's page soup."""
        # Find the modal div by id
        modal_div = soup.find("div", id="player-polygon")
        if modal_div:
            # Find the <img> inside the <h5 class="modal-title">
            h5 = modal_div.find("h5", class_="modal-title")
            if h5:
                img = h5.find("img")
                if img and img.has_attr("src"):
                    return img["src"]
        logger.warning("Player image URL not found.")
        return None
    
    def _get_image_binary(self, image_url):
        response = requests.get(image_url)
        if response.status_code == 200:
            img_binary = Binary(response.content)
            return img_binary
        logger.warning("Image binary not found.")
        return None


    def _get_team(self, soup):
        """Extracts the player's team from the player's page soup."""
        # Find all <a> tags with the team URL pattern
        team_links = [a for a in soup.find_all("a", href=True) if "https://www.futbolfantasy.com/laliga/equipos/" in a["href"]]
        if len(team_links) >= 41:
            team_a = team_links[40]  # 41st appearance (0-based index)
            img = team_a.find("img")
            if img and img.has_attr("alt"):
                return img["alt"]
        logger.warning("Team not found for player.")
        return None
        

class Bid():
    def __init__(self):
        self._footballer_id: int = None
        self._bidder_id: int = None
        self._amount: int = None
        self._timestamp: datetime.datetime = None

    @property
    def footballer_id(self):
        """Get the footballer ID associated with the bid."""
        return self._footballer_id
    
    @footballer_id.setter
    def footballer_id(self, value):
        """Set the footballer ID for the bid."""
        self._footballer_id = value

    @property
    def bidder_id(self):
        """Get the bidder ID."""
        return self._bidder_id
    
    @bidder_id.setter
    def bidder_id(self, value):
        """Set the bidder ID."""
        self._bidder_id = value

    @property
    def amount(self):
        """Get the bid amount."""
        return self._amount
    
    @amount.setter
    def amount(self, value):
        """Set the bid amount."""
        self._amount = value

    @property
    def timestamp(self):
        """Get the bid timestamp."""
        return self._timestamp
    
    @timestamp.setter
    def timestamp(self, value):
        """Set the bid timestamp."""
        self._timestamp = value

    def __str__(self):
        attrs = [attr for attr in dir(self) if attr.startswith('_') and not attr.startswith('__')]
        attr_strs = []
        for attr in attrs:
            attr_strs.append(f"{attr[1:]}={getattr(self, attr)}")

    def __repr__(self):
        attrs = [attr for attr in dir(self) if attr.startswith('_') and not attr.startswith('__')]
        attr_strs = []
        for attr in attrs:
            attr_strs.append(f"{attr[1:]}={getattr(self, attr)}")

        return '\n'.join(attr_strs)