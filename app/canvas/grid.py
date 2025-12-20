"""
Grid module - coordinate grid display
Модуль сетки - отображение координатной сетки
"""

import math
from typing import Tuple, List


class Grid:
    """
    Coordinate grid for CAD canvas
    Координатная сетка для холста CAD
    """
    
    def __init__(self):
        # Grid settings
        # Все координаты и шаг сетки в миллиметрах
        # All coordinates and grid step in millimeters
        self.step: float = 10.0          # Grid step in millimeters (по умолчанию 10 мм)
        self.visible: bool = True        # Grid visibility
        
        # Light theme colors
        self.color: str = "#E2E8F0"      # Grid line color (subtle)
        self.major_color: str = "#CBD5E1"  # Major grid line color (every 5 steps)
        self.axis_color: str = "#94A3B8"  # Axis color
        
        # Axis settings
        self.show_axes: bool = True
        self.axis_x_color: str = "#EF4444"  # X axis color (red)
        self.axis_y_color: str = "#22C55E"  # Y axis color (green)
        
        # Adaptive grid - adjust step based on zoom
        # Адаптивная сетка - автоматически меняет шаг в зависимости от масштаба
        # так чтобы на экране шаг был в разумных пределах (20-100 пикселей)
        # ВЫКЛЮЧЕНО по умолчанию - шаг сетки в миллиметрах остается постоянным
        self.adaptive: bool = False
        self.min_screen_step: float = 20.0   # Minimum grid step in pixels (минимум 20 пикселей)
        self.max_screen_step: float = 100.0  # Maximum grid step in pixels (максимум 100 пикселей)
        
        # Canvas item IDs
        self._grid_ids: List[int] = []
    
    def get_adaptive_step(self, scale: float) -> float:
        """
        Calculate adaptive grid step based on current zoom level
        Вычислить адаптивный шаг сетки на основе текущего масштаба
        
        Args:
            scale: Scale factor (pixels per millimeter)
        
        Returns:
            Grid step in millimeters (адаптированный для текущего масштаба)
        """
        if not self.adaptive:
            return self.step
        
        # Convert grid step from millimeters to screen pixels
        # scale уже содержит пиксели на миллиметр
        screen_step = self.step * scale
        
        # Adjust step to keep screen spacing reasonable
        # Увеличиваем/уменьшаем шаг так, чтобы на экране было 20-100 пикселей между линиями
        while screen_step < self.min_screen_step:
            screen_step *= 2
        while screen_step > self.max_screen_step:
            screen_step /= 2
        
        # Convert back to millimeters
        return screen_step / scale
    
    def draw(self, canvas, transform, width: int, height: int):
        """
        Draw grid on canvas
        Нарисовать сетку на холсте
        """
        self.clear(canvas)
        
        if not self.visible:
            return
        
        scale = transform.get_scale()
        step = self.get_adaptive_step(scale)
        
        # Get visible world coordinates
        corners = [
            transform.inverse_transform_point(0, 0),
            transform.inverse_transform_point(width, 0),
            transform.inverse_transform_point(width, height),
            transform.inverse_transform_point(0, height),
        ]
        
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        
        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)
        
        # Add margin
        margin = step * 5
        min_x -= margin
        max_x += margin
        min_y -= margin
        max_y += margin
        
        # Align to grid
        start_x = math.floor(min_x / step) * step
        start_y = math.floor(min_y / step) * step
        
        # Draw vertical lines
        x = start_x
        while x <= max_x:
            sx1, sy1 = transform.transform_point(x, min_y - margin)
            sx2, sy2 = transform.transform_point(x, max_y + margin)
            
            is_axis = abs(x) < step / 10
            is_major = abs(round(x / step) % 5) < 0.1
            
            if is_axis and self.show_axes:
                color = self.axis_y_color
                width_val = 2
            elif is_major:
                color = self.major_color
                width_val = 1
            else:
                color = self.color
                width_val = 1
            
            line_id = canvas.create_line(sx1, sy1, sx2, sy2, fill=color, width=width_val)
            self._grid_ids.append(line_id)
            
            x += step
        
        # Draw horizontal lines
        y = start_y
        while y <= max_y:
            sx1, sy1 = transform.transform_point(min_x - margin, y)
            sx2, sy2 = transform.transform_point(max_x + margin, y)
            
            is_axis = abs(y) < step / 10
            is_major = abs(round(y / step) % 5) < 0.1
            
            if is_axis and self.show_axes:
                color = self.axis_x_color
                width_val = 2
            elif is_major:
                color = self.major_color
                width_val = 1
            else:
                color = self.color
                width_val = 1
            
            line_id = canvas.create_line(sx1, sy1, sx2, sy2, fill=color, width=width_val)
            self._grid_ids.append(line_id)
            
            y += step
        
        # Draw origin marker
        if self.show_axes:
            ox, oy = transform.transform_point(0, 0)
            
            # Origin glow effect
            glow_id = canvas.create_oval(
                ox - 8, oy - 8, ox + 8, oy + 8,
                outline='#3B82F6',
                fill='',
                width=1
            )
            self._grid_ids.append(glow_id)
            
            origin_id = canvas.create_oval(
                ox - 5, oy - 5, ox + 5, oy + 5,
                outline='#3B82F6',
                fill='#FFFFFF',
                width=2
            )
            self._grid_ids.append(origin_id)
            
            label_id = canvas.create_text(
                ox + 14, oy + 14,
                text='0',
                fill='#3B82F6',
                font=('Segoe UI', 9, 'bold')
            )
            self._grid_ids.append(label_id)
    
    def clear(self, canvas):
        """Clear grid from canvas"""
        for item_id in self._grid_ids:
            try:
                canvas.delete(item_id)
            except:
                pass
        self._grid_ids.clear()
    
    def set_step(self, step: float):
        """Set grid step in millimeters"""
        self.step = max(0.1, step)
    
    def set_colors(self, grid_color: str = None, major_color: str = None, axis_color: str = None):
        """Set grid colors"""
        if grid_color:
            self.color = grid_color
        if major_color:
            self.major_color = major_color
        if axis_color:
            self.axis_color = axis_color
