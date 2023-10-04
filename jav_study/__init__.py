from .event import *
from .bp import *
from .jav_study import *
from .command import *

if os.path.exists("/data/plugins/jav_study/embyapi.py"):
    os.remove("/data/plugins/jav_study/embyapi.py")
