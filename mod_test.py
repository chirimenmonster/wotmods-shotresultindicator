import math
import BigWorld
import GUI
from debug_utils import LOG_CURRENT_EXCEPTION
import BattleReplay
from constants import ARENA_GUI_TYPE
from gui.battle_control import avatar_getter
from gui.Scaleform.daapi.view.battle.shared.crosshair import plugins
from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import ShotResultIndicatorPlugin
from AvatarInputHandler import gun_marker_ctrl
from AvatarInputHandler import aih_constants
    
class IndicatorPanel(object):

    def __init__(self):
        self.window = GUI.Window('')          # background
        self.window.materialFX = 'BLEND'
        self.window.horizontalPositionMode = 'PIXEL'
        self.window.verticalPositionMode = 'PIXEL'
        self.window.widthMode = 'PIXEL'
        self.window.heightMode = 'PIXEL'
        self.window.width = 200
        self.window.height = 100
        self.window.visible = False
        self.labels = {}
        self.labels['labelArmor'] = self._genLabel()
        self.labels['labelAngle'] = self._genLabel()
        self.labels['valueArmor'] = self._genLabel()
        self.labels['valueAngle'] = self._genLabel()
        self.labels['valuePierced'] = self._genLabel()
        self.labels['labelArmor'].text = 'armor='
        self.labels['labelAngle'].text = 'angle='
        for name in ( 'labelArmor', 'labelAngle' ):
            self.labels[name].horizontalAnchor = 'RIGHT'
        self.labels['valuePierced'].horizontalAnchor = 'CENTER'
        x = self.window.width / 2
        self.labels['labelArmor'].position = (x,  0, 1)
        self.labels['labelAngle'].position = (x, 24, 1)
        self.labels['valueArmor'].position = (x,  0, 1)
        self.labels['valueAngle'].position = (x, 24, 1)
        self.labels['valuePierced'].position = (x, 48, 1)
        for name in self.labels:
            self.window.addChild(self.labels[name])
            print 'label[{}] position={}'.format(name, self.labels[name].position)
        self.onChangeScreenResolution()
        print 'window position={}'.format(self.window.position)
        print 'window width={}, height={}'.format(self.window.width, self.window.height)
 
    def _genLabel(self):
        label = GUI.Text('')
        label.font = 'default_medium.font'
        label.horizontalAnchor = 'LEFT'
        label.verticalAnchor = 'TOP'
        label.horizontalPositionMode = 'PIXEL'
        label.verticalPositionMode = 'PIXEL'
        label.colour = (255, 255, 0, 255)
        label.colourFormatting = True
        label.visible = True
        return label
    
    def onChangeScreenResolution(self):
        screen = GUI.screenResolution()
        center = ( screen[0] / 2, screen[1] / 2)
        right = center[0] - 160
        top = center[1]
        self.window.horizontalAnchor = 'RIGHT'
        self.window.verticalAnchor = 'CENTER'
        self.window.position = (right, top, 1)

    def start(self):
        GUI.addRoot(self.window)
    
    def stop(self):
        GUI.delRoot(self.window)

    def setVisible(self, visible):
        self.window.visible = visible

    def setInfo(self, armor, hitAngleCos, pierced):
        s_armor = '{:.1f} ({:.1f})'.format(armor, armor / hitAngleCos) if armor is not None else ''
        s_angle = '{:.1f}'.format(math.degrees(math.acos(hitAngleCos))) if hitAngleCos is not None else ''
        s_pierced = ('UNDEFINED', 'NOT_PIERCED', 'LITTLE_PIERCED', 'GREAT_PIERCED')[pierced] if pierced is not None else ''
        BigWorld.logInfo('test', 'modified gunmarker: armor={}, angle={}, piercded={}'.format(s_armor, s_angle, s_pierced), None)
        self.labels['valueArmor'].text = s_armor
        self.labels['valueAngle'].text = s_angle
        self.labels['valuePierced'].text = s_pierced

