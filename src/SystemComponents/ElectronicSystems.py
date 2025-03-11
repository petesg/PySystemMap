import SystemMap
import sqlite3
import json

class PinMap(SystemMap.MapObject):
    pin: str
    net: str

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('''
                       CREATE TABLE pinouts (
                       connection INTEGER NOT NULL REFERENCES connections(rowid) ON DELETE CASCADE,
                       net INTEGER NOT NULL REFERENCES nets(rowid) ON DELETE CASCADE,
                       pin NOT NULL TEXT,
                       extraJson TEXT)
                       ''')
        dbConnection.commit()


class Net(SystemMap.MapObject):
    name: str

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('CREATE TABLE nets (name TEXT NOT NULL UNIQUE, bus INTEGER NOT NULL REFERENCES busses(rowid) ON DELETE CASCADE, extraJson TEXT)')
        dbConnection.commit()


class Bus(SystemMap.MapObject):
    name: str
    signal: str | None
    nets: list[Net] = []
    
    def StoreInDb(self, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('INSERT INTO busses (name, signal) VALUES (?, ?)', (self.name, self.signal))
        dbConnection.commit()
        cursor.execute('SELECT LAST_INSERT_ROWID();')
        busid = cursor.fetchone()[0]
        for net in self.nets:
            cursor.execute('INSERT INTO nets (name, bus, extraJson) VALUES (?, ?, ?)', (net.name, busid, net.extraJson, json.dumps(net.extraJson)))

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('CREATE TABLE busses (name TEXT NOT NULL UNIQUE, signal TEXT, extraJson TEXT)')
        dbConnection.commit()


class Connection(SystemMap.MapObject):
    name: str
    bus: str
    intCable: bool | None
    intConnector: bool | None
    connector: str | None
    direction: str | None
    pinout: list[PinMap] = []

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('''  CREATE TABLE connections (
                            name TEXT NOT NULL UNIQUE,
                            node INTEGER NOT NULL REFERENCES nodes(rowid) ON DELETE CASCADE,
                            bus INTEGER REFERENCES busses(rowid) ON DELETE CASCADE,
                            intcable BOOLEAN,
                            intconn BOOLEAN,
                            connector TEXT,
                            direction VARCHAR(2),
                            extraJson TEXT
                            )''')
        dbConnection.commit()


class ENode(SystemMap.MapObject):
    name: str
    location: str | None
    connections: list[Connection]

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('CREATE TABLE enodes (name TEXT NOT NULL UNIQUE, location TEXT, extraJson TEXT)')
        dbConnection.commit()
    