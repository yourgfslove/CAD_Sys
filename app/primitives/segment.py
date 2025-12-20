"""
Line segment primitive
Примитив отрезка
"""

import math
from typing import List, Tuple, Dict, Any
from .base import Primitive, ControlPoint, SnapPoint, SnapType, PrimitiveFactory
from ..utils.math_utils import distance, midpoint, angle_between_points, perpendicular_point


class Segment(Primitive):
    """Line segment primitive"""
    
    def __init__(self, x1: float = 0, y1: float = 0, x2: float = 100, y2: float = 0):
        super().__init__()
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
    
    def get_type_name(self) -> str:
        return "Отрезок"
    
    def draw(self, canvas, transform, style_manager) -> List[int]:
        self.clear_canvas_items(canvas)
        
        sx1, sy1 = transform.transform_point(self.x1, self.y1)
        sx2, sy2 = transform.transform_point(self.x2, self.y2)
        
        style = style_manager.get_style(self.style_id)
        if style is None:
            style = style_manager.get_style("solid_main")
        
        color = "#0066CC" if self.selected else style.color
        width = style.get_thickness_px()
        scale = transform.get_scale()
        
        from ..styles.line_style import LineType
        
        if style.line_type == LineType.SOLID_THIN_ZIGZAG:
            # Convert mm to pixels using scale - GOST style zigzag
            zigzag_params = {
                'amplitude': style.zigzag_amplitude * scale,
                'width': style.zigzag_width * scale,
                'gap': style.zigzag_gap * scale,
                'protrusion': style.zigzag_protrusion * scale,
            }
            self._draw_zigzag_gost(canvas, sx1, sy1, sx2, sy2, color, width, zigzag_params)
        elif style.line_type == LineType.SOLID_WAVY:
            # Convert mm to pixels using scale
            wavy_length_px = style.wavy_length * scale
            wavy_height_px = style.wavy_height * scale
            self._draw_wavy(canvas, sx1, sy1, sx2, sy2, color, width, wavy_length_px, wavy_height_px)
        else:
            dash = style.get_tkinter_dash()
            if dash:
                item_id = canvas.create_line(sx1, sy1, sx2, sy2, fill=color, width=width, dash=dash, capstyle="round")
            else:
                item_id = canvas.create_line(sx1, sy1, sx2, sy2, fill=color, width=width, capstyle="round")
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
    
    def _draw_zigzag_gost(self, canvas, x1, y1, x2, y2, color, width, params):
        """
        Draw GOST-style zigzag line with protrusions and gaps.
        
        Structure: выступ -> промежуток -> [излом вниз -> излом вверх] -> промежуток -> ... -> выступ
        
        params:
            amplitude: высота пика излома (pixels)
            width: ширина одного зигзага (pixels)
            gap: промежуток между изломами (pixels)
            protrusion: длина выступа (pixels)
        """
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1:
            return
        
        # Unit vectors: u = along line, p = perpendicular
        ux = dx / length
        uy = dy / length
        px = -uy
        py = ux
        
        amplitude = max(2, params.get('amplitude', 4))
        zigzag_width = max(3, params.get('width', 6))
        gap = max(1, params.get('gap', 8))
        protrusion = max(0, params.get('protrusion', 2))
        
        # Calculate how many zigzag patterns fit
        pattern_length = zigzag_width + gap  # One zigzag + gap after it
        available_length = length - 2 * protrusion - gap  # Space for patterns (with start gap)
        
        if available_length < zigzag_width:
            # Too short - just draw a straight line
            item_id = canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
            self._canvas_ids.append(item_id)
            return
        
        num_zigzags = max(1, int(available_length / pattern_length))
        
        # Recalculate gap to distribute evenly
        total_zigzag_width = num_zigzags * zigzag_width
        total_gap_space = length - 2 * protrusion - total_zigzag_width
        actual_gap = total_gap_space / (num_zigzags + 1)  # gaps between and around zigzags
        
        points = []
        
        # Start point
        current_x = x1
        current_y = y1
        points.extend([current_x, current_y])
        
        # Start protrusion (perpendicular line going down)
        if protrusion > 0:
            prot_x = current_x + px * protrusion
            prot_y = current_y + py * protrusion
            points.extend([prot_x, prot_y])
            # Back to baseline
            points.extend([current_x, current_y])
        
        # Move along the line
        pos = 0
        
        for i in range(num_zigzags):
            # Gap before zigzag
            pos += actual_gap
            gap_x = x1 + ux * pos
            gap_y = y1 + uy * pos
            points.extend([gap_x, gap_y])
            
            # Zigzag pattern: down -> center -> up (or alternating)
            half_width = zigzag_width / 2
            
            # Direction alternates
            sign = 1 if i % 2 == 0 else -1
            
            # Peak down
            peak_down_pos = pos + half_width * 0.5
            peak_down_x = x1 + ux * peak_down_pos + px * amplitude * sign
            peak_down_y = y1 + uy * peak_down_pos + py * amplitude * sign
            points.extend([peak_down_x, peak_down_y])
            
            # Peak up
            peak_up_pos = pos + half_width * 1.5
            peak_up_x = x1 + ux * peak_up_pos - px * amplitude * sign
            peak_up_y = y1 + uy * peak_up_pos - py * amplitude * sign
            points.extend([peak_up_x, peak_up_y])
            
            # End of zigzag
            pos += zigzag_width
            end_x = x1 + ux * pos
            end_y = y1 + uy * pos
            points.extend([end_x, end_y])
        
        # Final gap to end
        points.extend([x2, y2])
        
        # End protrusion
        if protrusion > 0:
            end_prot_x = x2 + px * protrusion
            end_prot_y = y2 + py * protrusion
            points.extend([end_prot_x, end_prot_y])
            # Back to endpoint
            points.extend([x2, y2])
        
        item_id = canvas.create_line(points, fill=color, width=width, joinstyle="miter")
        self._canvas_ids.append(item_id)
    
    def _draw_wavy(self, canvas, x1, y1, x2, y2, color, width, wave_length=15, wave_height=3):
        """Draw wavy line with configurable parameters"""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1:
            return
        
        ux = dx / length
        uy = dy / length
        px = -uy
        py = ux
        
        # Ensure minimum wave length
        wave_length = max(5, wave_length)
        
        points = []
        num_points = max(10, int(length / 2))
        
        for i in range(num_points + 1):
            t = i / num_points
            base_x = x1 + dx * t
            base_y = y1 + dy * t
            offset = math.sin(t * length / wave_length * 2 * math.pi) * wave_height
            wave_x = base_x + px * offset
            wave_y = base_y + py * offset
            points.extend([wave_x, wave_y])
        
        item_id = canvas.create_line(points, fill=color, width=width, smooth=True)
        self._canvas_ids.append(item_id)
    
    def get_control_points(self) -> List[ControlPoint]:
        mid = midpoint((self.x1, self.y1), (self.x2, self.y2))
        return [
            ControlPoint(x=self.x1, y=self.y1, name="Начало", index=0, snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=self.x2, y=self.y2, name="Конец", index=1, snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=mid[0], y=mid[1], name="Середина", index=2, snap_types=[SnapType.MIDPOINT]),
        ]
    
    def move_control_point(self, index: int, new_x: float, new_y: float):
        if index == 0:
            self.x1 = new_x
            self.y1 = new_y
        elif index == 1:
            self.x2 = new_x
            self.y2 = new_y
        elif index == 2:
            old_mid = midpoint((self.x1, self.y1), (self.x2, self.y2))
            dx = new_x - old_mid[0]
            dy = new_y - old_mid[1]
            self.x1 += dx
            self.y1 += dy
            self.x2 += dx
            self.y2 += dy
    
    def get_snap_points(self) -> List[SnapPoint]:
        mid = midpoint((self.x1, self.y1), (self.x2, self.y2))
        return [
            SnapPoint(x=self.x1, y=self.y1, snap_type=SnapType.ENDPOINT, primitive_id=self.id),
            SnapPoint(x=self.x2, y=self.y2, snap_type=SnapType.ENDPOINT, primitive_id=self.id),
            SnapPoint(x=mid[0], y=mid[1], snap_type=SnapType.MIDPOINT, primitive_id=self.id),
        ]
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        return (min(self.x1, self.x2), min(self.y1, self.y2), max(self.x1, self.x2), max(self.y1, self.y2))
    
    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        perp = perpendicular_point((x, y), (self.x1, self.y1), (self.x2, self.y2))
        seg_len = distance((self.x1, self.y1), (self.x2, self.y2))
        
        if seg_len < 0.001:
            return distance((x, y), (self.x1, self.y1)) <= tolerance
        
        d1 = distance((self.x1, self.y1), perp)
        d2 = distance(perp, (self.x2, self.y2))
        
        if d1 > seg_len + tolerance or d2 > seg_len + tolerance:
            return False
        
        return distance((x, y), perp) <= tolerance
    
    def get_length(self) -> float:
        return distance((self.x1, self.y1), (self.x2, self.y2))
    
    def get_angle(self) -> float:
        return angle_between_points((self.x1, self.y1), (self.x2, self.y2))
    
    def get_properties(self) -> Dict[str, Any]:
        return {
            "type": self.get_type_name(),
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "length": self.get_length(),
            "angle_deg": math.degrees(self.get_angle()),
            "style_id": self.style_id,
        }
    
    def set_property(self, name: str, value: Any) -> bool:
        try:
            if name == "x1":
                self.x1 = float(value)
            elif name == "y1":
                self.y1 = float(value)
            elif name == "x2":
                self.x2 = float(value)
            elif name == "y2":
                self.y2 = float(value)
            elif name == "style_id":
                self.style_id = str(value)
            else:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    def get_perpendicular_point(self, x: float, y: float) -> Tuple[float, float]:
        return perpendicular_point((x, y), (self.x1, self.y1), (self.x2, self.y2))


PrimitiveFactory.register("segment", Segment)
