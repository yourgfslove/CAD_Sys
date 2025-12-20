"""
Coordinate system utilities
Утилиты для работы с системами координат
"""

import math
from typing import Tuple
from enum import Enum


class CoordinateSystem(Enum):
    """Coordinate system type"""
    CARTESIAN = "cartesian"
    POLAR = "polar"


class AngleUnit(Enum):
    """Angle unit"""
    DEGREES = "degrees"
    RADIANS = "radians"


def cartesian_to_polar(x: float, y: float) -> Tuple[float, float]:
    """
    Convert Cartesian coordinates to polar
    Преобразовать декартовы координаты в полярные
    
    Returns:
        (r, theta) where r is distance, theta is angle in radians
    """
    r = math.sqrt(x * x + y * y)
    theta = math.atan2(y, x)
    return (r, theta)


def polar_to_cartesian(r: float, theta: float) -> Tuple[float, float]:
    """
    Convert polar coordinates to Cartesian
    Преобразовать полярные координаты в декартовы
    
    Args:
        r: Distance from origin
        theta: Angle in radians
    
    Returns:
        (x, y) Cartesian coordinates
    """
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    return (x, y)


class Transform:
    """
    2D transformation matrix
    
    Matrix form:
    [ a  b  tx ]
    [ c  d  ty ]
    [ 0  0  1  ]
    
    Transformation: x' = a*x + b*y + tx, y' = c*x + d*y + ty
    """
    
    def __init__(self):
        self.a: float = 1.0  # Scale X
        self.b: float = 0.0  # Skew Y
        self.c: float = 0.0  # Skew X
        self.d: float = 1.0  # Scale Y
        self.tx: float = 0.0  # Translation X
        self.ty: float = 0.0  # Translation Y
    
    def reset(self):
        """Reset to identity matrix"""
        self.a = 1.0
        self.b = 0.0
        self.c = 0.0
        self.d = 1.0
        self.tx = 0.0
        self.ty = 0.0
    
    def translate(self, dx: float, dy: float):
        """Translate by offset"""
        self.tx += self.a * dx + self.b * dy
        self.ty += self.c * dx + self.d * dy
    
    def scale(self, sx: float, sy: float = None, cx: float = 0, cy: float = 0):
        """Scale around center point"""
        if sy is None:
            sy = sx
        
        self.translate(-cx, -cy)
        self.a *= sx
        self.b *= sy
        self.c *= sx
        self.d *= sy
        self.translate(cx, cy)
    
    def rotate(self, angle: float, cx: float = 0, cy: float = 0):
        """Rotate around center point"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        self.translate(-cx, -cy)
        
        new_a = self.a * cos_a - self.c * sin_a
        new_b = self.b * cos_a - self.d * sin_a
        new_c = self.a * sin_a + self.c * cos_a
        new_d = self.b * sin_a + self.d * cos_a
        
        self.a = new_a
        self.b = new_b
        self.c = new_c
        self.d = new_d
        
        self.translate(cx, cy)
    
    def transform_point(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transform point from world to screen coordinates
        Преобразовать точку из мировых координат в экранные
        """
        tx = self.a * x + self.b * y + self.tx
        ty = self.c * x + self.d * y + self.ty
        return (tx, ty)
    
    def inverse_transform_point(self, x: float, y: float) -> Tuple[float, float]:
        """
        Inverse transform point from screen to world coordinates
        Обратное преобразование точки из экранных координат в мировые
        """
        # Calculate inverse matrix determinant
        det = self.a * self.d - self.b * self.c
        
        if abs(det) < 1e-10:
            # Singular matrix, return identity
            return (x, y)
        
        inv_det = 1.0 / det
        
        # Inverse matrix
        inv_a = self.d * inv_det
        inv_b = -self.b * inv_det
        inv_c = -self.c * inv_det
        inv_d = self.a * inv_det
        
        # Transform
        wx = inv_a * (x - self.tx) + inv_b * (y - self.ty)
        wy = inv_c * (x - self.tx) + inv_d * (y - self.ty)
        
        return (wx, wy)
    
    def get_scale(self) -> float:
        """
        Get approximate scale factor
        Получить приблизительный масштаб
        """
        # Average of X and Y scale
        scale_x = math.sqrt(self.a * self.a + self.c * self.c)
        scale_y = math.sqrt(self.b * self.b + self.d * self.d)
        return (scale_x + scale_y) / 2.0






