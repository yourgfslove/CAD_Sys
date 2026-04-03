"""
Dimension primitives - размерные линии по ГОСТ 2.307-2011
Линейные, радиальные, диаметральные и угловые размеры
"""

import math
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from .base import Primitive, ControlPoint, SnapPoint, SnapType, PrimitiveFactory
from ..utils.math_utils import distance, midpoint, angle_between_points


class DimensionType(Enum):
    """Тип размера"""
    LINEAR_HORIZONTAL = "horizontal"
    LINEAR_VERTICAL = "vertical"
    LINEAR_ALIGNED = "aligned"
    RADIAL = "radial"
    DIAMETER = "diameter"
    ANGULAR = "angular"


class ArrowType(Enum):
    """Тип стрелки по ГОСТ"""
    FILLED = "filled"       # Заполненная стрелка
    OPEN = "open"           # Открытая стрелка
    TICK = "tick"           # Засечка (для архитектурных)
    DOT = "dot"             # Точка


class TextPosition(Enum):
    """Положение текста относительно размерной линии"""
    ABOVE = "above"         # Над линией
    CENTER = "center"       # По центру (с разрывом линии)
    BELOW = "below"         # Под линией


@dataclass
class DimensionStyle:
    """Стиль размерной линии по ГОСТ 2.307-2011"""
    # Выносные линии
    ext_line_color: str = "#000000"
    ext_line_width: float = 1.0
    ext_line_extension: float = 3.0     # Выход за размерную линию (мм)
    ext_line_offset: float = 2.0        # Отступ от объекта (мм)

    # Размерная линия
    dim_line_color: str = "#000000"
    dim_line_width: float = 1.0

    # Стрелки
    arrow_type: ArrowType = ArrowType.FILLED
    arrow_size: float = 10.0            # Размер стрелки (пикс. при scale=1)
    arrow_filled: bool = True

    # Текст
    text_height: float = 14.0           # Высота текста (пикс. при scale=1)
    text_color: str = "#000000"
    text_position: TextPosition = TextPosition.ABOVE
    text_font: str = "ISOCPEUR"
    decimal_places: int = 1

    def get_arrow_size_px(self, scale: float = 1.0) -> float:
        return max(6, self.arrow_size * scale)

    def get_text_height_px(self, scale: float = 1.0) -> float:
        return max(8, self.text_height * scale)

    def get_ext_extension_px(self, scale: float = 1.0) -> float:
        return self.ext_line_extension * scale

    def get_ext_offset_px(self, scale: float = 1.0) -> float:
        return self.ext_line_offset * scale

    def get_line_width_px(self, base_width: float, scale: float = 1.0) -> float:
        return max(1, base_width * scale)

    def get_dash_pattern(self, scale: float = 1.0):
        d = max(2, int(5 * scale))
        g = max(1, int(3 * scale))
        return (d, g)

    def get_font_size(self, scale: float = 1.0) -> int:
        return max(8, int(self.text_height * scale))


# ==================== Линейный размер ====================

