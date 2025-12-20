"""
CAD Canvas - main drawing area with grid, primitives and navigation
Холст CAD - основная рабочая область
"""

import tkinter as tk
from typing import List, Optional, Callable, Tuple

from .grid import Grid
from .navigation import NavigationController
from ..primitives.base import Primitive
from ..styles.style_manager import StyleManager
from ..snaps.snap_manager import SnapManager
from ..utils.coordinates import Transform


class CADCanvas:
    """
    CAD Canvas - main drawing area with grid, primitives and navigation
    Холст CAD - основная рабочая область
    """
    
    def __init__(self, parent, **kwargs):
        # Light theme canvas
        self.canvas = tk.Canvas(
            parent,
            bg='#FFFFFF',  # White background
            highlightthickness=2,
            highlightbackground='#CBD5E1',
            highlightcolor='#3B82F6',
            **kwargs
        )
        
        self.transform = Transform()
        self.grid = Grid()
        self.navigation = NavigationController(self.transform)
        self.style_manager = StyleManager()
        self.snap_manager = SnapManager()
        
        self.primitives: List[Primitive] = []
        self.selected_primitives: List[Primitive] = []
        
        self._current_tool = None
        
        self._on_selection_changed: Optional[Callable] = None
        self._on_primitives_changed: Optional[Callable] = None
        self._on_cursor_moved: Optional[Callable] = None
        self._on_base_point_set: Optional[Callable[[float, float], None]] = None
        
        self._last_mouse_x = 0
        self._last_mouse_y = 0
        self._last_world_x = 0.0
        self._last_world_y = 0.0
        self._shift_pressed = False
        
        self._bind_events()
        
        self.navigation.set_on_view_changed(self.redraw)
        
        self.canvas.update_idletasks()
        self.navigation.reset_view(
            self.canvas.winfo_width() or 800,
            self.canvas.winfo_height() or 600
        )
    
    def _bind_events(self):
        """Bind canvas events"""
        self.canvas.bind('<Motion>', self._on_mouse_move)
        self.canvas.bind('<Button-1>', self._on_left_click)
        self.canvas.bind('<B1-Motion>', self._on_left_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_left_release)
        self.canvas.bind('<Button-2>', self._on_middle_click)
        self.canvas.bind('<B2-Motion>', self._on_middle_drag)
        self.canvas.bind('<ButtonRelease-2>', self._on_middle_release)
        self.canvas.bind('<Button-3>', self._on_right_click)
        self.canvas.bind('<MouseWheel>', self._on_mouse_wheel)
        self.canvas.bind('<Button-4>', self._on_scroll_up)
        self.canvas.bind('<Button-5>', self._on_scroll_down)
        self.canvas.bind('<Configure>', self._on_resize)
        self.canvas.bind('<Key>', self._on_key_press)
        self.canvas.bind('<Enter>', lambda e: self.canvas.focus_set())
    
    def _on_mouse_move(self, event):
        """Handle mouse movement"""
        self._last_mouse_x = event.x
        self._last_mouse_y = event.y
        self._last_world_x, self._last_world_y = self.navigation.screen_to_world(event.x, event.y)
        
        snap = self.snap_manager.find_snap(event.x, event.y, self.primitives, self.transform)
        
        if self._on_cursor_moved:
            if snap:
                self._on_cursor_moved(snap.x, snap.y, snap.snap_type.value)
            else:
                self._on_cursor_moved(self._last_world_x, self._last_world_y, None)
        
        if self._current_tool:
            self._current_tool.on_mouse_move(event.x, event.y, self._last_world_x, self._last_world_y)
        
        self._draw_snap_marker()
    
    def _on_left_click(self, event):
        """Handle left mouse button click"""
        self._shift_pressed = bool(event.state & 0x0001)
        if self._current_tool:
            wx, wy = (self._last_world_x, self._last_world_y)
            if self.snap_manager.current_snap:
                wx = self.snap_manager.current_snap.x
                wy = self.snap_manager.current_snap.y
            
            self._current_tool.on_left_click(event.x, event.y, wx, wy)
    
    def _on_left_drag(self, event):
        """Handle left mouse button drag"""
        self._last_mouse_x = event.x
        self._last_mouse_y = event.y
        self._last_world_x, self._last_world_y = self.navigation.screen_to_world(event.x, event.y)
        
        if self._current_tool:
            self._current_tool.on_left_drag(event.x, event.y, self._last_world_x, self._last_world_y)
    
    def _on_left_release(self, event):
        """Handle left mouse button release"""
        if self._current_tool:
            wx, wy = (self._last_world_x, self._last_world_y)
            if self.snap_manager.current_snap:
                wx = self.snap_manager.current_snap.x
                wy = self.snap_manager.current_snap.y
            
            self._current_tool.on_left_release(event.x, event.y, wx, wy)
    
    def _on_middle_click(self, event):
        """Handle middle mouse button click (pan start)"""
        self.navigation.start_pan(event.x, event.y)
        self.canvas.config(cursor='fleur')
    
    def _on_middle_drag(self, event):
        """Handle middle mouse button drag (pan)"""
        self.navigation.update_pan(event.x, event.y)
    
    def _on_middle_release(self, event):
        """Handle middle mouse button release (pan end)"""
        self.navigation.end_pan()
        self.canvas.config(cursor='')
    
    def _on_right_click(self, event):
        """Handle right mouse button click"""
        if self._current_tool:
            self._current_tool.on_right_click(event.x, event.y, self._last_world_x, self._last_world_y)
    
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel (zoom)"""
        if event.delta > 0:
            self.navigation.zoom_in(event.x, event.y)
        else:
            self.navigation.zoom_out(event.x, event.y)
    
    def _on_scroll_up(self, event):
        """Handle scroll up (Linux)"""
        self.navigation.zoom_in(event.x, event.y)
    
    def _on_scroll_down(self, event):
        """Handle scroll down (Linux)"""
        self.navigation.zoom_out(event.x, event.y)
    
    def _on_resize(self, event):
        """Handle canvas resize"""
        self.navigation.set_canvas_size(event.width, event.height)
        self.redraw()
    
    def _on_key_press(self, event):
        """Handle key press"""
        if self._current_tool and hasattr(self._current_tool, 'on_key_press'):
            result = self._current_tool.on_key_press(event)
            if result == 'break':
                return 'break'
    
    def redraw(self):
        """Redraw entire canvas"""
        self.canvas.delete('all')
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Draw grid
        self.grid.draw(self.canvas, self.transform, width, height)
        
        # Draw primitives
        for primitive in self.primitives:
            if primitive.visible:
                primitive.draw(self.canvas, self.transform, self.style_manager)
        
        # Draw tool preview
        if self._current_tool:
            self._current_tool.draw_preview(self.canvas, self.transform)
        
        # Draw snap markers
        self._draw_snap_marker()
    
    def _draw_snap_marker(self):
        """Draw snap point marker"""
        self.snap_manager.draw_snap_marker(self.canvas, self.transform)
    
    # ================== Primitive Management ==================
    
    def add_primitive(self, primitive: Primitive):
        """Add primitive to canvas"""
        self.primitives.append(primitive)
        self._notify_primitives_changed()
        self.redraw()
    
    def remove_primitive(self, primitive: Primitive):
        """Remove primitive from canvas"""
        if primitive in self.primitives:
            primitive.clear_canvas_items(self.canvas)
            self.primitives.remove(primitive)
            if primitive in self.selected_primitives:
                self.selected_primitives.remove(primitive)
            self._notify_selection_changed()
            self._notify_primitives_changed()
            self.redraw()
    
    def clear_primitives(self):
        """Clear all primitives"""
        for primitive in self.primitives:
            primitive.clear_canvas_items(self.canvas)
        self.primitives.clear()
        self.selected_primitives.clear()
        self._notify_selection_changed()
        self._notify_primitives_changed()
        self.redraw()
    
    # ================== Selection Management ==================
    
    def select_primitive(self, primitive: Primitive, add: bool = False):
        """Select a primitive"""
        if not add:
            self.deselect_all()
        
        if primitive not in self.selected_primitives:
            primitive.select()
            self.selected_primitives.append(primitive)
            self._notify_selection_changed()
            self.redraw()
    
    def deselect_primitive(self, primitive: Primitive):
        """Deselect a primitive"""
        if primitive in self.selected_primitives:
            primitive.deselect()
            self.selected_primitives.remove(primitive)
            self._notify_selection_changed()
            self.redraw()
    
    def deselect_all(self):
        """Deselect all primitives"""
        for primitive in self.selected_primitives:
            primitive.deselect()
        self.selected_primitives.clear()
        self._notify_selection_changed()
        self.redraw()
    
    def select_all(self):
        """Select all primitives"""
        for primitive in self.primitives:
            if primitive not in self.selected_primitives:
                primitive.select()
                self.selected_primitives.append(primitive)
        self._notify_selection_changed()
        self.redraw()
    
    def delete_selected(self):
        """Delete selected primitives"""
        for primitive in self.selected_primitives[:]:
            self.remove_primitive(primitive)
    
    def find_primitive_at(self, x: float, y: float, tolerance: float = 5.0) -> Optional[Primitive]:
        """Find primitive at given world coordinates"""
        for primitive in reversed(self.primitives):
            if primitive.visible and primitive.contains_point(x, y, tolerance / self.transform.get_scale()):
                return primitive
        return None
    
    # ================== Tool Management ==================
    
    def set_tool(self, tool):
        """Set active tool"""
        if self._current_tool:
            self._current_tool.deactivate()
        
        self._current_tool = tool
        
        if tool:
            tool.activate(self)
        
        self.redraw()
    
    def get_tool(self):
        """Get current tool"""
        return self._current_tool
    
    # ================== View Operations ==================
    
    def zoom_to_fit(self, margin: float = 0.1):
        """Zoom to fit all content"""
        if not self.primitives:
            return
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Ensure valid dimensions
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Calculate bounds of all primitives
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for primitive in self.primitives:
            if primitive.visible:
                bbox = primitive.get_bounding_box()
                min_x = min(min_x, bbox[0])
                min_y = min(min_y, bbox[1])
                max_x = max(max_x, bbox[2])
                max_y = max(max_y, bbox[3])
        
        if min_x == float('inf'):
            return
        
        self.navigation.zoom_to_fit(
            (min_x, min_y, max_x, max_y),
            canvas_width,
            canvas_height,
            margin
        )
    
    def reset_view(self):
        """Reset view to default"""
        self.navigation.reset_view(
            self.canvas.winfo_width(),
            self.canvas.winfo_height()
        )
    
    # ================== Callbacks ==================
    
    def set_on_selection_changed(self, callback: Callable):
        """Set callback for selection changes"""
        self._on_selection_changed = callback
    
    def set_on_primitives_changed(self, callback: Callable):
        """Set callback for primitives changes"""
        self._on_primitives_changed = callback
    
    def set_on_cursor_moved(self, callback: Callable):
        """Set callback for cursor movement"""
        self._on_cursor_moved = callback
    
    def set_on_base_point_set(self, callback: Callable):
        """Set callback for base point set"""
        self._on_base_point_set = callback
    
    def set_base_point(self, x: float, y: float):
        """Set base point for coordinate input"""
        if self._on_base_point_set:
            self._on_base_point_set(x, y)
    
    def clear_base_point(self):
        """Clear base point for coordinate input"""
        if self._on_base_point_set:
            self._on_base_point_set(None, None)
    
    # ================== Internal ==================
    
    def _notify_selection_changed(self):
        """Notify about selection change"""
        if self._on_selection_changed:
            self._on_selection_changed(self.selected_primitives)
    
    def _notify_primitives_changed(self):
        """Notify about primitives change"""
        if self._on_primitives_changed:
            self._on_primitives_changed(self.primitives)
    
    # ================== Utility ==================
    
    def get_cursor_world_pos(self) -> Tuple[float, float]:
        """Get current cursor position in world coordinates"""
        return (self._last_world_x, self._last_world_y)
    
    def get_widget(self) -> tk.Canvas:
        """Get tkinter canvas widget"""
        return self.canvas
    
    def pack(self, **kwargs):
        """Pack canvas widget"""
        self.canvas.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid canvas widget"""
        self.canvas.grid(**kwargs)
    
    def place(self, **kwargs):
        """Place canvas widget"""
        self.canvas.place(**kwargs)
