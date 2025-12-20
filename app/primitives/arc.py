"""
Arc primitive
Примитив дуги
"""

import math
from typing import List, Tuple, Dict, Any
from .base import Primitive, ControlPoint, SnapPoint, SnapType, PrimitiveFactory
from ..utils.math_utils import distance, rotate_point


class Arc(Primitive):
    """Arc primitive"""
    
    def __init__(self, cx: float = 0, cy: float = 0, radius: float = 50, start_angle: float = 0, end_angle: float = math.pi / 2):
        super().__init__()
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle
    
    def get_type_name(self) -> str:
        return "Дуга"
    
    def _get_arc_extent(self) -> float:
        extent = self.end_angle - self.start_angle
        return math.degrees(extent)
    
    def _get_start_degrees(self) -> float:
        return math.degrees(self.start_angle)
    
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
        from ..utils.line_renderer import sample_arc_points, apply_zigzag_to_points, apply_wavy_to_points
        
        if style.line_type == LineType.SOLID_THIN_ZIGZAG:
            arc_points = sample_arc_points(self.cx, self.cy, self.radius, self.start_angle, self.end_angle, 32)
            screen_points = []
            for p in arc_points:
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
            arc_points = sample_arc_points(self.cx, self.cy, self.radius, self.start_angle, self.end_angle, 64)
            screen_points = []
            for p in arc_points:
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
            arc_points = sample_arc_points(self.cx, self.cy, self.radius, self.start_angle, self.end_angle, 64)
            screen_points = []
            for p in arc_points:
                sp = transform.transform_point(p[0], p[1])
                screen_points.append(sp)
            coords = []
            for sp in screen_points:
                coords.extend([sp[0], sp[1]])
            dash = style.get_tkinter_dash()
            if len(coords) >= 4:
                if dash:
                    item_id = canvas.create_line(coords, fill=color, width=width, dash=dash, smooth=False)
                else:
                    item_id = canvas.create_line(coords, fill=color, width=width, smooth=False)
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
    
    def _get_point_on_arc(self, angle: float) -> Tuple[float, float]:
        x = self.cx + self.radius * math.cos(angle)
        y = self.cy + self.radius * math.sin(angle)
        return (x, y)
    
    def get_control_points(self) -> List[ControlPoint]:
        start_pt = self._get_point_on_arc(self.start_angle)
        end_pt = self._get_point_on_arc(self.end_angle)
        mid_angle = (self.start_angle + self.end_angle) / 2
        mid_pt = self._get_point_on_arc(mid_angle)
        return [
            ControlPoint(x=self.cx, y=self.cy, name="Центр", index=0, snap_types=[SnapType.CENTER]),
            ControlPoint(x=start_pt[0], y=start_pt[1], name="Начало дуги", index=1, snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=end_pt[0], y=end_pt[1], name="Конец дуги", index=2, snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=mid_pt[0], y=mid_pt[1], name="Середина дуги", index=3, snap_types=[SnapType.MIDPOINT]),
        ]
    
    def move_control_point(self, index: int, new_x: float, new_y: float):
        if index == 0:
            self.cx = new_x
            self.cy = new_y
        elif index == 1:
            self.radius = distance((self.cx, self.cy), (new_x, new_y))
            self.start_angle = math.atan2(new_y - self.cy, new_x - self.cx)
        elif index == 2:
            self.radius = distance((self.cx, self.cy), (new_x, new_y))
            self.end_angle = math.atan2(new_y - self.cy, new_x - self.cx)
        elif index == 3:
            self.radius = distance((self.cx, self.cy), (new_x, new_y))
    
    def get_snap_points(self) -> List[SnapPoint]:
        start_pt = self._get_point_on_arc(self.start_angle)
        end_pt = self._get_point_on_arc(self.end_angle)
        mid_angle = (self.start_angle + self.end_angle) / 2
        mid_pt = self._get_point_on_arc(mid_angle)
        return [
            SnapPoint(x=self.cx, y=self.cy, snap_type=SnapType.CENTER, primitive_id=self.id),
            SnapPoint(x=start_pt[0], y=start_pt[1], snap_type=SnapType.ENDPOINT, primitive_id=self.id),
            SnapPoint(x=end_pt[0], y=end_pt[1], snap_type=SnapType.ENDPOINT, primitive_id=self.id),
            SnapPoint(x=mid_pt[0], y=mid_pt[1], snap_type=SnapType.MIDPOINT, primitive_id=self.id),
        ]
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        return (self.cx - self.radius, self.cy - self.radius, self.cx + self.radius, self.cy + self.radius)
    
    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        d = distance((self.cx, self.cy), (x, y))
        if abs(d - self.radius) > tolerance:
            return False
        
        angle = math.atan2(y - self.cy, x - self.cx)
        start = self.start_angle
        end = self.end_angle
        
        while start < 0:
            start += 2 * math.pi
        while end < 0:
            end += 2 * math.pi
        while angle < 0:
            angle += 2 * math.pi
        
        if start <= end:
            return start <= angle <= end
        else:
            return angle >= start or angle <= end
    
    def get_arc_length(self) -> float:
        extent = abs(self.end_angle - self.start_angle)
        return self.radius * extent
    
    def get_properties(self) -> Dict[str, Any]:
        return {
            "type": self.get_type_name(),
            "cx": self.cx,
            "cy": self.cy,
            "radius": self.radius,
            "start_angle_deg": math.degrees(self.start_angle),
            "end_angle_deg": math.degrees(self.end_angle),
            "arc_length": self.get_arc_length(),
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
            elif name == "start_angle_deg":
                self.start_angle = math.radians(float(value))
            elif name == "end_angle_deg":
                self.end_angle = math.radians(float(value))
            elif name == "style_id":
                self.style_id = str(value)
            else:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def from_three_points(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> "Arc":
        from .circle import Circle
        circle = Circle.from_three_points(x1, y1, x2, y2, x3, y3)
        start_angle = math.atan2(y1 - circle.cy, x1 - circle.cx)
        end_angle = math.atan2(y3 - circle.cy, x3 - circle.cx)
        return Arc(circle.cx, circle.cy, circle.radius, start_angle, end_angle)
    
    @staticmethod
    def from_two_points_and_bulge(x1: float, y1: float, x2: float, y2: float, bx: float, by: float) -> "Arc":
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        dx = x2 - x1
        dy = y2 - y1
        chord_len = math.sqrt(dx * dx + dy * dy)
        
        if chord_len < 1e-10:
            return Arc(x1, y1, 1, 0, math.pi)
        
        px = -dy / chord_len
        py = dx / chord_len
        vx = bx - mx
        vy = by - my
        sagitta = vx * px + vy * py
        
        if abs(sagitta) < 1e-10:
            sagitta = 0.1 * (1 if vx * px + vy * py >= 0 else -1)
        
        half_chord = chord_len / 2
        abs_sagitta = abs(sagitta)
        radius = half_chord * half_chord / (2 * abs_sagitta) + abs_sagitta / 2
        center_dist = radius - abs_sagitta
        sign = -1 if sagitta > 0 else 1
        cx = mx + px * center_dist * sign
        cy = my + py * center_dist * sign
        
        angle1 = math.atan2(y1 - cy, x1 - cx)
        angle2 = math.atan2(y2 - cy, x2 - cx)
        angle_bulge = math.atan2(by - cy, bx - cx)
        
        def angle_diff(a1, a2):
            diff = a2 - a1
            while diff > math.pi:
                diff -= 2 * math.pi
            while diff < -math.pi:
                diff += 2 * math.pi
            return diff
        
        diff_start_end = angle_diff(angle1, angle2)
        diff_start_bulge = angle_diff(angle1, angle_bulge)
        diff_end_bulge = angle_diff(angle2, angle_bulge)
        
        arc_span = abs(diff_start_end)
        if arc_span > math.pi:
            bulge_in_arc = abs(diff_start_bulge) > arc_span or abs(diff_end_bulge) > arc_span
            if diff_start_end > 0:
                start_angle = angle2
                end_angle = angle1
            else:
                start_angle = angle1
                end_angle = angle2
        else:
            if diff_start_end > 0:
                bulge_in_arc = diff_start_bulge > 0 and diff_start_bulge <= diff_start_end
            else:
                bulge_in_arc = diff_start_bulge < 0 and diff_start_bulge >= diff_start_end
            
            if bulge_in_arc:
                start_angle = angle1
                end_angle = angle2
            else:
                start_angle = angle2
                end_angle = angle1
        
        return Arc(cx, cy, radius, start_angle, end_angle)


PrimitiveFactory.register("arc", Arc)
