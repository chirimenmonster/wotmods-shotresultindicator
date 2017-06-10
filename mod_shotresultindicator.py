import math
import BigWorld
import GUI
from debug_utils import LOG_CURRENT_EXCEPTION
import BattleReplay
from constants import ARENA_GUI_TYPE, SHELL_TYPES, SHELL_TYPES_INDICES
from gui import g_guiResetters
from gui.battle_control import avatar_getter
from gui.Scaleform.daapi.view.battle.shared.crosshair import plugins
from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import ShotResultIndicatorPlugin
from AvatarInputHandler import gun_marker_ctrl
from AvatarInputHandler import aih_constants
    
class IndicatorPanel(object):
    offset = (-170, 100)

    def __init__(self):
        self.window = GUI.Window('')          # background
        self.window.materialFX = 'BLEND'
        self.window.horizontalPositionMode = 'PIXEL'
        self.window.verticalPositionMode = 'PIXEL'
        self.window.widthMode = 'PIXEL'
        self.window.heightMode = 'PIXEL'
        self.window.width = 200
        self.window.height = 180
        self.window.visible = False
        self.labels = {}
        self.values = {}
        tags = (
            ('caliber',         'caliber'       ),
            ('piercingPower',   'piercing'      ),
            ('distance',        'distance'      ),
            ('angle',           'angle'         ),
            ('angleNormalized', 'norm. angle'   ),
            ('armor',           'armor'         ),
            ('armorEffective',  'effect. armor' ),
        )
        x = self.window.width / 2
        y = 0
        self.values['shellKind'] = self._genLabel(horizontalAnchor='RIGHT')
        self.values['shellKind'].position = (x + 64, y, 1)
        self.window.addChild(self.values['shellKind'])
        y = y + 16
        for desc in tags:
            name = desc[0]
            text = desc[1] 
            self.labels[name] = self._genLabel(horizontalAnchor='RIGHT', text=text)
            self.values[name] = self._genLabel(horizontalAnchor='RIGHT')
            self.labels[name].position = (x, y, 1)
            self.values[name].position = (x + 64, y, 1)
            self.window.addChild(self.labels[name])
            self.window.addChild(self.values[name])
            y = y + 16
        self.values['pierced'] = self._genLabel(horizontalAnchor='RIGHT')
        self.values['pierced'].position = (x + 64, y, 1)
        self.window.addChild(self.values['pierced'])
 
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
    
    def onScreenResolutionChanged(self):
        screen = GUI.screenResolution()
        center = ( screen[0] / 2, screen[1] / 2)
        right = center[0] + self.offset[0]
        top = center[1] + self.offset[1]
        self.window.horizontalAnchor = 'RIGHT'
        self.window.verticalAnchor = 'CENTER'
        self.window.position = (right, top, 1)
        print 'window position={}'.format(self.window.position)
        print 'window width={}, height={}'.format(self.window.width, self.window.height)

    def start(self):
        GUI.addRoot(self.window)
        self.onScreenResolutionChanged()
        g_guiResetters.add(self.onScreenResolutionChanged)
    
    def stop(self):
        g_guiResetters.discard(self.onScreenResolutionChanged)
        GUI.delRoot(self.window)

    def setVisible(self, visible):
        self.window.visible = visible

    def setInfo(self, result, info):
        if info:
            armor = info['armor']
            armorEffective = info['armorEffective']
            angleNormalized = info['angleNormalized']
            pierced = ('UNDEFINED', 'NOT_PIERCED', 'LITTLE_PIERCED', 'GREAT_PIERCED')[result]
            self.values['caliber'].text = '{:.1f}'.format(info['caliber'])
            self.values['piercingPower'].text = '{:.1f}'.format(info['piercingPower'])
            self.values['distance'].text = '{:.1f}'.format(info['distance'])
            self.values['armor'].text = '{:.1f}'.format(armor)
            self.values['armorEffective'].text = '{:.1f}'.format(armorEffective)
            self.values['angle'].text = '{:.1f}'.format(math.degrees(info['angle']))
            self.values['angleNormalized'].text = '{:.1f}'.format(math.degrees(info['angleNormalized']))
            self.values['pierced'].text = pierced
            self.values['shellKind'].text = info['shellKind']
            BigWorld.logInfo('test', 'modified gunmarker: effect. armor={:.1f}, norm.angle={:.1f}, piercded={}'.format(armorEffective, angleNormalized, pierced), None)
        else:
            for key in self.values:
                self.values[key].text = ''


class ShotResultIndicatorPluginModified(ShotResultIndicatorPlugin):
    indicator = None
    __cache = None

    def start(self):
        super(ShotResultIndicatorPluginModified, self).start()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onGunMarkerStateChanged -= self._ShotResultIndicatorPlugin__onGunMarkerStateChanged
            ctrl.onGunMarkerStateChanged += self.__onGunMarkerStateChanged
        ctrlAnmo = self.sessionProvider.shared.ammo
        if ctrlAnmo is not None:
            ctrlAnmo.onGunReloadTimeSet += self.__onGunReloadTimeSet
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
        ctrlAnmo = self.sessionProvider.shared.ammo
        if ctrlAnmo is not None:
            ctrlAnmo.onGunReloadTimeSet -= self.__onGunReloadTimeSet
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
            if self.__cache is None:
                self.__cache = {}
            self.__cache['markerType'] = markerType
            self.__cache['position'] = position
            self.__cache['collision'] = collision

    def __onGunReloadTimeSet(self, _, state):
        if state.isReloading():
            return
        if self._ShotResultIndicatorPlugin__isEnabled and self.__cache:
            self.__updateColor(self.__cache['markerType'], self.__cache['position'], self.__cache['collision'])


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
        shellKind = vDesc.shot['shell']['kind']
        caliber = vDesc.shot['shell']['caliber']
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
        angle = math.acos(collision.hitAngleCos)
        angleNormalized = angle
        if angle < math.radians(70.0) or caliber >= collision.armor * 3.0:
            if piercingPower > 0.0:
                if shellKind == SHELL_TYPES.ARMOR_PIERCING:
                    normalize = 5.0
                elif shellKind == SHELL_TYPES.ARMOR_PIERCING_CR:
                    normalize = 2.0
                else:
                    normalize = 0.0
                if caliber >= collision.armor * 2.0:
                    normalize = normalize * 1.4
                if normalize > 0.0:
                    angleNormalized = max(angle - math.radians(normalize), 0.0)
                else:
                    angleNormalized = angle
                armor = collision.armor / math.cos(angleNormalized)
                piercingPercent = 100.0 + (armor - piercingPower) / piercingPower * 100.0
        if piercingPercent >= 150:
            result = _SHOT_RESULT.NOT_PIERCED
        elif 90 < piercingPercent < 150:
            result = _SHOT_RESULT.LITTLE_PIERCED
        else:
            result = _SHOT_RESULT.GREAT_PIERCED
        info = {}
        info['shellKind'] = shellKind
        info['caliber'] = caliber
        info['piercingPower'] = piercingPower
        info['distance'] = dist
        info['hitAngleCos'] = collision.hitAngleCos
        info['angle'] = angle
        info['angleNormalized'] = angleNormalized
        info['armor'] = collision.armor
        info['armorEffective'] = armor
        return result, info
