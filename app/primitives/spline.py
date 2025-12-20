"""
Spline primitive (Catmull-Rom spline)
Примитив сплайна
"""

import math
from typing import List, Tuple, Dict, Any
from .base import Primitive, ControlPoint, SnapPoint, SnapType, PrimitiveFactory
from ..utils.math_utils import distance, catmull_rom_spline


class Spline(Primitive):
    """Spline primitive (Catmull-Rom)"""
    
    def __init__(self, control_points: List[Tuple[float, float]] = None):
        super().__init__()
        if control_points is None:
            control_points = [(0, 0), (50, -30), (100, 0)]
        self.control_points = list(control_points)
        self.num_segments = 20
    
    def get_type_name(self) -> str:
        return "Сплайн"
    
    def _get_curve_points(self) -> List[Tuple[float, float]]:
        if len(self.control_points) < 2:
            return self.control_points
        return catmull_rom_spline(self.control_points, self.num_segments)
    
    def draw(self, canvas, transform, style_manager) -> List[int]:
        self.clear_canvas_items(canvas)
        
        if len(self.control_points) < 2:
            return self._canvas_ids
        
        style = style_manager.get_style(self.style_id)
        if style is None:
            style = style_manager.get_style("solid_main")
        
        color = "#0066CC" if self.selected else style.color
        width = style.get_thickness_px()
        
        curve_points = self._get_curve_points()
        screen_points_list = [transform.transform_point(p[0], p[1]) for p in curve_points]
        
        from ..styles.line_style import LineType
        from ..utils.line_renderer import apply_zigzag_to_points, apply_wavy_to_points
        
        scale = transform.get_scale()
        
        if style.line_type == LineType.SOLID_THIN_ZIGZAG:
            zigzag_length_px = style.zigzag_length * scale
            zigzag_height_px = style.zigzag_height * scale
            zigzag_coords = apply_zigzag_to_points(screen_points_list, wave_length=zigzag_length_px, wave_height=zigzag_height_px)
            if len(zigzag_coords) >= 4:
                item_id = canvas.create_line(zigzag_coords, fill=color, width=width)
                self._canvas_ids.append(item_id)
        elif style.line_type == LineType.SOLID_WAVY:
            wavy_length_px = style.wavy_length * scale
            wavy_height_px = style.wavy_height * scale
            wavy_coords = apply_wavy_to_points(screen_points_list, wave_length=wavy_length_px, wave_height=wavy_height_px)
            if len(wavy_coords) >= 4:
                item_id = canvas.create_line(wavy_coords, fill=color, width=width, smooth=True)
                self._canvas_ids.append(item_id)
        else:
            screen_points = []
            for p in curve_points:
                sx, sy = transform.transform_point(p[0], p[1])
                screen_points.extend([sx, sy])
            dash = style.get_tkinter_dash()
            if len(screen_points) >= 4:
                if dash:
                    item_id = canvas.create_line(screen_points, fill=color, width=width, dash=dash, smooth=True, capstyle="round", joinstyle="round")
                else:
                    item_id = canvas.create_line(screen_points, fill=color, width=width, smooth=True, capstyle="round", joinstyle="round")
                self._canvas_ids.append(item_id)
        
        if self.selected:
            if len(self.control_points) >= 2:
                poly_points = []
                for p in self.control_points:
                    sx, sy = transform.transform_point(p[0], p[1])
                    poly_points.extend([sx, sy])
                poly_id = canvas.create_line(poly_points, fill="#AAAAAA", width=1, dash=(4, 4))
                self._canvas_ids.append(poly_id)
            
            for i, cp in enumerate(self.control_points):
                cpx, cpy = transform.transform_point(cp[0], cp[1])
                if i == 0 or i == len(self.control_points) - 1:
                    cp_id = canvas.create_rectangle(cpx - 5, cpy - 5, cpx + 5, cpy + 5, fill="#FFFFFF", outline="#0066CC", width=2)
                else:
                    cp_id = canvas.create_oval(cpx - 5, cpy - 5, cpx + 5, cpy + 5, fill="#FFFFFF", outline="#0066CC", width=2)
                self._canvas_ids.append(cp_id)
        
        return self._canvas_ids
    
    def get_control_points(self) -> List[ControlPoint]:
        points = []
        for i, (x, y) in enumerate(self.control_points):
            if i == 0:
                name = "Начало"
                snap_types = [SnapType.ENDPOINT]
            elif i == len(self.control_points) - 1:
                name = "Конец"
                snap_types = [SnapType.ENDPOINT]
            else:
                name = f"Контрольная точка {i}"
                snap_types = []
            points.append(ControlPoint(x=x, y=y, name=name, index=i, snap_types=snap_types))
        return points
    
    def move_control_point(self, index: int, new_x: float, new_y: float):
        if 0 <= index < len(self.control_points):
            self.control_points[index] = (new_x, new_y)
    
    def add_control_point(self, x: float, y: float, index: int = None):
        if index is None:
            self.control_points.append((x, y))
        else:
            self.control_points.insert(index, (x, y))
    
    def remove_control_point(self, index: int) -> bool:
        if len(self.control_points) <= 2:
            return False
        if 0 <= index < len(self.control_points):
            del self.control_points[index]
            return True
        return False
    
    def get_snap_points(self) -> List[SnapPoint]:
        points = []
        if len(self.control_points) >= 1:
            p = self.control_points[0]
            points.append(SnapPoint(x=p[0], y=p[1], snap_type=SnapType.ENDPOINT, primitive_id=self.id))
        if len(self.control_points) >= 2:
            p = self.control_points[-1]
            points.append(SnapPoint(x=p[0], y=p[1], snap_type=SnapType.ENDPOINT, primitive_id=self.id))
        return points
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        if not self.control_points:
            return (0, 0, 0, 0)
        curve_points = self._get_curve_points()
        xs = [p[0] for p in curve_points]
        ys = [p[1] for p in curve_points]
        return (min(xs), min(ys), max(xs), max(ys))
    
    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        curve_points = self._get_curve_points()
        if len(curve_points) < 2:
            if len(curve_points) == 1:
                return distance((x, y), curve_points[0]) <= tolerance
            return False
        
        from ..utils.math_utils import perpendicular_point
        for i in range(len(curve_points) - 1):
            p1 = curve_points[i]
            p2 = curve_points[i + 1]
            perp = perpendicular_point((x, y), p1, p2)
            seg_len = distance(p1, p2)
            d1 = distance(p1, perp)
            d2 = distance(perp, p2)
            if d1 <= seg_len + tolerance and d2 <= seg_len + tolerance:
                if distance((x, y), perp) <= tolerance:
                    return True
        return False
    
    def get_length(self) -> float:
        curve_points = self._get_curve_points()
        if len(curve_points) < 2:
            return 0
        total_length = 0
        for i in range(len(curve_points) - 1):
            total_length += distance(curve_points[i], curve_points[i + 1])
        return total_length
    
    def get_properties(self) -> Dict[str, Any]:
        return {
            "type": self.get_type_name(),
            "num_control_points": len(self.control_points),
            "control_points": self.control_points.copy(),
            "length": self.get_length(),
            "style_id": self.style_id,
        }
    
    def set_property(self, name: str, value: Any) -> bool:
        try:
            if name == "control_points" and isinstance(value, list):
                self.control_points = [(float(p[0]), float(p[1])) for p in value]
            elif name == "style_id":
                self.style_id = str(value)
            else:
                return False
            return True
        except (ValueError, TypeError, IndexError):
            return False


PrimitiveFactory.register("spline", Spline)
