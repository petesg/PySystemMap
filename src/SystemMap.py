import sqlite3
import json
import os
from _typeshed import SupportsRead

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
            extraJson = json.dumps({k: bus[k] for k in bus.keys() if k not in ['name', 'nets', 'signal']})
            if extraJson == {}:
                extraJson = None
            # save to db
            cursor.execute('INSERT INTO busses (name, signal) VALUES (?, ?)', [name, signal])
            self._db.commit()
            cursor.execute('SELECT LAST_INSERT_ROWID();')
            busId = cursor.fetchone()[0]
            if nets:
                for net in nets:
                    whozgda=
                    cursor.execute('INSERT INTO nets (name, bus, extrajson)')
            

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
