"""
Rectangle primitive
Примитив прямоугольника
"""

import math
from typing import List, Tuple, Dict, Any
from .base import Primitive, ControlPoint, SnapPoint, SnapType, PrimitiveFactory
from ..utils.math_utils import distance, midpoint, rotate_point


class Rectangle(Primitive):
    """Rectangle primitive"""
    
    def __init__(self, x: float = 0, y: float = 0, width: float = 100, height: float = 60, corner_radius: float = 0, rotation: float = 0):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.corner_radius = corner_radius
        self.rotation = rotation
    
    def get_type_name(self) -> str:
        return "Прямоугольник"
    
    def _get_corners(self) -> List[Tuple[float, float]]:
        return [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height),
        ]
    
    def _get_rotated_corners(self) -> List[Tuple[float, float]]:
        center = self.get_center()
        corners = self._get_corners()
        if self.rotation == 0:
            return corners
        return [rotate_point(c, center, self.rotation) for c in corners]
    
    def draw(self, canvas, transform, style_manager) -> List[int]:
        self.clear_canvas_items(canvas)
        
        style = style_manager.get_style(self.style_id)
        if style is None:
            style = style_manager.get_style("solid_main")
        
        color = "#0066CC" if self.selected else style.color
        width = style.get_thickness_px()
        
        corners = self._get_rotated_corners()
        screen_corners = [transform.transform_point(c[0], c[1]) for c in corners]
        
        from ..styles.line_style import LineType
        from ..utils.line_renderer import apply_zigzag_to_points, apply_wavy_to_points
        
        scale = transform.get_scale()
        
        if style.line_type == LineType.SOLID_THIN_ZIGZAG:
            closed_corners = screen_corners + [screen_corners[0]]
            zigzag_length_px = style.zigzag_length * scale
            zigzag_height_px = style.zigzag_height * scale
            zigzag_coords = apply_zigzag_to_points(closed_corners, wave_length=zigzag_length_px, wave_height=zigzag_height_px)
            if len(zigzag_coords) >= 4:
                item_id = canvas.create_line(zigzag_coords, fill=color, width=width)
                self._canvas_ids.append(item_id)
        elif style.line_type == LineType.SOLID_WAVY:
            closed_corners = screen_corners + [screen_corners[0]]
            wavy_length_px = style.wavy_length * scale
            wavy_height_px = style.wavy_height * scale
            wavy_coords = apply_wavy_to_points(closed_corners, wave_length=wavy_length_px, wave_height=wavy_height_px)
            if len(wavy_coords) >= 4:
                item_id = canvas.create_line(wavy_coords, fill=color, width=width, smooth=True)
                self._canvas_ids.append(item_id)
        else:
            points = []
            for c in screen_corners:
                points.extend([c[0], c[1]])
            dash = style.get_tkinter_dash()
            if self.corner_radius > 0:
                if dash:
                    item_id = canvas.create_polygon(points, outline=color, fill="", width=width, dash=dash, smooth=True)
                else:
                    item_id = canvas.create_polygon(points, outline=color, fill="", width=width, smooth=True)
            elif dash:
                item_id = canvas.create_polygon(points, outline=color, fill="", width=width, dash=dash)
            else:
                item_id = canvas.create_polygon(points, outline=color, fill="", width=width)
            self._canvas_ids.append(item_id)
        
        if self.selected:
            for cp in self.get_control_points():
                cpx, cpy = transform.transform_point(cp.x, cp.y)
                cp_id = canvas.create_rectangle(
                    cpx - 4, cpy - 4, cpx + 4, cpy + 4,
                    fill="#FFFFFF", outline="#0066CC", width=2
                )
                self._canvas_ids.append(cp_id)
        
        return self._canvas_ids
    
    def get_control_points(self) -> List[ControlPoint]:
        corners = self._get_rotated_corners()
        center = self.get_center()
        points = [
            ControlPoint(x=corners[0][0], y=corners[0][1], name="Верхний левый", index=0, snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=corners[1][0], y=corners[1][1], name="Верхний правый", index=1, snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=corners[2][0], y=corners[2][1], name="Нижний правый", index=2, snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=corners[3][0], y=corners[3][1], name="Нижний левый", index=3, snap_types=[SnapType.ENDPOINT]),
        ]
        for i in range(4):
            mid = midpoint(corners[i], corners[(i + 1) % 4])
            edge_names = ["Верхняя", "Правая", "Нижняя", "Левая"]
            points.append(ControlPoint(x=mid[0], y=mid[1], name=f"Середина ({edge_names[i]})", index=4 + i, snap_types=[SnapType.MIDPOINT]))
        points.append(ControlPoint(x=center[0], y=center[1], name="Центр", index=8, snap_types=[SnapType.CENTER]))
        return points
    
    def move_control_point(self, index: int, new_x: float, new_y: float):
        if index == 8:
            old_center = self.get_center()
            dx = new_x - old_center[0]
            dy = new_y - old_center[1]
            self.x += dx
            self.y += dy
        elif index < 4:
            if self.rotation == 0:
                if index == 0:
                    old_x2 = self.x + self.width
                    old_y2 = self.y + self.height
                    self.x = new_x
                    self.y = new_y
                    self.width = old_x2 - self.x
                    self.height = old_y2 - self.y
                elif index == 1:
                    old_y2 = self.y + self.height
                    self.width = new_x - self.x
                    self.y = new_y
                    self.height = old_y2 - self.y
                elif index == 2:
                    self.width = new_x - self.x
                    self.height = new_y - self.y
                elif index == 3:
                    old_x2 = self.x + self.width
                    self.x = new_x
                    self.width = old_x2 - self.x
                    self.height = new_y - self.y
        elif index >= 4 and index < 8:
            edge_idx = index - 4
            if self.rotation == 0:
                if edge_idx == 0:
                    old_y2 = self.y + self.height
                    self.y = new_y
                    self.height = old_y2 - self.y
                elif edge_idx == 1:
                    self.width = new_x - self.x
                elif edge_idx == 2:
                    self.height = new_y - self.y
                elif edge_idx == 3:
                    old_x2 = self.x + self.width
                    self.x = new_x
                    self.width = old_x2 - self.x
    
    def get_snap_points(self) -> List[SnapPoint]:
        corners = self._get_rotated_corners()
        center = self.get_center()
        points = [SnapPoint(x=center[0], y=center[1], snap_type=SnapType.CENTER, primitive_id=self.id)]
        for c in corners:
            points.append(SnapPoint(x=c[0], y=c[1], snap_type=SnapType.ENDPOINT, primitive_id=self.id))
        for i in range(4):
            mid = midpoint(corners[i], corners[(i + 1) % 4])
            points.append(SnapPoint(x=mid[0], y=mid[1], snap_type=SnapType.MIDPOINT, primitive_id=self.id))
        return points
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        corners = self._get_rotated_corners()
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        return (min(xs), min(ys), max(xs), max(ys))
    
    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        corners = self._get_rotated_corners()
        for i in range(4):
            c1 = corners[i]
            c2 = corners[(i + 1) % 4]
            from ..utils.math_utils import perpendicular_point
            perp = perpendicular_point((x, y), c1, c2)
            seg_len = distance(c1, c2)
            d1 = distance(c1, perp)
            d2 = distance(perp, c2)
            if d1 <= seg_len and d2 <= seg_len:
                if distance((x, y), perp) <= tolerance:
                    return True
        return False
    
    def get_center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def get_properties(self) -> Dict[str, Any]:
        return {
            "type": self.get_type_name(),
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "corner_radius": self.corner_radius,
            "rotation_deg": math.degrees(self.rotation),
            "perimeter": 2 * (self.width + self.height),
            "area": self.width * self.height,
            "style_id": self.style_id,
        }
    
    def set_property(self, name: str, value: Any) -> bool:
        try:
            if name == "x":
                self.x = float(value)
            elif name == "y":
                self.y = float(value)
            elif name == "width":
                self.width = abs(float(value))
            elif name == "height":
                self.height = abs(float(value))
            elif name == "corner_radius":
                self.corner_radius = max(0, float(value))
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
    def from_two_points(x1: float, y1: float, x2: float, y2: float) -> "Rectangle":
        x = min(x1, x2)
        y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        return Rectangle(x, y, width, height)
    
    @staticmethod
    def from_center(cx: float, cy: float, width: float, height: float) -> "Rectangle":
        x = cx - width / 2
        y = cy - height / 2
        return Rectangle(x, y, width, height)


PrimitiveFactory.register("rectangle", Rectangle)
