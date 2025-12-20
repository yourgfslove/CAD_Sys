"""
Select Tool - для выделения и редактирования
Инструмент выделения
"""

from typing import Optional, List, Tuple
from .base_tool import BaseTool
from ..primitives.base import Primitive, ControlPoint
from ..utils.math_utils import distance


class SelectTool(BaseTool):
    """Selection tool for selecting and editing primitives"""
    
    def __init__(self):
        super().__init__()
        self._dragging = False
        self._drag_start_x = 0.0
        self._drag_start_y = 0.0
        self._dragging_control_point: Optional[Tuple[Primitive, int]] = None
        self._selection_box = False
        self._box_start_x = 0.0
        self._box_start_y = 0.0
    
    def get_name(self) -> str:
        return "Выделение"
    
    def get_icon(self) -> str:
        return "⬚"
    
    def _reset_state(self):
        self._dragging = False
        self._dragging_control_point = None
        self._selection_box = False
    
    def on_left_click(self, sx: float, sy: float, wx: float, wy: float):
        if not self.canvas:
            return
        
        cp = self._find_control_point_at(sx, sy)
        if cp:
            self._dragging_control_point = cp
            self._dragging = True
            self._drag_start_x = wx
            self._drag_start_y = wy
            return
        
        primitive = self.canvas.find_primitive_at(wx, wy)
        if primitive:
            shift_pressed = getattr(self.canvas, '_shift_pressed', False)
            self.canvas.select_primitive(primitive, add=shift_pressed)
            self._dragging = True
            self._drag_start_x = wx
            self._drag_start_y = wy
        else:
            if not getattr(self.canvas, '_shift_pressed', False):
                self.canvas.deselect_all()
            self._selection_box = True
            self._box_start_x = wx
            self._box_start_y = wy
    
    def on_left_drag(self, sx: float, sy: float, wx: float, wy: float):
        if not self.canvas:
            return
        
        if self._dragging_control_point:
            primitive, cp_index = self._dragging_control_point
            primitive.move_control_point(cp_index, wx, wy)
            self.canvas.redraw()
        elif self._dragging and self.canvas.selected_primitives:
            dx = wx - self._drag_start_x
            dy = wy - self._drag_start_y
            for primitive in self.canvas.selected_primitives:
                primitive.translate(dx, dy)
            self._drag_start_x = wx
            self._drag_start_y = wy
            self.canvas.redraw()
        elif self._selection_box:
            self.canvas.redraw()
            self._draw_selection_box(wx, wy)
    
    def on_left_release(self, sx: float, sy: float, wx: float, wy: float):
        if self._selection_box:
            self._select_in_box(wx, wy)
        
        self._dragging = False
        self._dragging_control_point = None
        self._selection_box = False
        self._clear_preview()
        if self.canvas:
            self.canvas.redraw()
    
    def _find_control_point_at(self, sx: float, sy: float) -> Optional[Tuple[Primitive, int]]:
        if not self.canvas:
            return None
        
        tolerance = 8.0
        for primitive in self.canvas.selected_primitives:
            for cp in primitive.get_control_points():
                cpx, cpy = self.canvas.transform.transform_point(cp.x, cp.y)
                if distance((sx, sy), (cpx, cpy)) <= tolerance:
                    return (primitive, cp.index)
        return None
    
    def _draw_selection_box(self, wx: float, wy: float):
        if not self.canvas:
            return
        
        self._clear_preview()
        sx1, sy1 = self.canvas.transform.transform_point(self._box_start_x, self._box_start_y)
        sx2, sy2 = self.canvas.transform.transform_point(wx, wy)
        
        box_id = self.canvas.canvas.create_rectangle(sx1, sy1, sx2, sy2, outline="#0066CC", dash=(4, 4), width=1)
        self._preview_ids.append(box_id)
        fill_id = self.canvas.canvas.create_rectangle(sx1, sy1, sx2, sy2, fill="#0066CC", stipple="gray25", outline="")
        self._preview_ids.append(fill_id)
    
    def _select_in_box(self, wx: float, wy: float):
        if not self.canvas:
            return
        
        min_x = min(self._box_start_x, wx)
        max_x = max(self._box_start_x, wx)
        min_y = min(self._box_start_y, wy)
        max_y = max(self._box_start_y, wy)
        
        for primitive in self.canvas.primitives:
            bbox = primitive.get_bounding_box()
            if bbox[0] <= max_x and bbox[2] >= min_x and bbox[1] <= max_y and bbox[3] >= min_y:
                self.canvas.select_primitive(primitive, add=True)
    
    def draw_preview(self, canvas_widget, transform):
        pass
