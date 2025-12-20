"""
Settings Panel - панель настроек с современным дизайном
"""

import tkinter as tk
from tkinter import ttk, colorchooser
from typing import Callable, Optional
from ..utils.coordinates import AngleUnit, CoordinateSystem


class SettingsPanel(tk.Frame):
    """Modern panel for application settings"""
    
    # Light theme colors
    COLORS = {
        'bg': '#F8FAFC',
        'surface': '#FFFFFF',
        'input_bg': '#FFFFFF',
        'accent': '#3B82F6',
        'accent_alt': '#8B5CF6',
        'success': '#22C55E',
        'warning': '#F59E0B',
        'text': '#1E293B',
        'text_secondary': '#475569',
        'text_muted': '#94A3B8',
        'border': '#CBD5E1',
    }
    
    def __init__(self, parent, on_settings_changed: Callable = None, **kwargs):
        super().__init__(parent, bg=self.COLORS['bg'], **kwargs)
        self._on_settings_changed = on_settings_changed
        self._coordinate_system = CoordinateSystem.CARTESIAN
        self._angle_unit = AngleUnit.DEGREES
        self._grid_step = 10.0
        self._grid_visible = True
        self._grid_color = "#E2E8F0"
        self._background_color = "#FFFFFF"
        self._create_widgets()
    
    def _create_widgets(self):
        # Title
        title_frame = tk.Frame(self, bg=self.COLORS['bg'])
        title_frame.pack(fill=tk.X, padx=12, pady=(12, 8))
        
        tk.Label(
            title_frame, 
            text="⚙️ Настройки", 
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent'],
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W)
        
        # Separator
        tk.Frame(self, bg=self.COLORS['border'], height=1).pack(fill=tk.X, padx=12, pady=4)
        
        # Scrollable content
        content = tk.Frame(self, bg=self.COLORS['bg'])
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        # Coordinate system section
        self._create_section(content, "Система координат", self._create_coord_content)
        
        # Angle units section
        self._create_section(content, "Единицы углов", self._create_angle_content)
        
        # Grid section
        self._create_section(content, "Сетка", self._create_grid_content)
        
        # Snaps section
        self._create_section(content, "Привязки", self._create_snaps_content)
    
    def _create_section(self, parent, title: str, content_creator):
        """Create a settings section"""
        section = tk.Frame(parent, bg=self.COLORS['surface'])
        section.pack(fill=tk.X, pady=6)
        
        # Section header
        header = tk.Frame(section, bg=self.COLORS['surface'])
        header.pack(fill=tk.X, padx=10, pady=(10, 6))
        
        tk.Label(
            header, text=title,
            bg=self.COLORS['surface'], fg=self.COLORS['accent'],
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W)
        
        # Section content
        content = tk.Frame(section, bg=self.COLORS['surface'])
        content.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        content_creator(content)
    
    def _create_coord_content(self, parent):
        """Create coordinate system settings"""
        self._coord_var = tk.StringVar(value="cartesian")
        
        for value, text in [("cartesian", "Декартова (X, Y)"), ("polar", "Полярная (R, θ)")]:
            rb = tk.Radiobutton(
                parent, text=text, value=value, variable=self._coord_var,
                bg=self.COLORS['surface'], fg=self.COLORS['text'],
                selectcolor=self.COLORS['input_bg'],
                activebackground=self.COLORS['surface'],
                activeforeground=self.COLORS['accent'],
                font=("Segoe UI", 9),
                command=self._on_coord_change
            )
            rb.pack(anchor=tk.W, pady=2)
    
    def _create_angle_content(self, parent):
        """Create angle unit settings"""
        self._angle_var = tk.StringVar(value="degrees")
        
        for value, text in [("degrees", "Градусы (°)"), ("radians", "Радианы (рад)")]:
            rb = tk.Radiobutton(
                parent, text=text, value=value, variable=self._angle_var,
                bg=self.COLORS['surface'], fg=self.COLORS['text'],
                selectcolor=self.COLORS['input_bg'],
                activebackground=self.COLORS['surface'],
                activeforeground=self.COLORS['accent'],
                font=("Segoe UI", 9),
                command=self._on_angle_change
            )
            rb.pack(anchor=tk.W, pady=2)
    
    def _create_grid_content(self, parent):
        """Create grid settings"""
        # Grid visibility
        self._grid_visible_var = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(
            parent, text="Показывать сетку", variable=self._grid_visible_var,
            bg=self.COLORS['surface'], fg=self.COLORS['text'],
            selectcolor=self.COLORS['input_bg'],
            activebackground=self.COLORS['surface'],
            activeforeground=self.COLORS['accent'],
            font=("Segoe UI", 9),
            command=self._on_grid_visibility_change
        )
        cb.pack(anchor=tk.W, pady=2)
        
        # Grid step
        step_frame = tk.Frame(parent, bg=self.COLORS['surface'])
        step_frame.pack(fill=tk.X, pady=4)
        
        tk.Label(
            step_frame, text="Шаг сетки:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._grid_step_var = tk.StringVar(value="10")
        step_entry = tk.Entry(
            step_frame, textvariable=self._grid_step_var, width=8,
            bg=self.COLORS['input_bg'], fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 10),
            bd=0, highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        step_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        step_entry.bind("<Return>", self._on_grid_step_change)
        step_entry.bind("<FocusOut>", self._on_grid_step_change)
        
        tk.Label(
            step_frame, text="мм",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        # Color pickers
        colors_frame = tk.Frame(parent, bg=self.COLORS['surface'])
        colors_frame.pack(fill=tk.X, pady=4)
        
        # Grid color
        grid_color_frame = tk.Frame(colors_frame, bg=self.COLORS['surface'])
        grid_color_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(
            grid_color_frame, text="Цвет сетки:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._grid_color_btn = tk.Button(
            grid_color_frame, width=3, 
            bg=self._grid_color, 
            activebackground=self._grid_color,
            bd=0, highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            cursor="hand2",
            command=self._choose_grid_color
        )
        self._grid_color_btn.pack(side=tk.LEFT, padx=8)
        
        # Background color
        bg_color_frame = tk.Frame(colors_frame, bg=self.COLORS['surface'])
        bg_color_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(
            bg_color_frame, text="Цвет фона:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._bg_color_btn = tk.Button(
            bg_color_frame, width=3, 
            bg=self._background_color, 
            activebackground=self._background_color,
            bd=0, highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            cursor="hand2",
            command=self._choose_bg_color
        )
        self._bg_color_btn.pack(side=tk.LEFT, padx=8)
    
    def _create_snaps_content(self, parent):
        """Create snap settings"""
        self._snap_vars = {}
        snap_types = [
            ("endpoint", "◆ Конец"),
            ("midpoint", "◇ Середина"),
            ("center", "⊙ Центр"),
            ("intersection", "✕ Пересечение"),
            ("perpendicular", "⊥ Перпендикуляр"),
        ]
        
        for snap_id, snap_name in snap_types:
            var = tk.BooleanVar(value=True)
            self._snap_vars[snap_id] = var
            cb = tk.Checkbutton(
                parent, text=snap_name, variable=var,
                bg=self.COLORS['surface'], fg=self.COLORS['text'],
                selectcolor=self.COLORS['input_bg'],
                activebackground=self.COLORS['surface'],
                activeforeground=self.COLORS['accent'],
                font=("Segoe UI", 9),
                command=self._on_snap_change
            )
            cb.pack(anchor=tk.W, pady=1)
    
    def _on_coord_change(self):
        value = self._coord_var.get()
        self._coordinate_system = CoordinateSystem.CARTESIAN if value == "cartesian" else CoordinateSystem.POLAR
        self._notify_change("coordinate_system", self._coordinate_system)
    
    def _on_angle_change(self):
        value = self._angle_var.get()
        self._angle_unit = AngleUnit.DEGREES if value == "degrees" else AngleUnit.RADIANS
        self._notify_change("angle_unit", self._angle_unit)
    
    def _on_grid_visibility_change(self):
        self._grid_visible = self._grid_visible_var.get()
        self._notify_change("grid_visible", self._grid_visible)
    
    def _on_grid_step_change(self, event=None):
        try:
            step = float(self._grid_step_var.get())
            if step > 0:
                self._grid_step = step
                self._notify_change("grid_step", self._grid_step)
        except ValueError:
            pass
    
    def _choose_grid_color(self):
        color = colorchooser.askcolor(self._grid_color, title="Цвет сетки")
        if color[1]:
            self._grid_color = color[1]
            self._grid_color_btn.config(bg=self._grid_color, activebackground=self._grid_color)
            self._notify_change("grid_color", self._grid_color)
    
    def _choose_bg_color(self):
        color = colorchooser.askcolor(self._background_color, title="Цвет фона")
        if color[1]:
            self._background_color = color[1]
            self._bg_color_btn.config(bg=self._background_color, activebackground=self._background_color)
            self._notify_change("background_color", self._background_color)
    
    def _on_snap_change(self):
        enabled_snaps = [snap_id for snap_id, var in self._snap_vars.items() if var.get()]
        self._notify_change("snaps", enabled_snaps)
    
    def _notify_change(self, setting_name: str, value):
        if self._on_settings_changed:
            self._on_settings_changed(setting_name, value)
    
    def get_settings(self) -> dict:
        return {
            "coordinate_system": self._coordinate_system,
            "angle_unit": self._angle_unit,
            "grid_step": self._grid_step,
            "grid_visible": self._grid_visible,
            "grid_color": self._grid_color,
            "background_color": self._background_color,
            "snaps": [snap_id for snap_id, var in self._snap_vars.items() if var.get()],
        }
