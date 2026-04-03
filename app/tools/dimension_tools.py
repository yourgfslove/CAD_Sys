"""
Dimension Tools - инструменты создания размерных линий
Линейный, радиальный, диаметральный и угловой размеры
"""

import math
from typing import Optional, Tuple
from .base_tool import BaseTool
from ..primitives.dimension import (
    LinearDimension, RadialDimension, DiameterDimension, AngularDimension
)
from ..utils.math_utils import distance


class LinearDimensionTool(BaseTool):
    """Инструмент линейного размера (горизонт./вертик./выровненный)"""

    def __init__(self):
        super().__init__()
        self._point1: Optional[Tuple[float, float]] = None
        self._point2: Optional[Tuple[float, float]] = None
        self._current: Optional[Tuple[float, float]] = None
        self._dim_type = "aligned"  # aligned / horizontal / vertical

    def get_name(self) -> str:
        names = {
            "aligned": "Линейный размер",
            "horizontal": "Горизонт. размер",
            "vertical": "Вертик. размер",
        }
        return names.get(self._dim_type, "Линейный размер")

    def get_icon(self) -> str:
        return "↔"

    def set_dim_type(self, dim_type: str):
        self._dim_type = dim_type

    def _reset_state(self):
        self._point1 = None
        self._point2 = None
        self._current = None
        if self.canvas:
            self.canvas.clear_base_point()

    def on_left_click(self, sx, sy, wx, wy):
        if self._point1 is None:
            self._point1 = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        elif self._point2 is None:
            self._point2 = (wx, wy)
            # Теперь ждём третий клик для определения offset
        else:
            # Третий клик - определяем offset
            offset = self._compute_offset(wx, wy)
            dim = LinearDimension(
                self._point1[0], self._point1[1],
                self._point2[0], self._point2[1],
                offset=offset,
                dim_type=self._dim_type
            )
            self.canvas.add_primitive(dim)
            self._reset_state()
            self._clear_preview()

    def _compute_offset(self, wx, wy):
        if self._dim_type == "horizontal":
            return wy - self._point1[1]
        elif self._dim_type == "vertical":
            return wx - self._point1[0]
        else:
            # Выровненный: проецируем на нормаль
            dx = self._point2[0] - self._point1[0]
            dy = self._point2[1] - self._point1[1]
            length = math.sqrt(dx * dx + dy * dy)
            if length < 1e-6:
                return wy - self._point1[1]
            nx = -dy / length
            ny = dx / length
            return (wx - self._point1[0]) * nx + (wy - self._point1[1]) * ny

    def on_mouse_move(self, sx, sy, wx, wy):
        self._current = (wx, wy)
        if self._point1 and self.canvas:
            self.canvas.redraw()

    def on_key_press(self, event):
        key = event.keysym.lower()
        if key == 'h':
            self._dim_type = "horizontal"
        elif key == 'v' and self._point1:
            self._dim_type = "vertical"
        elif key == 'a' and self._point1:
            self._dim_type = "aligned"
        if self.canvas:
            self.canvas.redraw()

    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        if not self._point1 or not self._current:
            return

        sp1 = transform.transform_point(*self._point1)

        if self._point2 is None:
            # Показываем линию от p1 до курсора
            sc = transform.transform_point(*self._current)
            item = canvas_widget.create_line(
                sp1[0], sp1[1], sc[0], sc[1],
                fill="#3B82F6", width=1, dash=(6, 3)
            )
            self._preview_ids.append(item)

            # Отображаем расстояние
            d = distance(self._point1, self._current)
            mid_x = (sp1[0] + sc[0]) / 2
            mid_y = (sp1[1] + sc[1]) / 2
            txt = canvas_widget.create_text(
                mid_x, mid_y - 15,
                text=f"L: {d:.1f}",
                fill="#3B82F6", font=("Arial", 10)
            )
            self._preview_ids.append(txt)
        else:
            # Показываем предварительный вид размера
            sp2 = transform.transform_point(*self._point2)
            offset = self._compute_offset(*self._current)

            # Создаём временный размер для предпросмотра
            temp = LinearDimension(
                self._point1[0], self._point1[1],
                self._point2[0], self._point2[1],
                offset=offset, dim_type=self._dim_type
            )
            geom = temp._compute_geometry()

            # Выносные линии
            for ks, ke in [('ext1_start', 'ext1_end'), ('ext2_start', 'ext2_end')]:
                s1 = transform.transform_point(*geom[ks])
                s2 = transform.transform_point(*geom[ke])
                item = canvas_widget.create_line(
                    s1[0], s1[1], s2[0], s2[1],
                    fill="#3B82F6", width=1, dash=(4, 2)
                )
                self._preview_ids.append(item)

            # Размерная линия
            ds = transform.transform_point(*geom['dim_start'])
            de = transform.transform_point(*geom['dim_end'])
            item = canvas_widget.create_line(
                ds[0], ds[1], de[0], de[1],
                fill="#3B82F6", width=1, dash=(6, 3)
            )
            self._preview_ids.append(item)

            # Текст
            tp = transform.transform_point(*geom['text_pos'])
            txt = canvas_widget.create_text(
                tp[0], tp[1] - 12,
                text=temp.get_display_text(),
                fill="#3B82F6", font=("Arial", 10)
            )
            self._preview_ids.append(txt)

            # Подсказка типа
            type_names = {
                "aligned": "Выровн.",
                "horizontal": "Горизонт.",
                "vertical": "Вертик.",
            }
            hint = canvas_widget.create_text(
                50, 30,
                text=f"Тип: {type_names.get(self._dim_type, '')} [H/A]",
                fill="#3B82F6", font=("Arial", 9), anchor="w"
            )
            self._preview_ids.append(hint)


