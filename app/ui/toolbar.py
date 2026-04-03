"""
Toolbar - панель инструментов с современным дизайном
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict


class Toolbar(ttk.Frame):
    """Modern toolbar with drawing tools and actions"""
    
    # Color scheme (light theme)
    COLORS = {
        'bg': '#F8FAFC',
        'surface': '#FFFFFF',
        'surface_hover': '#F1F5F9',
        'accent': '#3B82F6',
        'accent_hover': '#2563EB',
        'text': '#1E293B',
        'text_muted': '#94A3B8',
        'success': '#22C55E',
        'warning': '#F59E0B',
        'border': '#CBD5E1',
    }
    
    def __init__(self, parent, on_tool_selected: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_tool_selected = on_tool_selected
        self._tool_buttons: Dict[str, tk.Button] = {}
        self._current_tool: Optional[str] = None
        self.configure(style="TFrame")
        self._create_widgets()
    
    def _create_widgets(self):
        # Main toolbar container with gradient-like effect
        self.configure(padding=(8, 4))
        
        # Tool groups with modern styling
        self._create_tool_group("Выделение", [
            ("select", "⬚", "Выделение (V)", False),
            ("pan", "✋", "Панорамирование (H)", False),
        ])
        
        self._add_separator()
        
        self._create_tool_group("Рисование", [
            ("segment", "╱", "Отрезок (L)", False),
            ("circle", "◯", "Окружность (C)", False),
            ("arc", "◜", "Дуга (A)", False),
            ("rectangle", "▢", "Прямоугольник (R)", False),
            ("ellipse", "⬯", "Эллипс (E)", False),
            ("polygon", "⬡", "Многоугольник (P)", False),
            ("spline", "∿", "Сплайн (S)", False),
        ])
        
        self._add_separator()

        self._create_tool_group("Размеры", [
            ("dim_linear", "↔", "Линейный размер (D)", False),
            ("dim_radius", "R", "Радиус", False),
            ("dim_diameter", "⌀", "Диаметр", False),
            ("dim_angle", "∠", "Угловой размер", False),
        ])

        self._add_separator()

        self._create_action_group("Навигация", [
            ("zoom_in", "⊕", "Увеличить (+)"),
            ("zoom_out", "⊖", "Уменьшить (-)"),
            ("zoom_fit", "◱", "Показать всё (F)"),
            ("rotate_left", "↺", "Повернуть влево ([)"),
            ("rotate_right", "↻", "Повернуть вправо (])"),
            ("reset_view", "⌂", "Сбросить вид (Home)"),
        ])
        
        self._add_separator()
        
        self._create_action_group("Редактирование", [
            ("delete", "🗑", "Удалить (Delete)"),
            ("clear_all", "⌧", "Очистить всё"),
        ], accent=True)
    
    def _create_tool_group(self, title: str, tools: list):
        """Create a group of tool buttons"""
        group_frame = tk.Frame(self, bg=self.COLORS['bg'])
        group_frame.pack(side=tk.LEFT, padx=4, pady=2)
        
        # Group label
        label = tk.Label(
            group_frame, 
            text=title, 
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_muted'],
            font=("Segoe UI", 8)
        )
        label.pack(side=tk.TOP, pady=(0, 2))
        
        # Buttons container
        btn_frame = tk.Frame(group_frame, bg=self.COLORS['bg'])
        btn_frame.pack(side=tk.TOP)
        
        for tool_id, icon, tooltip, is_accent in tools:
            self._add_tool_button(btn_frame, tool_id, icon, tooltip, is_accent)
    
    def _create_action_group(self, title: str, actions: list, accent: bool = False):
        """Create a group of action buttons"""
        group_frame = tk.Frame(self, bg=self.COLORS['bg'])
        group_frame.pack(side=tk.LEFT, padx=4, pady=2)
        
        # Group label
        label = tk.Label(
            group_frame, 
            text=title, 
            bg=self.COLORS['bg'],
            fg=self.COLORS['text_muted'],
            font=("Segoe UI", 8)
        )
        label.pack(side=tk.TOP, pady=(0, 2))
        
        # Buttons container
        btn_frame = tk.Frame(group_frame, bg=self.COLORS['bg'])
        btn_frame.pack(side=tk.TOP)
        
        for action_id, icon, tooltip in actions:
            self._add_action_button(btn_frame, action_id, icon, tooltip, accent)
    
    def _add_separator(self):
        """Add a vertical separator"""
        sep_frame = tk.Frame(self, bg=self.COLORS['border'], width=1)
        sep_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
    
    def _add_tool_button(self, parent, tool_id: str, icon: str, tooltip: str, is_accent: bool = False):
        """Create a modern tool button"""
        btn = tk.Button(
            parent,
            text=icon,
            font=("Segoe UI", 16),
            width=2,
            height=1,
            bd=0,
            bg=self.COLORS['surface'],
            fg=self.COLORS['text'],
            activebackground=self.COLORS['accent'],
            activeforeground=self.COLORS['bg'],
            cursor="hand2",
            relief="flat",
            command=lambda: self._select_tool(tool_id)
        )
        btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Bind hover effects
        btn.bind("<Enter>", lambda e: self._on_hover(btn, True))
        btn.bind("<Leave>", lambda e: self._on_hover(btn, False))
        
        self._tool_buttons[tool_id] = btn
        self._create_tooltip(btn, tooltip)
    
    def _add_action_button(self, parent, action_id: str, icon: str, tooltip: str, is_accent: bool = False):
        """Create a modern action button"""
        bg_color = self.COLORS['surface'] if not is_accent else self.COLORS['surface']
        
        btn = tk.Button(
            parent,
            text=icon,
            font=("Segoe UI", 14),
            width=2,
            height=1,
            bd=0,
            bg=bg_color,
            fg=self.COLORS['text'],
            activebackground=self.COLORS['accent'],
            activeforeground=self.COLORS['bg'],
            cursor="hand2",
            relief="flat",
            command=lambda: self._trigger_action(action_id)
        )
        btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Bind hover effects
        btn.bind("<Enter>", lambda e: self._on_hover(btn, True))
        btn.bind("<Leave>", lambda e: self._on_hover(btn, False))
        
        self._create_tooltip(btn, tooltip)
    
    def _on_hover(self, btn: tk.Button, entering: bool):
        """Handle button hover effect"""
        if btn in self._tool_buttons.values():
            tool_id = [k for k, v in self._tool_buttons.items() if v == btn]
            if tool_id and tool_id[0] == self._current_tool:
                return  # Don't change active button
        
        if entering:
            btn.configure(bg=self.COLORS['surface_hover'])
        else:
            btn.configure(bg=self.COLORS['surface'])
    
    def _select_tool(self, tool_id: str, notify: bool = True):
        """Select a tool and update button states"""
        # Reset all buttons
        for tid, btn in self._tool_buttons.items():
            if tid == tool_id:
                btn.configure(
                    bg=self.COLORS['accent'],
                    fg=self.COLORS['bg']
                )
            else:
                btn.configure(
                    bg=self.COLORS['surface'],
                    fg=self.COLORS['text']
                )
        
        self._current_tool = tool_id
        if notify and self._on_tool_selected:
            self._on_tool_selected(tool_id)
    
    def _trigger_action(self, action: str):
        """Trigger an action"""
        if self._on_tool_selected:
            self._on_tool_selected(f"action:{action}")
    
    def set_active_tool(self, tool_id: str):
        """Set the active tool externally"""
        self._select_tool(tool_id, notify=False)
    
    def _create_tooltip(self, widget, text: str):
        """Create a modern tooltip"""
        tooltip = None
        
        def show_tooltip(event):
            nonlocal tooltip
            if tooltip:
                return
            
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() + widget.winfo_height() + 5
            
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.configure(bg=self.COLORS['surface'])
            
            # Tooltip frame with border effect
            frame = tk.Frame(
                tooltip, 
                bg=self.COLORS['surface'],
                highlightbackground=self.COLORS['border'],
                highlightthickness=1
            )
            frame.pack()
            
            label = tk.Label(
                frame, 
                text=text, 
                bg=self.COLORS['surface'],
                fg=self.COLORS['text'],
                font=("Segoe UI", 9),
                padx=8,
                pady=4
            )
            label.pack()
            
            # Auto-hide after 2 seconds
            widget.after(2000, hide_tooltip)
        
        def hide_tooltip(event=None):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        widget.bind("<Enter>", lambda e: widget.after(500, lambda: show_tooltip(e) if widget.winfo_containing(widget.winfo_pointerx(), widget.winfo_pointery()) == widget else None))
        widget.bind("<Leave>", hide_tooltip)
