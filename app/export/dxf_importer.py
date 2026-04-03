"""
DXF Importer - импорт примитивов из формата DXF (AutoCAD Drawing Exchange Format)

Поддерживаемые версии: AC1009 (R12), AC1015 (R2000) и выше
Система координат: WCS (World Coordinate System), пересчёт из OCS при необходимости
Единицы измерения: миллиметры

Поддерживаемые примитивы:
    - LINE → Segment (отрезок)
    - CIRCLE → Circle (окружность)
    - ARC → Arc (дуга)
    - ELLIPSE → Ellipse (эллипс)
    - LWPOLYLINE → Polygon / Rectangle (многоугольник / прямоугольник)
    - POLYLINE + VERTEX → Polygon / Rectangle (старый формат)
    - SPLINE → Spline (сплайн)

Поддержка слоёв:
    - Чтение таблицы LAYER из секции TABLES
    - Привязка объектов к слоям через имя слоя
    - Извлечение цвета и типа линии слоя

Цвета и типы линий:
    - AutoCAD Color Index (ACI 1-255) → HEX
    - TrueColor (код 420) → HEX
    - Типы линий DXF → стили ГОСТ
"""

import math
import struct
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field

from ..primitives.segment import Segment
from ..primitives.circle import Circle
from ..primitives.arc import Arc
from ..primitives.ellipse import Ellipse
from ..primitives.polygon import Polygon, PolygonType
from ..primitives.rectangle import Rectangle
from ..primitives.spline import Spline
from ..primitives.base import Primitive
from ..styles.style_manager import StyleManager
from ..styles.line_style import LineStyle, LineType


