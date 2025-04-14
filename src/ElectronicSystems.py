import sqlite3
import json
from typing import Iterable

import SystemMap

class ElectronicSystemMap(SystemMap.SystemMap):
    def __init__(self, name: str, dataDir: str, jsonStr: str | None = None):
        super().__init__(name, dataDir, jsonStr, [ENode, Bus, Connection, Net, PinMap])

class PinMap(SystemMap.MapObject):
    pin: str
    net: str

    def StoreInDb(self, dbConnection: sqlite3.Connection, connId: int) -> int:
        cursor = dbConnection.cursor()
        cursor.execute('SELECT bus FROM connections WHERE rowid = ?', (connId,))
        busId = cursor.fetchone()[0]
        cursor.execute('SELECT rowid FROM nets WHERE bus = ? AND name = ?', (busId, self.net))
        try:
            netId = cursor.fetchone()[0]
        except TypeError:
            cursor.execute('SELECT name FROM busses WHERE rowid = ?', (busId,))
            raise ValueError(f'Net "{self.net}" for pin "{self.pin}" does not exist on bus "{cursor.fetchone()[0]}".')
        cursor.execute('INSERT INTO pinouts (connection, net, pin, extraJson) VALUES (?, ?, ?, ?)', (connId, netId, self.pin, self.net))
        dbConnection.commit()
        cursor.execute('SELECT last_insert_rowid()')
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('''
                       CREATE TABLE pinouts (
                       rowid INTEGER PRIMARY KEY,
                       connection INTEGER NOT NULL REFERENCES connections(rowid) ON DELETE CASCADE,
                       net INTEGER NOT NULL REFERENCES nets(rowid) ON DELETE CASCADE,
                       pin TEXT NOT NULL,
                       extraJson TEXT
                       )''')
        dbConnection.commit()
        cursor.close()


class Net(SystemMap.MapObject):
    name: str

    def StoreInDb(self, dbConnection: sqlite3.Connection, busId: int) -> int:
        cursor = dbConnection.cursor()
        cursor.execute('INSERT INTO nets (name, bus, extraJson) VALUES (?, ?, ?)', (self.name, busId, json.dumps(self.extraJson)))
        dbConnection.commit()
        cursor.execute('SELECT last_insert_rowid()')
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('''
                       CREATE TABLE nets (
                       rowid INTEGER PRIMARY KEY,
                       name TEXT NOT NULL,
                       bus INTEGER NOT NULL REFERENCES busses(rowid) ON DELETE CASCADE,
                       extraJson TEXT,
                       CONSTRAINT unique_nets_in_bus UNIQUE (bus, name)
                       )''')
        dbConnection.commit()
        cursor.close()


class Bus(SystemMap.MapObject):
    name: str
    signal: str | None = None
    nets: list[Net] = []
    
    def StoreInDb(self, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('INSERT INTO busses (name, signal) VALUES (?, ?)', (self.name, self.signal))
        dbConnection.commit()
        # dbConnection.commit() # TODO does it work without this?  If it does, then we can catch an exception and roll back (also we wouldn't need connection only cursor)
        cursor.execute('SELECT LAST_INSERT_ROWID();')
        busid = cursor.fetchone()[0]
        for net in self.nets:
            net.StoreInDb(dbConnection, busid)
        dbConnection.commit()
        cursor.close()
        return busid

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('CREATE TABLE busses (rowid INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, signal TEXT, extraJson TEXT)')
        dbConnection.commit()
        cursor.close()
    
    @classmethod
    def JsonKey(cls) -> str:
        return 'busses'


class Connection(SystemMap.MapObject):
    name: str | None
    bus: str
    intCable: bool | None = None
    intConnector: bool | None = None
    connector: str | None = None
    direction: str | None = None
    pinout: list[PinMap] = []

    def StoreInDb(self, dbConnection: sqlite3.Connection, nodeId: int):
        cursor = dbConnection.cursor()
        cursor.execute('SELECT rowid FROM busses WHERE name = ?', (self.bus,))
        busId = cursor.fetchone()[0]
        cursor.execute('''
                        INSERT INTO connections (name, node, bus, intcable, intconn, connector, direction, extraJson)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (self.name, nodeId, busId, self.intCable, self.intConnector, self.connector, self.direction, json.dumps(self.extraJson)))
        dbConnection.commit()
        cursor.execute('SELECT last_insert_rowid()')
        id = cursor.fetchone()[0]
        cursor.close()
        for pinMap in self.pinout:
            pinMap.StoreInDb(dbConnection, id)
        return id

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> int:
        cursor = dbConnection.cursor()
        cursor.execute('''  CREATE TABLE connections (
                            rowid INTEGER PRIMARY KEY,
                            name TEXT,
                            node INTEGER NOT NULL REFERENCES nodes(rowid) ON DELETE CASCADE,
                            bus INTEGER REFERENCES busses(rowid) ON DELETE CASCADE,
                            intcable BOOLEAN,
                            intconn BOOLEAN,
                            connector TEXT,
                            direction VARCHAR(2),
                            extraJson TEXT
                            )''')
        dbConnection.commit()
        cursor.close()
        return id


class ENode(SystemMap.MapObject):
    name: str
    location: str | None = None
    connections: list[Connection]

    def StoreInDb(self, dbConnection: sqlite3.Connection):
        cursor = dbConnection.cursor()
        cursor.execute('INSERT INTO nodes (name, location, extraJson) VALUES (?, ?, ?)', (self.name, self.location, json.dumps(self.extraJson)))
        dbConnection.commit()
        cursor.execute('SELECT last_insert_rowid()')
        id = cursor.fetchone()[0]
        for connection in self.connections:
            connection.StoreInDb(dbConnection, id)
        cursor.close()
        return id

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> None:
        cursor = dbConnection.cursor()
        cursor.execute('CREATE TABLE nodes (rowid INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, location TEXT, extraJson TEXT)')
        dbConnection.commit()
        cursor.close()
    
    @classmethod
    def JsonKey(cls) -> str:
        return "nodes"
    