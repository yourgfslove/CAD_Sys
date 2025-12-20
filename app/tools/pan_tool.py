"""
Pan Tool - для панорамирования
Инструмент панорамирования
"""

from .base_tool import BaseTool


class PanTool(BaseTool):
    """Pan tool for canvas navigation"""
    
    def __init__(self):
        super().__init__()
        self._panning = False
    
    def get_name(self) -> str:
        return "Рука"
    
    def get_icon(self) -> str:
        return "✋"
    
    def activate(self, canvas):
        super().activate(canvas)
        if canvas:
            canvas.canvas.config(cursor="fleur")
    
    def deactivate(self):
        if self.canvas:
            self.canvas.canvas.config(cursor="")
        super().deactivate()
    
    def _reset_state(self):
        self._panning = False
        if self.canvas:
            self.canvas.navigation.end_pan()
    
    def on_left_click(self, sx: float, sy: float, wx: float, wy: float):
        if self.canvas:
            self.canvas.navigation.start_pan(sx, sy)
            self._panning = True
    
    def on_left_drag(self, sx: float, sy: float, wx: float, wy: float):
        if self._panning and self.canvas:
            self.canvas.navigation.update_pan(sx, sy)
    
    def on_left_release(self, sx: float, sy: float, wx: float, wy: float):
        if self.canvas:
            self.canvas.navigation.end_pan()
            self._panning = False
