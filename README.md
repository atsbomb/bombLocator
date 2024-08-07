# bombLocator

Create a locator that plots out the position/rotation of current selection(s) or the animation thereof, later to be used to primarily as a driver of the original object for space switching.

# Installation

Make a copy of this entire folder under `maya/xxxx/scripts/bombLocator`. Access the functions directly from your preferred hotkey, or via provided marking menu. Place marking menu file `under maya/xxxx/prefs/markingMenus`.

# Functions

- Create Static Locator
```
from bombLocator.main import *

bl = BombLocator()
bl.createLocator(anim=0)
```
- Create Animated Locator
```
from bombLocator.main import *

bl = BombLocator()
bl.createLocator(anim=1)
```
- Pin to World
```
from bombLocator.main import *

bl = BombLocator()
bl.createLocator(anim=1)

bl = BombLocator()
bl.locatorDriver()
```
- Bake and Delete Locator
```
from bombLocator.main import *

bl = BombLocator()
bl.deleteLocator()
```
- Reparent
```
from bombLocator.main import *

bl = BombLocator()
bl.reparentLocator(toWorld=0)
```
- Reparent to World
```
from bombLocator.main import *

bl = BombLocator()
bl.reparentLocator(toWorld=1)
```
- Update Locator
```
import maya.cmds as cmds
from bombLocator import *

bl = BombLocator()
bl.updateLocator()
```
- Select All Locators
```
import maya.cmds as cmds
from bombLocator import *

bl = BombLocator()
cmds.select(bl.getBombLocator())
```

