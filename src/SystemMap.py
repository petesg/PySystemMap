import sqlite3
import json
import os
import re
from _typeshed import SupportsRead
from typing import Iterable, get_type_hints
# from SystemComponents.ElectronicSystems import Bus, Connection, Net, Node, Pinout

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
        self._ConnectDb(dbPath)
        
        self._dataDir = dataDir
        self._SetupDb()

        # load json if given
        if jsonStr:
            self.LoadFromJson(jsonStr, False)
        
    def __init__(self, dbDir: str):
        """Opens a sqlite .db file of a system map."""
        self._ConnectDb(dbDir)

    def __del__(self):
        self._db.close()

    def _ConnectDb(self, dbDir: str):
        self._db = sqlite3.connect(dbDir)
        cursor = self._db.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')

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

        return output

    def _SetupDb(self) -> None:
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
    
class MapObject():
    extraJson: dict[str, any] = {}
    def __init__(self, jsonDict: dict[str, any], recognizedMembers: Iterable['MapObject']):
        '''
        Base class for members in a system map.  
        '''
        # TODO make sure all recognizedMembers are our children (or is that ok if they're not?)
        # get list of properties in this object
        myTypes = get_type_hints(self)
        # myProps = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        # ^ this doesn't work because dir() doesn't list properties that were just type hinted and not assigned a value
        myProps = myTypes.keys()
        
        # load in all the keys we're getting
        for key in jsonDict.keys():
            incProp = re.sub(r'(a-zA-Z)[\s,.]+([a-zA-Z])', lambda m : m.group(0) + m.group(1).upper(), key)
            incVal = jsonDict[key]
            # see if the key matches any of our properties
            if incProp in myProps:
                # first check if incoming value matches the expected type
                if isinstance(incVal, myTypes[incProp]):
                    # easy to handle, assign the value to our property
                    self.__setattr__(incProp, incVal)
                # if not, check if our prop is a special type
                elif myTypes[incProp] in recognizedMembers:
                    # instantiate a new object of that type for the member and hand it the json contents we are looking at
                    self.__setattr__(incProp, globals()[myTypes[incProp]](incVal, recognizedMembers))
                # finally, check if it is a list of a special type
                elif myTypes[incProp] in [list[t] for t in recognizedMembers]:
                    self.__setattr__(incProp, [globals()[myTypes[incProp]](v, recognizedMembers) for v in incVal])
                # if it's something else, yell about it
                else:
                    raise TypeError(f'Incoming JSON "{key}" must contain "{myTypes[key]}", {type(incVal)} not allowed.')
            # put any unexpected keys and their contents in the extraJson dict
            else:
                self.extraJson[key] = incVal

        # make sure all required keys are supplied
        for incProp in myProps:
            missingProps = []
            if not isinstance(None, myTypes[incProp]) and self.__getattribute__(incProp) is None:
                missingProps.append(incProp)
            if missingProps:
                missingStr = ', '.join([f'"{p}"' for p in missingProps])
                raise TypeError(f'Incoming JSON missing required key{"s" if len(missingProps) > 1 else ""}: {missingStr}')

    def StoreInDb(self, dbConnection: sqlite3.Connection) -> int:
        raise NotImplementedError(f'{type(self)} has not implemented a direct-to-database storage method.  Either this class is meant to only be loaded by a class containing it as a member, or the `StoreInDb()` method needs to be implemented.')

    @classmethod
    def SetupDbTable(cls, dbConnection: sqlite3.Connection) -> None:
        raise NotImplementedError(f'{cls} is missing `SetupDbTable()` implementation.')
