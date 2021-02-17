from typing import List, Callable

from pynput import keyboard as kb


_MODIFIERS = ('ctrl','alt','shift','cmd','alt_gr',
'page_up','page_down', 'home','end',
'delete','space','enter','esc','tab','backspace',
'up','down','left','right',
'f1','f2','f3','f4','f5','f6','f7','f8','f9','f10','f11','f12')

class Hotkey(kb.HotKey):
    def __init__(self, keys, on_activate) -> None:
        super().__init__(keys, on_activate)
    
    def press(self, key):
        """Updates the hotkey state for a pressed key.
        If the key is not currently pressed, but is the last key for the full
        combination, the activation callback will be invoked.
        Please note that the callback will only be invoked once.
        :param key: The key being pressed.
        :type key: Key or KeyCode
        """
        # TODO: check that modifiers are pressed before other
        # TODO: not activate when extra modifier is pressed as well; if hotkey is <alt>+<pgup>,
        # hotkey should not activate on <ctrl>+<alt>+<pgup>
        if key in self._keys:
            # print(f"here: {key}")
            self._state.add(key)
            if self._state == self._keys:
                self._on_activate()
    # @staticmethod
    # def parse(keys):
    #     super().parse(keys)

class HotkeySet:
    _listener = None
    _instance = None
    _hotkeys = []

    class InvalidHotkey(ValueError):
        pass

    def __new__(cls, *args):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args)
        return cls._instance

    def __key_isvalid(self, key) -> bool:
        if len(key)==0:
            return False
        elif len(key)==1:
            if not key.isascii():
                return False
            if not (32 < ord(key) < 127):
                return False
        elif not key.lower() in _MODIFIERS:
            return False
        return True

    def register(self, hotkey: List[str], callback: Callable) -> None:
        """Register a new hotkey."""
        if len(hotkey)==0:
            raise self.InvalidHotkey("Length of hotkey cannot be 0.")
        
        current_hotkey = ""
        for key in hotkey:
            key=key.lower()
            if not self.__key_isvalid(key):
                raise self.InvalidHotkey(f"Invalid key '{key}'")
            if len(key)==1:
                current_hotkey += f'{key}+'
            else:
                current_hotkey += f'<{key}>+'
        current_hotkey = current_hotkey[:-1]

        self._hotkeys.append(Hotkey(
            Hotkey.parse(current_hotkey),
            callback))

    def _on_press(self,key):
        for hotkey in self._hotkeys:
            hotkey.press(self._listener.canonical(key))

    def _on_release(self, key):
        """The release callback.
        This is automatically registered upon creation.
        :param key: The key provided by the base class.
        """
        for hotkey in self._hotkeys:
            hotkey.release(self._listener.canonical(key))

    def listen(self) -> None:
        """Start listening to hotkeys. Non-blocking."""
        self._listener = kb.Listener(
                on_press=self._on_press, 
                on_release=self._on_release)
        self._listener.start()
    
    def listen_block(self) -> None:
        """Start listening to hotkeys. Blocking."""
        with kb.Listener(
                on_press=self._on_press, 
                on_release=self._on_release) as l:
            self._listener = l
            l.join()

if __name__ == '__main__':
    
    import sys
    hk = HotkeySet()
    hk.register(('ctrl', 'page_up'), lambda:print("ueu"))
    hk.register(('ctrl', 'cmd', 'esc'), lambda:sys.exit())
    hk.listen_block()
