import maya.cmds as cmds
import maya.mel as mel
from bombLocator.lib import SceneState

# todo
# x Object track
# x All feature to work with animation when range is selected
# - Vertex edge face track
# x Pin to world (use stored source)
# - Pin to world with offset
# x Reparent with maintain animation

class BombLocator(SceneState):
    def __init__(self):
        super().__init__()
        
        # CONSTANT
        self.warning_nothing_selected = 'Nothing is selected. Creating a locator at the origin instead.'
        self.bomb_locator_attribute_name = 'bombLocator'
        self.source_attribute_name = 'source'

        # CLASS VARIABLE
        self.playbackRange = self.getPlaybackRange()
        self.generated_locators = []

    def generateLocator(self, source):
        """ Actual locator generation.Adding meta data for later use. """
        loc = cmds.spaceLocator()[0]

        # same rotation order as source, skip if nothing is selected.
        if source and self.isSelectionComponent() == 0:
            cmds.setAttr(loc + '.ro', cmds.getAttr(source + '.ro'))
        if source:
            # embed meta data
            cmds.addAttr(loc, ln=self.bomb_locator_attribute_name, at='bool')
            cmds.addAttr(loc, ln=self.source_attribute_name, dt='string')
            cmds.setAttr(loc + '.' + self.bomb_locator_attribute_name, 1)
            cmds.setAttr(loc + '.' + self.source_attribute_name, source, type='string')

        self.generated_locators.append(loc)

    def getBombLocator(self):
        bomb_locators = []
        all_locators = cmds.ls(type='locator')
        for loc in all_locators:
            parent = cmds.listRelatives(loc, p=1)[0]
            if cmds.objExists(parent + '.' + self.bomb_locator_attribute_name):
                if cmds.getAttr(parent + '.' + self.bomb_locator_attribute_name) == 1:
                    bomb_locators.append(parent)

        return bomb_locators

    @SceneState.restreSymmetricModelingModeState
    @SceneState.restoreCurrentTime
    @SceneState.viewportUpdateSuspend
    def createLocator(self, anim=0):
        # if nothing is selected, create a single locator at the origin and exit.
        if not self.sels:
            cmds.warning(self.warning_nothing_selected)
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

        cmds.select(self.generated_locators)

        # snap locator(s) to the selection for the range selected.
        if anim:
            pairedSelection = []

            for loc in self.generated_locators:
                cmds.setKeyframe(loc + '.t', loc + '.r')
                source = cmds.getAttr(loc + '.' + self.source_attribute_name)
                pairedSelection.append([source, loc])

            for f in range(self.playbackRange[0], self.playbackRange[1]):
                cmds.currentTime(f)
                for pair in pairedSelection:
                    transform = cmds.xform(pair[0], q=1, ws=1, t=1)
                    cmds.xform(pair[1], ws=1, t=transform)
                    rotation = cmds.xform(pair[0], q=1, ws=1, ro=1)
                    cmds.xform(pair[1], ws=1, ro=rotation)

    @SceneState.restreSymmetricModelingModeState
    @SceneState.restoreCurrentTime
    @SceneState.viewportUpdateSuspend
    def locatorDriver(self):
        for sel in self.sels:
            source = cmds.getAttr(sel + '.' + self.source_attribute_name)
            # needs to check if the target attribute is open
            cmds.pointConstraint(sel, source)
            cmds.orientConstraint(sel, source)

    @SceneState.restreSymmetricModelingModeState
    @SceneState.restoreCurrentTime
    @SceneState.viewportUpdateSuspend
    def reparentLocator(self, toWorld=0):
        if toWorld:
            pass
        else:
            parentObject = self.sels[-1]
            self.sels = self.sels[:-1]

        for sel in self.sels:
            self.sels = [sel]
            self.createLocator(anim=1)
            self.sels = self.generated_locators
            self.locatorDriver()
            if toWorld:
                cmds.parent(sel, world=1)
            else:
                cmds.parent(sel, parentObject)
            # bake, simulation off, preserve outside keys on.
            cmds.bakeResults(sel, time=self.playbackRange, sb=1, sm=0, pok=1)
            cmds.filterCurve(sel)
            
            cmds.delete(self.generated_locators)
            self.generated_locators = []

    @SceneState.restreSymmetricModelingModeState
    @SceneState.restoreCurrentTime
    @SceneState.viewportUpdateSuspend
    def deleteLocator(self, bake=0):
        for sel in self.sels:
            
            # identify if it's bombLocator
            
            # check if it's driving the source in some way
            
            # ask if user wants to bake the source animation before locator deletion
            
            # bake if needed
            
            cmds.delete(sel)
        


