"""
Properties Panel - панель свойств объектов с современным дизайном
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable, Dict, Any
import math


class PropertiesPanel(tk.Frame):
    """Modern panel for editing primitive properties"""
    
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
    
    def __init__(self, parent, on_property_changed: Callable = None, **kwargs):
        super().__init__(parent, bg=self.COLORS['bg'], **kwargs)
        self._on_property_changed = on_property_changed
        self._current_primitives: List = []
        self._property_widgets: Dict[str, tk.Widget] = {}
        self._updating = False
        self._create_widgets()
    
    def _create_widgets(self):
        # Title
        title_frame = tk.Frame(self, bg=self.COLORS['bg'])
        title_frame.pack(fill=tk.X, padx=12, pady=(12, 8))
        
        tk.Label(
            title_frame, 
            text="📋 Свойства", 
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent'],
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W)
        
        # Separator
        tk.Frame(self, bg=self.COLORS['border'], height=1).pack(fill=tk.X, padx=12, pady=4)
        
        # Properties container
        self._props_frame = tk.Frame(self, bg=self.COLORS['bg'])
        self._props_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        self._show_no_selection()
    
    def _show_no_selection(self):
        """Show no selection message"""
        no_sel_frame = tk.Frame(self._props_frame, bg=self.COLORS['surface'])
        no_sel_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(
            no_sel_frame, 
            text="⬚ Нет выделенных объектов",
            bg=self.COLORS['surface'],
            fg=self.COLORS['text_muted'],
            font=("Segoe UI", 10),
            pady=20
        ).pack()
    
    def update_selection(self, primitives: List):
        """Update properties for selected primitives"""
        self._current_primitives = primitives
        
        # Clear existing widgets
        for widget in self._props_frame.winfo_children():
            widget.destroy()
        self._property_widgets.clear()
        
        if not primitives:
            self._show_no_selection()
            return
        
        if len(primitives) == 1:
            self._show_single_properties(primitives[0])
        else:
            self._show_multiple_properties(primitives)
    
    def _show_single_properties(self, primitive):
        """Show properties for single primitive"""
        props = primitive.get_properties()
        
        # Type info section
        type_section = tk.Frame(self._props_frame, bg=self.COLORS['surface'])
        type_section.pack(fill=tk.X, pady=(0, 8))
        
        type_inner = tk.Frame(type_section, bg=self.COLORS['surface'])
        type_inner.pack(fill=tk.X, padx=10, pady=8)
        
        tk.Label(
            type_inner, text="Тип объекта",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(anchor=tk.W)
        
        tk.Label(
            type_inner, text=props.get("type", "Неизвестно"),
            bg=self.COLORS['surface'], fg=self.COLORS['accent'],
            font=("Segoe UI", 11, "bold")
        ).pack(anchor=tk.W)
        
        # Editable properties section
        props_section = tk.Frame(self._props_frame, bg=self.COLORS['surface'])
        props_section.pack(fill=tk.X, pady=(0, 8))
        
        props_inner = tk.Frame(props_section, bg=self.COLORS['surface'])
        props_inner.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            props_inner, text="Свойства",
            bg=self.COLORS['surface'], fg=self.COLORS['accent'],
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W, pady=(0, 6))
        
        editable_props = self._get_editable_properties(primitive)
        for prop_name, prop_config in editable_props.items():
            if prop_name in props:
                self._create_property_row(props_inner, prop_name, props[prop_name], prop_config)
        
        # Computed properties section
        readonly_props = ["length", "area", "perimeter", "circumference", "arc_length"]
        computed = [(p, props[p]) for p in readonly_props if p in props]
        
        if computed:
            computed_section = tk.Frame(self._props_frame, bg=self.COLORS['surface'])
            computed_section.pack(fill=tk.X)
            
            computed_inner = tk.Frame(computed_section, bg=self.COLORS['surface'])
            computed_inner.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Label(
                computed_inner, text="Вычисляемые",
                bg=self.COLORS['surface'], fg=self.COLORS['accent_alt'],
                font=("Segoe UI", 9, "bold")
            ).pack(anchor=tk.W, pady=(0, 6))
            
            for prop_name, value in computed:
                self._create_readonly_row(computed_inner, prop_name, value)
    
    def _show_multiple_properties(self, primitives: List):
        """Show properties for multiple primitives"""
        # Selection info
        info_section = tk.Frame(self._props_frame, bg=self.COLORS['surface'])
        info_section.pack(fill=tk.X, pady=(0, 8))
        
        info_inner = tk.Frame(info_section, bg=self.COLORS['surface'])
        info_inner.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            info_inner, 
            text=f"⬚ Выделено: {len(primitives)} объектов",
            bg=self.COLORS['surface'], fg=self.COLORS['accent'],
            font=("Segoe UI", 11, "bold")
        ).pack(anchor=tk.W)
        
        # Type breakdown
        type_counts = {}
        for p in primitives:
            type_name = p.get_type_name()
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        for type_name, count in type_counts.items():
            tk.Label(
                info_inner, 
                text=f"  • {type_name}: {count}",
                bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
                font=("Segoe UI", 9)
            ).pack(anchor=tk.W)
        
        # Common style property
        style_section = tk.Frame(self._props_frame, bg=self.COLORS['surface'])
        style_section.pack(fill=tk.X)
        
        style_inner = tk.Frame(style_section, bg=self.COLORS['surface'])
        style_inner.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            style_inner, text="Общий стиль",
            bg=self.COLORS['surface'], fg=self.COLORS['accent'],
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W, pady=(0, 6))
        
        style_row = tk.Frame(style_inner, bg=self.COLORS['surface'])
        style_row.pack(fill=tk.X, pady=2)
        
        tk.Label(
            style_row, text="Стиль:", width=10,
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9), anchor=tk.W
        ).pack(side=tk.LEFT)
        
        from ..styles.style_manager import StyleManager
        sm = StyleManager()
        styles = sm.get_style_list()
        style_names = [s[1] for s in styles]
        style_ids = [s[0] for s in styles]
        
        var = tk.StringVar()
        primitive_styles = set((p.style_id for p in primitives))
        if len(primitive_styles) == 1:
            current_style_id = list(primitive_styles)[0]
            for sid, sname in styles:
                if sid == current_style_id:
                    var.set(sname)
                    break
        else:
            var.set("— Разные —")
        
        display_names = ["— Разные —"] + style_names
        display_ids = [None] + style_ids
        
        combo = ttk.Combobox(style_row, textvariable=var, values=display_names, state="readonly", width=20)
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def make_multi_style_handler(sids, snames, prims_list):
            def handler(event):
                selected_name = combo.get()
                if selected_name == "— Разные —":
                    return
                if selected_name in snames:
                    idx = snames.index(selected_name)
                    if idx >= 0 and idx < len(sids) and (sids[idx] is not None):
                        for primitive in prims_list:
                            primitive.set_property("style_id", sids[idx])
                        if self._on_property_changed:
                            self._on_property_changed()
            return handler
        
        combo.bind("<<ComboboxSelected>>", make_multi_style_handler(display_ids, display_names, primitives))
        self._property_widgets["style_id"] = (combo, var)
    
    def _get_editable_properties(self, primitive) -> Dict[str, Dict]:
        """Get editable properties configuration"""
        type_name = primitive.get_type_name()
        common_props = {"style_id": {"label": "Стиль", "type": "style"}}
        type_props = {
            "Отрезок": {
                "x1": {"label": "X₁", "type": "float"},
                "y1": {"label": "Y₁", "type": "float"},
                "x2": {"label": "X₂", "type": "float"},
                "y2": {"label": "Y₂", "type": "float"},
            },
            "Окружность": {
                "cx": {"label": "Центр X", "type": "float"},
                "cy": {"label": "Центр Y", "type": "float"},
                "radius": {"label": "Радиус", "type": "float"},
            },
            "Дуга": {
                "cx": {"label": "Центр X", "type": "float"},
                "cy": {"label": "Центр Y", "type": "float"},
                "radius": {"label": "Радиус", "type": "float"},
                "start_angle_deg": {"label": "Угол нач.", "type": "float"},
                "end_angle_deg": {"label": "Угол кон.", "type": "float"},
            },
            "Прямоугольник": {
                "x": {"label": "X", "type": "float"},
                "y": {"label": "Y", "type": "float"},
                "width": {"label": "Ширина", "type": "float"},
                "height": {"label": "Высота", "type": "float"},
                "corner_radius": {"label": "Скругл.", "type": "float"},
            },
            "Эллипс": {
                "cx": {"label": "Центр X", "type": "float"},
                "cy": {"label": "Центр Y", "type": "float"},
                "rx": {"label": "Полуось X", "type": "float"},
                "ry": {"label": "Полуось Y", "type": "float"},
            },
            "Многоугольник": {
                "cx": {"label": "Центр X", "type": "float"},
                "cy": {"label": "Центр Y", "type": "float"},
                "radius": {"label": "Радиус", "type": "float"},
                "num_sides": {"label": "Сторон", "type": "int"},
            },
        }
        props = type_props.get(type_name, {})
        props.update(common_props)
        return props
    
    def _create_property_row(self, parent, prop_name: str, value: Any, config: Dict):
        """Create a property edit row"""
        frame = tk.Frame(parent, bg=self.COLORS['surface'])
        frame.pack(fill=tk.X, pady=3)
        
        tk.Label(
            frame, text=config["label"] + ":", width=10,
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9), anchor=tk.W
        ).pack(side=tk.LEFT)
        
        prop_type = config.get("type", "string")
        
        if prop_type in ["float", "int"]:
            var = tk.StringVar(value=self._format_value(value, prop_type))
            entry = tk.Entry(
                frame, textvariable=var, width=12,
                bg=self.COLORS['input_bg'], fg=self.COLORS['text'],
                insertbackground=self.COLORS['accent'],
                font=("JetBrains Mono", 10),
                bd=0, highlightthickness=1,
                highlightbackground=self.COLORS['border'],
                highlightcolor=self.COLORS['accent']
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
            var.trace_add("write", lambda *args, pn=prop_name, v=var, pt=prop_type: self._on_entry_change(pn, v, pt))
            self._property_widgets[prop_name] = (entry, var)
            
        elif prop_type == "style":
            from ..styles.style_manager import StyleManager
            sm = StyleManager()
            styles = sm.get_style_list()
            style_names = [s[1] for s in styles]
            style_ids = [s[0] for s in styles]
            var = tk.StringVar()
            for sid, sname in styles:
                if sid == value:
                    var.set(sname)
                    break
            combo = ttk.Combobox(frame, textvariable=var, values=style_names, state="readonly", width=18)
            combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            def make_style_handler(pname, sids, snames):
                def handler(event):
                    selected_value = combo.get()
                    if selected_value in snames:
                        idx = snames.index(selected_value)
                        if idx >= 0 and idx < len(sids):
                            self._apply_property_change(pname, sids[idx])
                return handler
            
            combo.bind("<<ComboboxSelected>>", make_style_handler(prop_name, style_ids, style_names))
            self._property_widgets[prop_name] = (combo, var)
    
    def _create_readonly_row(self, parent, prop_name: str, value: Any):
        """Create a readonly property row"""
        frame = tk.Frame(parent, bg=self.COLORS['surface'])
        frame.pack(fill=tk.X, pady=2)
        
        labels = {
            "length": "Длина",
            "area": "Площадь",
            "perimeter": "Периметр",
            "circumference": "Длина окр.",
            "arc_length": "Длина дуги",
        }
        label_text = labels.get(prop_name, prop_name)
        
        tk.Label(
            frame, text=label_text + ":", width=10,
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9), anchor=tk.W
        ).pack(side=tk.LEFT)
        
        tk.Label(
            frame, text=f"{value:.2f}",
            bg=self.COLORS['surface'], fg=self.COLORS['text'],
            font=("JetBrains Mono", 10)
        ).pack(side=tk.LEFT)
    
    def _format_value(self, value: Any, prop_type: str) -> str:
        """Format value for display"""
        if prop_type == "float":
            return f"{value:.2f}"
        elif prop_type == "int":
            return str(int(value))
        return str(value)
    
    def _on_entry_change(self, prop_name: str, var: tk.StringVar, prop_type: str):
        """Handle entry value change"""
        if self._updating:
            return
        try:
            value_str = var.get()
            if prop_type == "float":
                value = float(value_str)
            elif prop_type == "int":
                value = int(value_str)
            else:
                value = value_str
            self._apply_property_change(prop_name, value)
        except ValueError:
            pass
    
    def _apply_property_change(self, prop_name: str, value: Any):
        """Apply property change to primitives"""
        if not self._current_primitives:
            return
        for primitive in self._current_primitives:
            primitive.set_property(prop_name, value)
        if self._on_property_changed:
            self._on_property_changed()
    
    def refresh(self):
        """Refresh properties display"""
        if self._current_primitives:
            self.update_selection(self._current_primitives)
