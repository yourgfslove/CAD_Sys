"""
Status Bar - строка состояния с современным дизайном
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from ..utils.coordinates import AngleUnit


class StatusBar(tk.Frame):
    """Modern status bar showing coordinates and system information"""
    
    # Color scheme (light theme)
    COLORS = {
        'bg': '#F1F5F9',
        'surface': '#FFFFFF',
        'accent': '#3B82F6',
        'accent_alt': '#8B5CF6',
        'success': '#22C55E',
        'warning': '#F59E0B',
        'text': '#1E293B',
        'text_secondary': '#475569',
        'text_muted': '#94A3B8',
        'border': '#CBD5E1',
    }
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=self.COLORS['bg'], **kwargs)
        self._angle_unit = AngleUnit.DEGREES
        self._create_widgets()
    
    def _create_widgets(self):
        # Configure consistent padding
        pad_x = 12
        pad_y = 6
        
        # === Left section: Coordinates ===
        coords_section = tk.Frame(self, bg=self.COLORS['bg'])
        coords_section.pack(side=tk.LEFT, padx=pad_x, pady=pad_y)
        
        # Cartesian coordinates
        self._create_coord_display(coords_section, "X", "x")
        self._create_coord_display(coords_section, "Y", "y")
        
        self._add_separator()
        
        # Polar coordinates
        polar_section = tk.Frame(self, bg=self.COLORS['bg'])
        polar_section.pack(side=tk.LEFT, padx=pad_x, pady=pad_y)
        
        self._create_coord_display(polar_section, "R", "r")
        self._create_coord_display(polar_section, "θ", "theta")
        
        self._add_separator()
        
        # === Center section: View info ===
        view_section = tk.Frame(self, bg=self.COLORS['bg'])
        view_section.pack(side=tk.LEFT, padx=pad_x, pady=pad_y)
        
        # Zoom indicator
        zoom_frame = tk.Frame(view_section, bg=self.COLORS['bg'])
        zoom_frame.pack(side=tk.LEFT, padx=8)
        
        tk.Label(
            zoom_frame, text="⊕", 
            bg=self.COLORS['bg'], fg=self.COLORS['accent'],
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        
        self._zoom_label = tk.Label(
            zoom_frame, text="100%", 
            bg=self.COLORS['bg'], fg=self.COLORS['text'],
            font=("Segoe UI", 10, "bold"), width=7
        )
        self._zoom_label.pack(side=tk.LEFT, padx=(4, 0))
        
        # Rotation indicator
        rotation_frame = tk.Frame(view_section, bg=self.COLORS['bg'])
        rotation_frame.pack(side=tk.LEFT, padx=8)
        
        tk.Label(
            rotation_frame, text="↻", 
            bg=self.COLORS['bg'], fg=self.COLORS['accent_alt'],
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        
        self._rotation_label = tk.Label(
            rotation_frame, text="0°", 
            bg=self.COLORS['bg'], fg=self.COLORS['text'],
            font=("Segoe UI", 10), width=7
        )
        self._rotation_label.pack(side=tk.LEFT, padx=(4, 0))
        
        self._add_separator()
        
        # === Snap indicator ===
        snap_section = tk.Frame(self, bg=self.COLORS['bg'])
        snap_section.pack(side=tk.LEFT, padx=pad_x, pady=pad_y)
        
        tk.Label(
            snap_section, text="◎", 
            bg=self.COLORS['bg'], fg=self.COLORS['success'],
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT)
        
        tk.Label(
            snap_section, text="Привязка:", 
            bg=self.COLORS['bg'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT, padx=(4, 4))
        
        self._snap_label = tk.Label(
            snap_section, text="—", 
            bg=self.COLORS['bg'], fg=self.COLORS['text'],
            font=("Segoe UI", 9), width=12, anchor="w"
        )
        self._snap_label.pack(side=tk.LEFT)
        
        # === Right section: Tool and selection info ===
        right_section = tk.Frame(self, bg=self.COLORS['bg'])
        right_section.pack(side=tk.RIGHT, padx=pad_x, pady=pad_y)
        
        # Selection count
        self._selection_label = tk.Label(
            right_section, text="⬚ 0", 
            bg=self.COLORS['bg'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        )
        self._selection_label.pack(side=tk.RIGHT, padx=8)
        
        # Separator
        tk.Frame(right_section, bg=self.COLORS['border'], width=1).pack(
            side=tk.RIGHT, fill=tk.Y, padx=8, pady=2
        )
        
        # Current tool
        self._tool_frame = tk.Frame(right_section, bg=self.COLORS['surface'], padx=8, pady=2)
        self._tool_frame.pack(side=tk.RIGHT)
        
        self._tool_label = tk.Label(
            self._tool_frame, text="Выделение", 
            bg=self.COLORS['surface'], fg=self.COLORS['accent'],
            font=("Segoe UI", 9, "bold")
        )
        self._tool_label.pack()
    
    def _create_coord_display(self, parent, label: str, var_name: str):
        """Create a coordinate display widget"""
        frame = tk.Frame(parent, bg=self.COLORS['bg'])
        frame.pack(side=tk.LEFT, padx=4)
        
        # Label
        lbl = tk.Label(
            frame, text=label + ":", 
            bg=self.COLORS['bg'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        )
        lbl.pack(side=tk.LEFT)
        
        # Value
        value_label = tk.Label(
            frame, text="0.00", 
            bg=self.COLORS['bg'], fg=self.COLORS['text'],
            font=("JetBrains Mono", 10), width=8, anchor="e"
        )
        value_label.pack(side=tk.LEFT, padx=(2, 0))
        
        # Store reference
        setattr(self, f"_{var_name}_label", value_label)
    
    def _add_separator(self):
        """Add a vertical separator"""
        tk.Frame(self, bg=self.COLORS['border'], width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=4, pady=4
        )
    
    def update_coordinates(self, x: float, y: float, snap_type: Optional[str] = None):
        """Update coordinate displays"""
        self._x_label.config(text=f"{x:>8.2f}")
        self._y_label.config(text=f"{y:>8.2f}")
        
        import math
        r = math.sqrt(x * x + y * y)
        theta = math.atan2(y, x)
        
        self._r_label.config(text=f"{r:>8.2f}")
        
        if self._angle_unit == AngleUnit.DEGREES:
            theta_deg = math.degrees(theta)
            self._theta_label.config(text=f"{theta_deg:>7.1f}°")
        else:
            self._theta_label.config(text=f"{theta:>6.3f}rad")
        
        # Update snap indicator
        if snap_type:
            self._snap_label.config(text=snap_type, fg=self.COLORS['success'])
        else:
            self._snap_label.config(text="—", fg=self.COLORS['text_muted'])
    
    def update_zoom(self, zoom: float):
        """Update zoom display"""
        self._zoom_label.config(text=f"{zoom:.0f}%")
    
    def update_rotation(self, rotation_deg: float):
        """Update rotation display"""
        self._rotation_label.config(text=f"{rotation_deg:.1f}°")
    
    def update_tool(self, tool_name: str):
        """Update current tool display"""
        self._tool_label.config(text=tool_name)
    
    def update_selection_count(self, count: int):
        """Update selection count"""
        if count > 0:
            self._selection_label.config(
                text=f"⬚ {count}", 
                fg=self.COLORS['accent']
            )
        else:
            self._selection_label.config(
                text="⬚ 0", 
                fg=self.COLORS['text_muted']
            )
    
    def update_selection(self, count: int):
        """Update selection count (alias)"""
        self.update_selection_count(count)
    
    def set_angle_unit(self, unit: AngleUnit):
        """Set angle unit for display"""
        self._angle_unit = unit
