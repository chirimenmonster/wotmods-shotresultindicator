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
        self.values = {}
        tags = {
            'piercingPower':    'piercing',
            'distance':         'distance',
            'angle':            'angle',
            'armor':            'armor',
            'armorEffective':   'effect. armor',
        }
        x = self.window.width / 2
        y = 0
        for name in ('distance', 'piercingPower', 'angle', 'armor', 'armorEffective'):
            self.labels[name] = self._genLabel(horizontalAnchor='RIGHT', text=tags[name])
            self.values[name] = self._genLabel(horizontalAnchor='RIGHT')
            self.labels[name].position = (x, y, 1)
            self.values[name].position = (x + 64, y, 1)
            self.window.addChild(self.labels[name])
            self.window.addChild(self.values[name])
            y = y + 16
        self.values['pierced'] = self._genLabel(horizontalAnchor='RIGHT')
        self.values['pierced'].position = (x + 64, y, 1)
        self.window.addChild(self.values['pierced'])
        for name in tags:
            print 'labels[{}] position={}'.format(name, self.labels[name].position)
            print 'values[{}] position={}'.format(name, self.values[name].position)
        self.onChangeScreenResolution()
        print 'window position={}'.format(self.window.position)
        print 'window width={}, height={}'.format(self.window.width, self.window.height)
 
    def _genLabel(self, **kwargs):
        label = GUI.Text('')
        label.font = 'default_small.font'
        label.horizontalAnchor = 'LEFT'
        label.verticalAnchor = 'TOP'
        label.horizontalPositionMode = 'PIXEL'
        label.verticalPositionMode = 'PIXEL'
        label.colour = (255, 255, 0, 180)
        label.colourFormatting = True
        label.visible = True
        for key, arg in kwargs.items():
            setattr(label, key, arg)
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

    def setInfo(self, result, info):
        if info:
            armor = info['armor']
            armorEffective = info['armorEffective']
            if info['hitAngleCos'] > 1.0 or info['hitAngleCos'] < 0.0:
                angle = None
            else:
                angle = math.degrees(math.acos(info['hitAngleCos']))
            pierced = ('UNDEFINED', 'NOT_PIERCED', 'LITTLE_PIERCED', 'GREAT_PIERCED')[result]
            self.values['piercingPower'].text = '{:.1f}'.format(info['piercingPower'])
            self.values['distance'].text = '{:.1f}'.format(info['distance'])
            self.values['armor'].text = '{:.1f}'.format(armor)
            self.values['armorEffective'].text = '{:.1f}'.format(armorEffective)
            self.values['angle'].text = '{:.1f}'.format(angle) if angle else 'ERROR'
            self.values['pierced'].text = pierced
            BigWorld.logInfo('test', 'modified gunmarker: armor={:.1f}, angle={:.1f}, piercded={}'.format(armor, angle, pierced), None)
        else:
            self.values['piercingPower'].text = ''
            self.values['distance'].text = ''
            self.values['armor'].text = ''
            self.values['armorEffective'].text = ''
            self.values['angle'].text = ''
            self.values['pierced'].text = ''

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
        result_orig = gun_marker_ctrl.getShotResult(position, collision, excludeTeam=self._ShotResultIndicatorPlugin__playerTeam)
        result, info = getShotResult(position, collision, excludeTeam=self._ShotResultIndicatorPlugin__playerTeam)
        if result in self._ShotResultIndicatorPlugin__colors:
            color = self._ShotResultIndicatorPlugin__colors[result]
            if self._ShotResultIndicatorPlugin__cache[markerType] != result and self._parentObj.setGunMarkerColor(markerType, color):
                self._ShotResultIndicatorPlugin__cache[markerType] = result
        else:
            LOG_WARNING('Color is not found by shot result', result)
            self.indicator.setInfo(None, None)
            return
        if self.indicator:
            if info:
                info['resultOrig'] = result_orig
                self.indicator.setInfo(result, info)
                self.indicator.setVisible(True)
            else:
                self.indicator.setInfo(None, None)
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

_SHOT_RESULT = aih_constants.SHOT_RESULT

def getShotResult(hitPoint, collision, excludeTeam = 0):
    """ Gets shot result by present state of gun marker.
    :param hitPoint: Vector3 containing shot position.
    :param collision: instance of EntityCollisionData.
    :param excludeTeam: integer containing number of team that is excluded from result.
    :return: one of SHOT_RESULT.*.
    """
    if collision is None:
        return _SHOT_RESULT.UNDEFINED, None
    else:
        entity = collision.entity
        if entity.health <= 0 or entity.publicInfo['team'] == excludeTeam:
            return _SHOT_RESULT.UNDEFINED, None
        player = BigWorld.player()
        if player is None:
            return _SHOT_RESULT.UNDEFINED, None
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
        armor = 1000.0
        if math.acos(collision.hitAngleCos) < math.radians(70.0):
            if piercingPower > 0.0:
                armor = collision.armor / collision.hitAngleCos
                piercingPercent = 100.0 + (armor - piercingPower) / piercingPower * 100.0
        if piercingPercent >= 150:
            result = _SHOT_RESULT.NOT_PIERCED
        elif 90 < piercingPercent < 150:
            result = _SHOT_RESULT.LITTLE_PIERCED
        else:
            result = _SHOT_RESULT.GREAT_PIERCED
        info = {}
        info['piercingPower'] = piercingPower
        info['distance'] = dist
        info['hitAngleCos'] = collision.hitAngleCos
        info['armor'] = collision.armor
        info['armorEffective'] = armor
        return result, info
