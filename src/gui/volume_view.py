import os,sys,logging
gui_path = os.path.dirname(os.path.realpath(__file__))
main_dir = os.path.abspath(os.path.join(gui_path, os.pardir))
sys.path.insert(1, main_dir) # add volume_control directory at runtime

from volume_controller import VolumeController
from PySide6.QtWidgets import (QWidget, QSlider, QVBoxLayout,
                             QLabel, QApplication)
from PySide6.QtCore import QAbstractAnimation, QFile, QMargins, QTextStream, QTimer, QTimerEvent, QUrl, Qt, QVariantAnimation, QEasingCurve, Signal, Slot

import sys

# colors
class VolumeView(QWidget):
    _alpha = 0.98
    _popup_display_duration = 2000
    _fade_out_duration = 2000
    _volume_changed = Signal(int)
    _muted_text = u"✕"

    def __init__(self, volume_service: VolumeController):
        super().__init__()

        self._prev_volume = None
        self._prev_text = None
        self._current_icon = None

        # window settings
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setFocusPolicy(Qt.NoFocus)

        # connect to backend service
        self._volume_service = volume_service
        self._volume_service.volume_changed.connect(self.set_volume)
        self._volume_service.volume_muted.connect(self.mute)
        self._volume_service.volume_unmuted.connect(self.unmute)

        self._volume_changed.connect(self._volume_service.set_volume_of_last_session)
        self._volume_changed.connect(self._change_text_value)

        # animation setup
        self._animation = QVariantAnimation()
        self._animation.valueChanged.connect(self.setWindowOpacity)
        self._animation.finished.connect(self.hide) # lambda : sys.exit(0)

        # timer
        self._popup_timer = QTimer()
        self._popup_timer.setSingleShot(True)
        self._popup_timer.setInterval(self._popup_display_duration)
        self._popup_timer.timeout.connect(self._start_fadeout)
        
        self.initUI()

        # for some reason qt uses a lot of time to first time render high unicode chars
        # this helps render once, so it will be a lot faster upcoming times
        # used to render _muted_text
        self.setWindowOpacity(0.0)
        self.show()
        self.hide()

    def initUI(self):
        # layout
        vbox = QVBoxLayout()

        # slider
        self._slider = QSlider(Qt.Vertical, self)
        self._slider.setRange(0, 100)
        self._slider.setPageStep(5)
        self._slider.valueChanged.connect(self._volume_changed.emit)
        
        # label
        self._label = QLabel(self._muted_text, self)
        self._label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self._label.setMinimumWidth(10)

        # add to layout
        vbox.addWidget(self._slider)
        vbox.addSpacing(2)
        vbox.setContentsMargins(QMargins(0,20,0,14))
        vbox.addWidget(self._label)
        
        vbox.setAlignment(self._slider, Qt.AlignHCenter)
        vbox.setAlignment(self._label, Qt.AlignHCenter)

        # set layout
        self.setLayout(vbox)
        self.setGeometry(50, 60, 65, 140)
        self.setWindowTitle('VolumeUI')

    @Slot(str)
    @Slot(int)
    def _change_text_value(self, value):
        logging.info(f"value changed: {value}")
        self._label.setText(str(value))

    def _show(self):
        if self._animation.state() == QAbstractAnimation.State.Running:
            self._animation.stop()
        
        if self._popup_timer.isActive():
            self._popup_timer.stop()
        
        if not abs(self.windowOpacity() - self._alpha) < 0.01:
            self.setWindowOpacity(self._alpha)

        if self.isHidden: self.show()

    def _popup(self):
        self._show()
        if not self.underMouse():
            self._popup_timer.start()

    def _start_fadeout(self):
        self._animation.stop()
        self._animation.setStartValue(self._alpha)
        self._animation.setEndValue(0.0)
        self._animation.setDuration(self._fade_out_duration)
        self._animation.setEasingCurve(QEasingCurve.OutBack)
        self._animation.start()

    def _update_volume(self, volume: int, text: str, icon):
        if self._prev_volume != volume:
            self._slider.blockSignals(True)
            self._slider.setValue(volume)
            self._slider.blockSignals(False)
            self._prev_volume=volume
        
        if self._prev_text != text:
            self._change_text_value(text)
            self._prev_text = text

        self._update_icon(icon)
        self._popup()

    def _update_icon(self, icon):
        if not icon == self._current_icon:
            # update/show icon
            pass

    @Slot(int, str)
    def set_volume(self, percentage: int, icon=None):
        self._update_volume(percentage, str(percentage), icon)

    @Slot(str)
    def mute(self, icon=None):
        self._update_volume(0, self._muted_text, icon)

    @Slot(int, str)
    def unmute(self, percentage: int, icon=None):
        self.set_volume(percentage, icon)

    def closeEvent(self, event):
        print('User has pressed the close button; ignoring')
        event.ignore()
        
    def enterEvent(self, event):
        print("enterEvent")
        self._show()
        # return super().enterEvent(event)

    def leaveEvent(self, event):
        print("leaveEvent")
        if not self.windowOpacity()==0.0:
            self._popup()
        # return super().enterEvent(event)


if __name__ == '__main__':
    import os
    app = QApplication(sys.argv)
    stylesheet = os.path.join(os.path.dirname(os.path.realpath(__file__)), "styles", "stylesheet.qss")

    file = QFile(stylesheet)
    print(stylesheet)
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())
    # file.close()
    
    # print(stylesheet)
    # app.setStyleSheet(stylesheet)
    # app.setQuitOnLastWindowClosed(True)

    volume_view = VolumeView(None)
    volume_view._popup()

    sys.exit(app.exec_())