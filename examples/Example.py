import json

from ..src import SystemMap
from ..src.SystemComponents import ElectronicSystems

if __name__ == '__main__':
    with open('examples/ExampleHookupDiagram.json') as f:
        j = json.loads(f.read())
    m = ElectronicSystems.ElectronicSystemMap('Example', 'localfiles', j)
