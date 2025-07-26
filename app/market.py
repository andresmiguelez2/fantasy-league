import datetime


class Market:
    """Market class to represent a certain market."""

    def __init__(self):
        self._id = None
        self._closing_ts = None

    @property
    def id(self):
        """Get the market ID."""
        return self._id

    @id.setter
    def id(self, value):
        """Set the market ID."""
        self._id = value

    @property
    def closing_ts(self):
        """Get the market closing timestamp."""
        return self._closing_ts

    @closing_ts.setter
    def closing_ts(self, value):
        """Set the market closing timestamp."""
        self._closing_ts = value

    def __str__(self):
        return f"Market(id={self._id}, closing_ts={self._closing_ts})"