# ============================================================
# Таблица ACI → RGB (первые 9 + основные)
# ============================================================
ACI_TO_RGB: Dict[int, Tuple[int, int, int]] = {
    1: (255, 0, 0),       # Red
    2: (255, 255, 0),     # Yellow
    3: (0, 255, 0),       # Green
    4: (0, 255, 255),     # Cyan
    5: (0, 0, 255),       # Blue
    6: (255, 0, 255),     # Magenta
    7: (255, 255, 255),   # White/Black
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


def aci_to_hex(aci: int) -> str:
    """Конвертация ACI в HEX цвет (#RRGGBB)"""
    if aci in ACI_TO_RGB:
        r, g, b = ACI_TO_RGB[aci]
    else:
        # Интерполяция для промежуточных ACI значений
        r, g, b = 0, 0, 0
    return f"#{r:02X}{g:02X}{b:02X}"


def truecolor_to_hex(truecolor: int) -> str:
    """Конвертация TrueColor (код 420) в HEX цвет"""
    r = (truecolor >> 16) & 0xFF
    g = (truecolor >> 8) & 0xFF
    b = truecolor & 0xFF
    return f"#{r:02X}{g:02X}{b:02X}"


# ============================================================
# Соответствие DXF linetype → ГОСТ стиль
# ============================================================
DXF_LINETYPE_TO_STYLE: Dict[str, str] = {
    "CONTINUOUS": "solid_main",
    "BYLAYER": "solid_main",
    "BYBLOCK": "solid_main",
    "DASHED": "dashed",
    "HIDDEN": "dashed",
    "HIDDEN2": "dashed",
    "DASHDOT": "dash_dot_thin",
    "CENTER": "dash_dot_thin",
    "CENTER2": "dash_dot_thin",
    "DASHDOTDOT": "dash_dot_dot",
    "DIVIDE": "dash_dot_dot",
    "DIVIDE2": "dash_dot_dot",
    "DOT": "dashed",
    "DOT2": "dashed",
    "PHANTOM": "dash_dot_dot",
    "PHANTOM2": "dash_dot_dot",
}


@dataclass
class DXFLayer:
    """Информация о слое DXF"""
    name: str
    color: int = 7          # ACI color
    linetype: str = "CONTINUOUS"
    frozen: bool = False
    off: bool = False


@dataclass
class DXFHeaderInfo:
    """Информация из секции HEADER"""
    version: str = "AC1009"
    insunits: int = 0       # 0=unitless, 1=inches, 4=mm, ...
    measurement: int = 0    # 0=English, 1=Metric
    extmin: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    extmax: Tuple[float, float, float] = (1000.0, 1000.0, 0.0)


@dataclass
class DXFEntity:
    """Разобранная DXF-сущность"""
    entity_type: str = ""
    layer: str = "0"
    color: Optional[int] = None        # ACI, код 62
    truecolor: Optional[int] = None    # TrueColor, код 420
    linetype: str = "BYLAYER"          # Код 6
    data: Dict[int, Any] = field(default_factory=dict)
    vertices: List[Tuple[float, float]] = field(default_factory=list)


class DXFReader:
    """
    Низкоуровневый парсер DXF-файлов.
    Разбирает текстовый (ASCII) DXF на секции и группы кодов.
    """

    def __init__(self):
        self.header = DXFHeaderInfo()
        self.layers: Dict[str, DXFLayer] = {}
        self.linetypes: Dict[str, str] = {}  # name -> description
        self.entities: List[DXFEntity] = []
        self.block_entities: List[DXFEntity] = []

    def read(self, filepath: str):
        """Прочитать и разобрать DXF-файл"""
        content = self._read_file(filepath)
        if content is None:
            raise ValueError(f"Не удалось прочитать файл: {filepath}")

        groups = self._parse_groups(content)
        self._parse_sections(groups)

    def _read_file(self, filepath: str) -> Optional[str]:
        """Чтение файла с определением формата (ASCII или двоичный)"""
        # Проверяем двоичный формат DXF
        try:
            with open(filepath, 'rb') as f:
                header = f.read(22)
                if header.startswith(b'AutoCAD Binary DXF\r\n\x1a\x00'):
                    # Двоичный DXF — конвертируем в текстовый формат
                    return self._read_binary_dxf(f, header)
        except Exception:
            pass

        # Текстовый (ASCII) формат
        encodings = ['utf-8', 'cp1251', 'latin-1', 'ascii']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise ValueError(f"Не удалось определить кодировку файла: {filepath}")

    def _read_binary_dxf(self, f, header: bytes) -> str:
        """Чтение двоичного DXF и конвертация в текстовый формат"""
        # Бинарный DXF: после заголовка (22 байта) идут пары (код, значение)
        # Код — 1 байт (unsigned) для кодов 0-254, или 2 байта для расширенных
        f.seek(22)
        raw = f.read()

        lines = []
        pos = 0
        while pos < len(raw):
            if pos + 1 > len(raw):
                break

            # Читаем код группы (1 байт, если < 255, иначе 2 байта)
            code_byte = raw[pos]
            pos += 1

            if code_byte == 255:
                if pos + 2 > len(raw):
                    break
                code = struct.unpack('<H', raw[pos:pos+2])[0]
                pos += 2
            else:
                code = code_byte

            # Определяем тип значения по коду группы
            value, pos = self._read_binary_value(raw, pos, code)
            if value is None:
                break

            lines.append(f"{code:3d}")
            lines.append(str(value))

        return "\n".join(lines)

    def _read_binary_value(self, raw: bytes, pos: int, code: int) -> Tuple[Any, int]:
        """Прочитать значение из двоичного DXF по коду группы"""
        try:
            if code in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 100, 102, 105):
                # Строковое значение: null-terminated
                end = raw.index(0, pos)
                value = raw[pos:end].decode('ascii', errors='replace')
                return value, end + 1
            elif 10 <= code <= 59:
                # Вещественное число (8 байт, double)
                if pos + 8 > len(raw):
                    return None, pos
                value = struct.unpack('<d', raw[pos:pos+8])[0]
                return value, pos + 8
            elif 60 <= code <= 79 or 90 <= code <= 99 or 170 <= code <= 175:
                # Целое число (2 байта, short)
                if pos + 2 > len(raw):
                    return None, pos
                value = struct.unpack('<h', raw[pos:pos+2])[0]
                return value, pos + 2
            elif 280 <= code <= 289:
                # Целое число (1 байт)
                if pos + 1 > len(raw):
                    return None, pos
                return raw[pos], pos + 1
            elif 300 <= code <= 369:
                # Строка
                end = raw.index(0, pos)
                value = raw[pos:end].decode('ascii', errors='replace')
                return value, end + 1
            elif 370 <= code <= 389 or 400 <= code <= 409:
                # Целое число (2 байта)
                if pos + 2 > len(raw):
                    return None, pos
                value = struct.unpack('<h', raw[pos:pos+2])[0]
                return value, pos + 2
            elif 410 <= code <= 419:
                # Строка
                end = raw.index(0, pos)
                value = raw[pos:end].decode('ascii', errors='replace')
                return value, end + 1
            elif 420 <= code <= 429:
                # Целое (4 байта) — TrueColor
                if pos + 4 > len(raw):
                    return None, pos
                value = struct.unpack('<i', raw[pos:pos+4])[0]
                return value, pos + 4
            elif 1000 <= code <= 1071:
                # Extended data — строки и числа
                if code in (1000, 1001, 1002, 1003, 1004, 1005):
                    end = raw.index(0, pos)
                    value = raw[pos:end].decode('ascii', errors='replace')
                    return value, end + 1
                elif code in (1010, 1020, 1030, 1040, 1041, 1042):
                    if pos + 8 > len(raw):
                        return None, pos
                    value = struct.unpack('<d', raw[pos:pos+8])[0]
                    return value, pos + 8
                elif code in (1070,):
                    if pos + 2 > len(raw):
                        return None, pos
                    value = struct.unpack('<h', raw[pos:pos+2])[0]
                    return value, pos + 2
                elif code in (1071,):
                    if pos + 4 > len(raw):
                        return None, pos
                    value = struct.unpack('<i', raw[pos:pos+4])[0]
                    return value, pos + 4
            else:
                # По умолчанию — строка
                end = raw.index(0, pos)
                value = raw[pos:end].decode('ascii', errors='replace')
                return value, end + 1
        except (ValueError, struct.error):
            return None, pos

        return None, pos

    def _parse_groups(self, content: str) -> List[Tuple[int, str]]:
        """Разобрать DXF-содержимое на пары (код группы, значение)"""
        groups = []
        lines = content.split('\n')
        i = 0
        while i < len(lines) - 1:
            code_line = lines[i].strip()
            value_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            try:
                code = int(code_line)
                groups.append((code, value_line))
            except ValueError:
                pass
            i += 2
        return groups

    def _parse_sections(self, groups: List[Tuple[int, str]]):
        """Разобрать секции DXF"""
        i = 0
        while i < len(groups):
            code, value = groups[i]
            if code == 0 and value == "SECTION":
                i += 1
                if i < len(groups):
                    sec_code, sec_name = groups[i]
                    if sec_code == 2:
                        i += 1
                        if sec_name == "HEADER":
                            i = self._parse_header(groups, i)
                        elif sec_name == "TABLES":
                            i = self._parse_tables(groups, i)
                        elif sec_name == "BLOCKS":
                            i = self._parse_blocks(groups, i)
                        elif sec_name == "ENTITIES":
                            i = self._parse_entities(groups, i)
                        else:
                            i = self._skip_section(groups, i)
                    else:
                        i += 1
                else:
                    break
            elif code == 0 and value == "EOF":
                break
            else:
                i += 1

    def _skip_section(self, groups: List[Tuple[int, str]], i: int) -> int:
        """Пропустить секцию до ENDSEC"""
        while i < len(groups):
            code, value = groups[i]
            if code == 0 and value == "ENDSEC":
                return i + 1
            i += 1
        return i

    def _parse_header(self, groups: List[Tuple[int, str]], i: int) -> int:
        """Разбор секции HEADER"""
        current_var = None
        while i < len(groups):
            code, value = groups[i]
            if code == 0 and value == "ENDSEC":
                return i + 1
            if code == 9:
                current_var = value
            elif current_var:
                if current_var == "$ACADVER" and code == 1:
                    self.header.version = value
                elif current_var == "$INSUNITS" and code == 70:
                    self.header.insunits = int(value)
                elif current_var == "$MEASUREMENT" and code == 70:
                    self.header.measurement = int(value)
                elif current_var == "$EXTMIN":
                    if code == 10:
                        self.header.extmin = (float(value), self.header.extmin[1], self.header.extmin[2])
                    elif code == 20:
                        self.header.extmin = (self.header.extmin[0], float(value), self.header.extmin[2])
                    elif code == 30:
                        self.header.extmin = (self.header.extmin[0], self.header.extmin[1], float(value))
                elif current_var == "$EXTMAX":
                    if code == 10:
                        self.header.extmax = (float(value), self.header.extmax[1], self.header.extmax[2])
                    elif code == 20:
                        self.header.extmax = (self.header.extmax[0], float(value), self.header.extmax[2])
                    elif code == 30:
                        self.header.extmax = (self.header.extmax[0], self.header.extmax[1], float(value))
            i += 1
        return i

    def _parse_tables(self, groups: List[Tuple[int, str]], i: int) -> int:
        """Разбор секции TABLES"""
        while i < len(groups):
            code, value = groups[i]
            if code == 0 and value == "ENDSEC":
                return i + 1
            if code == 0 and value == "TABLE":
                i += 1
                if i < len(groups):
                    _, table_name = groups[i]
                    i += 1
                    if table_name == "LAYER":
                        i = self._parse_layer_table(groups, i)
                    elif table_name == "LTYPE":
                        i = self._parse_ltype_table(groups, i)
                    else:
                        i = self._skip_table(groups, i)
                continue
            i += 1
        return i

    def _skip_table(self, groups: List[Tuple[int, str]], i: int) -> int:
        """Пропустить таблицу до ENDTAB"""
        while i < len(groups):
            code, value = groups[i]
            if code == 0 and value == "ENDTAB":
                return i + 1
            i += 1
        return i

    def _parse_layer_table(self, groups: List[Tuple[int, str]], i: int) -> int:
        """Разбор таблицы LAYER"""
        current_layer = None
        while i < len(groups):
            code, value = groups[i]
            if code == 0 and value == "ENDTAB":
                if current_layer:
                    self.layers[current_layer.name] = current_layer
                return i + 1
            if code == 0 and value == "LAYER":
                if current_layer:
                    self.layers[current_layer.name] = current_layer
                current_layer = DXFLayer(name="0")
            elif current_layer:
                if code == 2:
                    current_layer.name = value
                elif code == 62:
                    color_val = int(value)
                    if color_val < 0:
                        current_layer.off = True
                        current_layer.color = abs(color_val)
                    else:
                        current_layer.color = color_val
                elif code == 6:
                    current_layer.linetype = value.upper()
                elif code == 70:
                    flags = int(value)
                    current_layer.frozen = bool(flags & 1)
            i += 1
        return i

    def _parse_ltype_table(self, groups: List[Tuple[int, str]], i: int) -> int:
        """Разбор таблицы LTYPE"""
        current_name = None
        current_desc = ""
        while i < len(groups):
            code, value = groups[i]
            if code == 0 and value == "ENDTAB":
                if current_name:
                    self.linetypes[current_name] = current_desc
                return i + 1
            if code == 0 and value == "LTYPE":
                if current_name:
                    self.linetypes[current_name] = current_desc
                current_name = None
                current_desc = ""
            elif code == 2:
                current_name = value.upper()
            elif code == 3:
                current_desc = value
            i += 1
        return i

    def _parse_blocks(self, groups: List[Tuple[int, str]], i: int) -> int:
        """Разбор секции BLOCKS — извлекаем сущности из блоков"""
        while i < len(groups):
            code, value = groups[i]
            if code == 0 and value == "ENDSEC":
                return i + 1
            # Пропускаем определения блоков, но извлекаем сущности внутри
            if code == 0 and value in ("LINE", "CIRCLE", "ARC", "ELLIPSE",
                                        "LWPOLYLINE", "POLYLINE", "SPLINE"):
                entity, i = self._parse_one_entity(groups, i)
                if entity:
                    self.block_entities.append(entity)
                continue
            i += 1
        return i

    def _parse_entities(self, groups: List[Tuple[int, str]], i: int) -> int:
        """Разбор секции ENTITIES"""
        while i < len(groups):
            code, value = groups[i]
            if code == 0 and value == "ENDSEC":
                return i + 1
            if code == 0 and value in ("LINE", "CIRCLE", "ARC", "ELLIPSE",
                                        "LWPOLYLINE", "POLYLINE", "SPLINE",
                                        "POINT", "INSERT"):
                entity, i = self._parse_one_entity(groups, i)
                if entity:
                    self.entities.append(entity)
                continue
            i += 1
        return i

    def _parse_one_entity(self, groups: List[Tuple[int, str]], i: int) -> Tuple[Optional[DXFEntity], int]:
        """Разобрать одну DXF-сущность"""
        code, value = groups[i]
        entity = DXFEntity(entity_type=value)
        i += 1

        # Для POLYLINE нужно собирать VERTEX-ы до SEQEND
        if entity.entity_type == "POLYLINE":
            return self._parse_polyline(groups, i, entity)

        while i < len(groups):
            code, value = groups[i]
            if code == 0:
                # Начало новой сущности — прекращаем
                break
            self._apply_entity_code(entity, code, value)
            i += 1

        return entity, i

    def _parse_polyline(self, groups: List[Tuple[int, str]], i: int,
                        entity: DXFEntity) -> Tuple[Optional[DXFEntity], int]:
        """Разбор POLYLINE + VERTEX-ов до SEQEND"""
        # Считываем свойства POLYLINE
        while i < len(groups):
            code, value = groups[i]
            if code == 0:
                break
            self._apply_entity_code(entity, code, value)
            i += 1

        # Собираем VERTEX-ы
        while i < len(groups):
            code, value = groups[i]
            if code == 0 and value == "VERTEX":
                i += 1
                vx, vy = 0.0, 0.0
                while i < len(groups):
                    c, v = groups[i]
                    if c == 0:
                        break
                    if c == 10:
                        vx = float(v)
                    elif c == 20:
                        vy = float(v)
                    i += 1
                entity.vertices.append((vx, vy))
            elif code == 0 and value == "SEQEND":
                i += 1
                # Пропускаем атрибуты SEQEND
                while i < len(groups):
                    c, v = groups[i]
                    if c == 0:
                        break
                    i += 1
                break
            else:
                i += 1

        # Конвертируем POLYLINE в LWPOLYLINE-like формат
        entity.entity_type = "LWPOLYLINE"
        return entity, i

    def _apply_entity_code(self, entity: DXFEntity, code: int, value: str):
        """Применить код группы к сущности"""
        if code == 8:
            entity.layer = value
        elif code == 62:
            entity.color = int(value)
        elif code == 420:
            entity.truecolor = int(value)
        elif code == 6:
            entity.linetype = value.upper()
        else:
            # Для числовых кодов, связанных с координатами
            # Сохраняем как список для кодов, которые могут повторяться (10, 20, 30, 40 и т.д.)
            try:
                float_val = float(value)
                if code in entity.data:
                    existing = entity.data[code]
                    if isinstance(existing, list):
                        existing.append(float_val)
                    else:
                        entity.data[code] = [existing, float_val]
                else:
                    entity.data[code] = float_val
            except ValueError:
                entity.data[code] = value


