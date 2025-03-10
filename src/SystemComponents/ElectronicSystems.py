import SystemMap

class Pinout(SystemMap.MapObject):
    pin: str
    net: str

class Net(SystemMap.MapObject):
    name: str

class Bus(SystemMap.MapObject):
    name: str
    signal: str | None
    nets: list[Net] | None

class Connection(SystemMap.MapObject):
    name: str
    bus: str
    intCable: bool | None
    intConnector: bool | None
    connector: str | None
    direction: str | None
    pinout: list[Pinout]

class Node(SystemMap.MapObject):
    name: str
    location: str | None
    connections: list[Connection]
    