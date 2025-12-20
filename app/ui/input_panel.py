"""
Input Panel - панель ввода координат с современным дизайном
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Tuple
import math
from ..utils.coordinates import AngleUnit, polar_to_cartesian, cartesian_to_polar


class InputPanel(tk.Frame):
    """Modern panel for coordinate input (Cartesian and Polar)"""
    
    # Light theme colors
    COLORS = {
        'bg': '#F8FAFC',
        'surface': '#FFFFFF',
        'input_bg': '#FFFFFF',
        'accent': '#3B82F6',
        'accent_alt': '#8B5CF6',
        'success': '#22C55E',
        'text': '#1E293B',
        'text_secondary': '#475569',
        'text_muted': '#94A3B8',
        'border': '#CBD5E1',
    }
    
    def __init__(self, parent, on_point_entered: Callable = None, **kwargs):
        super().__init__(parent, bg=self.COLORS['bg'], **kwargs)
        self._on_point_entered = on_point_entered
        self._angle_unit = AngleUnit.DEGREES
        self._use_polar = False
        self._base_point: Optional[Tuple[float, float]] = None
        self._use_relative_to_base = False
        self._create_widgets()
    
    def _create_widgets(self):
        # Title
        title_frame = tk.Frame(self, bg=self.COLORS['bg'])
        title_frame.pack(fill=tk.X, padx=12, pady=(12, 8))
        
        tk.Label(
            title_frame, 
            text="📐 Ввод координат", 
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent'],
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W)
        
        # Separator
        tk.Frame(self, bg=self.COLORS['border'], height=1).pack(fill=tk.X, padx=12, pady=4)
        
        # Mode selection
        mode_frame = tk.Frame(self, bg=self.COLORS['bg'])
        mode_frame.pack(fill=tk.X, padx=12, pady=8)
        
        self._mode_var = tk.StringVar(value="cartesian")
        
        # Cartesian mode button
        self._cart_btn = tk.Button(
            mode_frame, text="Декартовы (X, Y)",
            bg=self.COLORS['accent'], fg=self.COLORS['input_bg'],
            activebackground=self.COLORS['accent_alt'],
            font=("Segoe UI", 9, "bold"),
            bd=0, padx=12, pady=6, cursor="hand2",
            command=lambda: self._set_mode("cartesian")
        )
        self._cart_btn.pack(side=tk.LEFT, padx=(0, 4))
        
        # Polar mode button
        self._polar_btn = tk.Button(
            mode_frame, text="Полярные (R, θ)",
            bg=self.COLORS['surface'], fg=self.COLORS['text'],
            activebackground=self.COLORS['accent'],
            font=("Segoe UI", 9),
            bd=0, padx=12, pady=6, cursor="hand2",
            command=lambda: self._set_mode("polar")
        )
        self._polar_btn.pack(side=tk.LEFT)
        
        # Input section
        input_section = tk.Frame(self, bg=self.COLORS['surface'])
        input_section.pack(fill=tk.X, padx=12, pady=8)
        
        # Add padding inside
        input_inner = tk.Frame(input_section, bg=self.COLORS['surface'])
        input_inner.pack(fill=tk.X, padx=12, pady=12)
        
        # First coordinate
        coord1_frame = tk.Frame(input_inner, bg=self.COLORS['surface'])
        coord1_frame.pack(fill=tk.X, pady=4)
        
        self._coord1_label = tk.Label(
            coord1_frame, text="X", width=3,
            bg=self.COLORS['surface'], fg=self.COLORS['accent'],
            font=("Segoe UI", 11, "bold")
        )
        self._coord1_label.pack(side=tk.LEFT)
        
        self._coord1_var = tk.StringVar(value="0")
        self._coord1_entry = tk.Entry(
            coord1_frame, 
            textvariable=self._coord1_var,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 11),
            bd=0, width=15,
            highlightthickness=2,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        self._coord1_entry.pack(side=tk.LEFT, padx=8, ipady=6)
        self._coord1_entry.bind("<Return>", self._on_enter_point)
        
        # Second coordinate
        coord2_frame = tk.Frame(input_inner, bg=self.COLORS['surface'])
        coord2_frame.pack(fill=tk.X, pady=4)
        
        self._coord2_label = tk.Label(
            coord2_frame, text="Y", width=3,
            bg=self.COLORS['surface'], fg=self.COLORS['accent_alt'],
            font=("Segoe UI", 11, "bold")
        )
        self._coord2_label.pack(side=tk.LEFT)
        
        self._coord2_var = tk.StringVar(value="0")
        self._coord2_entry = tk.Entry(
            coord2_frame, 
            textvariable=self._coord2_var,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 11),
            bd=0, width=15,
            highlightthickness=2,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        self._coord2_entry.pack(side=tk.LEFT, padx=8, ipady=6)
        self._coord2_entry.bind("<Return>", self._on_enter_point)
        
        # Angle unit (for polar mode)
        self._angle_frame = tk.Frame(input_inner, bg=self.COLORS['surface'])
        self._angle_var = tk.StringVar(value="degrees")
        
        tk.Label(
            self._angle_frame, text="Единицы угла:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._deg_btn = tk.Button(
            self._angle_frame, text="°",
            bg=self.COLORS['accent'], fg=self.COLORS['input_bg'],
            font=("Segoe UI", 10, "bold"),
            bd=0, padx=8, pady=2, cursor="hand2",
            command=lambda: self._set_angle_unit("degrees")
        )
        self._deg_btn.pack(side=tk.LEFT, padx=(8, 2))
        
        self._rad_btn = tk.Button(
            self._angle_frame, text="рад",
            bg=self.COLORS['surface'], fg=self.COLORS['text'],
            font=("Segoe UI", 9),
            bd=0, padx=8, pady=2, cursor="hand2",
            command=lambda: self._set_angle_unit("radians")
        )
        self._rad_btn.pack(side=tk.LEFT)
        
        # Submit button
        btn_frame = tk.Frame(input_inner, bg=self.COLORS['surface'])
        btn_frame.pack(fill=tk.X, pady=(12, 0))
        
        submit_btn = tk.Button(
            btn_frame, 
            text="⏎ Ввести точку",
            bg=self.COLORS['accent'],
            fg=self.COLORS['input_bg'],
            activebackground=self.COLORS['accent_alt'],
            font=("Segoe UI", 10, "bold"),
            bd=0, padx=16, pady=8, cursor="hand2",
            command=self._on_enter_point
        )
        submit_btn.pack(fill=tk.X)
        
        # Result section
        result_section = tk.Frame(self, bg=self.COLORS['bg'])
        result_section.pack(fill=tk.X, padx=12, pady=8)
        
        tk.Label(
            result_section, text="Результат",
            bg=self.COLORS['bg'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))
        
        result_box = tk.Frame(result_section, bg=self.COLORS['surface'])
        result_box.pack(fill=tk.X)
        
        result_inner = tk.Frame(result_box, bg=self.COLORS['surface'])
        result_inner.pack(fill=tk.X, padx=10, pady=8)
        
        self._cartesian_label = tk.Label(
            result_inner, 
            text="X: 0.00   Y: 0.00",
            bg=self.COLORS['surface'], fg=self.COLORS['text'],
            font=("JetBrains Mono", 10)
        )
        self._cartesian_label.pack(anchor=tk.W)
        
        self._polar_label = tk.Label(
            result_inner, 
            text="R: 0.00   θ: 0.00°",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("JetBrains Mono", 10)
        )
        self._polar_label.pack(anchor=tk.W)
        
        # Status
        self._status_frame = tk.Frame(self, bg=self.COLORS['input_bg'])
        self._status_frame.pack(fill=tk.X, padx=12, pady=8)
        
        self._status_label = tk.Label(
            self._status_frame, 
            text="  Режим: Абсолютные координаты",
            bg=self.COLORS['input_bg'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9),
            anchor=tk.W, padx=8, pady=6
        )
        self._status_label.pack(fill=tk.X)
        
        self._last_point: Optional[Tuple[float, float]] = None
    
    def _set_mode(self, mode: str):
        """Switch between cartesian and polar mode"""
        self._use_polar = mode == "polar"
        self._mode_var.set(mode)
        
        if self._use_polar:
            self._cart_btn.configure(bg=self.COLORS['surface'], fg=self.COLORS['text'])
            self._polar_btn.configure(bg=self.COLORS['accent'], fg=self.COLORS['input_bg'])
            self._coord1_label.config(text="R")
            self._coord2_label.config(text="θ")
            self._angle_frame.pack(fill=tk.X, pady=(8, 0))
        else:
            self._cart_btn.configure(bg=self.COLORS['accent'], fg=self.COLORS['input_bg'])
            self._polar_btn.configure(bg=self.COLORS['surface'], fg=self.COLORS['text'])
            self._coord1_label.config(text="X")
            self._coord2_label.config(text="Y")
            self._angle_frame.pack_forget()
    
    def _set_angle_unit(self, unit: str):
        """Set angle unit"""
        self._angle_unit = AngleUnit.DEGREES if unit == "degrees" else AngleUnit.RADIANS
        self._angle_var.set(unit)
        
        if unit == "degrees":
            self._deg_btn.configure(bg=self.COLORS['accent'], fg=self.COLORS['input_bg'])
            self._rad_btn.configure(bg=self.COLORS['surface'], fg=self.COLORS['text'])
        else:
            self._deg_btn.configure(bg=self.COLORS['surface'], fg=self.COLORS['text'])
            self._rad_btn.configure(bg=self.COLORS['accent'], fg=self.COLORS['input_bg'])
    
    def _on_enter_point(self, event=None):
        """Handle point entry"""
        try:
            coord1 = float(self._coord1_var.get())
            coord2 = float(self._coord2_var.get())
            
            if self._use_polar:
                theta_rad = coord2 if self._angle_unit == AngleUnit.RADIANS else math.radians(coord2)
                if self._use_relative_to_base and self._base_point:
                    x_rel, y_rel = polar_to_cartesian(coord1, theta_rad)
                    x = self._base_point[0] + x_rel
                    y = self._base_point[1] + y_rel
                else:
                    x, y = polar_to_cartesian(coord1, theta_rad)
            else:
                x, y = (coord1, coord2)
                if self._use_relative_to_base and self._base_point:
                    x += self._base_point[0]
                    y += self._base_point[1]
            
            self._last_point = (x, y)
            self._update_result(x, y)
            if self._on_point_entered:
                self._on_point_entered(x, y)
        except ValueError:
            pass
    
    def _update_result(self, x: float, y: float):
        """Update result display"""
        self._cartesian_label.config(text=f"X: {x:.2f}   Y: {y:.2f}")
        r, theta_rad = cartesian_to_polar(x, y)
        if self._angle_unit == AngleUnit.DEGREES:
            theta_deg = math.degrees(theta_rad)
            self._polar_label.config(text=f"R: {r:.2f}   θ: {theta_deg:.1f}°")
        else:
            self._polar_label.config(text=f"R: {r:.2f}   θ: {theta_rad:.3f} рад")
    
    def set_last_point(self, x: float, y: float):
        self._last_point = (x, y)
    
    def set_base_point(self, x: float, y: float, enable: bool = True):
        self._base_point = (x, y)
        self._use_relative_to_base = enable
        self._update_status()
    
    def clear_base_point(self):
        self._base_point = None
        self._use_relative_to_base = False
        self._update_status()
    
    def _update_status(self):
        if self._use_relative_to_base and self._base_point:
            self._status_label.config(
                text=f"  📍 Относительно: ({self._base_point[0]:.1f}, {self._base_point[1]:.1f})",
                fg=self.COLORS['accent']
            )
            self._status_frame.configure(bg=self.COLORS['surface'])
            self._status_label.configure(bg=self.COLORS['surface'])
        else:
            self._status_label.config(
                text="  Режим: Абсолютные координаты",
                fg=self.COLORS['text_muted']
            )
            self._status_frame.configure(bg=self.COLORS['input_bg'])
            self._status_label.configure(bg=self.COLORS['input_bg'])
    
    def get_point(self) -> Optional[Tuple[float, float]]:
        return self._last_point
    
    def clear(self):
        self._coord1_var.set("0")
        self._coord2_var.set("0")
        self._last_point = None
    
    def focus_input(self):
        self._coord1_entry.focus_set()
        self._coord1_entry.select_range(0, tk.END)