def _get_float(data: Dict[int, Any], code: int, default: float = 0.0) -> float:
    """Безопасное извлечение float из данных сущности"""
    val = data.get(code, default)
    if isinstance(val, list):
        return float(val[0]) if val else default
    return float(val)


def _get_float_list(data: Dict[int, Any], code: int) -> List[float]:
    """Извлечение списка float из данных сущности"""
    val = data.get(code)
    if val is None:
        return []
    if isinstance(val, list):
        return [float(v) for v in val]
    return [float(val)]


def _get_int(data: Dict[int, Any], code: int, default: int = 0) -> int:
    """Безопасное извлечение int из данных сущности"""
    val = data.get(code, default)
    if isinstance(val, list):
        return int(val[0]) if val else default
    return int(val)


def _ocs_to_wcs(x: float, y: float, z: float,
                nx: float, ny: float, nz: float) -> Tuple[float, float, float]:
    """
    Преобразование из OCS (Object Coordinate System) в WCS.
    Используется алгоритм произвольной оси (Arbitrary Axis Algorithm) из спецификации DXF.
    """
    # Если нормаль близка к (0,0,1), OCS ≈ WCS
    if abs(nx) < 1e-6 and abs(ny) < 1e-6 and abs(nz - 1.0) < 1e-6:
        return x, y, z

    # Arbitrary Axis Algorithm
    threshold = 1.0 / 64.0
    if abs(nx) < threshold and abs(ny) < threshold:
        ax_x, ax_y, ax_z = _cross(0.0, 1.0, 0.0, nx, ny, nz)
    else:
        ax_x, ax_y, ax_z = _cross(0.0, 0.0, 1.0, nx, ny, nz)

    # Нормализация
    length = math.sqrt(ax_x**2 + ax_y**2 + ax_z**2)
    if length < 1e-12:
        return x, y, z
    ax_x /= length
    ax_y /= length
    ax_z /= length

    # Ось Y OCS
    ay_x, ay_y, ay_z = _cross(nx, ny, nz, ax_x, ax_y, ax_z)
    length = math.sqrt(ay_x**2 + ay_y**2 + ay_z**2)
    if length < 1e-12:
        return x, y, z
    ay_x /= length
    ay_y /= length
    ay_z /= length

    # Преобразование
    wx = x * ax_x + y * ay_x + z * nx
    wy = x * ax_y + y * ay_y + z * ny
    wz = x * ax_z + y * ay_z + z * nz

    return wx, wy, wz


