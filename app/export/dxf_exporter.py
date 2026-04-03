"""
DXF Exporter - экспорт примитивов в формат DXF (AutoCAD Drawing Exchange Format)

Поддерживаемые версии: AC1009 (R12), AC1015 (R2000)
Система координат: WCS (World Coordinate System)
Единицы измерения: миллиметры (INSUNITS = 4)

Поддерживаемые примитивы:
    - POINT (точка)
    - LINE (отрезок)
    - CIRCLE (окружность)
    - ARC (дуга)
    - ELLIPSE (эллипс) — только R2000+
    - LWPOLYLINE (многоугольник, прямоугольник) — только R2000+
    - SPLINE (сплайн) — только R2000+

Поддержка слоёв:
    - Имя, цвет (ACI), тип линии

Цвета:
    - AutoCAD Color Index (ACI 1-255)
    - Преобразование из HEX (#RRGGBB) в ближайший ACI
"""

import math
from typing import List, Tuple, Optional, Dict, Any

from ..primitives.base import Primitive
from ..primitives.segment import Segment
from ..primitives.circle import Circle
from ..primitives.arc import Arc
from ..primitives.ellipse import Ellipse
from ..primitives.polygon import Polygon
from ..primitives.rectangle import Rectangle
from ..primitives.spline import Spline
from ..styles.line_style import LineStyle, LineType
from ..styles.style_manager import StyleManager


