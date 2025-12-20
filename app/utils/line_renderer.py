"""
Line rendering utilities for zigzag and wavy lines
Утилиты для отрисовки линий с изломами и волнами
"""

import math
from typing import List, Tuple


def apply_zigzag_to_points(points: List[Tuple[float, float]], 
                           wave_length: float = 10.0, 
                           wave_height: float = 4.0) -> List[float]:
    """
    Apply zigzag pattern to a sequence of points
    Применить зигзагообразный узор к последовательности точек
    """
    if len(points) < 2:
        return []
    
    result = []
    
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1:
            result.extend([p1[0], p1[1]])
            if i == len(points) - 2:
                result.extend([p2[0], p2[1]])
            continue
        
        ux = dx / length
        uy = dy / length
        px = -uy
        py = ux
        
        num_segments = max(1, int(length / wave_length))
        segment_length = length / num_segments
        
        for j in range(num_segments + 1):
            t = j / num_segments if num_segments > 0 else 0
            base_x = p1[0] + dx * t
            base_y = p1[1] + dy * t
            
            if j == 0 or j == num_segments:
                result.extend([base_x, base_y])
            else:
                sign = 1 if j % 2 == 0 else -1
                peak_x = base_x + px * wave_height * sign
                peak_y = base_y + py * wave_height * sign
                result.extend([peak_x, peak_y])
    
    return result


def apply_wavy_to_points(points: List[Tuple[float, float]], 
                         wave_length: float = 15.0, 
                         wave_height: float = 3.0,
                         num_samples: int = 50) -> List[float]:
    """
    Apply wavy pattern to a sequence of points
    Применить волнистый узор к последовательности точек
    """
    if len(points) < 2:
        return []
    
    result = []
    
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1:
            result.extend([p1[0], p1[1]])
            if i == len(points) - 2:
                result.extend([p2[0], p2[1]])
            continue
        
        ux = dx / length
        uy = dy / length
        px = -uy
        py = ux
        
        samples = max(2, int(num_samples * length / 100))
        
        for j in range(samples + 1):
            t = j / samples
            base_x = p1[0] + dx * t
            base_y = p1[1] + dy * t
            
            phase = t * length / wave_length * 2 * math.pi
            offset = math.sin(phase) * wave_height
            
            wave_x = base_x + px * offset
            wave_y = base_y + py * offset
            result.extend([wave_x, wave_y])
    
    return result


def sample_arc_points(cx: float, cy: float, radius: float, 
                     start_angle: float, end_angle: float, 
                     num_points: int = 50) -> List[Tuple[float, float]]:
    """
    Sample points along an arc
    Выбрать точки вдоль дуги
    """
    points = []
    sweep = end_angle - start_angle
    
    while sweep > 2 * math.pi:
        sweep -= 2 * math.pi
    while sweep < -2 * math.pi:
        sweep += 2 * math.pi
    
    for i in range(num_points + 1):
        t = i / num_points
        angle = start_angle + t * sweep
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))
    
    return points


def sample_circle_points(cx: float, cy: float, radius: float, 
                        num_points: int = 64) -> List[Tuple[float, float]]:
    """
    Sample points along a circle
    Выбрать точки вдоль окружности
    """
    points = []
    for i in range(num_points + 1):
        angle = 2 * math.pi * i / num_points
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))
    
    return points