class RadialDimensionTool(BaseTool):
    """Инструмент радиального размера"""

    def __init__(self):
        super().__init__()
        self._center: Optional[Tuple[float, float]] = None
        self._current: Optional[Tuple[float, float]] = None
        self._target_circle = None

    def get_name(self) -> str:
        return "Размер радиуса"

    def get_icon(self) -> str:
        return "R"

    def _reset_state(self):
        self._center = None
        self._current = None
        self._target_circle = None
        if self.canvas:
            self.canvas.clear_base_point()

    def on_left_click(self, sx, sy, wx, wy):
        if self._center is None:
            # Попробуем найти окружность под курсором
            if self.canvas:
                from ..primitives.circle import Circle
                from ..primitives.arc import Arc
                prim = self.canvas.find_primitive_at(wx, wy)
                if prim and isinstance(prim, (Circle, Arc)):
                    self._target_circle = prim
                    self._center = (prim.cx, prim.cy)
                    if self.canvas:
                        self.canvas.set_base_point(prim.cx, prim.cy)
                    return

            self._center = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        else:
            radius = distance(self._center, (wx, wy))
            angle = math.degrees(math.atan2(wy - self._center[1], wx - self._center[0]))
            if self._target_circle:
                radius = self._target_circle.radius if hasattr(self._target_circle, 'radius') else radius

            dim = RadialDimension(
                self._center[0], self._center[1],
                radius=radius, angle=angle
            )
            if self._target_circle:
                dim.set_associated_primitive(self._target_circle.id)
            self.canvas.add_primitive(dim)
            self._reset_state()
            self._clear_preview()

    def on_mouse_move(self, sx, sy, wx, wy):
        self._current = (wx, wy)
        if self._center and self.canvas:
            self.canvas.redraw()

    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        if not self._center or not self._current:
            return

        sc = transform.transform_point(*self._center)
        sp = transform.transform_point(*self._current)

        # Линия от центра к курсору
        item = canvas_widget.create_line(
            sc[0], sc[1], sp[0], sp[1],
            fill="#3B82F6", width=1, dash=(6, 3)
        )
        self._preview_ids.append(item)

        # Текст
        r = distance(self._center, self._current)
        if self._target_circle and hasattr(self._target_circle, 'radius'):
            r = self._target_circle.radius
        mid_x = (sc[0] + sp[0]) / 2
        mid_y = (sc[1] + sp[1]) / 2
        txt = canvas_widget.create_text(
            mid_x, mid_y - 15,
            text=f"R{r:.1f}",
            fill="#3B82F6", font=("Arial", 10)
        )
        self._preview_ids.append(txt)

        # Центр
        r_pt = 3
        pt = canvas_widget.create_oval(
            sc[0] - r_pt, sc[1] - r_pt, sc[0] + r_pt, sc[1] + r_pt,
            fill="#3B82F6", outline="#3B82F6"
        )
        self._preview_ids.append(pt)


