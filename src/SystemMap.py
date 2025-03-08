import sqlite3
import json
import os
from _typeshed import SupportsRead
from typing import Iterable, get_type_hints

class SystemMap:

    _dataDir: str
    _db: sqlite3.Connection

    def __init__(self, name: str, dataDir: str, jsonStr: str = None, overwrite: bool = False):
        """Initializes empty system map."""

        # make sure the name doesn't exist already
        dbPath = os.path.join(dataDir, f'{name}.db')
        if os.path.exists(dbPath):
            if overwrite:
                os.remove(dbPath)
            else:
                raise FileExistsError(f'Map "{name}" already exists')
        
        # open the database connection
        self._db = sqlite3.connect(dbPath)
        
        self._dataDir = dataDir
        self._SetupDb()

        # load json if given
        if jsonStr:
            self.LoadFromJson(jsonStr, False)
        

    def __init__(self, dbDir: str):
        """Opens a sqlite .db file of a system map."""

        self._db = sqlite3.connect(dbDir)


    def __del__(self):
        self._db.close()


    def LoadFromJson(self, jsonStr: str, eraseExisting: bool) -> list[str]:
        output: list[str] = []

        # load in as dict
        j: dict[str, any] = json.loads(jsonStr)

        # verify top-level keys
        reqdKeys = ['nodes', 'busses']
        for key in reqdKeys:
            if key not in j.keys():
                raise ValueError(f'Input JSON must include "{key}" key at top level.')
        for key in j.keys():
            if key not in reqdKeys:
                output.append(f'WARNING: Unknown top-level key "{key}" will be ignored.  Additional JSON data only supported at lower levels.')

        # make a cursor
        cursor = self._db.cursor()

        # load busses first
        if type(j['busses']) is not list:
            raise ValueError(f'JSON key "busses" must contain a list.')
        for bus in j['busses']:
            # load values
            name = bus['name']
            nets = bus['nets']
            signal = bus['signal']
            if nets and type(nets) is not list:
                raise ValueError(f'JSON key "nets" must contain a list.')
            extraBusInfo = json.dumps({k: bus[k] for k in bus.keys() if k not in ['name', 'nets', 'signal']})
            if extraBusInfo == {}:
                extraBusInfo = None
            # save to db
            cursor.execute('INSERT INTO busses (name, signal, extraJson) VALUES (?, ?, ?)', [name, signal, extraBusInfo])
            self._db.commit()
            cursor.execute('SELECT LAST_INSERT_ROWID();')
            busId = cursor.fetchone()[0]
            if nets:
                for net in nets:
                    name = net['name']
                    cursor.execute('INSERT INTO nets (name, bus, extrajson) VALUES (?, ?, ?)', [name, busId, ])
            

    def _SetupDb(self):
        cursor = self._db.cursor()

        cursor.execute('CREATE TABLE nodes (name TEXT NOT NULL UNIQUE, location TEXT, extraJson TEXT)')
        cursor.execute('CREATE TABLE busses (name TEXT NOT NULL UNIQUE, signal TEXT, extraJson TEXT)')
        cursor.execute('''
                        CREATE TABLE connections (
                        name TEXT NOT NULL UNIQUE,
                        node INTEGER NOT NULL REFERENCES nodes(rowid),
                        bus INTEGER REFERENCES busses(rowid),
                        intcable BOOLEAN,
                        intconn BOOLEAN,
                        connector TEXT,
                        direction VARCHAR(2),
                        extraJson TEXT
                       )''')
        cursor.execute('CREATE TABLE nets (name TEXT NOT NULL UNIQUE, bus INTEGER NOT NULL REFERENCES busses(rowid), extraJson TEXT)')
        cursor.execute('CREATE TABLE pinouts (connection INTEGER NOT NULL REFERENCES connections(rowid), net INTEGER NOT NULL REFERENCES nets(rowid), pin NOT NULL TEXT, extraJson TEXT)')
        
        self._db.commit()
        cursor.close()

    def _GetExtraJson(obj: dict[str, any], nonExtraKeys: Iterable[str]):
        """Returns `obj` as a JSON string, stripped of keys listed in `nonExtraKeys`"""
        return json.dumps({k: obj[k] for k in obj.keys() if k not in nonExtraKeys})
    
    class MapObject:
        extraJson: dict[str, any] | None
        def __init__(self, d: dict[str, any]):
            # get list of properties in this object
            props = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
            types = get_type_hints(self)
            # reqdKeys: dict[str, type]
            # optKeys: dict[str, type]

            # load in all the keys we're getting
            for key in d.keys():
                val = d[key]
                if key in props:
                    if isinstance(d, types[key]):
                        self.__setattr__(key, val)
                    else:
                        raise TypeError(f'Incoming JSON "{key}" must contain "{types[key]}", {type(val)} not allowed.')
                else:
                    self.extraJson[key] = val

            # make sure all required keys are supplied
            for prop in props:
                missingProps = []
                if not isinstance(None, types[prop]) and self.__getattribute__(prop) is None:
                    missingProps.append(prop)
                if missingProps:
                    missingStr = ', '.join([f'"{p}"' for p in missingProps])
                    raise TypeError(f'Incoming JSON missing required key{"s" if len(missingProps) > 1 else ""}: {missingStr}')
