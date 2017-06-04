import math
import BigWorld
import GUI
from debug_utils import LOG_CURRENT_EXCEPTION
from gui.Scaleform.daapi.view.battle.shared.crosshair import plugins
from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import ShotResultIndicatorPlugin
from AvatarInputHandler import gun_marker_ctrl

def init():
    try:
        BigWorld.logInfo('test', 'modified gunmarker', None)
    except:
        LOG_CURRENT_EXCEPTION()

_displayText = None

def _clearMsg():
    if _displayText:
        GUI.delRoot(_displayText)

def _setMsg(armor, angle, color):
    global _displayText
    msg = 'armor={:.0f}, angle={:.1f}, {}'.format(armor, math.degrees(angle), color)
    BigWorld.logInfo('test', 'modified gunmarker: {}'.format(msg), None)
    _displayText = GUI.Text(msg)
    GUI.addRoot(_displayText)


class ShotResultIndicatorPluginModified(ShotResultIndicatorPlugin):

    def start(self):
        super(ShotResultIndicatorPluginModified, self).start()
        ctrl = self.sessionProvider.shared.crosshair
        ctrl.onGunMarkerStateChanged -= self._ShotResultIndicatorPlugin__onGunMarkerStateChanged
        ctrl.onGunMarkerStateChanged += self.__onGunMarkerStateChanged

    def __updateColor(self, markerType, position, collision):
        self._ShotResultIndicatorPlugin__updateColor(markerType, position, collision)
        result = gun_marker_ctrl.getShotResult(position, collision, excludeTeam=self._ShotResultIndicatorPlugin__playerTeam)
        _clearMsg()
        if result in self._ShotResultIndicatorPlugin__colors and collision and collision.isVehicle():
            _setMsg(collision[2], collision[1], ('UNDEFINED', 'NOT_PIERCED', 'LITTLE_PIERCED', 'GREAT_PIERCED')[result])

    def __onGunMarkerStateChanged(self, markerType, position, _, collision):
        if self._ShotResultIndicatorPlugin__isEnabled:
            self.__updateColor(markerType, position, collision)

        
def _createPlugins():
    res = _createPlugins_orig()
    res['shotResultIndicator'] = ShotResultIndicatorPluginModified
    return res

_createPlugins_orig = plugins.createPlugins
plugins.createPlugins = _createPlugins