def _cross(ax: float, ay: float, az: float,
           bx: float, by: float, bz: float) -> Tuple[float, float, float]:
    """Векторное произведение"""
    return (ay * bz - az * by,
            az * bx - ax * bz,
            ax * by - ay * bx)


class DXFImporter:
    """
    Высокоуровневый импортёр DXF-файлов.
    Преобразует DXF-сущности во внутренние примитивы приложения.
    """

    def __init__(self):
        self.style_manager = StyleManager()
        self._layer_style_map: Dict[str, str] = {}  # layer_name -> style_id
        self._import_stats = {
            "total_entities": 0,
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "by_type": {},
        }

    def import_file(self, filepath: str) -> Tuple[List[Primitive], Dict[str, Any]]:
        """
        Импортировать DXF-файл.

        Args:
            filepath: путь к .dxf файлу

        Returns:
            Кортеж (список примитивов, словарь со статистикой импорта)
        """
        reader = DXFReader()
        reader.read(filepath)

        # Создаём стили на основе слоёв
        self._create_styles_from_layers(reader.layers)

        # Импортируем сущности
        primitives = []

        all_entities = reader.entities + reader.block_entities
        self._import_stats["total_entities"] = len(all_entities)

        for entity in all_entities:
            try:
                prim = self._convert_entity(entity, reader.layers)
                if prim is not None:
                    primitives.append(prim)
                    self._import_stats["imported"] += 1
                    type_name = entity.entity_type
                    self._import_stats["by_type"][type_name] = \
                        self._import_stats["by_type"].get(type_name, 0) + 1
                else:
                    self._import_stats["skipped"] += 1
            except Exception:
                self._import_stats["errors"] += 1

        # Формируем информацию об импорте
        info = {
            "version": reader.header.version,
            "units": reader.header.insunits,
            "layers": len(reader.layers),
            "extmin": reader.header.extmin,
            "extmax": reader.header.extmax,
            **self._import_stats,
        }

        return primitives, info

    def _create_styles_from_layers(self, layers: Dict[str, DXFLayer]):
        """Создать стили линий на основе слоёв DXF"""
        for layer_name, layer in layers.items():
            # Определяем стиль по типу линии слоя
            style_id = DXF_LINETYPE_TO_STYLE.get(layer.linetype, "solid_main")

            # Определяем цвет
            hex_color = aci_to_hex(layer.color)

            # Если цвет чёрный (стандартный) — используем стандартный стиль
            if hex_color in ("#000000", "#FFFFFF", "#ffffff") and style_id in (
                "solid_main", "solid_thin", "dashed", "dash_dot_thin",
                "dash_dot_thick", "dash_dot_dot"
            ):
                self._layer_style_map[layer_name] = style_id
                continue

            # Создаём пользовательский стиль для нестандартного цвета
            custom_id = self.style_manager.create_custom_style(
                name=f"Слой: {layer_name}",
                base_style_id=style_id,
                color=hex_color
            )
            if custom_id:
                self._layer_style_map[layer_name] = custom_id
            else:
                self._layer_style_map[layer_name] = style_id

    def _resolve_style(self, entity: DXFEntity, layers: Dict[str, DXFLayer]) -> str:
        """Определить стиль линии для сущности"""
        # Приоритет: сущность → слой → по умолчанию

        # 1. Тип линии сущности (если задан явно)
        if entity.linetype and entity.linetype not in ("BYLAYER", "BYBLOCK"):
            style_from_linetype = DXF_LINETYPE_TO_STYLE.get(entity.linetype, None)
            if style_from_linetype:
                # Если у сущности также задан свой цвет
                if entity.color is not None or entity.truecolor is not None:
                    hex_color = self._resolve_color(entity, layers)
                    if hex_color not in ("#000000", "#FFFFFF"):
                        custom_id = self.style_manager.create_custom_style(
                            name=f"Импорт: {entity.entity_type}",
                            base_style_id=style_from_linetype,
                            color=hex_color
                        )
                        if custom_id:
                            return custom_id
                return style_from_linetype

        # 2. Стиль по слою
        if entity.layer in self._layer_style_map:
            base_style = self._layer_style_map[entity.layer]
        else:
            base_style = "solid_main"

        # 3. Если у сущности свой цвет — создаём стиль
        if entity.color is not None or entity.truecolor is not None:
            hex_color = self._resolve_color(entity, layers)
            if hex_color not in ("#000000", "#FFFFFF"):
                custom_id = self.style_manager.create_custom_style(
                    name=f"Импорт: {entity.entity_type}",
                    base_style_id=base_style,
                    color=hex_color
                )
                if custom_id:
                    return custom_id

        return base_style

    def _resolve_color(self, entity: DXFEntity, layers: Dict[str, DXFLayer]) -> str:
        """Определить цвет сущности"""
        # TrueColor имеет приоритет
        if entity.truecolor is not None:
            return truecolor_to_hex(entity.truecolor)

        # ACI цвет сущности
        if entity.color is not None:
            if entity.color == 256:  # BYLAYER
                layer = layers.get(entity.layer)
                if layer:
                    return aci_to_hex(layer.color)
            elif entity.color == 0:  # BYBLOCK
                return "#000000"
            else:
                return aci_to_hex(entity.color)

        # Цвет по слою
        layer = layers.get(entity.layer)
        if layer:
            return aci_to_hex(layer.color)

        return "#000000"

    def _convert_entity(self, entity: DXFEntity,
                        layers: Dict[str, DXFLayer]) -> Optional[Primitive]:
        """Конвертировать DXF-сущность в примитив приложения"""
        # Получаем OCS-нормаль (коды 210, 220, 230)
        nx = _get_float(entity.data, 210, 0.0)
        ny = _get_float(entity.data, 220, 0.0)
        nz = _get_float(entity.data, 230, 1.0)

        converters = {
            "LINE": self._convert_line,
            "CIRCLE": self._convert_circle,
            "ARC": self._convert_arc,
            "ELLIPSE": self._convert_ellipse,
            "LWPOLYLINE": self._convert_lwpolyline,
            "SPLINE": self._convert_spline,
        }

        converter = converters.get(entity.entity_type)
        if converter is None:
            return None

        prim = converter(entity, nx, ny, nz)
        if prim is not None:
            style_id = self._resolve_style(entity, layers)
            prim.style_id = style_id

        return prim

    def _convert_line(self, entity: DXFEntity,
                      nx: float, ny: float, nz: float) -> Optional[Primitive]:
        """LINE → Segment"""
        x1 = _get_float(entity.data, 10)
        y1 = _get_float(entity.data, 20)
        z1 = _get_float(entity.data, 30)
        x2 = _get_float(entity.data, 11)
        y2 = _get_float(entity.data, 21)
        z2 = _get_float(entity.data, 31)

        # OCS → WCS
        wx1, wy1, _ = _ocs_to_wcs(x1, y1, z1, nx, ny, nz)
        wx2, wy2, _ = _ocs_to_wcs(x2, y2, z2, nx, ny, nz)

        return Segment(wx1, wy1, wx2, wy2)

    def _convert_circle(self, entity: DXFEntity,
                        nx: float, ny: float, nz: float) -> Optional[Primitive]:
        """CIRCLE → Circle"""
        cx = _get_float(entity.data, 10)
        cy = _get_float(entity.data, 20)
        cz = _get_float(entity.data, 30)
        radius = _get_float(entity.data, 40)

        if radius <= 0:
            return None

        # OCS → WCS
        wcx, wcy, _ = _ocs_to_wcs(cx, cy, cz, nx, ny, nz)

        return Circle(wcx, wcy, radius)

    def _convert_arc(self, entity: DXFEntity,
                     nx: float, ny: float, nz: float) -> Optional[Primitive]:
        """ARC → Arc"""
        cx = _get_float(entity.data, 10)
        cy = _get_float(entity.data, 20)
        cz = _get_float(entity.data, 30)
        radius = _get_float(entity.data, 40)
        start_deg = _get_float(entity.data, 50)
        end_deg = _get_float(entity.data, 51)

        if radius <= 0:
            return None

        # OCS → WCS
        wcx, wcy, _ = _ocs_to_wcs(cx, cy, cz, nx, ny, nz)

        # DXF углы в градусах → радианы
        start_rad = math.radians(start_deg)
        end_rad = math.radians(end_deg)

        return Arc(wcx, wcy, radius, start_rad, end_rad)

    def _convert_ellipse(self, entity: DXFEntity,
                         nx: float, ny: float, nz: float) -> Optional[Primitive]:
        """ELLIPSE → Ellipse"""
        # Центр
        cx = _get_float(entity.data, 10)
        cy = _get_float(entity.data, 20)
        cz = _get_float(entity.data, 30)

        # Вектор большой полуоси (от центра)
        major_x = _get_float(entity.data, 11)
        major_y = _get_float(entity.data, 21)

        # Отношение малой/большой оси
        ratio = _get_float(entity.data, 40, 1.0)

        if ratio <= 0:
            ratio = 1.0

        # OCS → WCS для центра
        wcx, wcy, _ = _ocs_to_wcs(cx, cy, cz, nx, ny, nz)

        # Длина большой полуоси
        major_len = math.sqrt(major_x**2 + major_y**2)
        if major_len < 1e-12:
            return None

        # Угол вращения
        rotation = math.atan2(major_y, major_x)

        # Полуоси
        rx = major_len
        ry = major_len * ratio

        return Ellipse(wcx, wcy, rx, ry, rotation)

    def _convert_lwpolyline(self, entity: DXFEntity,
                            nx: float, ny: float, nz: float) -> Optional[Primitive]:
        """
        LWPOLYLINE → Rectangle или Polygon.
        Анализируем количество вершин и форму для определения типа.
        """
        # Собираем вершины
        vertices = []

        # Для LWPOLYLINE вершины хранятся как повторяющиеся коды 10/20
        x_list = _get_float_list(entity.data, 10)
        y_list = _get_float_list(entity.data, 20)

        # Если вершины уже собраны (из POLYLINE)
        if entity.vertices:
            for vx, vy in entity.vertices:
                wx, wy, _ = _ocs_to_wcs(vx, vy, 0.0, nx, ny, nz)
                vertices.append((wx, wy))
        elif x_list and y_list:
            count = min(len(x_list), len(y_list))
            for idx in range(count):
                vx = x_list[idx]
                vy = y_list[idx]
                wx, wy, _ = _ocs_to_wcs(vx, vy, 0.0, nx, ny, nz)
                vertices.append((wx, wy))

        if len(vertices) < 3:
            # Если 2 вершины — это отрезок
            if len(vertices) == 2:
                return Segment(vertices[0][0], vertices[0][1],
                               vertices[1][0], vertices[1][1])
            return None

        closed = bool(_get_int(entity.data, 70) & 1)

        # Пробуем определить прямоугольник (4 вершины, прямые углы)
        if len(vertices) == 4 and closed:
            rect = self._try_as_rectangle(vertices)
            if rect is not None:
                return rect

        # Пробуем определить правильный многоугольник
        poly = self._try_as_polygon(vertices, closed)
        if poly is not None:
            return poly

        # Если не удалось — создаём как набор отрезков
        return self._polyline_to_segments_or_polygon(vertices, closed)

    def _try_as_rectangle(self, vertices: List[Tuple[float, float]]) -> Optional[Rectangle]:
        """Попытка распознать 4 вершины как прямоугольник"""
        if len(vertices) != 4:
            return None

        # Проверяем прямые углы
        for i in range(4):
            p0 = vertices[i]
            p1 = vertices[(i + 1) % 4]
            p2 = vertices[(i + 2) % 4]

            dx1 = p1[0] - p0[0]
            dy1 = p1[1] - p0[1]
            dx2 = p2[0] - p1[0]
            dy2 = p2[1] - p1[1]

            dot = dx1 * dx2 + dy1 * dy2
            len1 = math.sqrt(dx1**2 + dy1**2)
            len2 = math.sqrt(dx2**2 + dy2**2)

            if len1 < 1e-6 or len2 < 1e-6:
                return None

            # Cos угла должен быть ~0 (прямой угол)
            cos_angle = dot / (len1 * len2)
            if abs(cos_angle) > 0.01:  # Допуск ~0.6°
                return None

        # Это прямоугольник. Определяем параметры.
        p0, p1, p2, p3 = vertices

        # Ширина — расстояние p0→p1
        width = math.sqrt((p1[0] - p0[0])**2 + (p1[1] - p0[1])**2)
        # Высота — расстояние p1→p2
        height = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        # Угол вращения — угол первой стороны
        rotation = math.atan2(p1[1] - p0[1], p1[0] - p0[0])

        # Находим угол, ближайший к началу координат (минимальный x, y с учётом вращения)
        # Для простоты берём p0 как начальную точку
        return Rectangle(p0[0], p0[1], width, height, corner_radius=0, rotation=rotation)

    def _try_as_polygon(self, vertices: List[Tuple[float, float]],
                        closed: bool) -> Optional[Polygon]:
        """Попытка распознать вершины как правильный многоугольник"""
        if not closed or len(vertices) < 3:
            return None

        n = len(vertices)

        # Вычисляем центр
        cx = sum(v[0] for v in vertices) / n
        cy = sum(v[1] for v in vertices) / n

        # Расстояния до центра
        distances = [math.sqrt((v[0] - cx)**2 + (v[1] - cy)**2) for v in vertices]

        # Проверяем, что все расстояния примерно равны (правильный многоугольник)
        avg_dist = sum(distances) / n
        if avg_dist < 1e-6:
            return None

        max_deviation = max(abs(d - avg_dist) / avg_dist for d in distances)
        if max_deviation > 0.02:  # Допуск 2%
            return None

        # Проверяем равные углы между соседними вершинами
        angles = []
        for i in range(n):
            angle = math.atan2(vertices[i][1] - cy, vertices[i][0] - cx)
            angles.append(angle)

        # Сортируем углы и проверяем равномерность
        angles_sorted = sorted(angles)
        diffs = []
        for i in range(n):
            diff = angles_sorted[(i + 1) % n] - angles_sorted[i]
            if diff < 0:
                diff += 2 * math.pi
            diffs.append(diff)

        expected_diff = 2 * math.pi / n
        for diff in diffs:
            if abs(diff - expected_diff) / expected_diff > 0.05:  # Допуск 5%
                return None

        # Это правильный многоугольник
        rotation = math.atan2(vertices[0][1] - cy, vertices[0][0] - cx)

        return Polygon(cx, cy, avg_dist, n, PolygonType.INSCRIBED, rotation)

    def _polyline_to_segments_or_polygon(self, vertices: List[Tuple[float, float]],
                                          closed: bool) -> Optional[Primitive]:
        """
        Если полилиния не правильный многоугольник и не прямоугольник —
        создаём Polygon с вписанным типом (приближение) или Spline.
        """
        n = len(vertices)

        # Для замкнутых полилиний — используем многоугольник с центром и средним радиусом
        if closed and n >= 3:
            cx = sum(v[0] for v in vertices) / n
            cy = sum(v[1] for v in vertices) / n
            avg_r = sum(math.sqrt((v[0]-cx)**2 + (v[1]-cy)**2) for v in vertices) / n
            rotation = math.atan2(vertices[0][1] - cy, vertices[0][0] - cx)
            return Polygon(cx, cy, avg_r, n, PolygonType.INSCRIBED, rotation)

        # Для незамкнутых — сплайн через точки
        if n >= 2:
            return Spline(control_points=vertices)

        return None

    def _convert_spline(self, entity: DXFEntity,
                        nx: float, ny: float, nz: float) -> Optional[Primitive]:
        """SPLINE → Spline"""
        # Контрольные точки (коды 10/20)
        x_list = _get_float_list(entity.data, 10)
        y_list = _get_float_list(entity.data, 20)

        if not x_list or not y_list:
            return None

        count = min(len(x_list), len(y_list))
        if count < 2:
            return None

        control_points = []
        for idx in range(count):
            vx = x_list[idx]
            vy = y_list[idx]
            wx, wy, _ = _ocs_to_wcs(vx, vy, 0.0, nx, ny, nz)
            control_points.append((wx, wy))

        return Spline(control_points=control_points)