class DiameterDimensionTool(BaseTool):
    """Инструмент диаметрального размера"""

    def __init__(self):
        super().__init__()
        self._center: Optional[Tuple[float, float]] = None
        self._current: Optional[Tuple[float, float]] = None
        self._target_circle = None

    def get_name(self) -> str:
        return "Размер диаметра"

    def get_icon(self) -> str:
        return "\u2300"

    def _reset_state(self):
        self._center = None
        self._current = None
        self._target_circle = None
        if self.canvas:
            self.canvas.clear_base_point()

    def on_left_click(self, sx, sy, wx, wy):
        if self._center is None:
            if self.canvas:
                from ..primitives.circle import Circle
                from ..primitives.arc import Arc
                prim = self.canvas.find_primitive_at(wx, wy)
                if prim and isinstance(prim, (Circle, Arc)):
                    self._target_circle = prim
                    self._center = (prim.cx, prim.cy)
                    if self.canvas:
                        self.canvas.set_base_point(prim.cx, prim.cy)
                    return

            self._center = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        else:
            radius = distance(self._center, (wx, wy))
            angle = math.degrees(math.atan2(wy - self._center[1], wx - self._center[0]))
            if self._target_circle:
                radius = self._target_circle.radius if hasattr(self._target_circle, 'radius') else radius

            dim = DiameterDimension(
                self._center[0], self._center[1],
                radius=radius, angle=angle
            )
            if self._target_circle:
                dim.set_associated_primitive(self._target_circle.id)
            self.canvas.add_primitive(dim)
            self._reset_state()
            self._clear_preview()

    def on_mouse_move(self, sx, sy, wx, wy):
        self._current = (wx, wy)
        if self._center and self.canvas:
            self.canvas.redraw()

    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        if not self._center or not self._current:
            return

        sc = transform.transform_point(*self._center)
        sp = transform.transform_point(*self._current)

        r = distance(self._center, self._current)
        if self._target_circle and hasattr(self._target_circle, 'radius'):
            r = self._target_circle.radius

        angle = math.atan2(self._current[1] - self._center[1],
                           self._current[0] - self._center[0])

        # Диаметральная линия через центр
        p1 = (self._center[0] + r * math.cos(angle),
              self._center[1] + r * math.sin(angle))
        p2 = (self._center[0] - r * math.cos(angle),
              self._center[1] - r * math.sin(angle))
        sp1 = transform.transform_point(*p1)
        sp2 = transform.transform_point(*p2)

        item = canvas_widget.create_line(
            sp1[0], sp1[1], sp2[0], sp2[1],
            fill="#3B82F6", width=1, dash=(6, 3)
        )
        self._preview_ids.append(item)

        # Текст
        txt = canvas_widget.create_text(
            sc[0], sc[1] - 15,
            text=f"\u2300{r * 2:.1f}",
            fill="#3B82F6", font=("Arial", 10)
        )
        self._preview_ids.append(txt)


