import maya.cmds as cmds
import maya.mel as mel

class SceneState():
    def __init__(self):
        self.sels = cmds.ls(sl=1, fl=1)
        self.isSomethingSelected = 1 if self.sels else 0
        self.firstSel = self.sels[0] if self.isSomethingSelected else ''
        self.lastSel = self.sels[-1] if self.isSomethingSelected else ''
        
        self.minPlayTime = cmds.playbackOptions(q=1, min=1)
        self.maxPlayTime = cmds.playbackOptions(q=1, max=1)

    def restoreCurrentTime(func):
        def wrapper(*args, **kwargs):
            currentTime = cmds.currentTime(q=1)
            func(*args, **kwargs)
            cmds.currentTime(currentTime)
        return wrapper

    def restreSymmetricModelingModeState(func):
        def wrapper(*args, **kwargs):
            symState = cmds.symmetricModelling(q=1, s=1)
            cmds.symmetricModelling(e=1, s=0)        
            func(*args, **kwargs)
            cmds.symmetricModelling(e=1, s=symState)
        return wrapper

    def viewportUpdateSuspend(func):
        def wrapper(*args, **kwargs):
            cmds.refresh(suspend=1)
            func(*args, **kwargs)
            cmds.refresh(suspend=0)
        return wrapper

    def getActiveRange(self):
        """ Get selected range if time slider range is selected. Otherwise set current time and +1 range. """
        timeSlider = mel.eval('$tmp = $gPlayBackSlider')
        rangeSelected = 1 if cmds.timeControl(timeSlider, q=1, rv=1) else 0

        if rangeSelected:
            activeStart = cmds.timeControl(timeSlider, q=1, ra=1)[0]
            activeEnd = cmds.timeControl(timeSlider, q=1, ra=1)[1]
            return range(int(activeStart), int(activeEnd))
        else:
            currentTime = cmds.currentTime(q=1)
            currentTimePlusOne = cmds.currentTime(q=1) + 1
            return range(int(currentTime), int(currentTimePlusOne))

    def getPlaybackRange(self):
        return (int(self.minPlayTime), int(self.maxPlayTime))

    def isSelectionComponent(self):
        if self.sels:
            for sel in self.sels:
                if sel.find('[') != -1:
                    return 1
                else:
                    pass
            return 0
        return 0