class LinearDimension(Primitive):
    """
    Линейный размер (горизонтальный, вертикальный, выровненный)
    по ГОСТ 2.307-2011
    """

    def __init__(self, x1: float = 0, y1: float = 0,
                 x2: float = 100, y2: float = 0,
                 offset: float = 30,
                 dim_type: str = "aligned",
                 text_override: str = ""):
        super().__init__()
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.offset = offset            # Отступ размерной линии от объекта
        self.dim_type = dim_type         # horizontal / vertical / aligned
        self.text_override = text_override
        self.dim_style = DimensionStyle()
        self._associated_primitive_id: Optional[str] = None

    def get_type_name(self) -> str:
        names = {
            "horizontal": "Размер горизонт.",
            "vertical": "Размер вертик.",
            "aligned": "Размер выровн.",
        }
        return names.get(self.dim_type, "Линейный размер")

    def get_measured_value(self) -> float:
        if self.dim_type == "horizontal":
            return abs(self.x2 - self.x1)
        elif self.dim_type == "vertical":
            return abs(self.y2 - self.y1)
        else:
            return distance((self.x1, self.y1), (self.x2, self.y2))

    def get_display_text(self) -> str:
        if self.text_override:
            return self.text_override
        val = self.get_measured_value()
        return f"{val:.{self.dim_style.decimal_places}f}"

    def _compute_geometry(self):
        """Вычислить геометрию размерной линии"""
        if self.dim_type == "horizontal":
            # Горизонтальный размер
            sign = 1 if self.offset >= 0 else -1
            dim_y = self.y1 + self.offset
            return {
                'ext1_start': (self.x1, self.y1),
                'ext1_end': (self.x1, dim_y + sign * self.dim_style.ext_line_extension),
                'ext2_start': (self.x2, self.y2),
                'ext2_end': (self.x2, dim_y + sign * self.dim_style.ext_line_extension),
                'dim_start': (self.x1, dim_y),
                'dim_end': (self.x2, dim_y),
                'text_pos': ((self.x1 + self.x2) / 2, dim_y),
                'angle': 0,
            }
        elif self.dim_type == "vertical":
            # Вертикальный размер
            sign = 1 if self.offset >= 0 else -1
            dim_x = self.x1 + self.offset
            return {
                'ext1_start': (self.x1, self.y1),
                'ext1_end': (dim_x + sign * self.dim_style.ext_line_extension, self.y1),
                'ext2_start': (self.x2, self.y2),
                'ext2_end': (dim_x + sign * self.dim_style.ext_line_extension, self.y2),
                'dim_start': (dim_x, self.y1),
                'dim_end': (dim_x, self.y2),
                'text_pos': (dim_x, (self.y1 + self.y2) / 2),
                'angle': math.pi / 2,
            }
        else:
            # Выровненный размер
            dx = self.x2 - self.x1
            dy = self.y2 - self.y1
            length = math.sqrt(dx * dx + dy * dy)
            if length < 1e-6:
                return self._compute_geometry_fallback()

            # Нормаль к линии
            nx = -dy / length
            ny = dx / length

            ext_ext = self.dim_style.ext_line_extension
            sign = 1 if self.offset >= 0 else -1

            d1x = self.x1 + nx * self.offset
            d1y = self.y1 + ny * self.offset
            d2x = self.x2 + nx * self.offset
            d2y = self.y2 + ny * self.offset

            return {
                'ext1_start': (self.x1, self.y1),
                'ext1_end': (d1x + nx * sign * ext_ext, d1y + ny * sign * ext_ext),
                'ext2_start': (self.x2, self.y2),
                'ext2_end': (d2x + nx * sign * ext_ext, d2y + ny * sign * ext_ext),
                'dim_start': (d1x, d1y),
                'dim_end': (d2x, d2y),
                'text_pos': ((d1x + d2x) / 2, (d1y + d2y) / 2),
                'angle': math.atan2(dy, dx),
            }

    def _compute_geometry_fallback(self):
        return {
            'ext1_start': (self.x1, self.y1),
            'ext1_end': (self.x1, self.y1 + self.offset),
            'ext2_start': (self.x2, self.y2),
            'ext2_end': (self.x2, self.y2 + self.offset),
            'dim_start': (self.x1, self.y1 + self.offset),
            'dim_end': (self.x2, self.y2 + self.offset),
            'text_pos': ((self.x1 + self.x2) / 2, self.y1 + self.offset),
            'angle': 0,
        }

    def draw(self, canvas, transform, style_manager) -> List[int]:
        self.clear_canvas_items(canvas)
        geom = self._compute_geometry()
        scale = transform.get_scale()
        color = "#0066CC" if self.selected else self.dim_style.dim_line_color
        ext_color = "#0066CC" if self.selected else self.dim_style.ext_line_color
        text_color = "#0066CC" if self.selected else self.dim_style.text_color
        arrow_size = self.dim_style.get_arrow_size_px(scale)
        line_w = self.dim_style.get_line_width_px(self.dim_style.ext_line_width, scale)
        dim_w = self.dim_style.get_line_width_px(self.dim_style.dim_line_width, scale)
        dash = self.dim_style.get_dash_pattern(scale)
        font_size = self.dim_style.get_font_size(scale)

        # Выносные линии
        for key_start, key_end in [('ext1_start', 'ext1_end'), ('ext2_start', 'ext2_end')]:
            sx1, sy1 = transform.transform_point(*geom[key_start])
            sx2, sy2 = transform.transform_point(*geom[key_end])
            item = canvas.create_line(sx1, sy1, sx2, sy2,
                                      fill=ext_color, width=line_w, dash=dash)
            self._canvas_ids.append(item)

        # Размерная линия
        ds = transform.transform_point(*geom['dim_start'])
        de = transform.transform_point(*geom['dim_end'])
        dim_line_id = canvas.create_line(ds[0], ds[1], de[0], de[1],
                                         fill=color, width=dim_w)
        self._canvas_ids.append(dim_line_id)

        # Стрелки
        self._draw_arrow(canvas, ds[0], ds[1], de[0], de[1], arrow_size, color, scale)
        self._draw_arrow(canvas, de[0], de[1], ds[0], ds[1], arrow_size, color, scale)

        # Текст размера
        text = self.get_display_text()
        tp = transform.transform_point(*geom['text_pos'])
        angle_deg = -math.degrees(geom['angle'])
        if angle_deg > 90 or angle_deg < -90:
            angle_deg += 180

        text_h = self.dim_style.get_text_height_px(scale)
        text_offset = text_h * 0.6
        norm_angle = geom['angle'] + math.pi / 2
        text_x = tp[0] + math.cos(norm_angle) * text_offset
        text_y = tp[1] + math.sin(norm_angle) * text_offset

        text_id = canvas.create_text(
            text_x, text_y, text=text,
            fill=text_color,
            font=("Arial", font_size),
            angle=angle_deg
        )
        self._canvas_ids.append(text_id)

        # Белый фон под текстом
        bbox = canvas.bbox(text_id)
        if bbox:
            pad = max(1, int(scale * 0.5))
            bg_id = canvas.create_rectangle(
                bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad,
                fill="white", outline="", width=0
            )
            canvas.tag_lower(bg_id, text_id)
            self._canvas_ids.append(bg_id)

        # Контрольные точки при выделении
        if self.selected:
            for cp in self.get_control_points():
                cpx, cpy = transform.transform_point(cp.x, cp.y)
                cp_id = canvas.create_rectangle(
                    cpx - 4, cpy - 4, cpx + 4, cpy + 4,
                    fill="#FFFFFF", outline="#0066CC", width=2
                )
                self._canvas_ids.append(cp_id)

        return self._canvas_ids

    def _draw_arrow(self, canvas, x1, y1, x2, y2, size, color, scale=1.0):
        """Нарисовать стрелку от (x1,y1) в направлении (x2,y2)"""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1:
            return

        ux = dx / length
        uy = dy / length
        px = -uy
        py = ux

        ax1 = x1 + ux * size + px * size * 0.3
        ay1 = y1 + uy * size + py * size * 0.3
        ax2 = x1 + ux * size - px * size * 0.3
        ay2 = y1 + uy * size - py * size * 0.3
        arrow_w = self.dim_style.get_line_width_px(self.dim_style.dim_line_width, scale)

        if self.dim_style.arrow_type == ArrowType.FILLED:
            item = canvas.create_polygon(
                x1, y1, ax1, ay1, ax2, ay2,
                fill=color, outline=color
            )
        elif self.dim_style.arrow_type == ArrowType.OPEN:
            item = canvas.create_line(ax1, ay1, x1, y1, ax2, ay2,
                                      fill=color, width=arrow_w)
        elif self.dim_style.arrow_type == ArrowType.TICK:
            item = canvas.create_line(
                x1 - px * size * 0.4, y1 - py * size * 0.4,
                x1 + px * size * 0.4, y1 + py * size * 0.4,
                fill=color, width=max(1, arrow_w * 2)
            )
        else:  # DOT
            r = size * 0.2
            item = canvas.create_oval(x1 - r, y1 - r, x1 + r, y1 + r,
                                      fill=color, outline=color)
        self._canvas_ids.append(item)

    def get_control_points(self) -> List[ControlPoint]:
        geom = self._compute_geometry()
        return [
            ControlPoint(x=self.x1, y=self.y1, name="Точка 1", index=0,
                         snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=self.x2, y=self.y2, name="Точка 2", index=1,
                         snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=geom['text_pos'][0], y=geom['text_pos'][1],
                         name="Текст", index=2, snap_types=[]),
        ]

    def move_control_point(self, index: int, new_x: float, new_y: float):
        if index == 0:
            self.x1 = new_x
            self.y1 = new_y
        elif index == 1:
            self.x2 = new_x
            self.y2 = new_y
        elif index == 2:
            # Перемещение текста = изменение offset
            geom = self._compute_geometry()
            if self.dim_type == "horizontal":
                self.offset = new_y - self.y1
            elif self.dim_type == "vertical":
                self.offset = new_x - self.x1
            else:
                dx = self.x2 - self.x1
                dy = self.y2 - self.y1
                length = math.sqrt(dx * dx + dy * dy)
                if length > 1e-6:
                    nx = -dy / length
                    ny = dx / length
                    self.offset = (new_x - self.x1) * nx + (new_y - self.y1) * ny

    def get_snap_points(self) -> List[SnapPoint]:
        return [
            SnapPoint(x=self.x1, y=self.y1, snap_type=SnapType.ENDPOINT,
                      primitive_id=self.id),
            SnapPoint(x=self.x2, y=self.y2, snap_type=SnapType.ENDPOINT,
                      primitive_id=self.id),
        ]

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        geom = self._compute_geometry()
        all_x = [self.x1, self.x2, geom['dim_start'][0], geom['dim_end'][0]]
        all_y = [self.y1, self.y2, geom['dim_start'][1], geom['dim_end'][1]]
        return (min(all_x), min(all_y), max(all_x), max(all_y))

    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        geom = self._compute_geometry()
        # Проверяем попадание на размерную линию
        ds = geom['dim_start']
        de = geom['dim_end']
        return self._point_near_segment(x, y, ds[0], ds[1], de[0], de[1], tolerance)

    def _point_near_segment(self, px, py, x1, y1, x2, y2, tol):
        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-10:
            return distance((px, py), (x1, y1)) <= tol
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return distance((px, py), (proj_x, proj_y)) <= tol

    def get_properties(self) -> Dict[str, Any]:
        return {
            "type": self.get_type_name(),
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2,
            "offset": self.offset,
            "dim_type": self.dim_type,
            "value": self.get_measured_value(),
            "text_override": self.text_override,
            "style_id": self.style_id,
        }

    def set_property(self, name: str, value: Any) -> bool:
        try:
            if name == "x1": self.x1 = float(value)
            elif name == "y1": self.y1 = float(value)
            elif name == "x2": self.x2 = float(value)
            elif name == "y2": self.y2 = float(value)
            elif name == "offset": self.offset = float(value)
            elif name == "text_override": self.text_override = str(value)
            elif name == "style_id": self.style_id = str(value)
            else: return False
            return True
        except (ValueError, TypeError):
            return False

    def set_associated_primitive(self, primitive_id: str):
        self._associated_primitive_id = primitive_id

    def update_from_primitive(self, primitive):
        """Обновить размер при изменении связанного примитива (ассоциативность)"""
        if hasattr(primitive, 'x1'):
            self.x1 = primitive.x1
            self.y1 = primitive.y1
            self.x2 = primitive.x2
            self.y2 = primitive.y2


