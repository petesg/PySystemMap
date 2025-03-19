# some BS code to copy ourselves into the root directory to run because Python is stupid and .. imports don't work (on Linux?) somehow
import re
import os
from pathlib import Path
amStupidCopy = False
if not amStupidCopy:
    with open(__file__) as me:
        meStr = me.read()
    meStr = re.sub(r'from\s+\.\.([a-zA-Z._]+)\s+import\s+([a-zA-Z._]+)', lambda m : f'from {m.group(1)} import {m.group(2)}', meStr)
    meStr = meStr.replace('amStupidCopy = False', 'amStupidCopy = True')
    bsExcLoc = os.path.join(Path(__file__).parent.parent.absolute(), 'stupidExampleFile.py')
    with open(bsExcLoc, 'w+') as stupidMe:
        stupidMe.write(meStr)
    os.system(f'{"python3" if os.name == 'posix' else "python"} {bsExcLoc}')
    os.remove(bsExcLoc)
    exit()


# ACTUAL CODE STARTS HERE
###########################


from ..src import SystemMap
from ..src.SystemComponents import ElectronicSystems

if __name__ == '__main__':
    if os.path.exists('localfiles/Example.db'):
        os.remove('localfiles/Example.db')
    
    with open('examples/ExampleHookupDiagram.json') as f:
        j = f.read()
    m = ElectronicSystems.ElectronicSystemMap('Example', 'localfiles', j)
    # nodes = m.Query('SELECT * FROM nodes')
    # for r in nodes:
    #     print(r)
