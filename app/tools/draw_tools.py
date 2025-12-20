"""
Drawing Tools - инструменты рисования
Все инструменты для создания геометрических примитивов
"""

import math
from typing import List, Tuple, Optional
from .base_tool import BaseTool
from ..primitives.segment import Segment
from ..primitives.circle import Circle
from ..primitives.arc import Arc
from ..primitives.rectangle import Rectangle
from ..primitives.ellipse import Ellipse
from ..primitives.polygon import Polygon, PolygonType
from ..primitives.spline import Spline
from ..utils.math_utils import distance


class SegmentTool(BaseTool):
    """Line segment drawing tool"""
    
    def __init__(self):
        super().__init__()
        self._start_point: Optional[Tuple[float, float]] = None
        self._current_point: Optional[Tuple[float, float]] = None
        self._input_buffer: str = ""
    
    def get_name(self) -> str:
        return "Отрезок"
    
    def get_icon(self) -> str:
        return "╱"
    
    def _reset_state(self):
        self._start_point = None
        self._current_point = None
        self._input_buffer = ""
        if self.canvas:
            self.canvas.clear_base_point()
    
    def on_left_click(self, sx: float, sy: float, wx: float, wy: float):
        if self._start_point is None:
            self._start_point = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        else:
            segment = Segment(self._start_point[0], self._start_point[1], wx, wy)
            segment.style_id = self.canvas.style_manager.get_current_style_id()
            self.canvas.add_primitive(segment)
            self._reset_state()
            self._clear_preview()
    
    def on_mouse_move(self, sx: float, sy: float, wx: float, wy: float):
        self._current_point = (wx, wy)
        if self._start_point and self.canvas:
            self.canvas.redraw()
    
    def on_key_press(self, event):
        if not self._start_point:
            return
        
        key = event.keysym
        char = event.char
        
        if key == "Return" and self._input_buffer:
            try:
                length = float(self._input_buffer)
                if self._current_point and self._start_point:
                    dx = self._current_point[0] - self._start_point[0]
                    dy = self._current_point[1] - self._start_point[1]
                    current_len = math.sqrt(dx * dx + dy * dy)
                    if current_len > 0:
                        scale = length / current_len
                        end_x = self._start_point[0] + dx * scale
                        end_y = self._start_point[1] + dy * scale
                        segment = Segment(self._start_point[0], self._start_point[1], end_x, end_y)
                        segment.style_id = self.canvas.style_manager.get_current_style_id()
                        self.canvas.add_primitive(segment)
                        self._reset_state()
                        self._clear_preview()
            except ValueError:
                pass
            self._input_buffer = ""
        elif key == "BackSpace":
            self._input_buffer = self._input_buffer[:-1]
        elif char and (char.isdigit() or char in ".-"):
            self._input_buffer += char
        elif key == "Escape":
            self._input_buffer = ""
        
        if self.canvas:
            self.canvas.redraw()
    
    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        
        if self._input_buffer and self._start_point:
            text_id = canvas_widget.create_text(
                50, 50,
                text=f"Длина: {self._input_buffer}_",
                fill="#0066CC",
                font=("Arial", 12, "bold"),
                anchor="nw"
            )
            self._preview_ids.append(text_id)
        
        if self._start_point and self._current_point:
            sx1, sy1 = transform.transform_point(self._start_point[0], self._start_point[1])
            sx2, sy2 = transform.transform_point(self._current_point[0], self._current_point[1])
            
            line_id = canvas_widget.create_line(sx1, sy1, sx2, sy2, fill="#0066CC", dash=(6, 3), width=2)
            self._preview_ids.append(line_id)
            
            start_id = canvas_widget.create_oval(sx1 - 4, sy1 - 4, sx1 + 4, sy1 + 4, fill="#0066CC", outline="#FFFFFF", width=2)
            self._preview_ids.append(start_id)
            
            length = distance(self._start_point, self._current_point)
            angle = math.degrees(math.atan2(self._current_point[1] - self._start_point[1], self._current_point[0] - self._start_point[0]))
            mid_x = (sx1 + sx2) / 2
            mid_y = (sy1 + sy2) / 2
            text_id = canvas_widget.create_text(mid_x, mid_y - 15, text=f"L: {length:.1f}  ∠: {angle:.1f}°", fill="#0066CC", font=("Arial", 9, "bold"))
            self._preview_ids.append(text_id)
            bbox = canvas_widget.bbox(text_id)
            if bbox:
                bg_id = canvas_widget.create_rectangle(bbox[0] - 3, bbox[1] - 1, bbox[2] + 3, bbox[3] + 1, fill="#FFFFFF", outline="")
                canvas_widget.tag_lower(bg_id, text_id)
                self._preview_ids.append(bg_id)


