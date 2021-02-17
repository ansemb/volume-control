from win32gui import GetForegroundWindow
from win32process import GetWindowThreadProcessId, GetModuleFileNameEx
from win32api import OpenProcess, CloseHandle
from win32con import PROCESS_QUERY_INFORMATION, PROCESS_VM_READ
from ntpath import basename
import logging

# utility functions
def get_pid_active_window():
    _, pid = GetWindowThreadProcessId(GetForegroundWindow())
    return pid

def get_process_name(pid):
    pname = None
    try:
        handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        pname = GetModuleFileNameEx(handle, 0)
        CloseHandle(handle)
    except Exception as e:
        logging.exception(e)

    return pname

def get_process_name_active_window():
    return basename(get_process_name(get_pid_active_window()))
