import datetime


class Market:
    """Market class to represent a certain market."""

    def __init__(self):
        self._id = None
        self._closing_ts = None
        self._has_been_closed = None

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

    @property
    def has_been_closed(self):
        """Get the market closed status."""
        return self._has_been_closed

    @has_been_closed.setter
    def has_been_closed(self, value):
        """Set the market closed status."""
        self._has_been_closed = value

    def is_active(self):
        """Check if the market is still active based on the closing timestamp."""
        if self._closing_ts:
            return self._closing_ts > datetime.datetime.now(tz=datetime.timezone.utc)
        return False

    def __str__(self):
        return f"Market(id={self._id}, closing_ts={self._closing_ts}, has_been_closed={self._has_been_closed})"
