"""
Line styles according to GOST 2.303-68
Стили линий по ГОСТ 2.303-68
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum
import copy


class LineType(Enum):
    """Типы линий по ГОСТ 2.303-68"""
    SOLID_MAIN = "solid_main"
    SOLID_THIN = "solid_thin"
    SOLID_WAVY = "solid_wavy"
    DASHED = "dashed"
    DASH_DOT_THIN = "dash_dot_thin"
    DASH_DOT_THICK = "dash_dot_thick"
    DASH_DOT_DOT = "dash_dot_dot"
    SOLID_THIN_ZIGZAG = "solid_zigzag"


@dataclass
class LineStyle:
    """Line style with GOST parameters"""
    name: str
    line_type: LineType
    thickness: float = 0.8
    color: str = "#000000"
    dash_pattern: List[float] = field(default_factory=list)
    dash_length: float = 5.0
    gap_length: float = 2.0
    # Zigzag parameters (for SOLID_THIN_ZIGZAG) - GOST style
    zigzag_amplitude: float = 4.0      # Амплитуда - высота пика излома (mm)
    zigzag_width: float = 6.0          # Ширина излома - ширина одного зигзага (mm)
    zigzag_gap: float = 8.0            # Промежуток - расстояние между изломами (mm)
    zigzag_protrusion: float = 2.0     # Выступ - длина перпендикулярного сегмента (mm)
    zigzag_angle: float = 60.0         # Угол наклона излома (degrees)
    # Legacy parameters (for compatibility)
    zigzag_length: float = 10.0        # Deprecated, use zigzag_width + zigzag_gap
    zigzag_height: float = 4.0         # Deprecated, use zigzag_amplitude
    # Wavy parameters (for SOLID_WAVY)
    wavy_length: float = 15.0          # Wave length (mm)
    wavy_height: float = 3.0           # Wave amplitude (mm)
    is_system: bool = False
    
    def get_tkinter_dash(self, scale: float = 1.0) -> Tuple:
        """Convert dash pattern to tkinter format"""
        if not self.dash_pattern:
            return ()
        px_per_mm = 3.78
        return tuple((int(d * px_per_mm * scale) for d in self.dash_pattern))
    
    def get_thickness_px(self, base_thickness: float = None) -> float:
        """Get thickness in pixels"""
        if base_thickness is None:
            base_thickness = self.thickness
        return max(1, base_thickness * 3.78)
    
    def copy(self) -> "LineStyle":
        """Create a copy of this style"""
        return copy.deepcopy(self)


GOST_STYLES = {
    "solid_main": LineStyle(
        name="Сплошная основная",
        line_type=LineType.SOLID_MAIN,
        thickness=0.8,
        color="#000000",
        dash_pattern=[],
        is_system=True
    ),
    "solid_thin": LineStyle(
        name="Сплошная тонкая",
        line_type=LineType.SOLID_THIN,
        thickness=0.4,
        color="#000000",
        dash_pattern=[],
        is_system=True
    ),
    "solid_wavy": LineStyle(
        name="Сплошная волнистая",
        line_type=LineType.SOLID_WAVY,
        thickness=0.4,
        color="#000000",
        dash_pattern=[],
        wavy_length=15.0,
        wavy_height=3.0,
        is_system=True
    ),
    "dashed": LineStyle(
        name="Штриховая",
        line_type=LineType.DASHED,
        thickness=0.4,
        color="#000000",
        dash_pattern=[5.0, 2.0],
        dash_length=5.0,
        gap_length=2.0,
        is_system=True
    ),
    "dash_dot_thin": LineStyle(
        name="Штрихпунктирная тонкая",
        line_type=LineType.DASH_DOT_THIN,
        thickness=0.4,
        color="#000000",
        dash_pattern=[12.0, 3.0, 1.0, 3.0],
        dash_length=12.0,
        gap_length=3.0,
        is_system=True
    ),
    "dash_dot_thick": LineStyle(
        name="Штрихпунктирная утолщенная",
        line_type=LineType.DASH_DOT_THICK,
        thickness=0.8,
        color="#000000",
        dash_pattern=[12.0, 3.0, 1.0, 3.0],
        dash_length=12.0,
        gap_length=3.0,
        is_system=True
    ),
    "dash_dot_dot": LineStyle(
        name="Штрихпунктирная с двумя точками",
        line_type=LineType.DASH_DOT_DOT,
        thickness=0.4,
        color="#000000",
        dash_pattern=[12.0, 2.0, 1.0, 2.0, 1.0, 2.0],
        dash_length=12.0,
        gap_length=2.0,
        is_system=True
    ),
    "solid_zigzag": LineStyle(
        name="Сплошная тонкая с изломами",
        line_type=LineType.SOLID_THIN_ZIGZAG,
        thickness=0.4,
        color="#000000",
        dash_pattern=[],
        zigzag_amplitude=4.0,
        zigzag_width=6.0,
        zigzag_gap=8.0,
        zigzag_protrusion=2.0,
        is_system=True
    ),
}


def get_standard_thicknesses() -> List[float]:
    """Get standard line thicknesses according to GOST"""
    return [0.25, 0.35, 0.5, 0.7, 0.8, 1.0, 1.4]


def get_thin_thickness(main_thickness: float) -> float:
    """Get thin line thickness from main thickness"""
    return main_thickness / 2