# ============================================================
# Таблица соответствия ACI (AutoCAD Color Index) → RGB
# Первые 9 стандартных цветов AutoCAD
# ============================================================
ACI_COLORS: Dict[int, Tuple[int, int, int]] = {
    1: (255, 0, 0),       # Red
    2: (255, 255, 0),     # Yellow
    3: (0, 255, 0),       # Green
    4: (0, 255, 255),     # Cyan
    5: (0, 0, 255),       # Blue
    6: (255, 0, 255),     # Magenta
    7: (255, 255, 255),   # White/Black (depends on background)
    8: (128, 128, 128),   # Dark grey
    9: (192, 192, 192),   # Light grey
    10: (255, 0, 0),
    11: (255, 127, 127),
    12: (204, 0, 0),
    13: (204, 102, 102),
    14: (153, 0, 0),
    15: (153, 76, 76),
    16: (127, 0, 0),
    17: (127, 63, 63),
    18: (76, 0, 0),
    19: (76, 38, 38),
    20: (255, 63, 0),
    21: (255, 159, 127),
    22: (204, 51, 0),
    23: (204, 127, 102),
    24: (153, 38, 0),
    25: (153, 95, 76),
    30: (255, 127, 0),
    31: (255, 191, 127),
    40: (255, 191, 0),
    41: (255, 223, 127),
    50: (255, 255, 0),
    51: (255, 255, 127),
    60: (191, 255, 0),
    70: (127, 255, 0),
    80: (63, 255, 0),
    90: (0, 255, 0),
    100: (0, 255, 63),
    110: (0, 255, 127),
    120: (0, 255, 191),
    130: (0, 255, 255),
    140: (0, 191, 255),
    150: (0, 127, 255),
    160: (0, 63, 255),
    170: (0, 0, 255),
    180: (63, 0, 255),
    190: (127, 0, 255),
    200: (191, 0, 255),
    210: (255, 0, 255),
    220: (255, 0, 191),
    230: (255, 0, 127),
    240: (255, 0, 63),
    250: (51, 51, 51),
    251: (91, 91, 91),
    252: (132, 132, 132),
    253: (173, 173, 173),
    254: (214, 214, 214),
    255: (255, 255, 255),
}


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Конвертация HEX цвета (#RRGGBB) в RGB кортеж"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return (0, 0, 0)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)


def rgb_to_aci(r: int, g: int, b: int) -> int:
    """
    Преобразование RGB в ближайший AutoCAD Color Index (ACI).
    Перебирает таблицу ACI и находит ближайший цвет по евклидову расстоянию.
    """
    if r == 0 and g == 0 and b == 0:
        return 7  # Black → use color 7 (white/black, adapts to background)

    best_aci = 7
    best_dist = float('inf')

    for aci, (ar, ag, ab) in ACI_COLORS.items():
        dist = (r - ar) ** 2 + (g - ag) ** 2 + (b - ab) ** 2
        if dist < best_dist:
            best_dist = dist
            best_aci = aci

    return best_aci


# ============================================================
# Соответствие типов линий ГОСТ → DXF linetype name
# ============================================================
LINETYPE_MAP: Dict[str, str] = {
    "solid_main": "CONTINUOUS",
    "solid_thin": "CONTINUOUS",
    "solid_wavy": "CONTINUOUS",
    "dashed": "DASHED",
    "dash_dot_thin": "DASHDOT",
    "dash_dot_thick": "DASHDOT",
    "dash_dot_dot": "DASHDOTDOT",
    "solid_zigzag": "CONTINUOUS",
}


class DXFWriter:
    """
    Низкоуровневый генератор DXF-файлов.
    Формирует текстовый DXF согласно спецификации Autodesk.
    """

    def __init__(self, version: str = "R2000"):
        """
        Args:
            version: "R12" для AC1009 или "R2000" для AC1015
        """
        self.version = version
        self.ac_version = "AC1015" if version == "R2000" else "AC1009"
        self._header_vars: List[str] = []
        self._tables: List[str] = []
        self._blocks: List[str] = []
        self._entities: List[str] = []
        self._layers: Dict[str, Tuple[int, str]] = {}  # name -> (aci_color, linetype)
        self._linetypes: Dict[str, Tuple[str, List[float]]] = {}  # name -> (description, pattern)
        self._handle_counter = 100

    def _next_handle(self) -> str:
        """Получить следующий уникальный handle (HEX)"""
        h = format(self._handle_counter, 'X')
        self._handle_counter += 1
        return h

    def add_layer(self, name: str, color: int = 7, linetype: str = "CONTINUOUS"):
        """Добавить слой"""
        self._layers[name] = (color, linetype)

    def add_linetype(self, name: str, description: str, pattern: List[float]):
        """
        Добавить тип линии.
        pattern: список длин чередующихся штрихов и пробелов.
                 Положительные — штрих, отрицательные — пробел, 0 — точка.
        """
        self._linetypes[name] = (description, pattern)

    # ==================== Entity methods ====================

    def add_point(self, x: float, y: float, z: float = 0.0,
                  layer: str = "0", color: int = None):
        """Добавить точку (POINT)"""
        lines = [
            "  0", "POINT",
            "  5", self._next_handle(),
            "100", "AcDbEntity",
            "  8", layer,
        ]
        if color is not None:
            lines += ["  62", str(color)]
        lines += [
            "100", "AcDbPoint",
            " 10", f"{x:.6f}",
            " 20", f"{y:.6f}",
            " 30", f"{z:.6f}",
        ]
        self._entities.append("\n".join(lines))

    def add_line(self, x1: float, y1: float, x2: float, y2: float,
                 z1: float = 0.0, z2: float = 0.0,
                 layer: str = "0", color: int = None, linetype: str = None):
        """Добавить отрезок (LINE)"""
        lines = [
            "  0", "LINE",
            "  5", self._next_handle(),
            "100", "AcDbEntity",
            "  8", layer,
        ]
        if color is not None:
            lines += ["  62", str(color)]
        if linetype:
            lines += ["  6", linetype]
        lines += [
            "100", "AcDbLine",
            " 10", f"{x1:.6f}",
            " 20", f"{y1:.6f}",
            " 30", f"{z1:.6f}",
            " 11", f"{x2:.6f}",
            " 21", f"{y2:.6f}",
            " 31", f"{z2:.6f}",
        ]
        self._entities.append("\n".join(lines))

    def add_circle(self, cx: float, cy: float, radius: float,
                   cz: float = 0.0,
                   layer: str = "0", color: int = None, linetype: str = None):
        """Добавить окружность (CIRCLE)"""
        lines = [
            "  0", "CIRCLE",
            "  5", self._next_handle(),
            "100", "AcDbEntity",
            "  8", layer,
        ]
        if color is not None:
            lines += ["  62", str(color)]
        if linetype:
            lines += ["  6", linetype]
        lines += [
            "100", "AcDbCircle",
            " 10", f"{cx:.6f}",
            " 20", f"{cy:.6f}",
            " 30", f"{cz:.6f}",
            " 40", f"{radius:.6f}",
        ]
        self._entities.append("\n".join(lines))

    def add_arc(self, cx: float, cy: float, radius: float,
                start_angle_deg: float, end_angle_deg: float,
                cz: float = 0.0,
                layer: str = "0", color: int = None, linetype: str = None):
        """
        Добавить дугу (ARC).
        Углы в градусах, отсчитываются от оси X против часовой стрелки.
        """
        lines = [
            "  0", "ARC",
            "  5", self._next_handle(),
            "100", "AcDbEntity",
            "  8", layer,
        ]
        if color is not None:
            lines += ["  62", str(color)]
        if linetype:
            lines += ["  6", linetype]
        lines += [
            "100", "AcDbCircle",
            " 10", f"{cx:.6f}",
            " 20", f"{cy:.6f}",
            " 30", f"{cz:.6f}",
            " 40", f"{radius:.6f}",
            "100", "AcDbArc",
            " 50", f"{start_angle_deg:.6f}",
            " 51", f"{end_angle_deg:.6f}",
        ]
        self._entities.append("\n".join(lines))

    def add_ellipse(self, cx: float, cy: float,
                    major_axis_x: float, major_axis_y: float,
                    ratio: float,
                    start_param: float = 0.0, end_param: float = 6.283185307,
                    cz: float = 0.0, major_axis_z: float = 0.0,
                    layer: str = "0", color: int = None, linetype: str = None):
        """
        Добавить эллипс (ELLIPSE) — только R2000+.
        major_axis_x, major_axis_y: вектор большой полуоси (от центра)
        ratio: отношение малой полуоси к большой (0..1)
        start_param, end_param: параметры начала и конца (0..2*pi для полного)
        """
        lines = [
            "  0", "ELLIPSE",
            "  5", self._next_handle(),
            "100", "AcDbEntity",
            "  8", layer,
        ]
        if color is not None:
            lines += ["  62", str(color)]
        if linetype:
            lines += ["  6", linetype]
        lines += [
            "100", "AcDbEllipse",
            " 10", f"{cx:.6f}",
            " 20", f"{cy:.6f}",
            " 30", f"{cz:.6f}",
            " 11", f"{major_axis_x:.6f}",
            " 21", f"{major_axis_y:.6f}",
            " 31", f"{major_axis_z:.6f}",
            " 40", f"{ratio:.6f}",
            " 41", f"{start_param:.6f}",
            " 42", f"{end_param:.6f}",
        ]
        self._entities.append("\n".join(lines))

    def add_lwpolyline(self, vertices: List[Tuple[float, float]],
                       closed: bool = False,
                       layer: str = "0", color: int = None, linetype: str = None):
        """
        Добавить легковесную полилинию (LWPOLYLINE) — только R2000+.
        vertices: список (x, y) вершин
        closed: замкнутая ли полилиния
        """
        flag = 1 if closed else 0
        lines = [
            "  0", "LWPOLYLINE",
            "  5", self._next_handle(),
            "100", "AcDbEntity",
            "  8", layer,
        ]
        if color is not None:
            lines += ["  62", str(color)]
        if linetype:
            lines += ["  6", linetype]
        lines += [
            "100", "AcDbPolyline",
            " 90", str(len(vertices)),
            " 70", str(flag),
        ]
        for vx, vy in vertices:
            lines += [
                " 10", f"{vx:.6f}",
                " 20", f"{vy:.6f}",
            ]
        self._entities.append("\n".join(lines))

    def add_spline(self, control_points: List[Tuple[float, float]],
                   degree: int = 3,
                   layer: str = "0", color: int = None, linetype: str = None):
        """
        Добавить сплайн (SPLINE) — только R2000+.
        Используется открытый (clamped) B-spline с узловым вектором.
        """
        n = len(control_points)
        if n < 2:
            return

        # Для degree > n-1, понижаем степень
        actual_degree = min(degree, n - 1)

        # Clamped knot vector: [0]*( degree+1) ... [1]*(degree+1)
        num_knots = n + actual_degree + 1
        knots = []
        for i in range(num_knots):
            if i <= actual_degree:
                knots.append(0.0)
            elif i >= num_knots - actual_degree - 1:
                knots.append(1.0)
            else:
                knots.append((i - actual_degree) / (num_knots - 2 * actual_degree - 1))

        # Flags: 8 = planar, 1024 = method (fit points vs control points)
        flag = 8  # planar spline

        lines = [
            "  0", "SPLINE",
            "  5", self._next_handle(),
            "100", "AcDbEntity",
            "  8", layer,
        ]
        if color is not None:
            lines += ["  62", str(color)]
        if linetype:
            lines += ["  6", linetype]
        lines += [
            "100", "AcDbSpline",
            " 70", str(flag),
            " 71", str(actual_degree),
            " 72", str(len(knots)),
            " 73", str(n),
            # Normal vector for planar spline
            "210", "0.0",
            "220", "0.0",
            "230", "1.0",
        ]
        # Knots
        for k in knots:
            lines += [" 40", f"{k:.6f}"]
        # Control points
        for px, py in control_points:
            lines += [
                " 10", f"{px:.6f}",
                " 20", f"{py:.6f}",
                " 30", "0.000000",
            ]
        self._entities.append("\n".join(lines))

    # ==================== Build DXF ====================

    def build(self) -> str:
        """Собрать полный DXF-файл и вернуть как строку"""
        sections = []

        # HEADER section
        sections.append(self._build_header())

        # TABLES section
        sections.append(self._build_tables())

        # BLOCKS section
        sections.append(self._build_blocks())

        # ENTITIES section
        sections.append(self._build_entities())

        # OBJECTS section (R2000 only)
        if self.version == "R2000":
            sections.append(self._build_objects())

        # EOF
        sections.append("  0\nEOF")

        return "\n".join(sections)

    def _build_header(self) -> str:
        """Секция HEADER — версия, единицы, система координат"""
        lines = [
            "  0", "SECTION",
            "  2", "HEADER",
            # DXF version
            "  9", "$ACADVER",
            "  1", self.ac_version,
            # Единицы измерения — миллиметры (4)
            "  9", "$INSUNITS",
            " 70", "4",
            # Measurement system: 1 = metric
            "  9", "$MEASUREMENT",
            " 70", "1",
            # WCS base point
            "  9", "$INSBASE",
            " 10", "0.0",
            " 20", "0.0",
            " 30", "0.0",
            # Drawing extents (min)
            "  9", "$EXTMIN",
            " 10", "0.0",
            " 20", "0.0",
            " 30", "0.0",
            # Drawing extents (max)
            "  9", "$EXTMAX",
            " 10", "1000.0",
            " 20", "1000.0",
            " 30", "0.0",
            "  0", "ENDSEC",
        ]
        return "\n".join(lines)

    def _build_tables(self) -> str:
        """Секция TABLES — типы линий, слои"""
        parts = [
            "  0", "SECTION",
            "  2", "TABLES",
        ]

        # VPORT table
        parts += self._build_vport_table()

        # LTYPE table (типы линий)
        parts += self._build_ltype_table()

        # LAYER table (слои)
        parts += self._build_layer_table()

        # STYLE table (text styles)
        parts += self._build_style_table()

        parts += [
            "  0", "ENDSEC",
        ]
        return "\n".join(parts)

    def _build_vport_table(self) -> List[str]:
        """Таблица VPORT"""
        return [
            "  0", "TABLE",
            "  2", "VPORT",
            "  5", self._next_handle(),
            " 70", "1",
            "  0", "VPORT",
            "  5", self._next_handle(),
            "  2", "*ACTIVE",
            " 70", "0",
            " 10", "0.0",
            " 20", "0.0",
            " 11", "1.0",
            " 21", "1.0",
            " 12", "500.0",
            " 22", "500.0",
            " 40", "1000.0",
            " 41", "1.6",
            "  0", "ENDTAB",
        ]

    def _build_ltype_table(self) -> List[str]:
        """Таблица LTYPE — определения типов линий"""
        # Стандартные + пользовательские
        all_linetypes = {
            "CONTINUOUS": ("Solid", []),
            "BYLAYER": ("", []),
            "BYBLOCK": ("", []),
        }
        # Добавляем типы линий, соответствующие ГОСТ
        all_linetypes["DASHED"] = ("Dashed __ __ __", [10.0, 5.0, -2.5])
        all_linetypes["DASHDOT"] = ("Dash dot __ . __", [12.0, 6.5, -1.5, 0.0, -1.5])
        all_linetypes["DASHDOTDOT"] = ("Dash dot dot __ . . __", [15.0, 6.5, -1.0, 0.0, -1.0, 0.0, -1.0])

        # Пользовательские
        for name, (desc, pattern) in self._linetypes.items():
            if name not in all_linetypes:
                total = sum(abs(v) for v in pattern) if pattern else 0
                all_linetypes[name] = (desc, [total] + pattern if pattern else [])

        num_entries = len(all_linetypes)
        lines = [
            "  0", "TABLE",
            "  2", "LTYPE",
            "  5", self._next_handle(),
            " 70", str(num_entries),
        ]

        for lt_name, (desc, pattern) in all_linetypes.items():
            lines += [
                "  0", "LTYPE",
                "  5", self._next_handle(),
                "  2", lt_name,
                " 70", "0",
                "  3", desc,
                " 72", "65",  # 'A' — alignment
            ]
            if not pattern:
                lines += [" 73", "0", " 40", "0.0"]
            else:
                total_length = pattern[0]
                elements = pattern[1:]
                lines += [
                    " 73", str(len(elements)),
                    " 40", f"{total_length:.6f}",
                ]
                for elem in elements:
                    lines += [" 49", f"{elem:.6f}"]

        lines += ["  0", "ENDTAB"]
        return lines

    def _build_layer_table(self) -> List[str]:
        """Таблица LAYER — определения слоёв"""
        # Всегда есть слой "0"
        all_layers = {"0": (7, "CONTINUOUS")}
        all_layers.update(self._layers)

        lines = [
            "  0", "TABLE",
            "  2", "LAYER",
            "  5", self._next_handle(),
            " 70", str(len(all_layers)),
        ]

        for layer_name, (aci_color, linetype) in all_layers.items():
            lines += [
                "  0", "LAYER",
                "  5", self._next_handle(),
                "  2", layer_name,
                " 70", "0",
                " 62", str(aci_color),
                "  6", linetype,
            ]

        lines += ["  0", "ENDTAB"]
        return lines

    def _build_style_table(self) -> List[str]:
        """Таблица STYLE (текстовые стили) — минимальная"""
        return [
            "  0", "TABLE",
            "  2", "STYLE",
            "  5", self._next_handle(),
            " 70", "1",
            "  0", "STYLE",
            "  5", self._next_handle(),
            "  2", "STANDARD",
            " 70", "0",
            " 40", "0.0",
            " 41", "1.0",
            " 50", "0.0",
            " 71", "0",
            "  3", "txt",
            "  0", "ENDTAB",
        ]

    def _build_blocks(self) -> str:
        """Секция BLOCKS — пустая (без блоков)"""
        lines = [
            "  0", "SECTION",
            "  2", "BLOCKS",
            # Model space block
            "  0", "BLOCK",
            "  5", self._next_handle(),
            "  8", "0",
            "  2", "*MODEL_SPACE",
            " 70", "0",
            " 10", "0.0",
            " 20", "0.0",
            " 30", "0.0",
            "  3", "*MODEL_SPACE",
            "  0", "ENDBLK",
            "  5", self._next_handle(),
            "  8", "0",
            # Paper space block
            "  0", "BLOCK",
            "  5", self._next_handle(),
            "  8", "0",
            "  2", "*PAPER_SPACE",
            " 70", "0",
            " 10", "0.0",
            " 20", "0.0",
            " 30", "0.0",
            "  3", "*PAPER_SPACE",
            "  0", "ENDBLK",
            "  5", self._next_handle(),
            "  8", "0",
            "  0", "ENDSEC",
        ]
        return "\n".join(lines)

    def _build_entities(self) -> str:
        """Секция ENTITIES — все геометрические объекты"""
        lines = ["  0", "SECTION", "  2", "ENTITIES"]
        for entity in self._entities:
            lines.append(entity)
        lines += ["  0", "ENDSEC"]
        return "\n".join(lines)

    def _build_objects(self) -> str:
        """Секция OBJECTS — словари (минимальная для R2000)"""
        lines = [
            "  0", "SECTION",
            "  2", "OBJECTS",
            "  0", "DICTIONARY",
            "  5", self._next_handle(),
            "100", "AcDbDictionary",
            "  0", "ENDSEC",
        ]
        return "\n".join(lines)

    def save(self, filepath: str):
        """Сохранить DXF-файл"""
        content = self.build()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)


