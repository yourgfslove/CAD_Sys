"""
Circle primitive
Примитив окружности
"""

import math
from typing import List, Tuple, Dict, Any
from .base import Primitive, ControlPoint, SnapPoint, SnapType, PrimitiveFactory
from ..utils.math_utils import distance


class Circle(Primitive):
    """Circle primitive"""
    
    def __init__(self, cx: float = 0, cy: float = 0, radius: float = 50):
        super().__init__()
        self.cx = cx
        self.cy = cy
        self.radius = radius
    
    def get_type_name(self) -> str:
        return "Окружность"
    
    def draw(self, canvas, transform, style_manager) -> List[int]:
        self.clear_canvas_items(canvas)
        
        scx, scy = transform.transform_point(self.cx, self.cy)
        scale = transform.get_scale()
        sr = self.radius * scale
        
        style = style_manager.get_style(self.style_id)
        if style is None:
            style = style_manager.get_style("solid_main")
        
        color = "#0066CC" if self.selected else style.color
        width = style.get_thickness_px()
        
        from ..styles.line_style import LineType
        from ..utils.line_renderer import sample_circle_points, apply_zigzag_to_points, apply_wavy_to_points
        
        if style.line_type == LineType.SOLID_THIN_ZIGZAG:
            circle_points = sample_circle_points(self.cx, self.cy, self.radius, 64)
            screen_points = []
            for p in circle_points:
                sp = transform.transform_point(p[0], p[1])
                screen_points.append(sp)
            # Use style parameters converted to pixels
            zigzag_length_px = style.zigzag_length * scale
            zigzag_height_px = style.zigzag_height * scale
            zigzag_coords = apply_zigzag_to_points(screen_points, wave_length=zigzag_length_px, wave_height=zigzag_height_px)
            if len(zigzag_coords) >= 4:
                item_id = canvas.create_line(zigzag_coords, fill=color, width=width)
                self._canvas_ids.append(item_id)
        elif style.line_type == LineType.SOLID_WAVY:
            circle_points = sample_circle_points(self.cx, self.cy, self.radius, 128)
            screen_points = []
            for p in circle_points:
                sp = transform.transform_point(p[0], p[1])
                screen_points.append(sp)
            # Use style parameters converted to pixels
            wavy_length_px = style.wavy_length * scale
            wavy_height_px = style.wavy_height * scale
            wavy_coords = apply_wavy_to_points(screen_points, wave_length=wavy_length_px, wave_height=wavy_height_px)
            if len(wavy_coords) >= 4:
                item_id = canvas.create_line(wavy_coords, fill=color, width=width, smooth=True)
                self._canvas_ids.append(item_id)
        else:
            dash = style.get_tkinter_dash()
            if dash:
                item_id = canvas.create_oval(scx - sr, scy - sr, scx + sr, scy + sr, outline=color, width=width, dash=dash)
            else:
                item_id = canvas.create_oval(scx - sr, scy - sr, scx + sr, scy + sr, outline=color, width=width)
            self._canvas_ids.append(item_id)
        
        if self.selected:
            for cp in self.get_control_points():
                cpx, cpy = transform.transform_point(cp.x, cp.y)
                cp_id = canvas.create_rectangle(
                    cpx - 4, cpy - 4, cpx + 4, cpy + 4,
                    fill="#FFFFFF", outline="#0066CC", width=2
                )
                self._canvas_ids.append(cp_id)
            center_id = canvas.create_oval(scx - 3, scy - 3, scx + 3, scy + 3, fill="#0066CC", outline="#0066CC")
            self._canvas_ids.append(center_id)
        
        return self._canvas_ids
    
    def get_control_points(self) -> List[ControlPoint]:
        return [
            ControlPoint(x=self.cx, y=self.cy, name="Центр", index=0, snap_types=[SnapType.CENTER]),
            ControlPoint(x=self.cx + self.radius, y=self.cy, name="Правый квадрант", index=1, snap_types=[SnapType.QUADRANT]),
            ControlPoint(x=self.cx, y=self.cy - self.radius, name="Верхний квадрант", index=2, snap_types=[SnapType.QUADRANT]),
            ControlPoint(x=self.cx - self.radius, y=self.cy, name="Левый квадрант", index=3, snap_types=[SnapType.QUADRANT]),
            ControlPoint(x=self.cx, y=self.cy + self.radius, name="Нижний квадрант", index=4, snap_types=[SnapType.QUADRANT]),
        ]
    
    def move_control_point(self, index: int, new_x: float, new_y: float):
        if index == 0:
            self.cx = new_x
            self.cy = new_y
        else:
            self.radius = distance((self.cx, self.cy), (new_x, new_y))
    
    def get_snap_points(self) -> List[SnapPoint]:
        return [
            SnapPoint(x=self.cx, y=self.cy, snap_type=SnapType.CENTER, primitive_id=self.id),
            SnapPoint(x=self.cx + self.radius, y=self.cy, snap_type=SnapType.QUADRANT, primitive_id=self.id),
            SnapPoint(x=self.cx, y=self.cy - self.radius, snap_type=SnapType.QUADRANT, primitive_id=self.id),
            SnapPoint(x=self.cx - self.radius, y=self.cy, snap_type=SnapType.QUADRANT, primitive_id=self.id),
            SnapPoint(x=self.cx, y=self.cy + self.radius, snap_type=SnapType.QUADRANT, primitive_id=self.id),
        ]
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        return (self.cx - self.radius, self.cy - self.radius, self.cx + self.radius, self.cy + self.radius)
    
    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        d = distance((self.cx, self.cy), (x, y))
        return abs(d - self.radius) <= tolerance
    
    def get_properties(self) -> Dict[str, Any]:
        return {
            "type": self.get_type_name(),
            "cx": self.cx,
            "cy": self.cy,
            "radius": self.radius,
            "diameter": self.radius * 2,
            "circumference": 2 * math.pi * self.radius,
            "area": math.pi * self.radius ** 2,
            "style_id": self.style_id,
        }
    
    def set_property(self, name: str, value: Any) -> bool:
        try:
            if name == "cx":
                self.cx = float(value)
            elif name == "cy":
                self.cy = float(value)
            elif name == "radius":
                self.radius = abs(float(value))
            elif name == "diameter":
                self.radius = abs(float(value)) / 2
            elif name == "style_id":
                self.style_id = str(value)
            else:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def from_center_and_point(cx: float, cy: float, px: float, py: float) -> "Circle":
        radius = distance((cx, cy), (px, py))
        return Circle(cx, cy, radius)
    
    @staticmethod
    def from_three_points(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> "Circle":
        ax, ay = (x1, y1)
        bx, by = (x2, y2)
        cx, cy = (x3, y3)
        
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(d) < 1e-10:
            return Circle((x1 + x2 + x3) / 3, (y1 + y2 + y3) / 3, 50)
        
        ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
        uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
        radius = distance((ux, uy), (ax, ay))
        return Circle(ux, uy, radius)


PrimitiveFactory.register("circle", Circle)
