import sys,os
from volume_controller import VolumeController

from PySide6.QtCore import QFile, QTextStream
from PySide6.QtWidgets import QApplication
from hotkey.pyhotkey import HotkeySet
from pycaw.pycaw import AudioUtilities
from gui.volume_view import VolumeView
from process_volume_control import ActiveWindow_VolCtrl



if __name__ == '__main__':

    app = QApplication(sys.argv)

    # set default style
    stylesheet = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui", "styles", "stylesheet.qss")
    file = QFile(stylesheet)
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())
    file.close()

    # create volume controls
    active_window = ActiveWindow_VolCtrl()

    
    volume_controller = VolumeController([active_window])
    volumeview = VolumeView(volume_controller)

    # this needs to run before hotkeys, or error is thrown when running hotkey
    AudioUtilities.GetAllSessions()

    hk = HotkeySet()
    hk.register(('alt_gr', 'page_up'), lambda:active_window.volume_up())
    hk.register(('alt_gr', 'page_down'), lambda:active_window.volume_down())
    hk.register(('alt_gr', 'shift'), lambda:active_window.toggle_mute())
    hk.register(('ctrl', 'cmd', 'esc'), lambda:app.exit(0))
    hk.listen()
    
    sys.exit(app.exec_())
    
