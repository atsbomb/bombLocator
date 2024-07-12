import maya.cmds as cmds
import maya.mel as mel

class BombLocator:
    def __init__(self):
        # CONSTANT
        self.warning_nothing_selected = 'Nothing is selected. Creating a locator at the origin instead.'
        self.bomb_locator_attribute_name = 'bombLocator'
        self.source_attribute_name = 'source'

        # CLASS VARIABLE
        self.selection = self._getSelection()
        self.component_selection = self._isSelectionComponent()
        self.active_range = self._getActiveRange()
        self.generated_locators = []

    def _getSelection(self):
        sels = cmds.ls(sl=1, fl=1)
        if sels:
            return sels
        else:
            return 0

    def _isSelectionComponent(self):
        if self.selection:
            for sel in self.selection:
                if sel.find('[') != -1:
                    return 1
                else:
                    pass
            return 0

    def _getActiveRange(self):
        """ Get selected range if time slider range is selected. Otherwise set current time and +1 range. """
        timeSlider = mel.eval('$tmp = $gPlayBackSlider')
        range_selected = 1 if cmds.timeControl(timeSlider, q=1, rv=1) else 0

        if range_selected:
            active_start = cmds.timeControl(timeSlider, q=1, ra=1)[0]
            active_end = cmds.timeControl(timeSlider, q=1, ra=1)[1]
            return range(int(active_start), int(active_end))
        else:
            current_time = cmds.currentTime(q=1)
            current_time_plus_one = cmds.currentTime(q=1) + 1
            return range(int(current_time), int(current_time_plus_one))

    def _generateLocator(self, source):
        """ Actual locator generation.Adding meta data for later use. """
        loc = cmds.spaceLocator()[0]

        # same rotation order as source, skip if nothing is selected.
        if source and self.component_selection == 0:
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

    def createLocator(self):
        # store current time
        current_time = cmds.currentTime(q=1)
        
        # if nothing is selected, create a single locator at the origin and exit.
        if not self.selection:
            cmds.warning(self.warning_nothing_selected)
            self._generateLocator(source = '')
            return 0

        # create a static locator if time range wasn't selected.
        for sel in self.selection:
            loc = self._generateLocator(source = sel)

            # align with selection
            cmds.xform(loc, ws=1, t=cmds.xform(sel, q=1, ws=1, t=1))
            if self.component_selection:
                pass
            else:
                cmds.xform(loc, ws=1, ro=cmds.xform(sel, q=1, ws=1, ro=1))

        cmds.select(self.generated_locators)

        # snap locator(s) to the selection for the range selected.
        if len(self.active_range) > 1:
            paired_selection = []

            for loc in self.generated_locators:
                cmds.setKeyframe(loc + '.t', loc + '.r')
                source = cmds.getAttr(loc + '.' + self.source_attribute_name)
                paired_selection.append([source, loc])

            # start progress bar
            gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
            cmds.progressBar(gMainProgressBar, e=1, beginProgress=1, isInterruptable=1, maxValue=len(self.active_range))
            cmds.refresh(suspend=1)

            for f in self.active_range:
                cmds.currentTime(f)
                for pair in paired_selection:
                    transform = cmds.xform(pair[0], q=1, ws=1, t=1)
                    cmds.xform(pair[1], ws=1, t=transform)
                    rotation = cmds.xform(pair[0], q=1, ws=1, ro=1)
                    cmds.xform(pair[1], ws=1, ro=rotation)

                # progress progress bar
                if cmds.progressBar(gMainProgressBar, query=1, isCancelled=1):
                    break
                cmds.progressBar(gMainProgressBar, edit=1, step=1)

            # stop progress bar
            cmds.refresh(suspend=0)
            cmds.progressBar(gMainProgressBar, edit=1, endProgress=1)

        # restore current time
        cmds.currentTime(current_time)

