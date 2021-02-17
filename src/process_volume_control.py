import os
from PySide6.QtCore import QObject
from utils.event import Event
from utils.win_utils import *
from pycaw.pycaw import AudioUtilities
import operator
from time import perf_counter
from typing import Callable
from abc import ABC, abstractmethod
# from volume_control_service import VolumeService

VOLUME_STEP = 0.02

class VolumeCtrlBase(ABC):

    def __init__(self) -> None:
        super().__init__()
        
        self._volume_changed_event = Event()
        self._volume_muted_event = Event()
        self._volume_unmuted_event = Event()

    @abstractmethod
    def volume_up(self):
        pass

    @abstractmethod
    def volume_down(self):
        pass
    
    @abstractmethod
    def set_volume(self, volume: int):
        pass

    @abstractmethod
    def mute(self):
        pass
    
    @abstractmethod
    def unmute(self):
        pass

    @property
    def volume_changed_event(self) -> Event:
        """Volume changed event, args: (self, volume: int, icon)

        Returns:
            Event: an event that one can subscribe to
        """
        return self._volume_changed_event

    @property
    def volume_muted_event(self) -> Event:
        """Volume muted event, args: (self, icon)

        Returns:
            Event: an event that one can subscribe to
        """
        return self._volume_muted_event

    @property
    def volume_unmuted_event(self) -> Event:
        """Volume unmuted event, args: (self, volume: int, icon)

        Returns:
            Event: an event that one can subscribe to
        """
        return self._volume_unmuted_event


class ActiveWindow_VolCtrl(VolumeCtrlBase):
    def __init__(self, volume_step: float=VOLUME_STEP) -> None:
        super().__init__()
        # self._vol_service = volume_service
        self._interface = None
        self._volume_step = volume_step
        self._prev_time = 0.0
        self._audio_session_time = 0.0 # allow pid for same window to be updated
        self._prev_pid = None

    def _get_audio_session_active_window(self):
        pname = get_process_name_active_window()
        if len(pname)==0: return

        print(f"process name: {pname}")

        session = None
        sessions = AudioUtilities.GetAllSessions()
        for s in sessions:
            if s.Process and s.Process.name() == pname:
                session = s
                break
        return session

    def _set_interface_and_continue_execution(self, pid: int) -> bool:
        """Sets audio interface of active window, if pid has changed, and if it exists for current pid.
        Then tells the parent function to continue execution or stop.

        Args:
            pid (int): process id of active window

        Returns:
            bool: tell the parent function if it should continue the execution or stop
        """
        # TODO: maybe save interface for pid, and update only if needed

        # performance enhancement (minimize calls to "get_audio_session_active_window")
        cur_time = perf_counter()
        if pid == self._prev_pid and cur_time - self._audio_session_time < 2.0:
            if self._interface:
                return True
            return False

        # if the window of this process is activated, we want to skip th
        if pid == os.getpid():
            if self._interface: # use last audio interface if exist
                return True
            return False
        
        self._prev_pid = pid
        self._audio_session_time = cur_time

        # get session
        session = self._get_audio_session_active_window()
        if session is None:
            self._interface = None
            return False
        
        self._interface = session.SimpleAudioVolume

        if self._interface is None:
            return False
        return True

    def _volume_delta(self, op: Callable):
        # get process id of active window (lightweight task)
        pid = get_pid_active_window()
        if not self._set_interface_and_continue_execution(pid):
            return

        if self._interface.GetMute():
            self._interface.SetMute(0, None)
        vol = max(0.0, min(1.0, op(self._interface.GetMasterVolume(), self._volume_step)))
        self._interface.SetMasterVolume(vol, None)

        self._volume_changed_event(self._interface, int(round(vol*100)), icon=None)

    def volume_up(self):
        """Increase the volume of the active window
        """
        self._volume_delta(operator.add)

    def volume_down(self):
        self._volume_delta(operator.sub)

    def set_volume(self, volume: int):
        if not 0 <= volume <= 100:
            return
        # pid = get_pid_active_window()
        if not self._set_interface_and_continue_execution(get_pid_active_window()):
            return

        self._interface.SetMasterVolume(volume/100, None)
        self._volume_changed_event(self._interface, volume, icon=None)

    def _timeout_if_needed(self):
        # add timeout if called repeatedly, a call to 
        cur_time = perf_counter()
        if cur_time-self._prev_time < 0.1:
            return True
        self._prev_time = cur_time
        return  False

    def _mute(self, pid):
        self._interface.SetMute(1, None)
        print("sending muted event")
        self._volume_muted_event(self._interface, icon=None)
        # self._prev_pid = None

    def _unmute(self, pid):
        self._interface.SetMute(0, None)
        vol = int(round(self._interface.GetMasterVolume()*100))
        self._volume_unmuted_event(self._interface, vol, icon=None)
        # self._prev_pid = None

    def mute(self):
        if self._timeout_if_needed(): return
        pid = get_pid_active_window()
        if not self._set_interface_and_continue_execution(pid):
            return
        self._mute(pid)

    def unmute(self):
        if self._timeout_if_needed(): return
        pid = get_pid_active_window()
        if not self._set_interface_and_continue_execution(pid):
            return
        self._unmute(pid)

    def toggle_mute(self):
        if self._timeout_if_needed(): return
        pid = get_pid_active_window()
        if not self._set_interface_and_continue_execution(pid):
            return
        if self._interface.GetMute():
            self._unmute(pid)
        else:
            self._mute(pid)
