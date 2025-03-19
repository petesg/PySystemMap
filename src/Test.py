import os

import SystemMap
import ElectronicSystems

if __name__ == '__main__':
    if os.path.exists('localfiles/Example.db'):
        os.remove('localfiles/Example.db')
    
    with open('examples/ExampleHookupDiagram.json') as f:
        j = f.read()
    m = ElectronicSystems.ElectronicSystemMap('Example', 'localfiles', j)
    nodes = m.Query('SELECT * FROM nodes')
    for r in nodes:
        print(r)
