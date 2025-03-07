import sqlite3
import json
from _typeshed import SupportsRead

class SystemMap:

    def __init__(self, name: str, datadir: str):
        """Initializes empty system map."""
        

    def __init__(self, dbDir: str):
        """Opens a sqlite .db file of a system map."""
        

    def __init__(self, jsonFile: SupportsRead[str | bytes]):
        """Loads a system map from a json dict."""


    def LoadJson(self, )
