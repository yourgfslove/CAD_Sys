"""
Base Tool class
Базовый класс инструмента
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseTool(ABC):
    """
    Abstract base class for all tools
    Абстрактный базовый класс для всех инструментов
    """
    
    def __init__(self):
        self.canvas = None
        self.is_active = False
        self._preview_ids = []
    
    @abstractmethod
    def get_name(self) -> str:
        """Get tool name for display"""
        pass
    
    @abstractmethod
    def get_icon(self) -> str:
        """Get tool icon (Unicode character or path)"""
        pass
    
    def activate(self, canvas):
        """
        Activate the tool
        Активировать инструмент
        """
        self.canvas = canvas
        self.is_active = True
        self._reset_state()
    
    def deactivate(self):
        """
        Deactivate the tool
        Деактивировать инструмент
        """
        self._clear_preview()
        if self.canvas:
            self.canvas.clear_base_point()
        self.is_active = False
        self.canvas = None
    
    def _reset_state(self):
        """Reset tool state"""
        pass
    
    def _clear_preview(self):
        """Clear preview graphics"""
        if self.canvas:
            for item_id in self._preview_ids:
                try:
                    self.canvas.canvas.delete(item_id)
                except:
                    pass
            self._preview_ids.clear()
    
    def on_mouse_move(self, sx: float, sy: float, wx: float, wy: float):
        """
        Handle mouse movement
        Args:
            sx, sy: Screen coordinates
            wx, wy: World coordinates
        """
        pass
    
    def on_left_click(self, sx: float, sy: float, wx: float, wy: float):
        """Handle left mouse button click"""
        pass
    
    def on_left_drag(self, sx: float, sy: float, wx: float, wy: float):
        """Handle left mouse button drag"""
        pass
    
    def on_left_release(self, sx: float, sy: float, wx: float, wy: float):
        """Handle left mouse button release"""
        pass
    
    def on_right_click(self, sx: float, sy: float, wx: float, wy: float):
        """Handle right mouse button click (usually cancel)"""
        self._reset_state()
        self._clear_preview()
        if self.canvas:
            self.canvas.redraw()
    
    def draw_preview(self, canvas, transform):
        """
        Draw tool preview on canvas
        Нарисовать предпросмотр инструмента
        """
        pass
    
    def on_key_press(self, event):
        """Handle key press"""
        pass
