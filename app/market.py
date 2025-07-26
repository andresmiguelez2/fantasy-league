import datetime


class Market():
    def __init__(self):
        self._id = None
        self._closing_ts = None
    
    @property
    def id(self):
        return self._id
    
    @property
    def closing_timestamp(self):
        return self._closing_ts
    
    def __str__(self):
        return f"Market(id={self._id}, closing_ts={self._closing_ts})"