from msl.loadlib import Client64

class OverlayEditorClient(Client64):
    def __init__(self):
        super(OverlayEditorClient, self).__init__(module32='overlay_editor_server')

    def post_overlay_message(self, message: str, layer: str, params: str):
        return self.request32('post_overlay_message', message.encode('utf-8'), layer.encode('utf-8'), params.encode('utf-8'))