import datetime
import logging


logger = logging.getLogger(__name__)


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