PrimitiveFactory.register("linear_dimension", LinearDimension)


# ==================== Радиальный размер ====================

class RadialDimension(Primitive):
    """
    Радиальный размер (R) по ГОСТ 2.307-2011
    """

    def __init__(self, cx: float = 0, cy: float = 0,
                 radius: float = 50, angle: float = 45,
                 text_override: str = ""):
        super().__init__()
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.angle = math.radians(angle)  # Угол направления размерной линии
        self.text_override = text_override
        self.dim_style = DimensionStyle()
        self._associated_primitive_id: Optional[str] = None

    def get_type_name(self) -> str:
        return "Размер радиуса"

    def get_measured_value(self) -> float:
        return self.radius

    def get_display_text(self) -> str:
        if self.text_override:
            return self.text_override
        val = self.get_measured_value()
        return f"R{val:.{self.dim_style.decimal_places}f}"

    def _get_dim_point(self) -> Tuple[float, float]:
        """Точка на окружности"""
        return (
            self.cx + self.radius * math.cos(self.angle),
            self.cy + self.radius * math.sin(self.angle)
        )

    def draw(self, canvas, transform, style_manager) -> List[int]:
        self.clear_canvas_items(canvas)
        scale = transform.get_scale()
        color = "#0066CC" if self.selected else self.dim_style.dim_line_color
        text_color = "#0066CC" if self.selected else self.dim_style.text_color
        arrow_size = self.dim_style.get_arrow_size_px(scale)
        dim_w = self.dim_style.get_line_width_px(self.dim_style.dim_line_width, scale)
        font_size = self.dim_style.get_font_size(scale)

        # Центр и точка на окружности
        scx, scy = transform.transform_point(self.cx, self.cy)
        dim_pt = self._get_dim_point()
        sdx, sdy = transform.transform_point(*dim_pt)

        # Размерная линия от центра к точке на окружности
        line_id = canvas.create_line(scx, scy, sdx, sdy,
                                     fill=color, width=dim_w)
        self._canvas_ids.append(line_id)

        # Стрелка на окружности (указывает к центру)
        self._draw_arrow(canvas, sdx, sdy, scx, scy, arrow_size, color)

        # Текст
        text = self.get_display_text()
        text_h = self.dim_style.get_text_height_px(scale)

        tmx = (scx + sdx) / 2
        tmy = (scy + sdy) / 2
        angle_deg = -math.degrees(self.angle)
        if angle_deg > 90 or angle_deg < -90:
            angle_deg += 180

        norm_angle = self.angle + math.pi / 2
        text_offset = text_h * 0.6
        text_x = tmx + math.cos(norm_angle) * text_offset
        text_y = tmy + math.sin(norm_angle) * text_offset

        text_id = canvas.create_text(
            text_x, text_y, text=text,
            fill=text_color,
            font=("Arial", font_size),
            angle=angle_deg
        )
        self._canvas_ids.append(text_id)

        bbox = canvas.bbox(text_id)
        if bbox:
            pad = max(1, int(scale * 0.5))
            bg_id = canvas.create_rectangle(
                bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad,
                fill="white", outline="", width=0
            )
            canvas.tag_lower(bg_id, text_id)
            self._canvas_ids.append(bg_id)

        # Точка в центре
        r_pt = max(1, scale * 0.8)
        center_id = canvas.create_oval(scx - r_pt, scy - r_pt, scx + r_pt, scy + r_pt,
                                        fill=color, outline=color)
        self._canvas_ids.append(center_id)

        if self.selected:
            for cp in self.get_control_points():
                cpx, cpy = transform.transform_point(cp.x, cp.y)
                cp_id = canvas.create_rectangle(
                    cpx - 4, cpy - 4, cpx + 4, cpy + 4,
                    fill="#FFFFFF", outline="#0066CC", width=2
                )
                self._canvas_ids.append(cp_id)

        return self._canvas_ids

    def _draw_arrow(self, canvas, tip_x, tip_y, from_x, from_y, size, color):
        dx = from_x - tip_x
        dy = from_y - tip_y
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1:
            return
        ux = dx / length
        uy = dy / length
        px = -uy
        py = ux

        ax1 = tip_x + ux * size + px * size * 0.3
        ay1 = tip_y + uy * size + py * size * 0.3
        ax2 = tip_x + ux * size - px * size * 0.3
        ay2 = tip_y + uy * size - py * size * 0.3

        item = canvas.create_polygon(
            tip_x, tip_y, ax1, ay1, ax2, ay2,
            fill=color, outline=color
        )
        self._canvas_ids.append(item)

    def get_control_points(self) -> List[ControlPoint]:
        dim_pt = self._get_dim_point()
        return [
            ControlPoint(x=self.cx, y=self.cy, name="Центр", index=0,
                         snap_types=[SnapType.CENTER]),
            ControlPoint(x=dim_pt[0], y=dim_pt[1], name="На окружности", index=1,
                         snap_types=[SnapType.ENDPOINT]),
        ]

    def move_control_point(self, index: int, new_x: float, new_y: float):
        if index == 0:
            self.cx = new_x
            self.cy = new_y
        elif index == 1:
            self.radius = distance((self.cx, self.cy), (new_x, new_y))
            self.angle = math.atan2(new_y - self.cy, new_x - self.cx)

    def get_snap_points(self) -> List[SnapPoint]:
        dim_pt = self._get_dim_point()
        return [
            SnapPoint(x=self.cx, y=self.cy, snap_type=SnapType.CENTER,
                      primitive_id=self.id),
            SnapPoint(x=dim_pt[0], y=dim_pt[1], snap_type=SnapType.ENDPOINT,
                      primitive_id=self.id),
        ]

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        dim_pt = self._get_dim_point()
        all_x = [self.cx, dim_pt[0]]
        all_y = [self.cy, dim_pt[1]]
        return (min(all_x), min(all_y), max(all_x), max(all_y))

    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        dim_pt = self._get_dim_point()
        # Проверка на размерную линию
        dx = dim_pt[0] - self.cx
        dy = dim_pt[1] - self.cy
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-10:
            return distance((x, y), (self.cx, self.cy)) <= tolerance
        t = max(0, min(1, ((x - self.cx) * dx + (y - self.cy) * dy) / length_sq))
        proj_x = self.cx + t * dx
        proj_y = self.cy + t * dy
        return distance((x, y), (proj_x, proj_y)) <= tolerance

    def get_properties(self) -> Dict[str, Any]:
        return {
            "type": self.get_type_name(),
            "cx": self.cx, "cy": self.cy,
            "radius": self.radius,
            "angle_deg": math.degrees(self.angle),
            "text_override": self.text_override,
            "style_id": self.style_id,
        }

    def set_property(self, name: str, value: Any) -> bool:
        try:
            if name == "cx": self.cx = float(value)
            elif name == "cy": self.cy = float(value)
            elif name == "radius": self.radius = abs(float(value))
            elif name == "angle_deg": self.angle = math.radians(float(value))
            elif name == "text_override": self.text_override = str(value)
            elif name == "style_id": self.style_id = str(value)
            else: return False
            return True
        except (ValueError, TypeError):
            return False

    def set_associated_primitive(self, primitive_id: str):
        self._associated_primitive_id = primitive_id

    def update_from_primitive(self, primitive):
        if hasattr(primitive, 'cx') and hasattr(primitive, 'radius'):
            self.cx = primitive.cx
            self.cy = primitive.cy
            self.radius = primitive.radius


