import datetime


class Footballer():
    def __init__(self):
        self._id: int = None
        self._name: str = None
        self._price: int = None
        self._on_market: bool = None
        self._owner_id: int = None

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

    def __str__(self):
        attrs = [attr for attr in dir(self) if attr.startswith('_') and not attr.startswith('__')]
        attr_strs = []
        for attr in attrs:
            attr_strs.append(f"{attr[1:]}={getattr(self, attr)}")
        return f"Footballer({', '.join(attr_strs)})"
    

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