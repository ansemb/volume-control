from PySide6.QtCore import QObject, QThread, Signal, Slot
from pycaw.pycaw import ISimpleAudioVolume
from process_volume_control import VolumeCtrlBase
from typing import Any, List
import threading

class VolumeController(QObject):
    volume_changed = Signal(int, str)
    volume_muted = Signal(str)
    volume_unmuted = Signal(int, str)

    def __init__(self, volume_ctrls: List[VolumeCtrlBase]) -> None:
        super().__init__()
        self._current_volume_interface = None
        # self._volume_view = volume_view
        self._setup_events(volume_ctrls)

    def _vol_changed_from_backend(self, session: ISimpleAudioVolume, volume: int, icon):
        self._current_volume_interface = session
        self.volume_changed.emit(volume, icon)
    
    def _vol_muted_from_backend(self, session: ISimpleAudioVolume, icon):
        self._current_volume_interface = session
        self.volume_muted.emit(icon)
    
    def _vol_unmuted_from_backend(self, session: ISimpleAudioVolume, volume: int, icon):
        self._current_volume_interface = session
        self.volume_unmuted.emit(volume, icon)

    def _setup_events(self, volume_ctrls: List[VolumeCtrlBase]):
        for vol in volume_ctrls:
            vol.volume_changed_event.append(self._vol_changed_from_backend)
            vol.volume_muted_event.append(self._vol_muted_from_backend)
            vol.volume_unmuted_event.append(self._vol_unmuted_from_backend)
    
    @Slot(int)
    def set_volume_of_last_session(self, volume: int):
        # this will run on main (gui) thread (when called from gui)
        if not self._current_volume_interface:
            return
        if self._current_volume_interface.GetMute():
            self._current_volume_interface.SetMute(0, None)
        self._current_volume_interface.SetMasterVolume(volume/100, None)
