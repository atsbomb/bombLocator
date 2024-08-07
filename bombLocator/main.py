import maya.cmds as cmds
from . import lib

# todo
# x Object track
# x All feature to work with animation when range is selected
# - Vertex edge face track
# x Pin to world (use stored source)
# x change source
# x Reparent with maintain animation
# x make the bake and delete locator function
# x implement update locator function

class BombLocator(lib.SceneState):
    def __init__(self):
        super().__init__()
        
        # CONSTANT
        self.warningNothingSelected = 'Nothing is selected. Creating a locator at the origin instead.'
        self.bombLocatorAttributeName = 'bombLocator'
        self.sourceAttributeName = 'source'

        # CLASS VARIABLE
        self.playbackRange = self.getPlaybackRange()
        self.generatedLocators = []

    def generateLocator(self, source):
        """ Actual locator generation.Adding meta data for later use. """
        loc = cmds.spaceLocator()[0]

        # same rotation order as source, skip if nothing is selected.
        if source and self.isSelectionComponent() == 0:
            cmds.setAttr(loc + '.ro', cmds.getAttr(source + '.ro'))
        if source:
            # embed meta data
            cmds.addAttr(loc, ln=self.bombLocatorAttributeName, dt='string')
            cmds.addAttr(loc, ln=self.sourceAttributeName, dt='string')
            cmds.setAttr(f'{loc}.{self.bombLocatorAttributeName}', 'bombLocator', type='string')
            cmds.setAttr(f'{loc}.{self.sourceAttributeName}', source, type='string')
            cmds.setAttr(f'{loc}.{self.bombLocatorAttributeName}', lock=1)

        self.generatedLocators.append(loc)

    def isValidBombLocator(self, obj):
        if cmds.objExists(f'{obj}.{self.bombLocatorAttributeName}'):
            if cmds.getAttr(f'{obj}.{self.bombLocatorAttributeName}') == 'bombLocator':
                return 1
        else:
            return 0

    def isTranslationLocked(self, obj):
        if cmds.getAttr(obj + '.tx', l=1): return 1
        if cmds.getAttr(obj + '.ty', l=1): return 1
        if cmds.getAttr(obj + '.tz', l=1): return 1
        return 0

    def isRotationLocked(self, obj):
        if cmds.getAttr(obj + '.rx', l=1): return 1
        if cmds.getAttr(obj + '.ry', l=1): return 1
        if cmds.getAttr(obj + '.rz', l=1): return 1
        return 0

    def isSourceComponent(self, source):
        if '[' in source: return 1
        else: return 0

    def getBombLocator(self):
        foundLocators = []
        allLocators = cmds.ls(type='locator')
        for loc in allLocators:
            parent = cmds.listRelatives(loc, p=1)[0]
            if cmds.objExists(parent + '.' + self.bombLocatorAttributeName):
                if cmds.getAttr(parent + '.' + self.bombLocatorAttributeName) == 'bombLocator':
                    foundLocators.append(parent)

        return foundLocators

    @lib.SceneState.tempSceneState
    def createLocator(self, anim=0):
        # if nothing is selected, create a single locator at the origin and exit.
        if not self.sels:
            cmds.warning(self.warningNothingSelected)
            self.generateLocator(source = '')
            return 0

        # create a static locator if time range wasn't selected.
        for sel in self.sels:
            loc = self.generateLocator(source = sel)

            # align with selection
            cmds.xform(loc, ws=1, t=cmds.xform(sel, q=1, ws=1, t=1))
            if self.isSelectionComponent():
                pass
            else:
                cmds.xform(loc, ws=1, ro=cmds.xform(sel, q=1, ws=1, ro=1))

        cmds.select(self.generatedLocators)

        # snap locator(s) to the selection for the playback range.
        if anim:
            pairedSelection = []

            for loc in self.generatedLocators:
                cmds.setKeyframe(loc + '.t', loc + '.r')
                source = cmds.getAttr(loc + '.' + self.sourceAttributeName)
                pairedSelection.append([source, loc])

            for f in range(self.playbackRange[0], self.playbackRange[1] + 1):
                cmds.currentTime(f)
                for pair in pairedSelection:
                    transform = cmds.xform(pair[0], q=1, ws=1, t=1)
                    cmds.xform(pair[1], ws=1, t=transform)
                    rotation = cmds.xform(pair[0], q=1, ws=1, ro=1)
                    cmds.xform(pair[1], ws=1, ro=rotation)
                    cmds.setKeyframe(f'{pair[1]}.t')
                    cmds.setKeyframe(f'{pair[1]}.r')

    @lib.SceneState.tempSceneState
    def locatorDriver(self):
        for sel in self.sels:
            # error handling
            if not self.sels:
                cmds.warning('Nothing is selected. Aborting.')
                return 0
            if self.isValidBombLocator(sel) == 0:
                cmds.warning(f'{sel} is not a valid bombLocator. Aborting.')
                return 0
            
            source = cmds.getAttr(sel + '.' + self.sourceAttributeName)

            if self.isSourceComponent(source):
                cmds.warning(f"{sel}'s source {source} is component. Aborting parenting.")
                return 0

            if self.isTranslationLocked(source):
                cmds.warning(f'Translation of {source} is locked. Skipping to apply pointConstraint.')
            else:
                cmds.pointConstraint(sel, source)
                print(f'Applied pointConstraint {sel} -> {source}')

            if self.isRotationLocked(source):
                cmds.warning(f'Rotation of {source} is locked. Skipping to apply orientConstraint.')
            else:
                cmds.orientConstraint(sel, source)
                print(f'Applied orientConstraint {sel} -> {source}')

    @lib.SceneState.tempSceneState
    def reparentLocator(self, toWorld=0):
        # error handling for selection
        if not self.sels:
            cmds.warning('Nothing is selected. Aborting.')
            return 0
        if len(self.sels) <= 1 and toWorld == 0:
            cmds.warning(f'Not enough objects selected for reparenting.')
            return 0
        if len(self.sels) == 1:
            # skip if there's only one selection and the mode is set to world.
            if toWorld == 1:
                pass
        else:
            for obj in self.sels:
                # skip for last object as the last object CAN be non bombLocator
                if obj != self.sels[-1]:
                    if self.isValidBombLocator(obj) == 0:
                        cmds.warning(f'{obj} is not a valid bombLocator. Aborting reparenting.')
                        return 0

        if toWorld:
            for obj in self.sels:
                if self.isValidBombLocator(obj) == 0:
                    cmds.warning(f'{obj} is not a valid bombLocator. Aborting reparenting.')
                    return 0
        else:
            parentObject = self.sels[-1]
            self.sels = self.sels[:-1]

        for sel in self.sels:
            self.sels = [sel]
            self.createLocator(anim=1)
            self.sels = self.generatedLocators
            self.locatorDriver()
            if toWorld:
                cmds.parent(sel, world=1)
            else:
                cmds.parent(sel, parentObject)
            # bake, simulation off, preserve outside keys on.
            cmds.bakeResults(sel, time=self.playbackRange, sb=1, sm=0, pok=1)
            cmds.filterCurve(sel)

            cmds.delete(self.generatedLocators)
            self.generatedLocators = []

    @lib.SceneState.tempSceneState
    def deleteLocator(self, bake=0):
        for sel in self.sels:
            if self.isValidBombLocator(sel):
                source = cmds.getAttr(f'{sel}.{self.sourceAttributeName}')
                cmds.bakeResults(source, time=self.playbackRange, sb=1, sm=0, pok=1)
                cmds.delete(sel)
        
    @lib.SceneState.tempSceneState
    def updateLocator(self):
        for sel in self.sels:
            if self.isValidBombLocator(sel):
                pairedSelection = []
                
                for loc in self.sels:
                    source = cmds.getAttr(loc + '.' + self.sourceAttributeName)
                    
                    if not cmds.objExists(source):
                        cmds.warning(f"{loc}'s source {source} cannot be found. Aborting updating.")
                        return 0

                    cmds.setKeyframe(loc + '.t', loc + '.r')
                    pairedSelection.append([source, loc])

                for f in range(self.playbackRange[0], self.playbackRange[1] + 1):
                    cmds.currentTime(f)
                    for pair in pairedSelection:
                        transform = cmds.xform(pair[0], q=1, ws=1, t=1)
                        cmds.xform(pair[1], ws=1, t=transform)
                        rotation = cmds.xform(pair[0], q=1, ws=1, ro=1)
                        cmds.xform(pair[1], ws=1, ro=rotation)
                        cmds.setKeyframe(f'{pair[1]}.t')
                        cmds.setKeyframe(f'{pair[1]}.r')
