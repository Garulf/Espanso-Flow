import sys
from subprocess import Popen, PIPE, CREATE_NO_WINDOW
import ctypes
import time

user32 = ctypes.WinDLL('user32', use_last_error=True)
DEFAULT = r'C:\Users\Garulf\AppData\Local\Programs\Espanso\espanso.cmd'
SLEEP_INTERVAL = 0.1

def get_foreground_window_name():
    foreground_window = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(foreground_window)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(foreground_window, buff, length + 1)
    return buff.value

def main(path, trigger):
    for i in range(1, 10):
        foreground_window = get_foreground_window_name()
        if foreground_window != "Flow.Launcher":
            p = Popen([path, "match", "exec", "-t", trigger], stdout=PIPE, stderr=PIPE, creationflags=CREATE_NO_WINDOW)
            out, err = p.communicate()
            break
        time.sleep(SLEEP_INTERVAL)
        

if __name__ == "__main__":
    path = sys.argv[1]
    trigger = sys.argv[2]
    main(path, trigger)