class DXFExporter:
    """
    Высокоуровневый экспортёр примитивов приложения в DXF.
    Преобразует внутренние примитивы, стили и слои в DXF-формат.
    """

    def __init__(self, version: str = "R2000"):
        """
        Args:
            version: "R12" или "R2000"
        """
        self.version = version
        self.style_manager = StyleManager()

    def export(self, primitives: List[Primitive], filepath: str,
               version: str = None):
        """
        Экспортировать список примитивов в DXF-файл.

        Args:
            primitives: список примитивов для экспорта
            filepath: путь к выходному .dxf файлу
            version: версия DXF ("R12" или "R2000"), если None — используется из конструктора
        """
        ver = version or self.version
        writer = DXFWriter(version=ver)

        # Собираем все уникальные стили и создаём слои
        style_ids = set()
        for prim in primitives:
            if prim.visible:
                style_ids.add(prim.style_id)

        # Создаём слои на основе стилей
        for style_id in style_ids:
            style = self.style_manager.get_style(style_id)
            if style is None:
                continue
            layer_name = self._style_to_layer_name(style_id, style)
            aci_color = self._style_to_aci(style)
            dxf_linetype = LINETYPE_MAP.get(style_id, "CONTINUOUS")
            writer.add_layer(layer_name, aci_color, dxf_linetype)

        # Экспортируем каждый примитив
        for prim in primitives:
            if not prim.visible:
                continue
            self._export_primitive(writer, prim, ver)

        writer.save(filepath)

    def _style_to_layer_name(self, style_id: str, style: LineStyle) -> str:
        """Генерация имени слоя из стиля"""
        # Транслитерация и очистка для совместимости с AutoCAD
        name_map = {
            "solid_main": "GOST_Main",
            "solid_thin": "GOST_Thin",
            "solid_wavy": "GOST_Wavy",
            "dashed": "GOST_Dashed",
            "dash_dot_thin": "GOST_DashDotThin",
            "dash_dot_thick": "GOST_DashDotThick",
            "dash_dot_dot": "GOST_DashDotDot",
            "solid_zigzag": "GOST_Zigzag",
        }
        return name_map.get(style_id, f"Layer_{style_id}")

    def _style_to_aci(self, style: LineStyle) -> int:
        """Преобразование цвета стиля в ACI"""
        r, g, b = hex_to_rgb(style.color)
        return rgb_to_aci(r, g, b)

    def _get_entity_params(self, prim: Primitive) -> Dict[str, Any]:
        """Получить общие параметры DXF-сущности (слой, цвет, тип линии)"""
        style = self.style_manager.get_style(prim.style_id)
        if style is None:
            style = self.style_manager.get_style("solid_main")
        layer = self._style_to_layer_name(prim.style_id, style)
        aci = self._style_to_aci(style)
        linetype = LINETYPE_MAP.get(prim.style_id, "CONTINUOUS")
        return {"layer": layer, "color": aci, "linetype": linetype}

    def _export_primitive(self, writer: DXFWriter, prim: Primitive, version: str):
        """Экспортировать один примитив"""
        params = self._get_entity_params(prim)

        if isinstance(prim, Segment):
            self._export_segment(writer, prim, params)
        elif isinstance(prim, Circle):
            self._export_circle(writer, prim, params)
        elif isinstance(prim, Arc):
            self._export_arc(writer, prim, params)
        elif isinstance(prim, Ellipse):
            self._export_ellipse(writer, prim, params, version)
        elif isinstance(prim, Rectangle):
            self._export_rectangle(writer, prim, params, version)
        elif isinstance(prim, Polygon):
            self._export_polygon(writer, prim, params, version)
        elif isinstance(prim, Spline):
            self._export_spline(writer, prim, params, version)

    def _export_segment(self, writer: DXFWriter, seg: Segment, params: dict):
        """Экспорт отрезка → LINE"""
        writer.add_line(
            seg.x1, seg.y1, seg.x2, seg.y2,
            layer=params["layer"],
            color=params["color"],
            linetype=params["linetype"],
        )

    def _export_circle(self, writer: DXFWriter, circ: Circle, params: dict):
        """Экспорт окружности → CIRCLE"""
        writer.add_circle(
            circ.cx, circ.cy, circ.radius,
            layer=params["layer"],
            color=params["color"],
            linetype=params["linetype"],
        )

    def _export_arc(self, writer: DXFWriter, arc: Arc, params: dict):
        """
        Экспорт дуги → ARC.
        Преобразование из радиан в градусы.
        DXF использует углы в градусах, отсчёт от оси X CCW.
        """
        start_deg = math.degrees(arc.start_angle)
        end_deg = math.degrees(arc.end_angle)
        # Нормализация углов в диапазон [0, 360)
        start_deg = start_deg % 360
        end_deg = end_deg % 360
        writer.add_arc(
            arc.cx, arc.cy, arc.radius,
            start_deg, end_deg,
            layer=params["layer"],
            color=params["color"],
            linetype=params["linetype"],
        )

    def _export_ellipse(self, writer: DXFWriter, ell: Ellipse, params: dict, version: str):
        """
        Экспорт эллипса → ELLIPSE (R2000) или аппроксимация LWPOLYLINE (R12).

        DXF ELLIPSE задаётся:
        - центр (10, 20, 30)
        - вектор большой полуоси от центра (11, 21, 31)
        - ratio = minor/major (40)
        """
        if version == "R2000":
            # Вычисляем вектор большой полуоси с учётом вращения
            if ell.rx >= ell.ry:
                major_len = ell.rx
                ratio = ell.ry / ell.rx if ell.rx > 0 else 1.0
                major_angle = ell.rotation
            else:
                major_len = ell.ry
                ratio = ell.rx / ell.ry if ell.ry > 0 else 1.0
                major_angle = ell.rotation + math.pi / 2

            major_x = major_len * math.cos(major_angle)
            major_y = major_len * math.sin(major_angle)

            writer.add_ellipse(
                ell.cx, ell.cy,
                major_x, major_y,
                ratio,
                layer=params["layer"],
                color=params["color"],
                linetype=params["linetype"],
            )
        else:
            # R12: аппроксимация полилинией
            points = []
            num_pts = 72
            for i in range(num_pts):
                angle = 2 * math.pi * i / num_pts
                px, py = ell._get_point_on_ellipse(angle)
                points.append((px, py))
            writer.add_lwpolyline(
                points, closed=True,
                layer=params["layer"],
                color=params["color"],
                linetype=params["linetype"],
            )

    def _export_rectangle(self, writer: DXFWriter, rect: Rectangle, params: dict, version: str):
        """Экспорт прямоугольника → LWPOLYLINE (R2000) или 4 × LINE (R12)"""
        corners = rect._get_rotated_corners()

        if version == "R2000":
            writer.add_lwpolyline(
                corners, closed=True,
                layer=params["layer"],
                color=params["color"],
                linetype=params["linetype"],
            )
        else:
            # R12: 4 отдельных LINE
            for i in range(4):
                x1, y1 = corners[i]
                x2, y2 = corners[(i + 1) % 4]
                writer.add_line(
                    x1, y1, x2, y2,
                    layer=params["layer"],
                    color=params["color"],
                    linetype=params["linetype"],
                )

    def _export_polygon(self, writer: DXFWriter, poly: Polygon, params: dict, version: str):
        """Экспорт многоугольника → LWPOLYLINE (R2000) или N × LINE (R12)"""
        vertices = poly._get_vertices()

        if version == "R2000":
            writer.add_lwpolyline(
                vertices, closed=True,
                layer=params["layer"],
                color=params["color"],
                linetype=params["linetype"],
            )
        else:
            # R12: N отдельных LINE
            n = len(vertices)
            for i in range(n):
                x1, y1 = vertices[i]
                x2, y2 = vertices[(i + 1) % n]
                writer.add_line(
                    x1, y1, x2, y2,
                    layer=params["layer"],
                    color=params["color"],
                    linetype=params["linetype"],
                )

    def _export_spline(self, writer: DXFWriter, spl: Spline, params: dict, version: str):
        """
        Экспорт сплайна → SPLINE (R2000) или аппроксимация LWPOLYLINE (R12).
        """
        if len(spl.control_points) < 2:
            return

        if version == "R2000":
            writer.add_spline(
                spl.control_points,
                degree=3,
                layer=params["layer"],
                color=params["color"],
                linetype=params["linetype"],
            )
        else:
            # R12: аппроксимация кривыми точками как полилиния
            curve_points = spl._get_curve_points()
            writer.add_lwpolyline(
                curve_points, closed=False,
                layer=params["layer"],
                color=params["color"],
                linetype=params["linetype"],
            )
