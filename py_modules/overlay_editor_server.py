from ctypes import c_char_p
from msl.loadlib import Server32

class OverlayEditorServer(Server32):
    def __init__(self, host, port, **kwargs):
        super(OverlayEditorServer, self).__init__(b'C:\Program Files (x86)\RivaTuner Statistics Server\Plugins\Client\OverlayEditor.dll', 'cdll', host, port)

    def post_overlay_message(self, message: c_char_p, layer: c_char_p, params: c_char_p):
        self.lib.PostOverlayMessage.restype = None
        self.lib.PostOverlayMessage.argtypes = [c_char_p, c_char_p, c_char_p]
        self.lib.PostOverlayMessage(message, layer, params)