PrimitiveFactory.register("radial_dimension", RadialDimension)


# ==================== Диаметральный размер ====================

class DiameterDimension(Primitive):
    """
    Диаметральный размер (⌀) по ГОСТ 2.307-2011
    """

    def __init__(self, cx: float = 0, cy: float = 0,
                 radius: float = 50, angle: float = 45,
                 text_override: str = ""):
        super().__init__()
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.angle = math.radians(angle)
        self.text_override = text_override
        self.dim_style = DimensionStyle()
        self._associated_primitive_id: Optional[str] = None

    def get_type_name(self) -> str:
        return "Размер диаметра"

    def get_measured_value(self) -> float:
        return self.radius * 2

    def get_display_text(self) -> str:
        if self.text_override:
            return self.text_override
        val = self.get_measured_value()
        return f"\u2300{val:.{self.dim_style.decimal_places}f}"

    def _get_endpoints(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Две точки на окружности (диаметрально противоположные)"""
        p1 = (
            self.cx + self.radius * math.cos(self.angle),
            self.cy + self.radius * math.sin(self.angle)
        )
        p2 = (
            self.cx - self.radius * math.cos(self.angle),
            self.cy - self.radius * math.sin(self.angle)
        )
        return p1, p2

    def draw(self, canvas, transform, style_manager) -> List[int]:
        self.clear_canvas_items(canvas)
        scale = transform.get_scale()
        color = "#0066CC" if self.selected else self.dim_style.dim_line_color
        text_color = "#0066CC" if self.selected else self.dim_style.text_color
        arrow_size = self.dim_style.get_arrow_size_px(scale)
        dim_w = self.dim_style.get_line_width_px(self.dim_style.dim_line_width, scale)
        font_size = self.dim_style.get_font_size(scale)

        p1, p2 = self._get_endpoints()
        sp1 = transform.transform_point(*p1)
        sp2 = transform.transform_point(*p2)
        scx, scy = transform.transform_point(self.cx, self.cy)

        # Размерная линия через центр
        line_id = canvas.create_line(sp1[0], sp1[1], sp2[0], sp2[1],
                                     fill=color, width=dim_w)
        self._canvas_ids.append(line_id)

        # Стрелки на обоих концах
        self._draw_arrow(canvas, sp1[0], sp1[1], scx, scy, arrow_size, color)
        self._draw_arrow(canvas, sp2[0], sp2[1], scx, scy, arrow_size, color)

        # Текст
        text = self.get_display_text()
        text_h = self.dim_style.get_text_height_px(scale)

        angle_deg = -math.degrees(self.angle)
        if angle_deg > 90 or angle_deg < -90:
            angle_deg += 180

        norm_angle = self.angle + math.pi / 2
        text_offset = text_h * 0.6
        text_x = scx + math.cos(norm_angle) * text_offset
        text_y = scy + math.sin(norm_angle) * text_offset

        text_id = canvas.create_text(
            text_x, text_y, text=text,
            fill=text_color,
            font=("Arial", font_size),
            angle=angle_deg
        )
        self._canvas_ids.append(text_id)

        bbox = canvas.bbox(text_id)
        if bbox:
            pad = max(1, int(scale * 0.5))
            bg_id = canvas.create_rectangle(
                bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad,
                fill="white", outline="", width=0
            )
            canvas.tag_lower(bg_id, text_id)
            self._canvas_ids.append(bg_id)

        if self.selected:
            for cp in self.get_control_points():
                cpx, cpy = transform.transform_point(cp.x, cp.y)
                cp_id = canvas.create_rectangle(
                    cpx - 4, cpy - 4, cpx + 4, cpy + 4,
                    fill="#FFFFFF", outline="#0066CC", width=2
                )
                self._canvas_ids.append(cp_id)

        return self._canvas_ids

    def _draw_arrow(self, canvas, tip_x, tip_y, from_x, from_y, size, color):
        dx = from_x - tip_x
        dy = from_y - tip_y
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1:
            return
        ux = dx / length
        uy = dy / length
        px = -uy
        py = ux

        ax1 = tip_x + ux * size + px * size * 0.3
        ay1 = tip_y + uy * size + py * size * 0.3
        ax2 = tip_x + ux * size - px * size * 0.3
        ay2 = tip_y + uy * size - py * size * 0.3

        item = canvas.create_polygon(
            tip_x, tip_y, ax1, ay1, ax2, ay2,
            fill=color, outline=color
        )
        self._canvas_ids.append(item)

    def get_control_points(self) -> List[ControlPoint]:
        p1, p2 = self._get_endpoints()
        return [
            ControlPoint(x=self.cx, y=self.cy, name="Центр", index=0,
                         snap_types=[SnapType.CENTER]),
            ControlPoint(x=p1[0], y=p1[1], name="Точка 1", index=1,
                         snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=p2[0], y=p2[1], name="Точка 2", index=2,
                         snap_types=[SnapType.ENDPOINT]),
        ]

    def move_control_point(self, index: int, new_x: float, new_y: float):
        if index == 0:
            self.cx = new_x
            self.cy = new_y
        elif index == 1:
            self.radius = distance((self.cx, self.cy), (new_x, new_y))
            self.angle = math.atan2(new_y - self.cy, new_x - self.cx)
        elif index == 2:
            self.radius = distance((self.cx, self.cy), (new_x, new_y))
            self.angle = math.atan2(self.cy - new_y, self.cx - new_x)

    def get_snap_points(self) -> List[SnapPoint]:
        p1, p2 = self._get_endpoints()
        return [
            SnapPoint(x=self.cx, y=self.cy, snap_type=SnapType.CENTER,
                      primitive_id=self.id),
            SnapPoint(x=p1[0], y=p1[1], snap_type=SnapType.ENDPOINT,
                      primitive_id=self.id),
            SnapPoint(x=p2[0], y=p2[1], snap_type=SnapType.ENDPOINT,
                      primitive_id=self.id),
        ]

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        p1, p2 = self._get_endpoints()
        return (min(p1[0], p2[0]), min(p1[1], p2[1]),
                max(p1[0], p2[0]), max(p1[1], p2[1]))

    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        p1, p2 = self._get_endpoints()
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-10:
            return distance((x, y), (p1[0], p1[1])) <= tolerance
        t = max(0, min(1, ((x - p1[0]) * dx + (y - p1[1]) * dy) / length_sq))
        proj_x = p1[0] + t * dx
        proj_y = p1[1] + t * dy
        return distance((x, y), (proj_x, proj_y)) <= tolerance

    def get_properties(self) -> Dict[str, Any]:
        return {
            "type": self.get_type_name(),
            "cx": self.cx, "cy": self.cy,
            "radius": self.radius,
            "diameter": self.radius * 2,
            "angle_deg": math.degrees(self.angle),
            "text_override": self.text_override,
            "style_id": self.style_id,
        }

    def set_property(self, name: str, value: Any) -> bool:
        try:
            if name == "cx": self.cx = float(value)
            elif name == "cy": self.cy = float(value)
            elif name == "radius": self.radius = abs(float(value))
            elif name == "diameter": self.radius = abs(float(value)) / 2
            elif name == "angle_deg": self.angle = math.radians(float(value))
            elif name == "text_override": self.text_override = str(value)
            elif name == "style_id": self.style_id = str(value)
            else: return False
            return True
        except (ValueError, TypeError):
            return False

    def set_associated_primitive(self, primitive_id: str):
        self._associated_primitive_id = primitive_id

    def update_from_primitive(self, primitive):
        if hasattr(primitive, 'cx') and hasattr(primitive, 'radius'):
            self.cx = primitive.cx
            self.cy = primitive.cy
            self.radius = primitive.radius


PrimitiveFactory.register("diameter_dimension", DiameterDimension)


# ==================== Угловой размер ====================

class AngularDimension(Primitive):
    """
    Угловой размер по ГОСТ 2.307-2011
    Задаётся тремя точками: вершина угла + две точки на лучах
    """

    def __init__(self, cx: float = 0, cy: float = 0,
                 x1: float = 100, y1: float = 0,
                 x2: float = 0, y2: float = 100,
                 arc_radius: float = 40,
                 text_override: str = ""):
        super().__init__()
        self.cx = cx        # Вершина угла
        self.cy = cy
        self.x1 = x1        # Точка на первом луче
        self.y1 = y1
        self.x2 = x2        # Точка на втором луче
        self.y2 = y2
        self.arc_radius = arc_radius   # Радиус размерной дуги
        self.text_override = text_override
        self.dim_style = DimensionStyle()
        self._associated_primitive_id: Optional[str] = None

    def get_type_name(self) -> str:
        return "Угловой размер"

    def get_measured_value(self) -> float:
        """Угол в градусах"""
        a1 = math.atan2(self.y1 - self.cy, self.x1 - self.cx)
        a2 = math.atan2(self.y2 - self.cy, self.x2 - self.cx)
        angle = a2 - a1
        # Нормализация к [0, 2*pi)
        while angle < 0:
            angle += 2 * math.pi
        while angle >= 2 * math.pi:
            angle -= 2 * math.pi
        # Берём меньший угол
        if angle > math.pi:
            angle = 2 * math.pi - angle
        return math.degrees(angle)

    def get_display_text(self) -> str:
        if self.text_override:
            return self.text_override
        val = self.get_measured_value()
        return f"{val:.{self.dim_style.decimal_places}f}\u00b0"

    def _get_angles(self):
        """Получить начальный и конечный углы дуги"""
        a1 = math.atan2(self.y1 - self.cy, self.x1 - self.cx)
        a2 = math.atan2(self.y2 - self.cy, self.x2 - self.cx)

        # Нормализация
        while a1 < 0: a1 += 2 * math.pi
        while a2 < 0: a2 += 2 * math.pi

        # Определяем направление (берём меньший угол)
        diff = a2 - a1
        while diff < 0: diff += 2 * math.pi
        while diff >= 2 * math.pi: diff -= 2 * math.pi

        if diff > math.pi:
            return a2, a1, 2 * math.pi - diff
        return a1, a2, diff

    def draw(self, canvas, transform, style_manager) -> List[int]:
        self.clear_canvas_items(canvas)
        scale = transform.get_scale()
        color = "#0066CC" if self.selected else self.dim_style.dim_line_color
        ext_color = "#0066CC" if self.selected else self.dim_style.ext_line_color
        text_color = "#0066CC" if self.selected else self.dim_style.text_color
        arrow_size = self.dim_style.get_arrow_size_px(scale)
        line_w = self.dim_style.get_line_width_px(self.dim_style.ext_line_width, scale)
        dim_w = self.dim_style.get_line_width_px(self.dim_style.dim_line_width, scale)
        dash = self.dim_style.get_dash_pattern(scale)
        font_size = self.dim_style.get_font_size(scale)

        scx, scy = transform.transform_point(self.cx, self.cy)
        start_angle, end_angle, sweep = self._get_angles()

        # Выносные линии (лучи от вершины)
        r = self.arc_radius
        ext_ext = self.dim_style.ext_line_extension

        for a in [start_angle, end_angle]:
            ex = self.cx + (r + ext_ext) * math.cos(a)
            ey = self.cy + (r + ext_ext) * math.sin(a)
            sex, sey = transform.transform_point(ex, ey)
            item = canvas.create_line(scx, scy, sex, sey,
                                      fill=ext_color, width=line_w, dash=dash)
            self._canvas_ids.append(item)

        # Размерная дуга
        arc_points = []
        num_segments = max(16, int(sweep * 20))
        for i in range(num_segments + 1):
            t = i / num_segments
            a = start_angle + sweep * t
            ax = self.cx + r * math.cos(a)
            ay = self.cy + r * math.sin(a)
            sx, sy = transform.transform_point(ax, ay)
            arc_points.extend([sx, sy])

        if len(arc_points) >= 4:
            arc_id = canvas.create_line(arc_points, fill=color, width=dim_w, smooth=True)
            self._canvas_ids.append(arc_id)

        # Стрелки на концах дуги
        arc_start_x = self.cx + r * math.cos(start_angle)
        arc_start_y = self.cy + r * math.sin(start_angle)
        sa_sx, sa_sy = transform.transform_point(arc_start_x, arc_start_y)
        tang_start_x = arc_start_x - math.sin(start_angle)
        tang_start_y = arc_start_y + math.cos(start_angle)
        ts_sx, ts_sy = transform.transform_point(tang_start_x, tang_start_y)
        self._draw_arrow(canvas, sa_sx, sa_sy, ts_sx, ts_sy, arrow_size, color)

        arc_end_x = self.cx + r * math.cos(end_angle)
        arc_end_y = self.cy + r * math.sin(end_angle)
        ae_sx, ae_sy = transform.transform_point(arc_end_x, arc_end_y)
        tang_end_x = arc_end_x + math.sin(end_angle)
        tang_end_y = arc_end_y - math.cos(end_angle)
        te_sx, te_sy = transform.transform_point(tang_end_x, tang_end_y)
        self._draw_arrow(canvas, ae_sx, ae_sy, te_sx, te_sy, arrow_size, color)

        # Текст
        text = self.get_display_text()
        text_h = self.dim_style.get_text_height_px(scale)

        mid_angle = start_angle + sweep / 2
        # Смещение текста: в мировых координатах + доп. отступ
        text_world_offset = self.dim_style.text_height / scale if scale > 0 else 0
        text_r = r + text_world_offset * 0.8
        tx = self.cx + text_r * math.cos(mid_angle)
        ty = self.cy + text_r * math.sin(mid_angle)
        stx, sty = transform.transform_point(tx, ty)

        text_angle_deg = -math.degrees(mid_angle) + 90
        if text_angle_deg > 90 or text_angle_deg < -90:
            text_angle_deg += 180

        text_id = canvas.create_text(
            stx, sty, text=text,
            fill=text_color,
            font=("Arial", font_size),
            angle=text_angle_deg
        )
        self._canvas_ids.append(text_id)

        bbox = canvas.bbox(text_id)
        if bbox:
            pad = max(1, int(scale * 0.5))
            bg_id = canvas.create_rectangle(
                bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad,
                fill="white", outline="", width=0
            )
            canvas.tag_lower(bg_id, text_id)
            self._canvas_ids.append(bg_id)

        if self.selected:
            for cp in self.get_control_points():
                cpx, cpy = transform.transform_point(cp.x, cp.y)
                cp_id = canvas.create_rectangle(
                    cpx - 4, cpy - 4, cpx + 4, cpy + 4,
                    fill="#FFFFFF", outline="#0066CC", width=2
                )
                self._canvas_ids.append(cp_id)

        return self._canvas_ids

    def _draw_arrow(self, canvas, tip_x, tip_y, towards_x, towards_y, size, color):
        dx = towards_x - tip_x
        dy = towards_y - tip_y
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1:
            return
        ux = dx / length
        uy = dy / length
        px = -uy
        py = ux

        ax1 = tip_x + ux * size + px * size * 0.3
        ay1 = tip_y + uy * size + py * size * 0.3
        ax2 = tip_x + ux * size - px * size * 0.3
        ay2 = tip_y + uy * size - py * size * 0.3

        item = canvas.create_polygon(
            tip_x, tip_y, ax1, ay1, ax2, ay2,
            fill=color, outline=color
        )
        self._canvas_ids.append(item)

    def get_control_points(self) -> List[ControlPoint]:
        start_angle, end_angle, sweep = self._get_angles()
        mid_angle = start_angle + sweep / 2
        arc_mid_x = self.cx + self.arc_radius * math.cos(mid_angle)
        arc_mid_y = self.cy + self.arc_radius * math.sin(mid_angle)

        return [
            ControlPoint(x=self.cx, y=self.cy, name="Вершина", index=0,
                         snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=self.x1, y=self.y1, name="Луч 1", index=1,
                         snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=self.x2, y=self.y2, name="Луч 2", index=2,
                         snap_types=[SnapType.ENDPOINT]),
            ControlPoint(x=arc_mid_x, y=arc_mid_y, name="Дуга", index=3,
                         snap_types=[]),
        ]

    def move_control_point(self, index: int, new_x: float, new_y: float):
        if index == 0:
            dx = new_x - self.cx
            dy = new_y - self.cy
            self.cx = new_x
            self.cy = new_y
            self.x1 += dx
            self.y1 += dy
            self.x2 += dx
            self.y2 += dy
        elif index == 1:
            self.x1 = new_x
            self.y1 = new_y
        elif index == 2:
            self.x2 = new_x
            self.y2 = new_y
        elif index == 3:
            self.arc_radius = distance((self.cx, self.cy), (new_x, new_y))

    def get_snap_points(self) -> List[SnapPoint]:
        return [
            SnapPoint(x=self.cx, y=self.cy, snap_type=SnapType.ENDPOINT,
                      primitive_id=self.id),
        ]

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        r = self.arc_radius
        return (self.cx - r, self.cy - r, self.cx + r, self.cy + r)

    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        d = distance((x, y), (self.cx, self.cy))
        if abs(d - self.arc_radius) > tolerance:
            return False
        # Проверяем что точка в пределах углового диапазона
        a = math.atan2(y - self.cy, x - self.cx)
        while a < 0: a += 2 * math.pi
        start_angle, end_angle, sweep = self._get_angles()
        diff = a - start_angle
        while diff < 0: diff += 2 * math.pi
        while diff >= 2 * math.pi: diff -= 2 * math.pi
        return diff <= sweep + 0.1

    def get_properties(self) -> Dict[str, Any]:
        return {
            "type": self.get_type_name(),
            "cx": self.cx, "cy": self.cy,
            "x1": self.x1, "y1": self.y1,
            "x2": self.x2, "y2": self.y2,
            "arc_radius": self.arc_radius,
            "angle_value": self.get_measured_value(),
            "text_override": self.text_override,
            "style_id": self.style_id,
        }

    def set_property(self, name: str, value: Any) -> bool:
        try:
            if name == "cx": self.cx = float(value)
            elif name == "cy": self.cy = float(value)
            elif name == "x1": self.x1 = float(value)
            elif name == "y1": self.y1 = float(value)
            elif name == "x2": self.x2 = float(value)
            elif name == "y2": self.y2 = float(value)
            elif name == "arc_radius": self.arc_radius = abs(float(value))
            elif name == "text_override": self.text_override = str(value)
            elif name == "style_id": self.style_id = str(value)
            else: return False
            return True
        except (ValueError, TypeError):
            return False

    def set_associated_primitive(self, primitive_id: str):
        self._associated_primitive_id = primitive_id


PrimitiveFactory.register("angular_dimension", AngularDimension)
