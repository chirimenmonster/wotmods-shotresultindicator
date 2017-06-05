import math
import BigWorld
import GUI
from debug_utils import LOG_CURRENT_EXCEPTION
from gui.Scaleform.daapi.view.battle.shared.crosshair import plugins
from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import ShotResultIndicatorPlugin
from AvatarInputHandler import gun_marker_ctrl

    
class IndicatorPanel(object):

    def __init__(self):
        self.window = GUI.Window('')          # background
        self.window.materialFX = 'BLEND'
        self.window.horizontalAnchor = 'LEFT'
        self.window.verticalAnchor = 'TOP'
        self.window.horizontalPositionMode = 'PIXEL'
        self.window.verticalPositionMode = 'PIXEL'
        self.window.widthMode = 'PIXEL'
        self.window.heightMode = 'PIXEL'
        self.window.width = 200
        self.window.height = 32
        self.window.position = (400, 600, 1)
        self.window.visible = False
        self.label = GUI.Text('')
        self.label.font = 'default_medium.font'
        self.label.horizontalAnchor = 'LEFT'
        self.label.verticalAnchor = 'TOP'
        self.label.horizontalPositionMode = 'PIXEL'
        self.label.verticalPositionMode = 'PIXEL'
        self.label.position = (0, 0, 1)
        self.label.colourFormatting = True
        self.label.visible = True
        self.window.addChild(self.label)

    def start(self):
        GUI.addRoot(self.window)
    
    def stop(self):
        GUI.delRoot(self.window)

    def setVisible(self, visible):
        self.window.visible = visible

    def setInfo(self, armor, angle, pierced):
        msg = 'armor={:.0f}, angle={:.1f}, {}'.format(armor, math.degrees(angle), pierced)
        BigWorld.logInfo('test', 'modified gunmarker: {}'.format(msg), None)
        color = '\cFFFF00FF;'
        self.label.text = color + msg


class ShotResultIndicatorPluginModified(ShotResultIndicatorPlugin):

    def start(self):
        super(ShotResultIndicatorPluginModified, self).start()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onGunMarkerStateChanged -= self._ShotResultIndicatorPlugin__onGunMarkerStateChanged
            ctrl.onGunMarkerStateChanged += self.__onGunMarkerStateChanged
        self.indicator = IndicatorPanel()
        self.indicator.start()
        return
    
    def stop(self):
        super(ShotResultIndicatorPluginModified, self).stop()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onGunMarkersSetChanged -= self.__onGunMarkerStateChanged
        self.indicator.stop()
        return

    def __updateColor(self, markerType, position, collision):
        self._ShotResultIndicatorPlugin__updateColor(markerType, position, collision)
        result = gun_marker_ctrl.getShotResult(position, collision, excludeTeam=self._ShotResultIndicatorPlugin__playerTeam)
        if result in self._ShotResultIndicatorPlugin__colors and collision and collision.isVehicle():
            self.indicator.setInfo(collision[2], collision[1], ('UNDEFINED', 'NOT_PIERCED', 'LITTLE_PIERCED', 'GREAT_PIERCED')[result])
            self.indicator.setVisible(True)
        else:
            self.indicator.setVisible(False)

    def __onGunMarkerStateChanged(self, markerType, position, _, collision):
        if self._ShotResultIndicatorPlugin__isEnabled:
            self.__updateColor(markerType, position, collision)

        
def _createPlugins():
    res = _createPlugins_orig()
    res['shotResultIndicator'] = ShotResultIndicatorPluginModified
    return res

_createPlugins_orig = plugins.createPlugins
plugins.createPlugins = _createPlugins
