"""
Base primitive class
Базовый класс геометрического примитива
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import uuid


class SnapType(Enum):
    """Типы привязок"""
    ENDPOINT = "endpoint"       # Конец
    MIDPOINT = "midpoint"       # Середина
    CENTER = "center"           # Центр
    INTERSECTION = "intersection"  # Пересечение
    PERPENDICULAR = "perpendicular"  # Перпендикуляр
    TANGENT = "tangent"         # Касательная
    QUADRANT = "quadrant"       # Квадрант (для окружностей)


@dataclass
class ControlPoint:
    """
    Control point for editing primitives
    Контрольная точка для редактирования примитивов
    """
    x: float
    y: float
    name: str                   # Название точки (для UI)
    index: int                  # Индекс точки в примитиве
    snap_types: List[SnapType]  # Типы привязок для этой точки


@dataclass 
class SnapPoint:
    """
    Snap point on a primitive
    Точка привязки на примитиве
    """
    x: float
    y: float
    snap_type: SnapType
    primitive_id: str


class Primitive(ABC):
    """
    Abstract base class for all geometric primitives
    Абстрактный базовый класс для всех геометрических примитивов
    """
    
    def __init__(self):
        self.id: str = str(uuid.uuid4())
        self.style_id: str = "solid_main"  # Default GOST style
        self.selected: bool = False
        self.visible: bool = True
        self.locked: bool = False
        self._canvas_ids: List[int] = []  # tkinter canvas item IDs
    
    @abstractmethod
    def get_type_name(self) -> str:
        """Get type name for UI display"""
        pass
    
    @abstractmethod
    def draw(self, canvas, transform, style_manager) -> List[int]:
        """
        Draw primitive on canvas
        Отрисовать примитив на холсте
        
        Args:
            canvas: tkinter Canvas
            transform: Transform object for coordinate conversion
            style_manager: StyleManager for line styles
        
        Returns:
            List of canvas item IDs
        """
        pass
    
    @abstractmethod
    def get_control_points(self) -> List[ControlPoint]:
        """
        Get control points for editing
        Получить контрольные точки для редактирования
        """
        pass
    
    @abstractmethod
    def move_control_point(self, index: int, new_x: float, new_y: float):
        """
        Move a control point
        Переместить контрольную точку
        """
        pass
    
    @abstractmethod
    def get_snap_points(self) -> List[SnapPoint]:
        """
        Get snap points for this primitive
        Получить точки привязки для этого примитива
        """
        pass
    
    @abstractmethod
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """
        Get bounding box (min_x, min_y, max_x, max_y)
        Получить ограничивающий прямоугольник
        """
        pass
    
    @abstractmethod
    def contains_point(self, x: float, y: float, tolerance: float = 5.0) -> bool:
        """
        Check if point is on or near the primitive
        Проверить, находится ли точка на примитиве или рядом с ним
        """
        pass
    
    @abstractmethod
    def get_properties(self) -> Dict[str, Any]:
        """
        Get properties for property panel
        Получить свойства для панели свойств
        """
        pass
    
    @abstractmethod
    def set_property(self, name: str, value: Any) -> bool:
        """
        Set a property value
        Установить значение свойства
        """
        pass
    
    def translate(self, dx: float, dy: float):
        """
        Move primitive by offset
        Переместить примитив на смещение
        """
        for cp in self.get_control_points():
            self.move_control_point(cp.index, cp.x + dx, cp.y + dy)
    
    def get_center(self) -> Tuple[float, float]:
        """
        Get center of primitive (center of bounding box by default)
        Получить центр примитива
        """
        x1, y1, x2, y2 = self.get_bounding_box()
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def clear_canvas_items(self, canvas):
        """Remove all canvas items for this primitive"""
        for item_id in self._canvas_ids:
            try:
                canvas.delete(item_id)
            except:
                pass
        self._canvas_ids.clear()
    
    def set_style(self, style_id: str):
        """Set line style"""
        self.style_id = style_id
    
    def select(self):
        """Select this primitive"""
        self.selected = True
    
    def deselect(self):
        """Deselect this primitive"""
        self.selected = False
    
    def toggle_selection(self):
        """Toggle selection state"""
        self.selected = not self.selected


class PrimitiveFactory:
    """
    Factory for creating primitives
    Фабрика для создания примитивов
    """
    
    _creators = {}
    
    @classmethod
    def register(cls, type_name: str, creator):
        """Register a primitive type"""
        cls._creators[type_name] = creator
    
    @classmethod
    def create(cls, type_name: str, **kwargs) -> Optional[Primitive]:
        """Create a primitive by type name"""
        if type_name not in cls._creators:
            return None
        return cls._creators[type_name](**kwargs)
    
    @classmethod
    def get_types(cls) -> List[str]:
        """Get all registered primitive types"""
        return list(cls._creators.keys())






