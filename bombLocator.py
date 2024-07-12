import maya.cmds as mc
import maya.mel as mm

class Locator:
    def __init__(self):
        # CONSTANT
        self.warning_nothing_selected = 'Nothing is selected. Creating a locator at the origin instead.'
        self.bomb_locator_attribute_name = 'bombLocator'
        self.source_attribute_name = 'source'

        # CLASS VARIABLE
        self.selection = self.get_selection()
        self.component_selection = self.is_selection_component()
        self.active_range = self.get_active_range()
        self.generated_locators = []

    def get_selection(self):
        sels = mc.ls(sl=1, fl=1)
        if sels:
            return sels
        else:
            return 0

    def is_selection_component(self):
        if self.selection:
            for sel in self.selection:
                if sel.find('[') != -1:
                    return 1
                else:
                    pass
            return 0

    def get_active_range(self):
        """ Get selected range if time slider range is selected. Otherwise set current time and +1 range. """
        timeSlider = mm.eval('$tmp = $gPlayBackSlider')
        range_selected = 1 if mc.timeControl(timeSlider, q=1, rv=1) else 0

        if range_selected:
            active_start = mc.timeControl(timeSlider, q=1, ra=1)[0]
            active_end = mc.timeControl(timeSlider, q=1, ra=1)[1]
            return range(int(active_start), int(active_end))
        else:
            current_time = mc.currentTime(q=1)
            current_time_plus_one = mc.currentTime(q=1) + 1
            return range(int(current_time), int(current_time_plus_one))

    def generate_locator(self, source):
        """ Actual locator generation.Adding meta data for later use. """
        loc = mc.spaceLocator()[0]

        # same rotation order as source, skip if nothing is selected.
        if source and self.component_selection == 0:
            mc.setAttr(loc + '.ro', mc.getAttr(source + '.ro'))
        if source:
            # embed meta data
            mc.addAttr(loc, ln=self.bomb_locator_attribute_name, at='bool')
            mc.addAttr(loc, ln=self.source_attribute_name, dt='string')
            mc.setAttr(loc + '.' + self.bomb_locator_attribute_name, 1)
            mc.setAttr(loc + '.' + self.source_attribute_name, source, type='string')

        self.generated_locators.append(loc)

    def get_bomb_locator(self):
        bomb_locators = []
        all_locators = mc.ls(type='locator')
        for loc in all_locators:
            parent = mc.listRelatives(loc, p=1)[0]
            if mc.objExists(parent + '.' + self.bomb_locator_attribute_name):
                if mc.getAttr(parent + '.' + self.bomb_locator_attribute_name) == 1:
                    bomb_locators.append(parent)

        return bomb_locators

    def create_locator(self):
        # if nothing is selected, create a single locator at the origin and exit.
        if not self.selection:
            mc.warning(self.warning_nothing_selected)
            self.generate_locator(source = '')
            return 0

        # create a static locator if time range wasn't selected.
        for sel in self.selection:
            loc = self.generate_locator(source = sel)

            # align with selection
            mc.xform(loc, ws=1, t=mc.xform(sel, q=1, ws=1, t=1))
            if self.component_selection:
                pass
            else:
                mc.xform(loc, ws=1, ro=mc.xform(sel, q=1, ws=1, ro=1))

        mc.select(self.generated_locators)

        # snap locator(s) to the selection for the range selected.
        if len(self.active_range) > 1:
            paired_selection = []

            for loc in self.generated_locators:
                mc.setKeyframe(loc + '.t', loc + '.r')
                source = mc.getAttr(loc + '.' + self.source_attribute_name)
                paired_selection.append([source, loc])

            # start progress bar
            gMainProgressBar = mm.eval('$tmp = $gMainProgressBar')
            mc.progressBar(gMainProgressBar, e=1, beginProgress=1, isInterruptable=1, maxValue=len(self.active_range))
            mc.refresh(suspend=1)

            # store current time
            current_time = mc.currentTime(q=1)

            for f in self.active_range:
                mc.currentTime(f)
                for pair in paired_selection:
                    transform = mc.xform(pair[0], q=1, ws=1, t=1)
                    mc.xform(pair[1], ws=1, t=transform)
                    rotation = mc.xform(pair[0], q=1, ws=1, ro=1)
                    mc.xform(pair[1], ws=1, ro=rotation)

                # progress progress bar
                if mc.progressBar(gMainProgressBar, query=1, isCancelled=1):
                    break
                mc.progressBar(gMainProgressBar, edit=1, step=1)

            # restore current time
            mc.currentTime(current_time)

            # stop progress bar
            mc.refresh(suspend=0)
            mc.progressBar(gMainProgressBar, edit=1, endProgress=1)

def run():
    l = Locator()
    l.create_locator();

def select_bomb_locator():
    l = Locator()
    mc.select(l.get_bomb_locator())