class CircleTool(BaseTool):
    MODE_CENTER_RADIUS = 0
    MODE_CENTER_DIAMETER = 1
    MODE_TWO_POINTS = 2
    MODE_THREE_POINTS = 3
    
    def __init__(self):
        super().__init__()
        self._center: Optional[Tuple[float, float]] = None
        self._current_point: Optional[Tuple[float, float]] = None
        self._input_buffer: str = ""
        self._mode = self.MODE_CENTER_RADIUS
        self._point1: Optional[Tuple[float, float]] = None
        self._point2: Optional[Tuple[float, float]] = None
        self._diameter_point1: Optional[Tuple[float, float]] = None
    
    def get_name(self) -> str:
        mode_names = {
            self.MODE_CENTER_RADIUS: "Окружность (Центр+Радиус)",
            self.MODE_CENTER_DIAMETER: "Окружность (Центр+Диаметр)",
            self.MODE_TWO_POINTS: "Окружность (Две точки)",
            self.MODE_THREE_POINTS: "Окружность (3 точки)"
        }
        return mode_names.get(self._mode, "Окружность")
    
    def get_icon(self) -> str:
        return "○"
    
    def _reset_state(self):
        self._center = None
        self._current_point = None
        self._input_buffer = ""
        self._point1 = None
        self._point2 = None
        self._diameter_point1 = None
    
    def _switch_mode(self):
        self._mode = (self._mode + 1) % 4
        self._reset_state()
        if self.canvas:
            self.canvas.redraw()
    
    def on_left_click(self, sx: float, sy: float, wx: float, wy: float):
        if self._mode == self.MODE_CENTER_RADIUS:
            self._on_center_radius_click(wx, wy)
        elif self._mode == self.MODE_CENTER_DIAMETER:
            self._on_center_diameter_click(wx, wy)
        elif self._mode == self.MODE_TWO_POINTS:
            self._on_two_points_click(wx, wy)
        elif self._mode == self.MODE_THREE_POINTS:
            self._on_three_points_click(wx, wy)
    
    def _on_center_radius_click(self, wx: float, wy: float):
        if self._center is None:
            self._center = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        else:
            radius = distance(self._center, (wx, wy))
            if radius > 0:
                circle = Circle(self._center[0], self._center[1], radius)
                circle.style_id = self.canvas.style_manager.get_current_style_id()
                self.canvas.add_primitive(circle)
                self._reset_state()
                self._clear_preview()
    
    def _on_three_points_click(self, wx: float, wy: float):
        if self._point1 is None:
            self._point1 = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        elif self._point2 is None:
            self._point2 = (wx, wy)
        else:
            try:
                circle = Circle.from_three_points(self._point1[0], self._point1[1], self._point2[0], self._point2[1], wx, wy)
                circle.style_id = self.canvas.style_manager.get_current_style_id()
                self.canvas.add_primitive(circle)
            except:
                circle = Circle(wx, wy, 50)
                circle.style_id = self.canvas.style_manager.get_current_style_id()
                self.canvas.add_primitive(circle)
            self._reset_state()
            self._clear_preview()
    
    def _on_center_diameter_click(self, wx: float, wy: float):
        if self._center is None:
            self._center = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        else:
            diameter = 2 * distance(self._center, (wx, wy))
            if diameter > 0:
                circle = Circle(self._center[0], self._center[1], diameter / 2)
                circle.style_id = self.canvas.style_manager.get_current_style_id()
                self.canvas.add_primitive(circle)
                self._reset_state()
                self._clear_preview()
    
    def _on_two_points_click(self, wx: float, wy: float):
        if self._diameter_point1 is None:
            self._diameter_point1 = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        else:
            cx = (self._diameter_point1[0] + wx) / 2
            cy = (self._diameter_point1[1] + wy) / 2
            radius = distance((cx, cy), (wx, wy))
            if radius > 0:
                circle = Circle(cx, cy, radius)
                circle.style_id = self.canvas.style_manager.get_current_style_id()
                self.canvas.add_primitive(circle)
                self._reset_state()
                self._clear_preview()
    
    def on_mouse_move(self, sx: float, sy: float, wx: float, wy: float):
        self._current_point = (wx, wy)
        should_redraw = self._center is not None or self._point1 is not None or self._diameter_point1 is not None
        if should_redraw and self.canvas:
            self.canvas.redraw()
    
    def on_key_press(self, event):
        key = event.keysym
        char = event.char
        
        if key == "Tab":
            self._switch_mode()
            return "break"
        
        if self._mode == self.MODE_CENTER_RADIUS or self._mode == self.MODE_CENTER_DIAMETER:
            if not self._center:
                return
            if key == "Return" and self._input_buffer:
                try:
                    value = float(self._input_buffer)
                    if value > 0:
                        if self._mode == self.MODE_CENTER_RADIUS:
                            circle = Circle(self._center[0], self._center[1], value)
                        else:
                            circle = Circle(self._center[0], self._center[1], value / 2)
                        circle.style_id = self.canvas.style_manager.get_current_style_id()
                        self.canvas.add_primitive(circle)
                        self._reset_state()
                        self._clear_preview()
                except ValueError:
                    pass
                self._input_buffer = ""
            elif key == "BackSpace":
                self._input_buffer = self._input_buffer[:-1]
            elif char and (char.isdigit() or char in ".-"):
                self._input_buffer += char
            elif key == "Escape":
                self._input_buffer = ""
                self._reset_state()
                self._clear_preview()
        
        if self.canvas:
            self.canvas.redraw()
    
    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        
        mode_names = {
            self.MODE_CENTER_RADIUS: "Режим: Центр+Радиус (Tab - сменить)",
            self.MODE_CENTER_DIAMETER: "Режим: Центр+Диаметр (Tab - сменить)",
            self.MODE_TWO_POINTS: "Режим: Две точки (Tab - сменить)",
            self.MODE_THREE_POINTS: "Режим: 3 точки (Tab - сменить)"
        }
        mode_text_id = canvas_widget.create_text(50, 30, text=mode_names.get(self._mode, ""), fill="#0066CC", font=("Arial", 10), anchor="nw")
        self._preview_ids.append(mode_text_id)
        
        if self._mode == self.MODE_CENTER_RADIUS:
            self._draw_center_radius_preview(canvas_widget, transform)
        elif self._mode == self.MODE_CENTER_DIAMETER:
            self._draw_center_diameter_preview(canvas_widget, transform)
        elif self._mode == self.MODE_TWO_POINTS:
            self._draw_two_points_preview(canvas_widget, transform)
        elif self._mode == self.MODE_THREE_POINTS:
            self._draw_three_points_preview(canvas_widget, transform)
    
    def _draw_center_radius_preview(self, canvas_widget, transform):
        if self._input_buffer and self._center:
            text_id = canvas_widget.create_text(50, 50, text=f"Радиус: {self._input_buffer}_", fill="#0066CC", font=("Arial", 12, "bold"), anchor="nw")
            self._preview_ids.append(text_id)
        
        if self._center:
            scx, scy = transform.transform_point(self._center[0], self._center[1])
            center_id = canvas_widget.create_oval(scx - 4, scy - 4, scx + 4, scy + 4, fill="#0066CC", outline="#FFFFFF", width=2)
            self._preview_ids.append(center_id)
            
            if self._current_point:
                radius = distance(self._center, self._current_point)
                sr = radius * transform.get_scale()
                circle_id = canvas_widget.create_oval(scx - sr, scy - sr, scx + sr, scy + sr, outline="#0066CC", dash=(6, 3), width=2)
                self._preview_ids.append(circle_id)
                
                sx2, sy2 = transform.transform_point(self._current_point[0], self._current_point[1])
                line_id = canvas_widget.create_line(scx, scy, sx2, sy2, fill="#0066CC", dash=(3, 3), width=1)
                self._preview_ids.append(line_id)
                
                mid_x = (scx + sx2) / 2
                mid_y = (scy + sy2) / 2
                text_id = canvas_widget.create_text(mid_x, mid_y - 12, text=f"R: {radius:.1f}", fill="#0066CC", font=("Arial", 9, "bold"))
                self._preview_ids.append(text_id)
    
    def _draw_three_points_preview(self, canvas_widget, transform):
        if self._point1:
            sp1x, sp1y = transform.transform_point(self._point1[0], self._point1[1])
            p1_id = canvas_widget.create_oval(sp1x - 4, sp1y - 4, sp1x + 4, sp1y + 4, fill="#0066CC", outline="#FFFFFF", width=2)
            self._preview_ids.append(p1_id)
            text_id = canvas_widget.create_text(sp1x + 10, sp1y - 10, text="Точка 1", fill="#0066CC", font=("Arial", 9, "bold"))
            self._preview_ids.append(text_id)
        
        if self._point2:
            sp2x, sp2y = transform.transform_point(self._point2[0], self._point2[1])
            p2_id = canvas_widget.create_oval(sp2x - 4, sp2y - 4, sp2x + 4, sp2y + 4, fill="#0066CC", outline="#FFFFFF", width=2)
            self._preview_ids.append(p2_id)
            text_id = canvas_widget.create_text(sp2x + 10, sp2y - 10, text="Точка 2", fill="#0066CC", font=("Arial", 9, "bold"))
            self._preview_ids.append(text_id)
            line_id = canvas_widget.create_line(sp1x, sp1y, sp2x, sp2y, fill="#0066CC", dash=(3, 3), width=1)
            self._preview_ids.append(line_id)
        
        if self._point1 and self._point2 and self._current_point:
            try:
                preview_circle = Circle.from_three_points(self._point1[0], self._point1[1], self._point2[0], self._point2[1], self._current_point[0], self._current_point[1])
                scx, scy = transform.transform_point(preview_circle.cx, preview_circle.cy)
                sr = preview_circle.radius * transform.get_scale()
                circle_id = canvas_widget.create_oval(scx - sr, scy - sr, scx + sr, scy + sr, outline="#0066CC", dash=(6, 3), width=2)
                self._preview_ids.append(circle_id)
            except:
                pass
        
        if self._current_point:
            scx, scy = transform.transform_point(self._current_point[0], self._current_point[1])
            if not self._point1 or (self._point1 and (not self._point2)):
                point_id = canvas_widget.create_oval(scx - 4, scy - 4, scx + 4, scy + 4, fill="#FF6600", outline="#FFFFFF", width=2)
                self._preview_ids.append(point_id)
    
    def _draw_center_diameter_preview(self, canvas_widget, transform):
        if self._input_buffer and self._center:
            text_id = canvas_widget.create_text(50, 50, text=f"Диаметр: {self._input_buffer}_", fill="#0066CC", font=("Arial", 12, "bold"), anchor="nw")
            self._preview_ids.append(text_id)
        
        if self._center:
            scx, scy = transform.transform_point(self._center[0], self._center[1])
            center_id = canvas_widget.create_oval(scx - 4, scy - 4, scx + 4, scy + 4, fill="#0066CC", outline="#FFFFFF", width=2)
            self._preview_ids.append(center_id)
            
            if self._current_point:
                diameter = 2 * distance(self._center, self._current_point)
                radius = diameter / 2
                sr = radius * transform.get_scale()
                circle_id = canvas_widget.create_oval(scx - sr, scy - sr, scx + sr, scy + sr, outline="#0066CC", dash=(6, 3), width=2)
                self._preview_ids.append(circle_id)
                
                sx2, sy2 = transform.transform_point(self._current_point[0], self._current_point[1])
                line_id = canvas_widget.create_line(scx, scy, sx2, sy2, fill="#0066CC", dash=(3, 3), width=1)
                self._preview_ids.append(line_id)
                
                mid_x = (scx + sx2) / 2
                mid_y = (scy + sy2) / 2
                text_id = canvas_widget.create_text(mid_x, mid_y - 12, text=f"D: {diameter:.1f}", fill="#0066CC", font=("Arial", 9, "bold"))
                self._preview_ids.append(text_id)
    
    def _draw_two_points_preview(self, canvas_widget, transform):
        if self._diameter_point1:
            sp1x, sp1y = transform.transform_point(self._diameter_point1[0], self._diameter_point1[1])
            p1_id = canvas_widget.create_oval(sp1x - 4, sp1y - 4, sp1x + 4, sp1y + 4, fill="#0066CC", outline="#FFFFFF", width=2)
            self._preview_ids.append(p1_id)
        
        if self._current_point:
            sp2x, sp2y = transform.transform_point(self._current_point[0], self._current_point[1])
            line_id = canvas_widget.create_line(sp1x, sp1y, sp2x, sp2y, fill="#0066CC", dash=(6, 3), width=2)
            self._preview_ids.append(line_id)
            
            cx = (self._diameter_point1[0] + self._current_point[0]) / 2
            cy = (self._diameter_point1[1] + self._current_point[1]) / 2
            radius = distance((cx, cy), self._current_point)
            scx, scy = transform.transform_point(cx, cy)
            sr = radius * transform.get_scale()
            center_id = canvas_widget.create_oval(scx - 3, scy - 3, scx + 3, scy + 3, fill="#FF6600", outline="#FFFFFF", width=1)
            self._preview_ids.append(center_id)
            circle_id = canvas_widget.create_oval(scx - sr, scy - sr, scx + sr, scy + sr, outline="#0066CC", dash=(6, 3), width=2)
            self._preview_ids.append(circle_id)
            
            mid_x = (sp1x + sp2x) / 2
            mid_y = (sp1y + sp2y) / 2
            text_id = canvas_widget.create_text(mid_x, mid_y - 12, text=f"D: {radius * 2:.1f}", fill="#0066CC", font=("Arial", 9, "bold"))
            self._preview_ids.append(text_id)