class AngularDimensionTool(BaseTool):
    """Инструмент углового размера"""

    def __init__(self):
        super().__init__()
        self._vertex: Optional[Tuple[float, float]] = None
        self._point1: Optional[Tuple[float, float]] = None
        self._point2: Optional[Tuple[float, float]] = None
        self._current: Optional[Tuple[float, float]] = None

    def get_name(self) -> str:
        return "Угловой размер"

    def get_icon(self) -> str:
        return "∠"

    def _reset_state(self):
        self._vertex = None
        self._point1 = None
        self._point2 = None
        self._current = None
        if self.canvas:
            self.canvas.clear_base_point()

    def on_left_click(self, sx, sy, wx, wy):
        if self._vertex is None:
            self._vertex = (wx, wy)
            if self.canvas:
                self.canvas.set_base_point(wx, wy)
        elif self._point1 is None:
            self._point1 = (wx, wy)
        elif self._point2 is None:
            self._point2 = (wx, wy)
            # Теперь ждём клик для определения радиуса дуги
        else:
            arc_radius = distance(self._vertex, (wx, wy))
            dim = AngularDimension(
                self._vertex[0], self._vertex[1],
                self._point1[0], self._point1[1],
                self._point2[0], self._point2[1],
                arc_radius=arc_radius
            )
            self.canvas.add_primitive(dim)
            self._reset_state()
            self._clear_preview()

    def on_mouse_move(self, sx, sy, wx, wy):
        self._current = (wx, wy)
        if self._vertex and self.canvas:
            self.canvas.redraw()

    def draw_preview(self, canvas_widget, transform):
        self._clear_preview()
        if not self._vertex or not self._current:
            return

        sv = transform.transform_point(*self._vertex)
        sc = transform.transform_point(*self._current)

        if self._point1 is None:
            # Рисуем первый луч
            item = canvas_widget.create_line(
                sv[0], sv[1], sc[0], sc[1],
                fill="#3B82F6", width=1, dash=(6, 3)
            )
            self._preview_ids.append(item)

            hint = canvas_widget.create_text(
                50, 30, text="Укажите точку на 1-м луче",
                fill="#3B82F6", font=("Arial", 9), anchor="w"
            )
            self._preview_ids.append(hint)

        elif self._point2 is None:
            # Рисуем оба луча
            sp1 = transform.transform_point(*self._point1)
            item1 = canvas_widget.create_line(
                sv[0], sv[1], sp1[0], sp1[1],
                fill="#3B82F6", width=1, dash=(6, 3)
            )
            self._preview_ids.append(item1)

            item2 = canvas_widget.create_line(
                sv[0], sv[1], sc[0], sc[1],
                fill="#3B82F6", width=1, dash=(6, 3)
            )
            self._preview_ids.append(item2)

            # Угол
            a1 = math.atan2(self._point1[1] - self._vertex[1],
                            self._point1[0] - self._vertex[0])
            a2 = math.atan2(self._current[1] - self._vertex[1],
                            self._current[0] - self._vertex[0])
            angle_deg = abs(math.degrees(a2 - a1))
            if angle_deg > 180:
                angle_deg = 360 - angle_deg

            txt = canvas_widget.create_text(
                sv[0] + 30, sv[1] - 15,
                text=f"{angle_deg:.1f}\u00b0",
                fill="#3B82F6", font=("Arial", 10)
            )
            self._preview_ids.append(txt)

            hint = canvas_widget.create_text(
                50, 30, text="Укажите точку на 2-м луче",
                fill="#3B82F6", font=("Arial", 9), anchor="w"
            )
            self._preview_ids.append(hint)

        else:
            # Предпросмотр готового размера
            sp1 = transform.transform_point(*self._point1)
            sp2 = transform.transform_point(*self._point2)

            item1 = canvas_widget.create_line(
                sv[0], sv[1], sp1[0], sp1[1],
                fill="#3B82F6", width=1, dash=(6, 3)
            )
            self._preview_ids.append(item1)

            item2 = canvas_widget.create_line(
                sv[0], sv[1], sp2[0], sp2[1],
                fill="#3B82F6", width=1, dash=(6, 3)
            )
            self._preview_ids.append(item2)

            # Дуга предпросмотра
            arc_r = distance(self._vertex, self._current)
            temp = AngularDimension(
                self._vertex[0], self._vertex[1],
                self._point1[0], self._point1[1],
                self._point2[0], self._point2[1],
                arc_radius=arc_r
            )
            start_angle, end_angle, sweep = temp._get_angles()

            arc_pts = []
            num = max(16, int(sweep * 20))
            for i in range(num + 1):
                t = i / num
                a = start_angle + sweep * t
                ax = self._vertex[0] + arc_r * math.cos(a)
                ay = self._vertex[1] + arc_r * math.sin(a)
                sax, say = transform.transform_point(ax, ay)
                arc_pts.extend([sax, say])

            if len(arc_pts) >= 4:
                arc_id = canvas_widget.create_line(
                    arc_pts, fill="#3B82F6", width=1, dash=(6, 3), smooth=True
                )
                self._preview_ids.append(arc_id)

            # Текст угла
            txt = canvas_widget.create_text(
                sv[0] + 40, sv[1] - 20,
                text=temp.get_display_text(),
                fill="#3B82F6", font=("Arial", 10)
            )
            self._preview_ids.append(txt)

            hint = canvas_widget.create_text(
                50, 30, text="Укажите положение размерной дуги",
                fill="#3B82F6", font=("Arial", 9), anchor="w"
            )
            self._preview_ids.append(hint)
