import maya.cmds as cmds
import maya.mel as mel
from bombLocator.lib import SceneState

# todo
# x Object track
# x All feature to work with animation when range is selected
# - Vertex edge face track
# x Pin to world (use stored source)
# - Pin to world with offset
# x change source
# x Reparent with maintain animation
# - make the bake and delete locator function

class BombLocator(SceneState):
    def __init__(self):
        super().__init__()
        
        # CONSTANT
        self.warningNothingSelected = 'Nothing is selected. Creating a locator at the origin instead.'
        self.bombLocatorAttributeName = 'bombLocator'
        self.sourceAttributeName = 'source'
        self.offsetAttributeName = 'offset'

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
            cmds.addAttr(loc, ln=self.offsetAttributeName, at='bool')
            cmds.setAttr(f'{loc}.{self.bombLocatorAttributeName}', 'bombLocator', type='string')
            cmds.setAttr(f'{loc}.{self.sourceAttributeName}', source, type='string')
            cmds.setAttr(f'{loc}.{self.offsetAttributeName}', 0)
            cmds.setAttr(f'{loc}.{self.bombLocatorAttributeName}', lock=1)

        self.generatedLocators.append(loc)

    def isValidBombLocator(self, obj):
        if cmds.objExists(f'{obj}.{self.bombLocatorAttributeName}'):
            if cmds.getAttr(f'{obj}.{self.bombLocatorAttributeName}') == 'bombLocator':
                return 1
        else:
            return 0

    def getBombLocator(self):
        bomb_locators = []
        all_locators = cmds.ls(type='locator')
        for loc in all_locators:
            parent = cmds.listRelatives(loc, p=1)[0]
            if cmds.objExists(parent + '.' + self.bombLocatorAttributeName):
                if cmds.getAttr(parent + '.' + self.bombLocatorAttributeName) == 1:
                    bomb_locators.append(parent)

        return bomb_locators

    @SceneState.tempSceneState
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

        # snap locator(s) to the selection for the range selected.
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

    @SceneState.tempSceneState
    def locatorDriver(self):
        for sel in self.sels:
            source = cmds.getAttr(sel + '.' + self.sourceAttributeName)
            # needs to check if the target attribute is open
            cmds.pointConstraint(sel, source)
            cmds.orientConstraint(sel, source)

    @SceneState.tempSceneState
    def reparentLocator(self, toWorld=0):
        if toWorld:
            pass
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

    @SceneState.tempSceneState
    def changeSource(self, offset=0):
        newSource = self.sels[1]
        cmds.setAttr(f'{self.sels[0]}.{self.sourceAttributeName}', newSource, type='string')
        
        if offset:
            cmds.setAttr(f'{loc}.{self.offsetAttributeName}', 1)

    @SceneState.tempSceneState
    def deleteLocator(self, bake=0):
        for sel in self.sels:
            if self.isValidBombLocator(sel):
                source = cmds.getAttr(f'{sel}.{self.sourceAttributeName}')
                cmds.bakeResults(source, time=self.playbackRange, sb=1, sm=0, pok=1)
                cmds.delete(sel)
        


