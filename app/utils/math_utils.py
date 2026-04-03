"""
Mathematical utilities for geometry
Математические утилиты для геометрии
"""

import math
from typing import Tuple, List, Optional


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate distance between two points"""
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def midpoint(p1: Tuple[float, float], p2: Tuple[float, float]) -> Tuple[float, float]:
    """Calculate midpoint between two points"""
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def angle_between_points(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate angle from p1 to p2"""
    return math.atan2(p2[1] - p1[1], p2[0] - p1[0])


def degrees_to_radians(degrees: float) -> float:
    """Convert degrees to radians"""
    return math.radians(degrees)


def radians_to_degrees(radians: float) -> float:
    """Convert radians to degrees"""
    return math.degrees(radians)


def rotate_point(point: Tuple[float, float], center: Tuple[float, float], angle: float) -> Tuple[float, float]:
    """Rotate point around center by angle (in radians)"""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    new_x = dx * cos_a - dy * sin_a
    new_y = dx * sin_a + dy * cos_a
    return (new_x + center[0], new_y + center[1])


def scale_point(point: Tuple[float, float], center: Tuple[float, float], scale: float) -> Tuple[float, float]:
    """Scale point relative to center"""
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    return (center[0] + dx * scale, center[1] + dy * scale)


def line_intersection(p1: Tuple[float, float], p2: Tuple[float, float],
                     p3: Tuple[float, float], p4: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    """
    Find intersection point of two line segments
    Returns None if lines are parallel or don't intersect
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    
    x = x1 + t * (x2 - x1)
    y = y1 + t * (y2 - y1)
    
    return (x, y)


def point_on_segment(point: Tuple[float, float], seg_start: Tuple[float, float],
                     seg_end: Tuple[float, float], tolerance: float = 1e-6) -> bool:
    """Check if point is on line segment"""
    d1 = distance(seg_start, point)
    d2 = distance(point, seg_end)
    d3 = distance(seg_start, seg_end)
    return abs(d1 + d2 - d3) < tolerance


def perpendicular_point(point: Tuple[float, float], line_start: Tuple[float, float],
                       line_end: Tuple[float, float]) -> Tuple[float, float]:
    """Find point on line perpendicular to given point"""
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return line_start
    t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    return (x1 + t * dx, y1 + t * dy)


def point_to_line_distance(point: Tuple[float, float], line_start: Tuple[float, float],
                           line_end: Tuple[float, float]) -> float:
    """Calculate distance from point to line"""
    perp = perpendicular_point(point, line_start, line_end)
    return distance(point, perp)


def normalize_angle(angle: float) -> float:
    """Normalize angle to [0, 2π) range"""
    while angle < 0:
        angle += 2 * math.pi
    while angle >= 2 * math.pi:
        angle -= 2 * math.pi
    return angle


def snap_angle(angle: float, snap_degrees: float = 90) -> float:
    """Snap angle to nearest multiple of snap_degrees"""
    snap_rad = math.radians(snap_degrees)
    return round(angle / snap_rad) * snap_rad


def bezier_point(t: float, points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Calculate point on Bezier curve at parameter t [0, 1]"""
    n = len(points) - 1
    x = 0
    y = 0
    for i, (px, py) in enumerate(points):
        coef = math.comb(n, i) * (1 - t) ** (n - i) * t ** i
        x += coef * px
        y += coef * py
    return (x, y)


def catmull_rom_spline(points: List[Tuple[float, float]], num_segments: int = 20) -> List[Tuple[float, float]]:
    """Generate Catmull-Rom spline through points"""
    if len(points) < 2:
        return points
    
    result = []
    pts = [points[0]] + points + [points[-1]]
    
    for i in range(1, len(pts) - 2):
        p0 = pts[i - 1]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2]
        
        for j in range(num_segments):
            t = j / num_segments
            t2 = t * t
            t3 = t2 * t
            
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t +
                      (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                      (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t +
                      (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                      (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            
            result.append((x, y))
    
    result.append(points[-1])
    return result








