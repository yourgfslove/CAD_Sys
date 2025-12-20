"""
Ellipse primitive
Примитив эллипса
"""

import math
from typing import List, Tuple, Dict, Any
from .base import Primitive, ControlPoint, SnapPoint, SnapType, PrimitiveFactory
from ..utils.math_utils import distance, rotate_point


class Ellipse(Primitive):
    """Ellipse primitive"""
    
    def __init__(self, cx: float = 0, cy: float = 0, rx: float = 80, ry: float = 50, rotation: float = 0):
        super().__init__()
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry
        self.rotation = rotation
    
    def get_type_name(self) -> str:
        return "Эллипс"
    
    def _get_point_on_ellipse(self, angle: float) -> Tuple[float, float]:
        x = self.rx * math.cos(angle)
        y = self.ry * math.sin(angle)
        if self.rotation != 0:
            cos_r = math.cos(self.rotation)
            sin_r = math.sin(self.rotation)
            x_rot = x * cos_r - y * sin_r
            y_rot = x * sin_r + y * cos_r
            x, y = (x_rot, y_rot)
        return (self.cx + x, self.cy + y)
    
    def draw(self, canvas, transform, style_manager) -> List[int]:
        self.clear_canvas_items(canvas)
        
        style = style_manager.get_style(self.style_id)
        if style is None:
            style = style_manager.get_style("solid_main")
        
        color = "#0066CC" if self.selected else style.color
        width = style.get_thickness_px()
        dash = style.get_tkinter_dash()
        
        from ..styles.line_style import LineType
        from ..utils.line_renderer import apply_zigzag_to_points, apply_wavy_to_points
        
        num_points = 72
        ellipse_points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            px, py = self._get_point_on_ellipse(angle)
            ellipse_points.append((px, py))
        
        screen_points = [transform.transform_point(p[0], p[1]) for p in ellipse_points]
        
        scale = transform.get_scale()
        
        if style.line_type == LineType.SOLID_THIN_ZIGZAG:
            closed_points = screen_points + [screen_points[0]]
            zigzag_length_px = style.zigzag_length * scale
            zigzag_height_px = style.zigzag_height * scale
            zigzag_coords = apply_zigzag_to_points(closed_points, wave_length=zigzag_length_px, wave_height=zigzag_height_px)
            if len(zigzag_coords) >= 4:
                item_id = canvas.create_line(zigzag_coords, fill=color, width=width)
                self._canvas_ids.append(item_id)
        elif style.line_type == LineType.SOLID_WAVY:
            closed_points = screen_points + [screen_points[0]]
            wavy_length_px = style.wavy_length * scale
            wavy_height_px = style.wavy_height * scale
            wavy_coords = apply_wavy_to_points(closed_points, wave_length=wavy_length_px, wave_height=wavy_height_px)
            if len(wavy_coords) >= 4:
                item_id = canvas.create_line(wavy_coords, fill=color, width=width, smooth=True)
                self._canvas_ids.append(item_id)
        else:
            points = []
            for sx, sy in screen_points:
                points.extend([sx, sy])
            dash = style.get_tkinter_dash()
            if dash:
                item_id = canvas.create_polygon(points, outline=color, fill="", width=width, dash=dash, smooth=True)
            else:
                item_id = canvas.create_polygon(points, outline=color, fill="", width=width, smooth=True)
            self._canvas_ids.append(item_id)
        
        if self.selected:
            for cp in self.get_control_points():
                cpx, cpy = transform.transform_point(cp.x, cp.y)
                cp_id = canvas.create_rectangle(
                    cpx - 4, cpy - 4, cpx + 4, cpy + 4,
                    fill="#FFFFFF", outline="#0066CC", width=2
                )
                self._canvas_ids.append(cp_id)
            scx, scy = transform.transform_point(self.cx, self.cy)
            center_id = canvas.create_oval(scx - 3, scy - 3, scx + 3, scy + 3, fill="#0066CC", outline="#0066CC")
            self._canvas_ids.append(center_id)
        
        return self._canvas_ids
    
    def get_control_points(self) -> List[ControlPoint]:
        right = self._get_point_on_ellipse(0)
        top = self._get_point_on_ellipse(math.pi / 2)
        left = self._get_point_on_ellipse(math.pi)
        bottom = self._get_point_on_ellipse(3 * math.pi / 2)
        return [
            ControlPoint(x=self.cx, y=self.cy, name="Центр", index=0, snap_types=[SnapType.CENTER]),
            ControlPoint(x=right[0], y=right[1], name="Правая ось", index=1, snap_types=[SnapType.QUADRANT]),
            ControlPoint(x=top[0], y=top[1], name="Верхняя ось", index=2, snap_types=[SnapType.QUADRANT]),
            ControlPoint(x=left[0], y=left[1], name="Левая ось", index=3, snap_types=[SnapType.QUADRANT]),
            ControlPoint(x=bottom[0], y=bottom[1], name="Нижняя ось", index=4, snap_types=[SnapType.QUADRANT]),
        ]
    
    def move_control_point(self, index: int, new_x: float, new_y: float):
        if index == 0:
            self.cx = new_x
            self.cy = new_y
        elif index == 1 or index == 3:
            self.rx = distance((self.cx, self.cy), (new_x, new_y))
        elif index == 2 or index == 4:
            self.ry = distance((self.cx, self.cy), (new_x, new_y))
    
    def get_snap_points(self) -> List[SnapPoint]:
        right = self._get_point_on_ellipse(0)
        top = self._get_point_on_ellipse(math.pi / 2)
        left = self._get_point_on_ellipse(math.pi)
        bottom = self._get_point_on_ellipse(3 * math.pi / 2)
        return [
            SnapPoint(x=self.cx, y=self.cy, snap_type=SnapType.CENTER, primitive_id=self.id),
            SnapPoint(x=right[0], y=right[1], snap_type=SnapType.QUADRANT, primitive_id=self.id),
            SnapPoint(x=top[0], y=top[1], snap_type=SnapType.QUADRANT, primitive_id=self.id),
            SnapPoint(x=left[0], y=left[1], snap_type=SnapType.QUADRANT, primitive_id=self.id),
            SnapPoint(x=bottom[0], y=bottom[1], snap_type=SnapType.QUADRANT, primitive_id=self.id),
        ]
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        if self.rotation == 0:
            return (self.cx - self.rx, self.cy - self.ry, self.cx + self.rx, self.cy + self.ry)
        points = [self._get_point_on_ellipse(i * math.pi / 18) for i in range(36)]
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return (min(xs), min(ys), max(xs), max(ys))
    
    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        dx = x - self.cx
        dy = y - self.cy
        if self.rotation != 0:
            cos_r = math.cos(-self.rotation)
            sin_r = math.sin(-self.rotation)
            dx_rot = dx * cos_r - dy * sin_r
            dy_rot = dx * sin_r + dy * cos_r
            dx, dy = (dx_rot, dy_rot)
        if self.rx == 0 or self.ry == 0:
            return False
        value = (dx / self.rx) ** 2 + (dy / self.ry) ** 2
        avg_radius = (self.rx + self.ry) / 2
        rel_tolerance = tolerance / avg_radius if avg_radius > 0 else 0.1
        return abs(value - 1) <= rel_tolerance
    
    def get_properties(self) -> Dict[str, Any]:
        return {
            "type": self.get_type_name(),
            "cx": self.cx,
            "cy": self.cy,
            "rx": self.rx,
            "ry": self.ry,
            "rotation_deg": math.degrees(self.rotation),
            "perimeter": self._approximate_perimeter(),
            "area": math.pi * self.rx * self.ry,
            "style_id": self.style_id,
        }
    
    def _approximate_perimeter(self) -> float:
        a = self.rx
        b = self.ry
        h = (a - b) ** 2 / (a + b) ** 2
        return math.pi * (a + b) * (1 + 3 * h / (10 + math.sqrt(4 - 3 * h)))
    
    def set_property(self, name: str, value: Any) -> bool:
        try:
            if name == "cx":
                self.cx = float(value)
            elif name == "cy":
                self.cy = float(value)
            elif name == "rx":
                self.rx = abs(float(value))
            elif name == "ry":
                self.ry = abs(float(value))
            elif name == "rotation_deg":
                self.rotation = math.radians(float(value))
            elif name == "style_id":
                self.style_id = str(value)
            else:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def from_center_and_axes(cx: float, cy: float, ax1: float, ay1: float, ax2: float, ay2: float) -> "Ellipse":
        rx = distance((cx, cy), (ax1, ay1))
        ry = distance((cx, cy), (ax2, ay2))
        rotation = math.atan2(ay1 - cy, ax1 - cx)
        return Ellipse(cx, cy, rx, ry, rotation)


PrimitiveFactory.register("ellipse", Ellipse)
