"""
Style Panel - панель стилей линий с современным дизайном
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from ..styles.style_manager import StyleManager
from ..styles.line_style import LineStyle, LineType, get_standard_thicknesses


class StylePanel(tk.Frame):
    """Modern panel for managing line styles"""
    
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
    
    def __init__(self, parent, on_style_changed: Callable = None, **kwargs):
        super().__init__(parent, bg=self.COLORS['bg'], **kwargs)
        self._on_style_changed = on_style_changed
        self._style_manager = StyleManager()
        self._dash_frame_packed = False
        self._create_widgets()
        self._update_style_list()
        self._style_manager.add_listener(self._update_style_list)
    
    def _create_widgets(self):
        # Title
        title_frame = tk.Frame(self, bg=self.COLORS['bg'])
        title_frame.pack(fill=tk.X, padx=12, pady=(12, 8))
        
        tk.Label(
            title_frame, 
            text="🎨 Стили линий", 
            bg=self.COLORS['bg'],
            fg=self.COLORS['accent'],
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W)
        
        # Separator
        tk.Frame(self, bg=self.COLORS['border'], height=1).pack(fill=tk.X, padx=12, pady=4)
        
        # Current style section
        current_section = tk.Frame(self, bg=self.COLORS['surface'])
        current_section.pack(fill=tk.X, padx=12, pady=8)
        
        current_inner = tk.Frame(current_section, bg=self.COLORS['surface'])
        current_inner.pack(fill=tk.X, padx=12, pady=12)
        
        tk.Label(
            current_inner, text="Текущий стиль",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W, pady=(0, 8))
        
        # Style selector
        self._current_style_var = tk.StringVar()
        self._style_combo = ttk.Combobox(
            current_inner, 
            textvariable=self._current_style_var, 
            state="readonly", 
            width=28,
            font=("Segoe UI", 10)
        )
        self._style_combo.pack(fill=tk.X, pady=4)
        self._style_combo.bind("<<ComboboxSelected>>", self._on_style_selected)
        
        # Preview canvas
        preview_frame = tk.Frame(current_inner, bg=self.COLORS['input_bg'], highlightthickness=1, highlightbackground=self.COLORS['border'])
        preview_frame.pack(fill=tk.X, pady=8)
        
        self._preview_canvas = tk.Canvas(
            preview_frame, 
            width=200, height=40, 
            bg=self.COLORS['input_bg'], 
            highlightthickness=0
        )
        self._preview_canvas.pack(fill=tk.X, padx=2, pady=2)
        
        # Thickness selector
        thick_frame = tk.Frame(current_inner, bg=self.COLORS['surface'])
        thick_frame.pack(fill=tk.X, pady=4)
        
        tk.Label(
            thick_frame, text="Толщина:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._thickness_var = tk.StringVar(value="0.8")
        thickness_values = [str(t) for t in get_standard_thicknesses()]
        self._thickness_combo = ttk.Combobox(
            thick_frame, 
            textvariable=self._thickness_var, 
            values=thickness_values, 
            state="readonly", 
            width=8,
            font=("Segoe UI", 10)
        )
        self._thickness_combo.pack(side=tk.LEFT, padx=8)
        self._thickness_combo.bind("<<ComboboxSelected>>", self._on_thickness_changed)
        
        tk.Label(
            thick_frame, text="мм",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        # Dash pattern section (hidden by default)
        self._dash_frame = tk.Frame(current_inner, bg=self.COLORS['surface'])
        
        tk.Label(
            self._dash_frame, text="Шаблон штриховки",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W, pady=(8, 4))
        
        # Dash length
        dash_length_frame = tk.Frame(self._dash_frame, bg=self.COLORS['surface'])
        dash_length_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(
            dash_length_frame, text="Длина штриха:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._dash_length_var = tk.StringVar(value="5.0")
        self._dash_length_entry = tk.Entry(
            dash_length_frame, 
            textvariable=self._dash_length_var, 
            width=8,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 10),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        self._dash_length_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self._dash_length_entry.bind("<KeyRelease>", self._on_dash_pattern_changed)
        
        tk.Label(
            dash_length_frame, text="мм",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        # Gap length
        gap_length_frame = tk.Frame(self._dash_frame, bg=self.COLORS['surface'])
        gap_length_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(
            gap_length_frame, text="Расстояние:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._gap_length_var = tk.StringVar(value="2.0")
        self._gap_length_entry = tk.Entry(
            gap_length_frame, 
            textvariable=self._gap_length_var, 
            width=8,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 10),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        self._gap_length_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self._gap_length_entry.bind("<KeyRelease>", self._on_dash_pattern_changed)
        
        tk.Label(
            gap_length_frame, text="мм",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        # Zigzag parameters section (hidden by default) - GOST style
        self._zigzag_frame = tk.Frame(current_inner, bg=self.COLORS['surface'])
        self._zigzag_frame_packed = False
        
        tk.Label(
            self._zigzag_frame, text="⚡ Параметры изломов (ГОСТ)",
            bg=self.COLORS['surface'], fg=self.COLORS['accent'],
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W, pady=(8, 4))
        
        # Zigzag amplitude (высота пика)
        zigzag_amp_frame = tk.Frame(self._zigzag_frame, bg=self.COLORS['surface'])
        zigzag_amp_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(
            zigzag_amp_frame, text="Амплитуда:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._zigzag_amplitude_var = tk.StringVar(value="4.0")
        self._zigzag_amplitude_entry = tk.Entry(
            zigzag_amp_frame, 
            textvariable=self._zigzag_amplitude_var, 
            width=6,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 10),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        self._zigzag_amplitude_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self._zigzag_amplitude_entry.bind("<KeyRelease>", self._on_zigzag_changed)
        
        tk.Label(
            zigzag_amp_frame, text="мм",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        # Zigzag width (ширина излома)
        zigzag_width_frame = tk.Frame(self._zigzag_frame, bg=self.COLORS['surface'])
        zigzag_width_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(
            zigzag_width_frame, text="Ширина излома:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._zigzag_width_var = tk.StringVar(value="6.0")
        self._zigzag_width_entry = tk.Entry(
            zigzag_width_frame, 
            textvariable=self._zigzag_width_var, 
            width=6,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 10),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        self._zigzag_width_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self._zigzag_width_entry.bind("<KeyRelease>", self._on_zigzag_changed)
        
        tk.Label(
            zigzag_width_frame, text="мм",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        # Zigzag gap (промежуток)
        zigzag_gap_frame = tk.Frame(self._zigzag_frame, bg=self.COLORS['surface'])
        zigzag_gap_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(
            zigzag_gap_frame, text="Промежуток:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._zigzag_gap_var = tk.StringVar(value="8.0")
        self._zigzag_gap_entry = tk.Entry(
            zigzag_gap_frame, 
            textvariable=self._zigzag_gap_var, 
            width=6,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 10),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        self._zigzag_gap_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self._zigzag_gap_entry.bind("<KeyRelease>", self._on_zigzag_changed)
        
        tk.Label(
            zigzag_gap_frame, text="мм",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        # Zigzag protrusion (выступ)
        zigzag_prot_frame = tk.Frame(self._zigzag_frame, bg=self.COLORS['surface'])
        zigzag_prot_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(
            zigzag_prot_frame, text="Выступ:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._zigzag_protrusion_var = tk.StringVar(value="2.0")
        self._zigzag_protrusion_entry = tk.Entry(
            zigzag_prot_frame, 
            textvariable=self._zigzag_protrusion_var, 
            width=6,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 10),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        self._zigzag_protrusion_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self._zigzag_protrusion_entry.bind("<KeyRelease>", self._on_zigzag_changed)
        
        tk.Label(
            zigzag_prot_frame, text="мм",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        # Legacy variables for compatibility
        self._zigzag_length_var = tk.StringVar(value="10.0")
        self._zigzag_height_var = tk.StringVar(value="4.0")
        
        # Wavy parameters section (hidden by default)
        self._wavy_frame = tk.Frame(current_inner, bg=self.COLORS['surface'])
        self._wavy_frame_packed = False
        
        tk.Label(
            self._wavy_frame, text="〰 Параметры волны",
            bg=self.COLORS['surface'], fg=self.COLORS['accent_alt'],
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W, pady=(8, 4))
        
        # Wavy length
        wavy_length_frame = tk.Frame(self._wavy_frame, bg=self.COLORS['surface'])
        wavy_length_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(
            wavy_length_frame, text="Длина волны:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._wavy_length_var = tk.StringVar(value="15.0")
        self._wavy_length_entry = tk.Entry(
            wavy_length_frame, 
            textvariable=self._wavy_length_var, 
            width=8,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 10),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        self._wavy_length_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self._wavy_length_entry.bind("<KeyRelease>", self._on_wavy_changed)
        
        tk.Label(
            wavy_length_frame, text="мм",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        # Wavy height
        wavy_height_frame = tk.Frame(self._wavy_frame, bg=self.COLORS['surface'])
        wavy_height_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(
            wavy_height_frame, text="Амплитуда:",
            bg=self.COLORS['surface'], fg=self.COLORS['text_secondary'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        self._wavy_height_var = tk.StringVar(value="3.0")
        self._wavy_height_entry = tk.Entry(
            wavy_height_frame, 
            textvariable=self._wavy_height_var, 
            width=8,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['accent'],
            font=("JetBrains Mono", 10),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.COLORS['border'],
            highlightcolor=self.COLORS['accent']
        )
        self._wavy_height_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self._wavy_height_entry.bind("<KeyRelease>", self._on_wavy_changed)
        
        tk.Label(
            wavy_height_frame, text="мм",
            bg=self.COLORS['surface'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)
        
        # Available styles section
        list_section = tk.Frame(self, bg=self.COLORS['bg'])
        list_section.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        tk.Label(
            list_section, text="Доступные стили",
            bg=self.COLORS['bg'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W, pady=(0, 4))
        
        # Listbox with scrollbar
        list_container = tk.Frame(list_section, bg=self.COLORS['input_bg'])
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._style_listbox = tk.Listbox(
            list_container, 
            yscrollcommand=scrollbar.set, 
            height=8,
            selectmode=tk.SINGLE,
            bg=self.COLORS['input_bg'],
            fg=self.COLORS['text'],
            selectbackground=self.COLORS['accent'],
            selectforeground=self.COLORS['input_bg'],
            highlightthickness=0,
            bd=0,
            font=("Segoe UI", 10)
        )
        self._style_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._style_listbox.yview)
        self._style_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        
        # Quick access buttons
        quick_section = tk.Frame(self, bg=self.COLORS['bg'])
        quick_section.pack(fill=tk.X, padx=12, pady=(4, 12))
        
        tk.Label(
            quick_section, text="Быстрый доступ",
            bg=self.COLORS['bg'], fg=self.COLORS['text_muted'],
            font=("Segoe UI", 9)
        ).pack(anchor=tk.W, pady=(0, 4))
        
        buttons_frame = tk.Frame(quick_section, bg=self.COLORS['bg'])
        buttons_frame.pack(fill=tk.X)
        
        quick_styles = [
            ("Основная", "solid_main", self.COLORS['text']),
            ("Тонкая", "solid_thin", self.COLORS['text_secondary']),
            ("Штриховая", "dashed", self.COLORS['warning']),
            ("С изломами", "solid_zigzag", self.COLORS['accent']),
        ]
        
        for text, style_id, color in quick_styles:
            btn = tk.Button(
                buttons_frame, 
                text=text,
                bg=self.COLORS['surface'],
                fg=color,
                activebackground=self.COLORS['accent'],
                activeforeground=self.COLORS['input_bg'],
                font=("Segoe UI", 9),
                bd=0, padx=12, pady=6, cursor="hand2",
                command=lambda s=style_id: self._quick_select(s)
            )
            btn.pack(side=tk.LEFT, padx=(0, 4))
    
    def _update_style_list(self):
        """Update the style list"""
        styles = self._style_manager.get_style_list()
        style_names = [s[1] for s in styles]
        self._style_combo["values"] = style_names
        
        self._style_listbox.delete(0, tk.END)
        for style_id, style_name in styles:
            style = self._style_manager.get_style(style_id)
            prefix = "● " if style.is_system else "○ "
            self._style_listbox.insert(tk.END, prefix + style_name)
        
        current_id = self._style_manager.get_current_style_id()
        current_style = self._style_manager.get_style(current_id)
        if current_style:
            self._current_style_var.set(current_style.name)
            self._thickness_var.set(str(current_style.thickness))
            self._dash_length_var.set(str(current_style.dash_length))
            self._gap_length_var.set(str(current_style.gap_length))
            self._zigzag_amplitude_var.set(str(current_style.zigzag_amplitude))
            self._zigzag_width_var.set(str(current_style.zigzag_width))
            self._zigzag_gap_var.set(str(current_style.zigzag_gap))
            self._zigzag_protrusion_var.set(str(current_style.zigzag_protrusion))
            self._wavy_length_var.set(str(current_style.wavy_length))
            self._wavy_height_var.set(str(current_style.wavy_height))
            self._update_special_frames_visibility()
            self._update_preview()
    
    def _update_preview(self):
        """Update the preview canvas"""
        self._preview_canvas.delete("all")
        current_id = self._style_manager.get_current_style_id()
        style = self._style_manager.get_style(current_id)
        if not style:
            return
        
        width = self._preview_canvas.winfo_width() or 200
        y = 20
        dash = style.get_tkinter_dash(0.5)
        line_width = max(1, style.thickness * 2)
        
        # Use accent color for preview
        color = self.COLORS['accent']
        
        if dash:
            self._preview_canvas.create_line(15, y, width - 15, y, fill=color, width=line_width, dash=dash)
        else:
            self._preview_canvas.create_line(15, y, width - 15, y, fill=color, width=line_width)
    
    def _on_style_selected(self, event):
        """Handle style selection from combobox"""
        style_name = self._current_style_var.get()
        styles = self._style_manager.get_style_list()
        for style_id, name in styles:
            if name == style_name:
                self._style_manager.set_current_style(style_id)
                style = self._style_manager.get_style(style_id)
                if style:
                    self._thickness_var.set(str(style.thickness))
                    self._dash_length_var.set(str(style.dash_length))
                    self._gap_length_var.set(str(style.gap_length))
                    self._zigzag_amplitude_var.set(str(style.zigzag_amplitude))
                    self._zigzag_width_var.set(str(style.zigzag_width))
                    self._zigzag_gap_var.set(str(style.zigzag_gap))
                    self._zigzag_protrusion_var.set(str(style.zigzag_protrusion))
                    self._wavy_length_var.set(str(style.wavy_length))
                    self._wavy_height_var.set(str(style.wavy_height))
                    self._update_special_frames_visibility()
                    self._update_preview()
                if self._on_style_changed:
                    self._on_style_changed(style_id)
                break
    
    def _on_listbox_select(self, event):
        """Handle style selection from listbox"""
        selection = self._style_listbox.curselection()
        if not selection:
            return
        styles = self._style_manager.get_style_list()
        if selection[0] < len(styles):
            style_id = styles[selection[0]][0]
            self._style_manager.set_current_style(style_id)
            self._current_style_var.set(styles[selection[0]][1])
            style = self._style_manager.get_style(style_id)
            if style:
                self._thickness_var.set(str(style.thickness))
                self._dash_length_var.set(str(style.dash_length))
                self._gap_length_var.set(str(style.gap_length))
                self._zigzag_amplitude_var.set(str(style.zigzag_amplitude))
                self._zigzag_width_var.set(str(style.zigzag_width))
                self._zigzag_gap_var.set(str(style.zigzag_gap))
                self._zigzag_protrusion_var.set(str(style.zigzag_protrusion))
                self._wavy_length_var.set(str(style.wavy_length))
                self._wavy_height_var.set(str(style.wavy_height))
                self._update_special_frames_visibility()
                self._update_preview()
            if self._on_style_changed:
                self._on_style_changed(style_id)
    
    def _on_thickness_changed(self, event):
        """Handle thickness change"""
        try:
            thickness = float(self._thickness_var.get())
            current_id = self._style_manager.get_current_style_id()
            self._style_manager.update_style(current_id, thickness=thickness)
            self._update_preview()
            if self._on_style_changed:
                self._on_style_changed(current_id)
        except ValueError:
            pass
    
    def _on_dash_pattern_changed(self, event=None):
        """Handle dash pattern change"""
        try:
            dash_length = float(self._dash_length_var.get())
            gap_length = float(self._gap_length_var.get())
            current_id = self._style_manager.get_current_style_id()
            style = self._style_manager.get_style(current_id)
            if style and style.dash_pattern:
                from ..styles.line_style import LineType
                if style.line_type == LineType.DASHED:
                    new_pattern = [dash_length, gap_length]
                elif style.line_type == LineType.DASH_DOT_THIN or style.line_type == LineType.DASH_DOT_THICK:
                    new_pattern = [dash_length, gap_length, 1.0, gap_length]
                elif style.line_type == LineType.DASH_DOT_DOT:
                    new_pattern = [dash_length, gap_length, 1.0, gap_length, 1.0, gap_length]
                else:
                    new_pattern = style.dash_pattern.copy()
                self._style_manager.update_style(current_id, dash_length=dash_length, gap_length=gap_length, dash_pattern=new_pattern)
                self._update_preview()
                if self._on_style_changed:
                    self._on_style_changed(current_id)
        except ValueError:
            pass
    
    def _update_special_frames_visibility(self):
        """Show/hide special parameter controls based on line type"""
        from ..styles.line_style import LineType
        
        current_id = self._style_manager.get_current_style_id()
        style = self._style_manager.get_style(current_id)
        
        if not style:
            return
        
        # Hide all special frames first
        if self._dash_frame_packed:
            self._dash_frame.pack_forget()
            self._dash_frame_packed = False
        if self._zigzag_frame_packed:
            self._zigzag_frame.pack_forget()
            self._zigzag_frame_packed = False
        if self._wavy_frame_packed:
            self._wavy_frame.pack_forget()
            self._wavy_frame_packed = False
        
        # Show appropriate frame based on line type
        if style.line_type == LineType.SOLID_THIN_ZIGZAG:
            self._zigzag_frame.pack(fill=tk.X, pady=(8, 0))
            self._zigzag_frame_packed = True
        elif style.line_type == LineType.SOLID_WAVY:
            self._wavy_frame.pack(fill=tk.X, pady=(8, 0))
            self._wavy_frame_packed = True
        elif style.dash_pattern and len(style.dash_pattern) > 0:
            self._dash_frame.pack(fill=tk.X, pady=(8, 0))
            self._dash_frame_packed = True
    
    def _update_dash_frame_visibility(self):
        """Legacy method - calls new method"""
        self._update_special_frames_visibility()
    
    def _on_zigzag_changed(self, event=None):
        """Handle zigzag parameter change - GOST style"""
        try:
            zigzag_amplitude = float(self._zigzag_amplitude_var.get())
            zigzag_width = float(self._zigzag_width_var.get())
            zigzag_gap = float(self._zigzag_gap_var.get())
            zigzag_protrusion = float(self._zigzag_protrusion_var.get())
            
            if zigzag_amplitude > 0 and zigzag_width > 0 and zigzag_gap >= 0:
                current_id = self._style_manager.get_current_style_id()
                self._style_manager.update_style(
                    current_id, 
                    zigzag_amplitude=zigzag_amplitude,
                    zigzag_width=zigzag_width,
                    zigzag_gap=zigzag_gap,
                    zigzag_protrusion=zigzag_protrusion
                )
                self._update_preview()
                if self._on_style_changed:
                    self._on_style_changed(current_id)
        except ValueError:
            pass
    
    def _on_wavy_changed(self, event=None):
        """Handle wavy parameter change"""
        try:
            wavy_length = float(self._wavy_length_var.get())
            wavy_height = float(self._wavy_height_var.get())
            
            if wavy_length > 0 and wavy_height > 0:
                current_id = self._style_manager.get_current_style_id()
                self._style_manager.update_style(
                    current_id, 
                    wavy_length=wavy_length, 
                    wavy_height=wavy_height
                )
                self._update_preview()
                if self._on_style_changed:
                    self._on_style_changed(current_id)
        except ValueError:
            pass
    
    def _quick_select(self, style_id: str):
        """Quick select a style"""
        self._style_manager.set_current_style(style_id)
        style = self._style_manager.get_style(style_id)
        if style:
            self._current_style_var.set(style.name)
            self._thickness_var.set(str(style.thickness))
            self._dash_length_var.set(str(style.dash_length))
            self._gap_length_var.set(str(style.gap_length))
            self._zigzag_amplitude_var.set(str(style.zigzag_amplitude))
            self._zigzag_width_var.set(str(style.zigzag_width))
            self._zigzag_gap_var.set(str(style.zigzag_gap))
            self._zigzag_protrusion_var.set(str(style.zigzag_protrusion))
            self._wavy_length_var.set(str(style.wavy_length))
            self._wavy_height_var.set(str(style.wavy_height))
            self._update_special_frames_visibility()
            self._update_preview()
        if self._on_style_changed:
            self._on_style_changed(style_id)
    
    def get_current_style_id(self) -> str:
        return self._style_manager.get_current_style_id()
