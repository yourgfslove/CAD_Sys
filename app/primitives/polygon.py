"""
Polygon primitive
Примитив многоугольника
"""

import math
from typing import List, Tuple, Dict, Any
from enum import Enum
from .base import Primitive, ControlPoint, SnapPoint, SnapType, PrimitiveFactory
from ..utils.math_utils import distance, midpoint, rotate_point


class PolygonType(Enum):
    INSCRIBED = "inscribed"
    CIRCUMSCRIBED = "circumscribed"


class Polygon(Primitive):
    """Polygon primitive"""
    
    def __init__(self, cx: float = 0, cy: float = 0, radius: float = 50, num_sides: int = 6, polygon_type: PolygonType = PolygonType.INSCRIBED, rotation: float = 0):
        super().__init__()
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.num_sides = max(3, num_sides)
        self.polygon_type = polygon_type
        self.rotation = rotation
    
    def get_type_name(self) -> str:
        return "Многоугольник"
    
    def _get_effective_radius(self) -> float:
        if self.polygon_type == PolygonType.INSCRIBED:
            return self.radius
        else:
            return self.radius / math.cos(math.pi / self.num_sides)
    
    def _get_vertices(self) -> List[Tuple[float, float]]:
        r = self._get_effective_radius()
        vertices = []
        for i in range(self.num_sides):
            angle = self.rotation + 2 * math.pi * i / self.num_sides - math.pi / 2
            x = self.cx + r * math.cos(angle)
            y = self.cy + r * math.sin(angle)
            vertices.append((x, y))
        return vertices
    
    def draw(self, canvas, transform, style_manager) -> List[int]:
        self.clear_canvas_items(canvas)
        
        style = style_manager.get_style(self.style_id)
        if style is None:
            style = style_manager.get_style("solid_main")
        
        color = "#0066CC" if self.selected else style.color
        width = style.get_thickness_px()
        
        vertices = self._get_vertices()
        screen_points = [transform.transform_point(v[0], v[1]) for v in vertices]
        
        from ..styles.line_style import LineType
        from ..utils.line_renderer import apply_zigzag_to_points, apply_wavy_to_points
        
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
            for v in vertices:
                sx, sy = transform.transform_point(v[0], v[1])
                points.extend([sx, sy])
            dash = style.get_tkinter_dash()
            if dash:
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
            scx, scy = transform.transform_point(self.cx, self.cy)
            center_id = canvas.create_oval(scx - 3, scy - 3, scx + 3, scy + 3, fill="#0066CC", outline="#0066CC")
            self._canvas_ids.append(center_id)
        
        return self._canvas_ids
    
    def get_control_points(self) -> List[ControlPoint]:
        vertices = self._get_vertices()
        points = [ControlPoint(x=self.cx, y=self.cy, name="Центр", index=0, snap_types=[SnapType.CENTER])]
        for i, v in enumerate(vertices):
            points.append(ControlPoint(x=v[0], y=v[1], name=f"Вершина {i+1}", index=i+1, snap_types=[SnapType.ENDPOINT]))
        for i in range(self.num_sides):
            mid = midpoint(vertices[i], vertices[(i + 1) % self.num_sides])
            points.append(ControlPoint(x=mid[0], y=mid[1], name=f"Середина стороны {i+1}", index=self.num_sides + 1 + i, snap_types=[SnapType.MIDPOINT]))
        return points
    
    def move_control_point(self, index: int, new_x: float, new_y: float):
        if index == 0:
            self.cx = new_x
            self.cy = new_y
        elif index <= self.num_sides:
            new_radius = distance((self.cx, self.cy), (new_x, new_y))
            if self.polygon_type == PolygonType.CIRCUMSCRIBED:
                new_radius = new_radius * math.cos(math.pi / self.num_sides)
            self.radius = new_radius
            if index == 1:
                self.rotation = math.atan2(new_y - self.cy, new_x - self.cx) + math.pi / 2
    
    def get_snap_points(self) -> List[SnapPoint]:
        vertices = self._get_vertices()
        points = [SnapPoint(x=self.cx, y=self.cy, snap_type=SnapType.CENTER, primitive_id=self.id)]
        for v in vertices:
            points.append(SnapPoint(x=v[0], y=v[1], snap_type=SnapType.ENDPOINT, primitive_id=self.id))
        for i in range(self.num_sides):
            mid = midpoint(vertices[i], vertices[(i + 1) % self.num_sides])
            points.append(SnapPoint(x=mid[0], y=mid[1], snap_type=SnapType.MIDPOINT, primitive_id=self.id))
        return points
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        vertices = self._get_vertices()
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        return (min(xs), min(ys), max(xs), max(ys))
    
    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        vertices = self._get_vertices()
        from ..utils.math_utils import perpendicular_point
        for i in range(self.num_sides):
            v1 = vertices[i]
            v2 = vertices[(i + 1) % self.num_sides]
            perp = perpendicular_point((x, y), v1, v2)
            seg_len = distance(v1, v2)
            d1 = distance(v1, perp)
            d2 = distance(perp, v2)
            if d1 <= seg_len and d2 <= seg_len:
                if distance((x, y), perp) <= tolerance:
                    return True
        return False
    
    def get_properties(self) -> Dict[str, Any]:
        r = self._get_effective_radius()
        side_length = 2 * r * math.sin(math.pi / self.num_sides)
        perimeter = self.num_sides * side_length
        area = 0.5 * self.num_sides * r ** 2 * math.sin(2 * math.pi / self.num_sides)
        return {
            "type": self.get_type_name(),
            "cx": self.cx,
            "cy": self.cy,
            "radius": self.radius,
            "num_sides": self.num_sides,
            "polygon_type": self.polygon_type.value,
            "rotation_deg": math.degrees(self.rotation),
            "perimeter": perimeter,
            "area": area,
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
            elif name == "num_sides":
                self.num_sides = max(3, int(value))
            elif name == "polygon_type":
                if isinstance(value, str):
                    self.polygon_type = PolygonType(value)
                elif isinstance(value, PolygonType):
                    self.polygon_type = value
            elif name == "rotation_deg":
                self.rotation = math.radians(float(value))
            elif name == "style_id":
                self.style_id = str(value)
            else:
                return False
            return True
        except (ValueError, TypeError):
            return False


PrimitiveFactory.register("polygon", Polygon)