class ShotResultIndicatorPluginModified(ShotResultIndicatorPlugin):
    indicator = None

    def start(self):
        super(ShotResultIndicatorPluginModified, self).start()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onGunMarkerStateChanged -= self._ShotResultIndicatorPlugin__onGunMarkerStateChanged
            ctrl.onGunMarkerStateChanged += self.__onGunMarkerStateChanged
        print 'guiType = {} {}'.format(avatar_getter.getArena().guiType, ARENA_GUI_TYPE.TRAINING)
        if BattleReplay.isPlaying() or avatar_getter.getArena().guiType == ARENA_GUI_TYPE.TRAINING:
            self.indicator = IndicatorPanel()
            self.indicator.start()
        return
    
    def stop(self):
        super(ShotResultIndicatorPluginModified, self).stop()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onGunMarkersSetChanged -= self.__onGunMarkerStateChanged
        if self.indicator:
            self.indicator.stop()
            self.indicator = None
        return

    def __updateColor(self, markerType, position, collision):
        self._ShotResultIndicatorPlugin__updateColor(markerType, position, collision)
        result = gun_marker_ctrl.getShotResult(position, collision, excludeTeam=self._ShotResultIndicatorPlugin__playerTeam)
        if self.indicator:
            if result in self._ShotResultIndicatorPlugin__colors and collision and collision.isVehicle():
                self.indicator.setInfo(collision.armor, collision.hitAngleCos, result)
                self.indicator.setVisible(True)
            else:
                self.indicator.setInfo(None, None, None)
                self.indicator.setVisible(True)

    def __onGunMarkerStateChanged(self, markerType, position, _, collision):
        if self._ShotResultIndicatorPlugin__isEnabled:
            self.__updateColor(markerType, position, collision)

        
def _createPlugins():
    res = _createPlugins_orig()
    res['shotResultIndicator'] = ShotResultIndicatorPluginModified
    return res

_createPlugins_orig = plugins.createPlugins
plugins.createPlugins = _createPlugins

_SHOT_RESULT = aih_constants.SHOT_RESULT

def getShotResult(hitPoint, collision, excludeTeam = 0):
    """ Gets shot result by present state of gun marker.
    :param hitPoint: Vector3 containing shot position.
    :param collision: instance of EntityCollisionData.
    :param excludeTeam: integer containing number of team that is excluded from result.
    :return: one of SHOT_RESULT.*.
    """
    if collision is None:
        return _SHOT_RESULT.UNDEFINED
    else:
        entity = collision.entity
        if entity.health <= 0 or entity.publicInfo['team'] == excludeTeam:
            return _SHOT_RESULT.UNDEFINED
        player = BigWorld.player()
        if player is None:
            return _SHOT_RESULT.UNDEFINED
        vDesc = player.getVehicleDescriptor()
        ppDesc = vDesc.shot['piercingPower']
        maxDist = vDesc.shot['maxDistance']
        dist = (hitPoint - player.getOwnVehiclePosition()).length
        if dist <= 100.0:
            piercingPower = ppDesc[0]
        elif maxDist > dist:
            p100, p500 = ppDesc
            piercingPower = p100 + (p500 - p100) * (dist - 100.0) / 400.0
            if piercingPower < 0.0:
                piercingPower = 0.0
        else:
            piercingPower = 0.0
        piercingPercent = 1000.0
        if piercingPower > 0.0:
            armor = collision.armor / collision.hitAngleCos
            piercingPercent = 100.0 + (armor - piercingPower) / piercingPower * 100.0
        if piercingPercent >= 150:
            result = _SHOT_RESULT.NOT_PIERCED
        elif 90 < piercingPercent < 150:
            result = _SHOT_RESULT.LITTLE_PIERCED
        else:
            result = _SHOT_RESULT.GREAT_PIERCED
        return result
