"""
Navigation Controller - pan, zoom, rotate
Контроллер навигации - панорамирование, масштабирование, поворот

ЛР №2 - Навигация в графических приложениях

Панорамирование: x' = x + dx, y' = y + dy
Масштабирование: x' = x * s, y' = y * s
Поворот: x' = x * cos(θ) - y * sin(θ), y' = x * sin(θ) + y * cos(θ)
"""

import math
from typing import Tuple, Optional, Callable
from ..utils.coordinates import Transform


class NavigationController:
    """
    Navigation controller for CAD canvas
    Контроллер навигации для холста CAD
    
    Способы активации:
    - Панорамирование: СКМ + перетаскивание, инструмент "Рука"
    - Масштабирование: колесико мыши, горячие клавиши +/-
    - Поворот: горячие клавиши, кнопки панели
    """
    
    def __init__(self, transform: Transform = None):
        # Transform matrix
        self.transform = transform if transform else Transform()
        
        # Navigation state
        self._is_panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0
        self._pan_start_tx = 0
        self._pan_start_ty = 0
        
        # Zoom settings
        self.zoom_factor: float = 1.2    # Zoom multiplier per step
        self.min_zoom: float = 0.01      # Minimum zoom level
        self.max_zoom: float = 100.0     # Maximum zoom level
        
        # Rotation settings
        self.rotation_step: float = math.radians(15)  # Rotation step (15 degrees)
        self.snap_to_angles: bool = True  # Snap to 90-degree angles with Shift
        self._rotation_angle: float = 0.0  # Track rotation separately for stability
        
        # Canvas dimensions (needed for center-based rotation)
        self._canvas_width: float = 800
        self._canvas_height: float = 600
        
        # View bounds (for "show all" function)
        self._content_bounds: Optional[Tuple[float, float, float, float]] = None
        
        # Callback for view changes
        self._on_view_changed: Optional[Callable] = None
    
    def set_canvas_size(self, width: float, height: float):
        """Update canvas dimensions"""
        self._canvas_width = width
        self._canvas_height = height
    
    def set_on_view_changed(self, callback: Callable):
        """Set callback for view changes"""
        self._on_view_changed = callback
    
    def _notify_view_changed(self):
        """Notify about view changes"""
        if self._on_view_changed:
            self._on_view_changed()
    
    # ================== Панорамирование (Pan) ==================
    
    def start_pan(self, x: float, y: float):
        """
        Start panning operation
        Начать операцию панорамирования
        """
        self._is_panning = True
        self._pan_start_x = x
        self._pan_start_y = y
        self._pan_start_tx = self.transform.tx
        self._pan_start_ty = self.transform.ty
    
    def update_pan(self, x: float, y: float):
        """
        Update panning position
        Обновить позицию панорамирования
        """
        if not self._is_panning:
            return
        
        dx = x - self._pan_start_x
        dy = y - self._pan_start_y
        
        self.transform.tx = self._pan_start_tx + dx
        self.transform.ty = self._pan_start_ty + dy
        
        self._notify_view_changed()
    
    def end_pan(self):
        """End panning operation"""
        self._is_panning = False
    
    def is_panning(self) -> bool:
        """Check if currently panning"""
        return self._is_panning
    
    def pan_by(self, dx: float, dy: float):
        """Pan by offset"""
        self.transform.tx += dx
        self.transform.ty += dy
        self._notify_view_changed()
    
    # ================== Масштабирование (Zoom) ==================
    
    def zoom(self, factor: float, center_x: float = None, center_y: float = None):
        """
        Zoom view by factor around center point
        Масштабировать вид на коэффициент относительно центральной точки
        """
        current_scale = self.transform.get_scale()
        new_scale = current_scale * factor
        
        if new_scale < self.min_zoom or new_scale > self.max_zoom:
            return
        
        # Use screen center if no center specified
        if center_x is None:
            center_x = self._canvas_width / 2
        if center_y is None:
            center_y = self._canvas_height / 2
        
        # Get world point at zoom center
        world_x, world_y = self.transform.inverse_transform_point(center_x, center_y)
        
        # Update transform matrix with zoom
        self.transform.tx = center_x - world_x * self.transform.a * factor - world_y * self.transform.b * factor
        self.transform.ty = center_y - world_x * self.transform.c * factor - world_y * self.transform.d * factor
        
        self.transform.a *= factor
        self.transform.b *= factor
        self.transform.c *= factor
        self.transform.d *= factor
        
        self._notify_view_changed()
    
    def zoom_in(self, center_x: float = None, center_y: float = None):
        """Zoom in"""
        self.zoom(self.zoom_factor, center_x, center_y)
    
    def zoom_out(self, center_x: float = None, center_y: float = None):
        """Zoom out"""
        self.zoom(1 / self.zoom_factor, center_x, center_y)
    
    def zoom_to_fit(self, bounds: Tuple[float, float, float, float], 
                    canvas_width: float, canvas_height: float,
                    margin: float = 0.1):
        """
        Zoom to fit content bounds
        Показать весь чертеж
        """
        min_x, min_y, max_x, max_y = bounds
        
        content_width = max_x - min_x
        content_height = max_y - min_y
        
        if content_width <= 0 or content_height <= 0:
            return
        
        # Save current rotation angle (before reset)
        saved_rotation = self._rotation_angle
        
        # Calculate required scale, accounting for rotation
        # When view is rotated, the bounding box projection is larger
        available_width = canvas_width * (1 - 2 * margin)
        available_height = canvas_height * (1 - 2 * margin)
        
        # If rotated, calculate the bounding box of the rotated content
        if abs(saved_rotation) > 1e-6:
            # Calculate bounding box of rotated content
            # Transform the 4 corners of the content bounding box through rotation
            # Note: We need to account for Y-axis inversion in screen coordinates (d = -scale)
            content_center_x = (min_x + max_x) / 2
            content_center_y = (min_y + max_y) / 2
            
            # Get corners relative to center
            corners = [
                (min_x - content_center_x, min_y - content_center_y),
                (max_x - content_center_x, min_y - content_center_y),
                (max_x - content_center_x, max_y - content_center_y),
                (min_x - content_center_x, max_y - content_center_y),
            ]
            
            # Rotate corners accounting for Y-axis inversion
            # Screen transform: screen_x = scale * (x * cos(θ) + y * sin(θ))
            #                   screen_y = scale * (x * sin(θ) - y * cos(θ))
            cos_a = math.cos(saved_rotation)
            sin_a = math.sin(saved_rotation)
            rotated_corners = []
            for cx, cy in corners:
                # Apply rotation with Y-inversion consideration
                rx = cx * cos_a + cy * sin_a
                ry = cx * sin_a - cy * cos_a
                rotated_corners.append((rx, ry))
            
            # Find bounding box of rotated corners
            rot_min_x = min(c[0] for c in rotated_corners)
            rot_max_x = max(c[0] for c in rotated_corners)
            rot_min_y = min(c[1] for c in rotated_corners)
            rot_max_y = max(c[1] for c in rotated_corners)
            
            # Use rotated dimensions for scale calculation
            rotated_width = rot_max_x - rot_min_x
            rotated_height = rot_max_y - rot_min_y
            
            scale_x = available_width / rotated_width if rotated_width > 0 else 1.0
            scale_y = available_height / rotated_height if rotated_height > 0 else 1.0
        else:
            # No rotation, use original dimensions
            scale_x = available_width / content_width
            scale_y = available_height / content_height
        
        scale = min(scale_x, scale_y)
        
        # Reset transform and rotation tracking
        self.transform.reset()
        self._rotation_angle = 0.0
        
        # Apply scale (Y flipped for screen coordinates)
        self.transform.a = scale
        self.transform.d = -scale
        
        # Center content
        content_center_x = (min_x + max_x) / 2
        content_center_y = (min_y + max_y) / 2
        
        self.transform.tx = canvas_width / 2 - content_center_x * scale
        self.transform.ty = canvas_height / 2 + content_center_y * scale
        
        # Restore rotation if it was not zero
        # Apply rotation around screen center
        if abs(saved_rotation) > 1e-6:
            screen_center_x = canvas_width / 2
            screen_center_y = canvas_height / 2
            
            # Get world point at screen center before rotation
            world_cx, world_cy = self.transform.inverse_transform_point(screen_center_x, screen_center_y)
            
            # Apply rotation to transform matrix
            cos_a = math.cos(saved_rotation)
            sin_a = math.sin(saved_rotation)
            
            new_a = self.transform.a * cos_a - self.transform.c * sin_a
            new_b = self.transform.b * cos_a - self.transform.d * sin_a
            new_c = self.transform.a * sin_a + self.transform.c * cos_a
            new_d = self.transform.b * sin_a + self.transform.d * cos_a
            
            self.transform.a = new_a
            self.transform.b = new_b
            self.transform.c = new_c
            self.transform.d = new_d
            
            # Recalculate translation to keep center point fixed
            self.transform.tx = screen_center_x - world_cx * self.transform.a - world_cy * self.transform.b
            self.transform.ty = screen_center_y - world_cx * self.transform.c - world_cy * self.transform.d
            
            # Update rotation tracking
            self._rotation_angle = saved_rotation
        
        self._notify_view_changed()
    
    def set_zoom(self, scale: float, center_x: float = None, center_y: float = None):
        """Set absolute zoom level"""
        current_scale = self.transform.get_scale()
        if current_scale > 0:
            factor = scale / current_scale
            self.zoom(factor, center_x, center_y)
    
    def get_zoom(self) -> float:
        """Get current zoom level"""
        return self.transform.get_scale()
    
    def get_zoom_percent(self) -> float:
        """Get current zoom level as percentage"""
        return self.transform.get_scale() * 100
    
    # ================== Поворот (Rotation) ==================
    
    def rotate(self, angle: float, center_x: float = None, center_y: float = None):
        """
        Rotate view by angle around screen center
        Повернуть вид на угол относительно центра экрана
        """
        # Use screen center if no center specified
        if center_x is None:
            center_x = self._canvas_width / 2
        if center_y is None:
            center_y = self._canvas_height / 2
        
        # Get world point at screen center
        world_cx, world_cy = self.transform.inverse_transform_point(center_x, center_y)
        
        # Apply rotation to transform matrix
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        new_a = self.transform.a * cos_a - self.transform.c * sin_a
        new_b = self.transform.b * cos_a - self.transform.d * sin_a
        new_c = self.transform.a * sin_a + self.transform.c * cos_a
        new_d = self.transform.b * sin_a + self.transform.d * cos_a
        
        self.transform.a = new_a
        self.transform.b = new_b
        self.transform.c = new_c
        self.transform.d = new_d
        
        # Recalculate translation to keep center point fixed
        self.transform.tx = center_x - world_cx * self.transform.a - world_cy * self.transform.b
        self.transform.ty = center_y - world_cx * self.transform.c - world_cy * self.transform.d
        
        # Track rotation angle
        self._rotation_angle += angle
        
        self._notify_view_changed()
    
    def rotate_left(self, snap: bool = False):
        """Rotate view left (counterclockwise)"""
        angle = self.rotation_step
        if snap:
            angle = math.radians(90)
        self.rotate(angle)
    
    def rotate_right(self, snap: bool = False):
        """Rotate view right (clockwise)"""
        angle = -self.rotation_step
        if snap:
            angle = math.radians(-90)
        self.rotate(angle)
    
    def set_rotation(self, angle: float):
        """Set absolute rotation angle"""
        delta = angle - self._rotation_angle
        self.rotate(delta)
    
    def get_rotation(self) -> float:
        """Get current rotation in radians"""
        return self._rotation_angle
    
    def get_rotation_degrees(self) -> float:
        """Get current rotation in degrees"""
        return math.degrees(self._rotation_angle)
    
    # ================== Управление видом ==================
    
    def reset_view(self, canvas_width: float = None, canvas_height: float = None):
        """
        Reset view to default
        Сбросить вид по умолчанию
        """
        if canvas_width:
            self._canvas_width = canvas_width
        if canvas_height:
            self._canvas_height = canvas_height
        
        self.transform.reset()
        self._rotation_angle = 0.0
        
        # Center view at origin
        self.transform.d = -1  # Flip Y axis
        self.transform.tx = self._canvas_width / 2
        self.transform.ty = self._canvas_height / 2
        
        self._notify_view_changed()
    
    # ================== Преобразование координат ==================
    
    def screen_to_world(self, x: float, y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        return self.transform.inverse_transform_point(x, y)
    
    def world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates"""
        return self.transform.transform_point(x, y)
    
    # ================== Content bounds ==================
    
    def set_content_bounds(self, bounds: Tuple[float, float, float, float]):
        """Set content bounds for zoom to content"""
        self._content_bounds = bounds
    
    def zoom_to_content(self, canvas_width: float, canvas_height: float):
        """Zoom to fit content bounds"""
        if self._content_bounds:
            self.zoom_to_fit(self._content_bounds, canvas_width, canvas_height)