class ArcTool(BaseTool):
    MODE_THREE_POINTS = 0
    MODE_CENTER_ANGLES = 1
    
    def __init__(self):
        super().__init__()
        self._mode = self.MODE_THREE_POINTS
        self._points: List[Tuple[float, float]] = []
        self._current_point: Optional[Tuple[float, float]] = None
        self._center: Optional[Tuple[float, float]] = None
        self._start_angle_point: Optional[Tuple[float, float]] = None
        self._input_buffer: str = ""
        self._input_type: str = ""
        self._radius: float = 0.0
    
    def get_name(self) -> str:
        mode_names = {
            self.MODE_THREE_POINTS: "Дуга (3 точки)",
            self.MODE_CENTER_ANGLES: "Дуга (Центр+Углы)"
        }
        return mode_names.get(self._mode, "Дуга")
    
    def get_icon(self) -> str:
        return "⌒"
    
    def _reset_state(self):
        self._points = []
        self._current_point = None
        self._center = None
        self._start_angle_point = None
        self._input_buffer = ""
        self._input_type = ""
        self._radius = 0.0
    
    def _switch_mode(self):
        self._mode = (self._mode + 1) % 2
        self._reset_state()
        if self.canvas:
            self.canvas.redraw()
    
    def on_key_press(self, event):
        key = event.keysym
        if key == "Tab":
            self._switch_mode()
            return "break"
        if self.canvas:
            self.canvas.redraw()
    
    def on_left_click(self, sx: float, sy: float, wx: float, wy: float):
        if self._mode == self.MODE_THREE_POINTS:
            self._on_three_points_click(wx, wy)
        elif self._mode == self.MODE_CENTER_ANGLES:
            self._on_center_angles_click(wx, wy)
    
    def _on_three_points_click(self, wx: float, wy: float):
        self._points.append((wx, wy))
        if len(self._points) == 1 and self.canvas:
            self.canvas.set_base_point(wx, wy)
        if len(self._points) == 3:
            p1, p2, p3 = self._points
            arc = Arc.from_two_points_and_bulge(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
            arc.style_id = self.canvas.style_manager.get_current_style_id()
            self.canvas.add_primitive(arc)
            self._reset_state()
            self._clear_preview()
        elif self.canvas:
            self.canvas.redraw()
    
    def _on_center_angles_click(self, wx: float, wy: float):
        import math
        
        if self._center is None:
            self._center = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        elif self._input_type == "":
            radius = distance(self._center, (wx, wy))
            if radius > 0:
                self._radius = radius
                self._input_type = "start_angle"
        elif self._input_type == "start_angle":
            self._start_angle_point = (wx, wy)
            self._input_type = "end_angle"
        elif self._input_type == "end_angle":
            start_angle = math.atan2(self._start_angle_point[1] - self._center[1], self._start_angle_point[0] - self._center[0])
            end_angle = math.atan2(wy - self._center[1], wx - self._center[0])
            arc = Arc(self._center[0], self._center[1], self._radius, start_angle, end_angle)
            arc.style_id = self.canvas.style_manager.get_current_style_id()
            self.canvas.add_primitive(arc)
            self._reset_state()
            self._clear_preview()
            return
        
        if self.canvas:
            self.canvas.redraw()
    
    def on_mouse_move(self, sx: float, sy: float, wx: float, wy: float):
        self._current_point = (wx, wy)
        if self.canvas:
            self.canvas.redraw()
    
    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        mode_text = {
            self.MODE_THREE_POINTS: "Режим: 3 точки (Tab - сменить)",
            self.MODE_CENTER_ANGLES: "Режим: Центр+Углы (Tab - сменить)"
        }
        mode_text_id = canvas_widget.create_text(50, 30, text=mode_text.get(self._mode, ""), fill="#0066CC", font=("Arial", 10), anchor="nw")
        self._preview_ids.append(mode_text_id)
        
        if self._mode == self.MODE_THREE_POINTS:
            self._draw_three_points_preview(canvas_widget, transform)
        elif self._mode == self.MODE_CENTER_ANGLES:
            self._draw_center_angles_preview(canvas_widget, transform)
    
    def _draw_three_points_preview(self, canvas_widget, transform):
        if len(self._points) == 0:
            text = "1/3: Укажите начало дуги"
        elif len(self._points) == 1:
            text = "2/3: Укажите конец дуги"
        else:
            text = "3/3: Укажите третью точку дуги"
        
        text_id = canvas_widget.create_text(50, 50, text=text, fill="#0066CC", font=("Arial", 10), anchor="nw")
        self._preview_ids.append(text_id)
        
        if not self._points:
            return
        
        labels = ["Начало", "Конец", "Точка"]
        for i, p in enumerate(self._points):
            spx, spy = transform.transform_point(p[0], p[1])
            pt_id = canvas_widget.create_oval(spx - 4, spy - 4, spx + 4, spy + 4, fill="#0066CC", outline="#FFFFFF", width=2)
            self._preview_ids.append(pt_id)
            label_id = canvas_widget.create_text(spx + 10, spy - 10, text=labels[i], fill="#0066CC", font=("Arial", 8))
            self._preview_ids.append(label_id)
        
        if len(self._points) >= 1 and self._current_point:
            if len(self._points) == 1:
                sx1, sy1 = transform.transform_point(self._points[0][0], self._points[0][1])
                sx2, sy2 = transform.transform_point(self._current_point[0], self._current_point[1])
                line_id = canvas_widget.create_line(sx1, sy1, sx2, sy2, fill="#0066CC", dash=(4, 4), width=1)
                self._preview_ids.append(line_id)
            elif len(self._points) == 2:
                sx1, sy1 = transform.transform_point(self._points[0][0], self._points[0][1])
                sx2, sy2 = transform.transform_point(self._points[1][0], self._points[1][1])
                line_id = canvas_widget.create_line(sx1, sy1, sx2, sy2, fill="#AAAAAA", dash=(4, 4), width=1)
                self._preview_ids.append(line_id)
                if self._current_point:
                    self._draw_arc_preview(canvas_widget, transform)
    
    def _draw_arc_preview(self, canvas_widget, transform):
        if len(self._points) < 2 or not self._current_point:
            return
        
        p1 = self._points[0]
        p2 = self._points[1]
        p3 = self._current_point
        
        try:
            temp_arc = Arc.from_two_points_and_bulge(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
            from ..utils.line_renderer import sample_arc_points
            arc_points = sample_arc_points(temp_arc.cx, temp_arc.cy, temp_arc.radius, temp_arc.start_angle, temp_arc.end_angle, 32)
            points = []
            for px, py in arc_points:
                sx, sy = transform.transform_point(px, py)
                points.extend([sx, sy])
            if len(points) >= 4:
                arc_id = canvas_widget.create_line(points, fill="#0066CC", dash=(6, 3), width=2, smooth=True)
                self._preview_ids.append(arc_id)
                scx, scy = transform.transform_point(temp_arc.cx, temp_arc.cy)
                center_id = canvas_widget.create_oval(scx - 3, scy - 3, scx + 3, scy + 3, fill="#0066CC", outline="#FFFFFF")
                self._preview_ids.append(center_id)
                text_id = canvas_widget.create_text(scx + 15, scy, text=f"R: {temp_arc.radius:.1f}", fill="#0066CC", font=("Arial", 9, "bold"), anchor="w")
                self._preview_ids.append(text_id)
        except Exception:
            pass
    
    def _draw_center_angles_preview(self, canvas_widget, transform):
        import math
        from ..utils.line_renderer import sample_arc_points
        
        if self._center:
            scx, scy = transform.transform_point(self._center[0], self._center[1])
            center_id = canvas_widget.create_oval(scx - 4, scy - 4, scx + 4, scy + 4, fill="#0066CC", outline="#FFFFFF", width=2)
            self._preview_ids.append(center_id)
            
            if self._input_type == "":
                text = "1/4: Центр установлен. Укажите радиус"
            elif self._input_type == "start_angle":
                text = "2/4: Радиус установлен. Укажите начальный угол"
            elif self._input_type == "end_angle":
                text = "3/4: Начальный угол установлен. Укажите конечный угол"
            else:
                text = ""
            
            text_id = canvas_widget.create_text(50, 50, text=text, fill="#0066CC", font=("Arial", 10), anchor="nw")
            self._preview_ids.append(text_id)
            
            if self._radius > 0:
                sr = self._radius * transform.get_scale()
                circle_id = canvas_widget.create_oval(scx - sr, scy - sr, scx + sr, scy + sr, outline="#AAAAAA", dash=(2, 2), width=1)
                self._preview_ids.append(circle_id)
            
            if self._start_angle_point:
                ssx, ssy = transform.transform_point(self._start_angle_point[0], self._start_angle_point[1])
                line1_id = canvas_widget.create_line(scx, scy, ssx, ssy, fill="#00AA00", width=2)
                self._preview_ids.append(line1_id)
                pt1_id = canvas_widget.create_oval(ssx - 4, ssy - 4, ssx + 4, ssy + 4, fill="#00AA00", outline="#FFFFFF", width=2)
                self._preview_ids.append(pt1_id)
                
                if self._current_point:
                    sex, sey = transform.transform_point(self._current_point[0], self._current_point[1])
                    line2_id = canvas_widget.create_line(scx, scy, sex, sey, fill="#FF6600", width=2)
                    self._preview_ids.append(line2_id)
                    start_angle = math.atan2(self._start_angle_point[1] - self._center[1], self._start_angle_point[0] - self._center[0])
                    end_angle = math.atan2(self._current_point[1] - self._center[1], self._current_point[0] - self._center[0])
                    arc_points = sample_arc_points(self._center[0], self._center[1], self._radius, start_angle, end_angle, 32)
                    points = []
                    for px, py in arc_points:
                        sx, sy = transform.transform_point(px, py)
                        points.extend([sx, sy])
                    if len(points) >= 4:
                        arc_id = canvas_widget.create_line(points, fill="#0066CC", dash=(6, 3), width=2, smooth=True)
                        self._preview_ids.append(arc_id)
            elif self._current_point:
                scx2, scy2 = transform.transform_point(self._current_point[0], self._current_point[1])
                radius = math.sqrt((self._current_point[0] - self._center[0]) ** 2 + (self._current_point[1] - self._center[1]) ** 2)
                sr = radius * transform.get_scale()
                circle_preview_id = canvas_widget.create_oval(scx - sr, scy - sr, scx + sr, scy + sr, outline="#0066CC", dash=(6, 3), width=2)
                self._preview_ids.append(circle_preview_id)
                line_id = canvas_widget.create_line(scx, scy, scx2, scy2, fill="#0066CC", dash=(3, 3), width=1)
                self._preview_ids.append(line_id)
                text_id = canvas_widget.create_text((scx + scx2) / 2, (scy + scy2) / 2 - 12, text=f"R: {radius:.1f}", fill="#0066CC", font=("Arial", 9, "bold"))
                self._preview_ids.append(text_id)


class RectangleTool(BaseTool):
    MODE_TWO_POINTS = 0
    MODE_POINT_SIZE = 1
    MODE_CENTER_SIZE = 2
    
    def __init__(self):
        super().__init__()
        self._mode = self.MODE_TWO_POINTS
        self._start_point: Optional[Tuple[float, float]] = None
        self._center_point: Optional[Tuple[float, float]] = None
        self._current_point: Optional[Tuple[float, float]] = None
        self._input_buffer: str = ""
        self._corner_radius: float = 0.0
    
    def get_name(self) -> str:
        mode_names = {
            self.MODE_TWO_POINTS: "Прямоугольник (2 точки)",
            self.MODE_POINT_SIZE: "Прямоугольник (Точка+Размер)",
            self.MODE_CENTER_SIZE: "Прямоугольник (Центр+Размер)"
        }
        return mode_names.get(self._mode, "Прямоугольник")
    
    def get_icon(self) -> str:
        return "▭"
    
    def _reset_state(self):
        self._start_point = None
        self._center_point = None
        self._current_point = None
        self._input_buffer = ""
        self._corner_radius = 0.0
    
    def _switch_mode(self):
        self._mode = (self._mode + 1) % 3
        self._reset_state()
        if self.canvas:
            self.canvas.redraw()
    
    def on_left_click(self, sx: float, sy: float, wx: float, wy: float):
        if self._mode == self.MODE_TWO_POINTS:
            self._on_two_points_click(wx, wy)
        elif self._mode == self.MODE_POINT_SIZE:
            self._on_point_size_click(wx, wy)
        elif self._mode == self.MODE_CENTER_SIZE:
            self._on_center_size_click(wx, wy)
    
    def _on_two_points_click(self, wx: float, wy: float):
        if self._start_point is None:
            self._start_point = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        else:
            rect = Rectangle.from_two_points(self._start_point[0], self._start_point[1], wx, wy)
            rect.corner_radius = self._corner_radius
            rect.style_id = self.canvas.style_manager.get_current_style_id()
            self.canvas.add_primitive(rect)
            self._reset_state()
            self._clear_preview()
    
    def _on_point_size_click(self, wx: float, wy: float):
        if self._start_point is None:
            self._start_point = (wx, wy)
        if self.canvas:
            self.canvas.redraw()
    
    def _on_center_size_click(self, wx: float, wy: float):
        if self._center_point is None:
            self._center_point = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        if self.canvas:
            self.canvas.redraw()
    
    def on_mouse_move(self, sx: float, sy: float, wx: float, wy: float):
        self._current_point = (wx, wy)
        if self._start_point and self.canvas:
            self.canvas.redraw()
    
    def on_key_press(self, event):
        key = event.keysym
        char = event.char
        
        if key == "Tab":
            self._switch_mode()
            return "break"
        
        if (self._mode == self.MODE_POINT_SIZE and (not self._start_point)) or (self._mode == self.MODE_CENTER_SIZE and (not self._center_point)):
            return
        
        if key == "Return" and self._input_buffer:
            try:
                if "," in self._input_buffer:
                    parts = self._input_buffer.split(",")
                elif "x" in self._input_buffer.lower():
                    parts = self._input_buffer.lower().split("x")
                else:
                    parts = [self._input_buffer, self._input_buffer]
                
                w = abs(float(parts[0]))
                h = abs(float(parts[1])) if len(parts) > 1 else w
                
                if self._mode == self.MODE_POINT_SIZE and self._start_point:
                    rect = Rectangle(self._start_point[0], self._start_point[1], w, h)
                elif self._mode == self.MODE_CENTER_SIZE and self._center_point:
                    rect = Rectangle.from_center(self._center_point[0], self._center_point[1], w, h)
                else:
                    return
                
                rect.corner_radius = self._corner_radius
                rect.style_id = self.canvas.style_manager.get_current_style_id()
                self.canvas.add_primitive(rect)
                self._reset_state()
                self._clear_preview()
            except (ValueError, IndexError):
                pass
            self._input_buffer = ""
        elif key == "BackSpace":
            self._input_buffer = self._input_buffer[:-1]
        elif char and (char.isdigit() or char in ".-, xX"):
            self._input_buffer += char
        elif key == "Escape":
            self._input_buffer = ""
            self._reset_state()
            self._clear_preview()
        
        if self.canvas:
            self.canvas.redraw()
    
    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        
        mode_names = {
            self.MODE_TWO_POINTS: "Режим: 2 точки (Tab - сменить)",
            self.MODE_POINT_SIZE: "Режим: Точка+Размер (Tab - сменить)",
            self.MODE_CENTER_SIZE: "Режим: Центр+Размер (Tab - сменить)"
        }
        mode_text_id = canvas_widget.create_text(50, 30, text=mode_names.get(self._mode, ""), fill="#0066CC", font=("Arial", 10), anchor="nw")
        self._preview_ids.append(mode_text_id)
        
        if self._mode == self.MODE_TWO_POINTS:
            self._draw_two_points_preview(canvas_widget, transform)
        elif self._mode == self.MODE_POINT_SIZE:
            self._draw_point_size_preview(canvas_widget, transform)
        elif self._mode == self.MODE_CENTER_SIZE:
            self._draw_center_size_preview(canvas_widget, transform)
    
    def _draw_two_points_preview(self, canvas_widget, transform):
        if self._start_point and self._current_point:
            sx1, sy1 = transform.transform_point(self._start_point[0], self._start_point[1])
            sx2, sy2 = transform.transform_point(self._current_point[0], self._current_point[1])
            rect_id = canvas_widget.create_rectangle(sx1, sy1, sx2, sy2, outline="#0066CC", dash=(6, 3), width=2)
            self._preview_ids.append(rect_id)
    
    def _draw_point_size_preview(self, canvas_widget, transform):
        if self._input_buffer and self._start_point:
            text_id = canvas_widget.create_text(50, 50, text=f"Размер (Ш, В): {self._input_buffer}_", fill="#0066CC", font=("Arial", 12, "bold"), anchor="nw")
            self._preview_ids.append(text_id)
        
        if self._start_point:
            try:
                if "," in self._input_buffer:
                    parts = self._input_buffer.split(",")
                elif "x" in self._input_buffer.lower():
                    parts = self._input_buffer.lower().split("x")
                else:
                    parts = []
                
                if len(parts) >= 2:
                    w = abs(float(parts[0]))
                    h = abs(float(parts[1]))
                elif len(parts) == 1 and parts[0]:
                    w = h = abs(float(parts[0]))
                else:
                    sx, sy = transform.transform_point(self._start_point[0], self._start_point[1])
                    pt_id = canvas_widget.create_oval(sx - 4, sy - 4, sx + 4, sy + 4, fill="#0066CC", outline="#FFFFFF", width=2)
                    self._preview_ids.append(pt_id)
                    return
                
                sx1, sy1 = transform.transform_point(self._start_point[0], self._start_point[1])
                sx2 = sx1 + w * transform.get_scale()
                sy2 = sy1 + h * transform.get_scale()
                rect_id = canvas_widget.create_rectangle(sx1, sy1, sx2, sy2, outline="#0066CC", dash=(6, 3), width=2)
                self._preview_ids.append(rect_id)
            except (ValueError, IndexError):
                sx, sy = transform.transform_point(self._start_point[0], self._start_point[1])
                pt_id = canvas_widget.create_oval(sx - 4, sy - 4, sx + 4, sy + 4, fill="#0066CC", outline="#FFFFFF", width=2)
                self._preview_ids.append(pt_id)
    
    def _draw_center_size_preview(self, canvas_widget, transform):
        if self._input_buffer and self._center_point:
            text_id = canvas_widget.create_text(50, 50, text=f"Размер (Ш, В): {self._input_buffer}_", fill="#0066CC", font=("Arial", 12, "bold"), anchor="nw")
            self._preview_ids.append(text_id)
        
        if self._center_point:
            try:
                if "," in self._input_buffer:
                    parts = self._input_buffer.split(",")
                elif "x" in self._input_buffer.lower():
                    parts = self._input_buffer.lower().split("x")
                else:
                    parts = []
                
                if len(parts) >= 2:
                    w = abs(float(parts[0]))
                    h = abs(float(parts[1]))
                elif len(parts) == 1 and parts[0]:
                    w = h = abs(float(parts[0]))
                else:
                    scx, scy = transform.transform_point(self._center_point[0], self._center_point[1])
                    center_id = canvas_widget.create_oval(scx - 4, scy - 4, scx + 4, scy + 4, fill="#0066CC", outline="#FFFFFF", width=2)
                    self._preview_ids.append(center_id)
                    return
                
                rect = Rectangle.from_center(self._center_point[0], self._center_point[1], w, h)
                corners = rect._get_rotated_corners()
                screen_corners = [transform.transform_point(c[0], c[1]) for c in corners]
                coords = []
                for c in screen_corners:
                    coords.extend(c)
                coords.extend(screen_corners[0])
                rect_id = canvas_widget.create_line(coords, fill="#0066CC", dash=(6, 3), width=2)
                self._preview_ids.append(rect_id)
                scx, scy = transform.transform_point(self._center_point[0], self._center_point[1])
                center_id = canvas_widget.create_oval(scx - 3, scy - 3, scx + 3, scy + 3, fill="#FF6600", outline="#FFFFFF", width=1)
                self._preview_ids.append(center_id)
            except (ValueError, IndexError):
                scx, scy = transform.transform_point(self._center_point[0], self._center_point[1])
                center_id = canvas_widget.create_oval(scx - 4, scy - 4, scx + 4, scy + 4, fill="#0066CC", outline="#FFFFFF", width=2)
                self._preview_ids.append(center_id)


class EllipseTool(BaseTool):
    def __init__(self):
        super().__init__()
        self._center: Optional[Tuple[float, float]] = None
        self._axis1: Optional[Tuple[float, float]] = None
        self._current_point: Optional[Tuple[float, float]] = None
    
    def get_name(self) -> str:
        return "Эллипс"
    
    def get_icon(self) -> str:
        return "⬭"
    
    def _reset_state(self):
        self._center = None
        self._axis1 = None
        self._current_point = None
    
    def on_left_click(self, sx: float, sy: float, wx: float, wy: float):
        if self._center is None:
            self._center = (wx, wy)
        elif self._axis1 is None:
            self._axis1 = (wx, wy)
        else:
            ellipse = Ellipse.from_center_and_axes(self._center[0], self._center[1], self._axis1[0], self._axis1[1], wx, wy)
            ellipse.style_id = self.canvas.style_manager.get_current_style_id()
            self.canvas.add_primitive(ellipse)
            self._reset_state()
            self._clear_preview()
        if self.canvas:
            self.canvas.redraw()
    
    def on_mouse_move(self, sx: float, sy: float, wx: float, wy: float):
        self._current_point = (wx, wy)
        if self._center and self.canvas:
            self.canvas.redraw()
    
    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        
        if self._center is None:
            text = "Укажите центр"
        elif self._axis1 is None:
            text = "Первая полуось"
        else:
            text = "Вторая полуось"
        
        text_id = canvas_widget.create_text(50, 30, text=text, fill="#0066CC", font=("Arial", 10), anchor="nw")
        self._preview_ids.append(text_id)
        
        if not self._center:
            return
        
        scx, scy = transform.transform_point(self._center[0], self._center[1])
        center_id = canvas_widget.create_oval(scx - 4, scy - 4, scx + 4, scy + 4, fill="#0066CC", outline="#FFFFFF", width=2)
        self._preview_ids.append(center_id)
        
        if self._axis1:
            sx1, sy1 = transform.transform_point(self._axis1[0], self._axis1[1])
            line_id = canvas_widget.create_line(scx, scy, sx1, sy1, fill="#0066CC", dash=(3, 3), width=1)
            self._preview_ids.append(line_id)
            rx = distance(self._center, self._axis1)
            
            if self._current_point:
                sx2, sy2 = transform.transform_point(self._current_point[0], self._current_point[1])
                line_id = canvas_widget.create_line(scx, scy, sx2, sy2, fill="#0066CC", dash=(3, 3), width=1)
                self._preview_ids.append(line_id)
                ry = distance(self._center, self._current_point)
                sr_x = rx * transform.get_scale()
                sr_y = ry * transform.get_scale()
                ellipse_id = canvas_widget.create_oval(scx - sr_x, scy - sr_y, scx + sr_x, scy + sr_y, outline="#0066CC", dash=(6, 3), width=2)
                self._preview_ids.append(ellipse_id)
                text_id = canvas_widget.create_text(scx, scy - sr_y - 15, text=f"Rx: {rx:.1f} Ry: {ry:.1f}", fill="#0066CC", font=("Arial", 9, "bold"))
                self._preview_ids.append(text_id)


class PolygonTool(BaseTool):
    MODE_INSCRIBED = 0
    MODE_CIRCUMSCRIBED = 1
    
    def __init__(self, num_sides: int = 6):
        super().__init__()
        self.num_sides = num_sides
        self._mode = self.MODE_INSCRIBED
        self._center: Optional[Tuple[float, float]] = None
        self._current_point: Optional[Tuple[float, float]] = None
        self._input_buffer: str = ""
    
    def get_name(self) -> str:
        mode_names = ["Вписанный", "Описанный"]
        mode_name = mode_names[self._mode]
        return f"Многоугольник ({self.num_sides}, {mode_name})"
    
    def get_icon(self) -> str:
        return "⬡"
    
    def _reset_state(self):
        self._center = None
        self._current_point = None
        self._input_buffer = ""
    
    def set_num_sides(self, num_sides: int):
        self.num_sides = max(3, num_sides)
    
    def _cycle_mode(self):
        self._mode = (self._mode + 1) % 2
        if self.canvas:
            self.canvas.redraw()
    
    def on_left_click(self, sx: float, sy: float, wx: float, wy: float):
        if self._center is None:
            self._center = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        else:
            radius = distance(self._center, (wx, wy))
            if radius > 0:
                polygon_type = PolygonType.INSCRIBED if self._mode == self.MODE_INSCRIBED else PolygonType.CIRCUMSCRIBED
                polygon = Polygon(self._center[0], self._center[1], radius, self.num_sides, polygon_type=polygon_type)
                polygon.style_id = self.canvas.style_manager.get_current_style_id()
                self.canvas.add_primitive(polygon)
                self._reset_state()
                self._clear_preview()
    
    def on_mouse_move(self, sx: float, sy: float, wx: float, wy: float):
        self._current_point = (wx, wy)
        if self._center and self.canvas:
            self.canvas.redraw()
    
    def on_key_press(self, event):
        key = event.keysym
        char = event.char
        
        if key == "Tab":
            self._cycle_mode()
            return "break"
        
        if self._center is None:
            if char and char.isdigit():
                self._input_buffer += char
            elif key == "BackSpace":
                self._input_buffer = self._input_buffer[:-1]
            elif key == "Return" and self._input_buffer:
                try:
                    n = int(self._input_buffer)
                    if n >= 3:
                        self.num_sides = n
                except ValueError:
                    pass
                self._input_buffer = ""
            elif key == "Escape":
                self._input_buffer = ""
        elif key == "Return" and self._input_buffer:
            try:
                radius = float(self._input_buffer)
                if radius > 0:
                    polygon_type = PolygonType.INSCRIBED if self._mode == self.MODE_INSCRIBED else PolygonType.CIRCUMSCRIBED
                    polygon = Polygon(self._center[0], self._center[1], radius, self.num_sides, polygon_type=polygon_type)
                    polygon.style_id = self.canvas.style_manager.get_current_style_id()
                    self.canvas.add_primitive(polygon)
                    self._reset_state()
                    self._clear_preview()
            except ValueError:
                pass
            self._input_buffer = ""
        elif key == "BackSpace":
            self._input_buffer = self._input_buffer[:-1]
        elif char and (char.isdigit() or char in ".-"):
            self._input_buffer += char
        elif key == "Escape":
            self._input_buffer = ""
        
        if self.canvas:
            self.canvas.redraw()
    
    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        
        if self._center is None:
            mode_names = {
                self.MODE_INSCRIBED: "Вписанный (вершины на окружности)",
                self.MODE_CIRCUMSCRIBED: "Описанный (стороны касаются окружности)"
            }
            mode_name = mode_names[self._mode]
            if self._input_buffer:
                text = f"Число сторон: {self._input_buffer}_ (Enter - подтвердить)"
            else:
                text = f"Многоугольник: {self.num_sides} сторон"
            text_id = canvas_widget.create_text(50, 30, text=text, fill="#0066CC", font=("Arial", 10), anchor="nw")
            self._preview_ids.append(text_id)
            mode_text_id = canvas_widget.create_text(50, 50, text=f"{mode_name} |Tab - переключить режим", fill="#666666", font=("Arial", 8), anchor="nw")
            self._preview_ids.append(mode_text_id)
            return
        
        if self._input_buffer:
            text_id = canvas_widget.create_text(50, 50, text=f"Радиус: {self._input_buffer}_", fill="#0066CC", font=("Arial", 12, "bold"), anchor="nw")
            self._preview_ids.append(text_id)
        
        scx, scy = transform.transform_point(self._center[0], self._center[1])
        center_id = canvas_widget.create_oval(scx - 4, scy - 4, scx + 4, scy + 4, fill="#0066CC", outline="#FFFFFF", width=2)
        self._preview_ids.append(center_id)
        
        if self._current_point:
            radius = distance(self._center, self._current_point)
            mode_names = {
                self.MODE_INSCRIBED: "Вписанный (вершины на окружности)",
                self.MODE_CIRCUMSCRIBED: "Описанный (стороны касаются окружности)"
            }
            mode_name = mode_names[self._mode]
            mode_text_id = canvas_widget.create_text(50, 70, text=f"Режим: {mode_name}", fill="#0066CC", font=("Arial", 9), anchor="nw")
            self._preview_ids.append(mode_text_id)
            help_text_id = canvas_widget.create_text(50, 90, text="Tab - переключить режим", fill="#666666", font=("Arial", 8), anchor="nw")
            self._preview_ids.append(help_text_id)
            
            polygon_type = PolygonType.INSCRIBED if self._mode == self.MODE_INSCRIBED else PolygonType.CIRCUMSCRIBED
            temp_polygon = Polygon(self._center[0], self._center[1], radius, self.num_sides, polygon_type=polygon_type)
            vertices = temp_polygon._get_vertices()
            sr = radius * transform.get_scale()
            circle_id = canvas_widget.create_oval(scx - sr, scy - sr, scx + sr, scy + sr, outline="#999999", fill="", dash=(2, 2), width=1)
            self._preview_ids.append(circle_id)
            points = []
            for v in vertices:
                spx, spy = transform.transform_point(v[0], v[1])
                points.extend([spx, spy])
            poly_id = canvas_widget.create_polygon(points, outline="#0066CC", fill="", dash=(6, 3), width=2)
            self._preview_ids.append(poly_id)
            sx2, sy2 = transform.transform_point(self._current_point[0], self._current_point[1])
            line_id = canvas_widget.create_line(scx, scy, sx2, sy2, fill="#0066CC", dash=(3, 3), width=1)
            self._preview_ids.append(line_id)
            if self._mode == self.MODE_INSCRIBED:
                info_text = f"Радиус окружности: {radius:.1f}  Сторон: {self.num_sides}"
            else:
                info_text = f"Радиус вписанной окр.: {radius:.1f}  Сторон: {self.num_sides}"
            text_id = canvas_widget.create_text(scx, scy + radius * transform.get_scale() + 20, text=info_text, fill="#0066CC", font=("Arial", 9, "bold"))
            self._preview_ids.append(text_id)


class SplineTool(BaseTool):
    def __init__(self):
        super().__init__()
        self._points: List[Tuple[float, float]] = []
        self._current_point: Optional[Tuple[float, float]] = None
    
    def get_name(self) -> str:
        return "Сплайн"
    
    def get_icon(self) -> str:
        return "〰"
    
    def _reset_state(self):
        self._points = []
        self._current_point = None
    
    def on_left_click(self, sx: float, sy: float, wx: float, wy: float):
        self._points.append((wx, wy))
        if len(self._points) == 1 and self.canvas:
            self.canvas.set_base_point(wx, wy)
        if self.canvas:
            self.canvas.redraw()
    
    def on_right_click(self, sx: float, sy: float, wx: float, wy: float):
        if len(self._points) >= 2:
            spline = Spline(self._points)
            spline.style_id = self.canvas.style_manager.get_current_style_id()
            self.canvas.add_primitive(spline)
            self._reset_state()
            self._clear_preview()
        if self.canvas:
            self.canvas.redraw()
    
    def on_mouse_move(self, sx: float, sy: float, wx: float, wy: float):
        self._current_point = (wx, wy)
        if self.canvas:
            self.canvas.redraw()
    
    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        
        if not self._points:
            text = "ЛКМ - добавить точку, ПКМ - завершить"
        else:
            text = f"Точек: {len(self._points)} (ПКМ - завершить)"
        
        text_id = canvas_widget.create_text(50, 30, text=text, fill="#0066CC", font=("Arial", 10), anchor="nw")
        self._preview_ids.append(text_id)
        
        if not self._points:
            return
        
        for i, p in enumerate(self._points):
            spx, spy = transform.transform_point(p[0], p[1])
            if i == 0:
                pt_id = canvas_widget.create_rectangle(spx - 5, spy - 5, spx + 5, spy + 5, fill="#FFFFFF", outline="#0066CC", width=2)
            else:
                pt_id = canvas_widget.create_oval(spx - 5, spy - 5, spx + 5, spy + 5, fill="#FFFFFF", outline="#0066CC", width=2)
            self._preview_ids.append(pt_id)
        
        points = self._points[:]
        if self._current_point:
            points.append(self._current_point)
        
        if len(points) >= 2:
            screen_points = []
            for p in points:
                spx, spy = transform.transform_point(p[0], p[1])
                screen_points.extend([spx, spy])
            poly_id = canvas_widget.create_line(screen_points, fill="#AAAAAA", dash=(4, 4), width=1)
            self._preview_ids.append(poly_id)
            
            from ..utils.math_utils import catmull_rom_spline
            curve_points = catmull_rom_spline(points)
            if len(curve_points) >= 2:
                screen_curve = []
                for p in curve_points:
                    spx, spy = transform.transform_point(p[0], p[1])
                    screen_curve.extend([spx, spy])
                curve_id = canvas_widget.create_line(screen_curve, fill="#0066CC", width=2, smooth=True)
                self._preview_ids.append(curve_id)
