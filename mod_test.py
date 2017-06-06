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

    def setInfo(self, armor, angle, pierced):
        result = ('UNDEFINED', 'NOT_PIERCED', 'LITTLE_PIERCED', 'GREAT_PIERCED')[pierced]
        msg = 'armor={:.0f}, angle={:.1f}, {}'.format(armor, math.degrees(angle), pierced)
        BigWorld.logInfo('test', 'modified gunmarker: {}'.format(msg), None)
        self.labels['valueArmor'].text = '{:.0f}'.format(armor)
        self.labels['valueAngle'].text = '{:.1f}'.format(math.degrees(angle))
        self.labels['valuePierced'].text = result if pierced > 0 else ''


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
            self.indicator.setInfo(collision[2], collision[1], result)
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
