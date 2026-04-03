"""
Main CAD Application
Главное приложение CAD системы
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math

from .canvas import CADCanvas
from .tools import SelectTool, PanTool
from .tools.draw_tools import (
    SegmentTool, CircleTool, ArcTool, RectangleTool,
    EllipseTool, PolygonTool, SplineTool
)
from .tools.dimension_tools import (
    LinearDimensionTool, RadialDimensionTool,
    DiameterDimensionTool, AngularDimensionTool
)
from .ui import Toolbar, PropertiesPanel, StylePanel, StatusBar, SettingsPanel, InputPanel
from .primitives.base import SnapType
from .export.dxf_exporter import DXFExporter
from .export.dxf_importer import DXFImporter


class CADApplication:
    """
    Main CAD Application class
    Главный класс CAD приложения
    """
    
    def __init__(self):
        # Create main window
        self.root = tk.Tk()
        self.root.title("GeomModel CAD - Система геометрического моделирования")
        self.root.geometry("1600x1000")
        
        # Set minimum size
        self.root.minsize(1200, 700)
        
        # Configure style
        self._configure_styles()
        
        # Create tools
        self._tools = {
            "select": SelectTool(),
            "pan": PanTool(),
            "segment": SegmentTool(),
            "circle": CircleTool(),
            "arc": ArcTool(),
            "rectangle": RectangleTool(),
            "ellipse": EllipseTool(),
            "polygon": PolygonTool(),
            "spline": SplineTool(),
            "dim_linear": LinearDimensionTool(),
            "dim_radius": RadialDimensionTool(),
            "dim_diameter": DiameterDimensionTool(),
            "dim_angle": AngularDimensionTool(),
        }
        
        # Create UI
        self._create_menu()
        self._create_ui()
        
        # Bind keyboard shortcuts
        self._bind_shortcuts()
        
        # Set default tool
        self._set_tool("select")
    
    def _configure_styles(self):
        """Configure ttk styles with modern light design"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern light color scheme
        bg_light = "#F8FAFC"       # Main light background
        bg_medium = "#FFFFFF"      # White for panels
        bg_dark = "#F1F5F9"        # Slightly darker for inputs
        surface = "#E2E8F0"        # Surface color for buttons
        
        accent_primary = "#3B82F6"  # Vibrant blue accent
        accent_secondary = "#8B5CF6" # Purple accent for active states
        accent_success = "#22C55E"  # Green for success
        accent_warning = "#F59E0B"  # Amber for warnings
        
        text_primary = "#1E293B"   # Dark text
        text_secondary = "#475569" # Secondary text
        text_muted = "#94A3B8"     # Muted text
        
        border_color = "#CBD5E1"   # Border color
        border_focus = "#3B82F6"   # Focus border
        
        # Configure root window background
        self.root.configure(bg=bg_light)
        
        # Root and main frames
        style.configure(".", background=bg_light, foreground=text_primary, font=("Segoe UI", 10))
        style.configure("TFrame", background=bg_light)
        style.configure("TLabel", background=bg_light, foreground=text_primary)
        
        # Panel frames (for sidebar)
        style.configure("Panel.TFrame", background=bg_medium)
        style.configure("Panel.TLabel", background=bg_medium, foreground=text_primary)
        
        # Notebook (tabs) - modern tab style
        style.configure("TNotebook", background=bg_light, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("TNotebook.Tab", 
                       background=bg_medium, 
                       foreground=text_secondary,
                       padding=[16, 10], 
                       borderwidth=0,
                       font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab",
                 background=[("selected", accent_primary), ("!selected", bg_medium)],
                 foreground=[("selected", "#FFFFFF"), ("!selected", text_secondary)])
        
        # Label frames with modern look
        style.configure("TLabelframe", 
                       background=bg_medium, 
                       borderwidth=1, 
                       relief="flat",
                       bordercolor=border_color)
        style.configure("TLabelframe.Label", 
                       background=bg_medium, 
                       foreground=accent_primary, 
                       font=("Segoe UI", 9, "bold"))
        
        # Toolbar buttons - sleek modern style
        style.configure("Toolbar.TButton",
                       background=bg_medium,
                       foreground=text_primary,
                       padding=8,
                       borderwidth=0,
                       font=("Segoe UI", 14))
        style.map("Toolbar.TButton",
                 background=[("active", accent_primary), ("pressed", accent_secondary)],
                 foreground=[("active", "#FFFFFF"), ("pressed", "#FFFFFF")])
        
        # Active toolbar button
        style.configure("Active.Toolbar.TButton",
                       background=accent_primary,
                       foreground="#FFFFFF")
        
        # Entry with light theme
        style.configure("TEntry",
                       fieldbackground="#FFFFFF",
                       foreground=text_primary,
                       insertcolor=text_primary,
                       borderwidth=2,
                       relief="flat",
                       padding=8)
        style.map("TEntry",
                 fieldbackground=[("focus", "#FFFFFF")],
                 bordercolor=[("focus", accent_primary)])
        
        # Combobox light theme
        style.configure("TCombobox",
                       fieldbackground="#FFFFFF",
                       background="#FFFFFF",
                       foreground=text_primary,
                       arrowcolor=text_secondary,
                       borderwidth=2,
                       relief="flat",
                       padding=5)
        style.map("TCombobox",
                 fieldbackground=[("focus", "#FFFFFF"), ("readonly", "#FFFFFF")],
                 background=[("active", bg_dark)],
                 arrowcolor=[("focus", accent_primary)])
        
        # Modern scrollbar
        style.configure("TScrollbar",
                       background=bg_medium,
                       troughcolor=bg_light,
                       borderwidth=0,
                       arrowcolor=text_muted,
                       width=12)
        style.map("TScrollbar",
                 background=[("active", accent_primary), ("!active", surface)])
        
        # Checkbutton and Radiobutton
        style.configure("TCheckbutton",
                       background=bg_medium,
                       foreground=text_primary,
                       focuscolor="none",
                       indicatorcolor="#FFFFFF")
        style.map("TCheckbutton",
                 background=[("active", bg_medium)],
                 indicatorcolor=[("selected", accent_primary)])
        
        style.configure("TRadiobutton",
                       background=bg_medium,
                       foreground=text_primary,
                       focuscolor="none",
                       indicatorcolor="#FFFFFF")
        style.map("TRadiobutton",
                 background=[("active", bg_medium)],
                 indicatorcolor=[("selected", accent_primary)])
        
        # Modern button
        style.configure("TButton",
                       background=surface,
                       foreground=text_primary,
                       borderwidth=0,
                       relief="flat",
                       padding=[12, 8],
                       focuscolor="none",
                       font=("Segoe UI", 9))
        style.map("TButton",
                 background=[("active", accent_primary), ("pressed", accent_secondary)],
                 foreground=[("active", "#FFFFFF"), ("pressed", "#FFFFFF")])
        
        # Accent button (for primary actions)
        style.configure("Accent.TButton",
                       background=accent_primary,
                       foreground="#FFFFFF",
                       font=("Segoe UI", 9, "bold"))
        style.map("Accent.TButton",
                 background=[("active", accent_secondary), ("pressed", accent_primary)])
        
        # Scale
        style.configure("TScale",
                       background=bg_medium,
                       troughcolor=bg_dark,
                       borderwidth=0)
        style.map("TScale",
                 background=[("active", accent_primary)])
        
        # Separator
        style.configure("TSeparator", background=border_color)
        
        # Progressbar
        style.configure("TProgressbar",
                       background=accent_primary,
                       troughcolor=bg_dark,
                       borderwidth=0)
        
        # Store colors for use in other components
        self._colors = {
            'bg_light': bg_light,
            'bg_medium': bg_medium,
            'bg_dark': bg_dark,
            'surface': surface,
            'accent_primary': accent_primary,
            'accent_secondary': accent_secondary,
            'accent_success': accent_success,
            'text_primary': text_primary,
            'text_secondary': text_secondary,
            'text_muted': text_muted,
            'border': border_color,
        }
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новый", command=self._new_document, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Импорт DXF...", command=self._import_dxf, accelerator="Ctrl+I")
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт в DXF (R2000)...", command=lambda: self._export_dxf("R2000"), accelerator="Ctrl+E")
        file_menu.add_command(label="Экспорт в DXF (R12)...", command=lambda: self._export_dxf("R12"))
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_close, accelerator="Alt+F4")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Редактирование", menu=edit_menu)
        edit_menu.add_command(label="Удалить", command=self._delete_selected, accelerator="Delete")
        edit_menu.add_command(label="Выделить всё", command=self._select_all, accelerator="Ctrl+A")
        edit_menu.add_separator()
        edit_menu.add_command(label="Очистить всё", command=self._clear_all)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)
        view_menu.add_command(label="Увеличить", command=self._zoom_in, accelerator="+")
        view_menu.add_command(label="Уменьшить", command=self._zoom_out, accelerator="-")
        view_menu.add_command(label="Показать всё", command=self._zoom_fit, accelerator="F")
        view_menu.add_separator()
        view_menu.add_command(label="Повернуть влево", command=self._rotate_left, accelerator="[")
        view_menu.add_command(label="Повернуть вправо", command=self._rotate_right, accelerator="]")
        view_menu.add_separator()
        view_menu.add_command(label="Сбросить вид", command=self._reset_view, accelerator="Home")
        
        # Draw menu
        draw_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Рисование", menu=draw_menu)
        draw_menu.add_command(label="Отрезок", command=lambda: self._set_tool("segment"), accelerator="L")
        draw_menu.add_command(label="Окружность", command=lambda: self._set_tool("circle"), accelerator="C")
        draw_menu.add_command(label="Дуга", command=lambda: self._set_tool("arc"), accelerator="A")
        draw_menu.add_command(label="Прямоугольник", command=lambda: self._set_tool("rectangle"), accelerator="R")
        draw_menu.add_command(label="Эллипс", command=lambda: self._set_tool("ellipse"), accelerator="E")
        draw_menu.add_command(label="Многоугольник", command=lambda: self._set_tool("polygon"), accelerator="P")
        draw_menu.add_command(label="Сплайн", command=lambda: self._set_tool("spline"), accelerator="S")

        # Dimensions menu
        dim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Размеры", menu=dim_menu)
        dim_menu.add_command(label="Линейный", command=lambda: self._set_tool("dim_linear"), accelerator="D")
        dim_menu.add_command(label="Радиус", command=lambda: self._set_tool("dim_radius"))
        dim_menu.add_command(label="Диаметр", command=lambda: self._set_tool("dim_diameter"))
        dim_menu.add_command(label="Угловой", command=lambda: self._set_tool("dim_angle"))

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._show_about)
    
    def _create_ui(self):
        """Create main UI layout"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar at top
        self._toolbar = Toolbar(main_container, on_tool_selected=self._on_tool_selected)
        self._toolbar.pack(fill=tk.X, side=tk.TOP)
        
        # Status bar at bottom
        self._status_bar = StatusBar(main_container)
        self._status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Main content area
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel (input, settings, styles, and properties)
        left_panel = ttk.Frame(content_frame, width=280)
        left_panel.pack(fill=tk.Y, side=tk.LEFT, padx=2, pady=2)
        left_panel.pack_propagate(False)
        
        # Create notebook for tabs
        left_notebook = ttk.Notebook(left_panel)
        left_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Input panel tab
        input_frame = ttk.Frame(left_notebook)
        left_notebook.add(input_frame, text="Ввод")
        self._input_panel = InputPanel(input_frame, on_point_entered=self._on_point_entered)
        self._input_panel.pack(fill=tk.BOTH, expand=True)
        
        # Settings panel tab
        settings_frame = ttk.Frame(left_notebook)
        left_notebook.add(settings_frame, text="Настройки")
        self._settings_panel = SettingsPanel(settings_frame, on_settings_changed=self._on_settings_changed)
        self._settings_panel.pack(fill=tk.BOTH, expand=True)
        
        # Style panel tab
        style_frame = ttk.Frame(left_notebook)
        left_notebook.add(style_frame, text="Стили")
        self._style_panel = StylePanel(style_frame, on_style_changed=self._on_style_changed)
        self._style_panel.pack(fill=tk.BOTH, expand=True)
        
        # Properties panel tab (moved from right panel)
        properties_frame = ttk.Frame(left_notebook)
        left_notebook.add(properties_frame, text="Свойства")
        self._properties_panel = PropertiesPanel(properties_frame, on_property_changed=self._on_property_changed)
        self._properties_panel.pack(fill=tk.BOTH, expand=True)
        
        # Canvas in center
        canvas_frame = ttk.Frame(content_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self._cad_canvas = CADCanvas(canvas_frame)
        self._cad_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Set up canvas callbacks
        self._cad_canvas.set_on_selection_changed(self._on_selection_changed)
        self._cad_canvas.set_on_cursor_moved(self._on_cursor_moved)
        self._cad_canvas.set_on_base_point_set(self._on_base_point_set)
        
        # Set up navigation callbacks
        self._cad_canvas.navigation.set_on_view_changed(self._on_view_changed)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind("<Control-n>", lambda e: self._new_document())
        self.root.bind("<Control-i>", lambda e: self._import_dxf())
        self.root.bind("<Control-e>", lambda e: self._export_dxf("R2000"))
        self.root.bind("<Control-a>", lambda e: self._select_all())
        self.root.bind("<Delete>", lambda e: self._delete_selected())
        
        # Tool shortcuts
        self.root.bind("<v>", lambda e: self._set_tool("select"))
        self.root.bind("<h>", lambda e: self._set_tool("pan"))
        self.root.bind("<l>", lambda e: self._set_tool("segment"))
        self.root.bind("<c>", lambda e: self._set_tool("circle"))
        self.root.bind("<a>", lambda e: self._set_tool("arc"))
        self.root.bind("<r>", lambda e: self._set_tool("rectangle"))
        self.root.bind("<e>", lambda e: self._set_tool("ellipse"))
        self.root.bind("<p>", lambda e: self._set_tool("polygon"))
        self.root.bind("<s>", lambda e: self._set_tool("spline"))
        self.root.bind("<d>", lambda e: self._set_tool("dim_linear"))

        # View shortcuts
        self.root.bind("<plus>", lambda e: self._zoom_in())
        self.root.bind("<equal>", lambda e: self._zoom_in())
        self.root.bind("<minus>", lambda e: self._zoom_out())
        self.root.bind("<f>", lambda e: self._zoom_fit())
        self.root.bind("<Home>", lambda e: self._reset_view())
        self.root.bind("<bracketleft>", lambda e: self._rotate_left())
        self.root.bind("<bracketright>", lambda e: self._rotate_right())
        
        # Escape to cancel current operation
        self.root.bind("<Escape>", lambda e: self._cancel_operation())
        
        # Window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    # ================== Tool Management ==================
    
    def _on_tool_selected(self, tool_id: str):
        """Handle tool selection from toolbar"""
        if tool_id.startswith("action:"):
            action = tool_id[7:]
            self._handle_action(action)
        else:
            self._set_tool(tool_id)
    
    def _set_tool(self, tool_id: str):
        """Set active tool"""
        if tool_id in self._tools:
            self._cad_canvas.set_tool(self._tools[tool_id])
            self._toolbar.set_active_tool(tool_id)
            self._status_bar.update_tool(self._tools[tool_id].get_name())
    
    def _handle_action(self, action: str):
        """Handle toolbar action"""
        actions = {
            "zoom_in": self._zoom_in,
            "zoom_out": self._zoom_out,
            "zoom_fit": self._zoom_fit,
            "rotate_left": self._rotate_left,
            "rotate_right": self._rotate_right,
            "reset_view": self._reset_view,
            "delete": self._delete_selected,
            "clear_all": self._clear_all,
        }
        if action in actions:
            actions[action]()
    
    def _cancel_operation(self):
        """Cancel current operation"""
        current_tool = self._cad_canvas.get_tool()
        if current_tool:
            current_tool._reset_state()
            current_tool._clear_preview()
            self._cad_canvas.redraw()
    
    # ================== View Operations ==================
    
    def _zoom_in(self):
        """Zoom in"""
        self._cad_canvas.navigation.zoom_in()
    
    def _zoom_out(self):
        """Zoom out"""
        self._cad_canvas.navigation.zoom_out()
    
    def _zoom_fit(self):
        """Zoom to fit all content"""
        self._cad_canvas.zoom_to_fit()
    
    def _reset_view(self):
        """Reset view to default"""
        self._cad_canvas.reset_view()
    
    def _rotate_left(self):
        """Rotate view left"""
        self._cad_canvas.navigation.rotate_left()
    
    def _rotate_right(self):
        """Rotate view right"""
        self._cad_canvas.navigation.rotate_right()
    
    # ================== Document Operations ==================
    
    def _export_dxf(self, version: str = "R2000"):
        """Export drawing to DXF file"""
        if not self._cad_canvas.primitives:
            messagebox.showwarning("Экспорт DXF", "Нет объектов для экспорта.")
            return

        filepath = filedialog.asksaveasfilename(
            title=f"Экспорт в DXF ({version})",
            defaultextension=".dxf",
            filetypes=[("DXF файлы", "*.dxf"), ("Все файлы", "*.*")],
            initialfile=f"drawing_{version}.dxf",
        )
        if not filepath:
            return

        try:
            exporter = DXFExporter(version=version)
            exporter.export(self._cad_canvas.primitives, filepath, version=version)
            messagebox.showinfo(
                "Экспорт DXF",
                f"Файл успешно сохранён:\n{filepath}\n\n"
                f"Версия: {version}\n"
                f"Объектов: {len(self._cad_canvas.primitives)}\n"
                f"Формат: {'AC1015' if version == 'R2000' else 'AC1009'}"
            )
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", f"Не удалось экспортировать:\n{str(e)}")

    def _import_dxf(self):
        """Import drawing from DXF file"""
        filepath = filedialog.askopenfilename(
            title="Импорт DXF",
            filetypes=[("DXF файлы", "*.dxf"), ("Все файлы", "*.*")],
        )
        if not filepath:
            return

        try:
            importer = DXFImporter()
            primitives, info = importer.import_file(filepath)

            if not primitives:
                messagebox.showwarning(
                    "Импорт DXF",
                    f"Файл не содержит поддерживаемых объектов.\n\n"
                    f"Версия: {info.get('version', '?')}\n"
                    f"Всего сущностей: {info.get('total_entities', 0)}\n"
                    f"Пропущено: {info.get('skipped', 0)}\n"
                    f"Ошибок: {info.get('errors', 0)}"
                )
                return

            # Добавляем примитивы на канвас
            for prim in primitives:
                self._cad_canvas.add_primitive(prim)

            self._cad_canvas.redraw()
            self._cad_canvas.zoom_to_fit()

            # Формируем статистику по типам
            by_type = info.get("by_type", {})
            type_lines = "\n".join(
                f"  {t}: {c}" for t, c in sorted(by_type.items())
            )

            messagebox.showinfo(
                "Импорт DXF",
                f"Файл успешно импортирован:\n{filepath}\n\n"
                f"Версия: {info.get('version', '?')}\n"
                f"Слоёв: {info.get('layers', 0)}\n"
                f"Импортировано объектов: {info.get('imported', 0)}\n"
                f"Пропущено: {info.get('skipped', 0)}\n"
                f"Ошибок: {info.get('errors', 0)}\n\n"
                f"По типам:\n{type_lines}"
            )
        except Exception as e:
            messagebox.showerror("Ошибка импорта", f"Не удалось импортировать:\n{str(e)}")

    def _new_document(self):
        """Create new document"""
        if self._cad_canvas.primitives:
            if not messagebox.askyesno("Новый документ", "Очистить текущий чертеж?"):
                return
            self._cad_canvas.clear_primitives()
            self._cad_canvas.reset_view()
    
    def _delete_selected(self):
        """Delete selected objects"""
        self._cad_canvas.delete_selected()
    
    def _select_all(self):
        """Select all objects"""
        self._cad_canvas.select_all()
    
    def _clear_all(self):
        """Clear all objects"""
        if messagebox.askyesno("Очистить всё", "Удалить все объекты?"):
            self._cad_canvas.clear_primitives()
    
    # ================== Callbacks ==================
    
    def _on_selection_changed(self, selected_primitives):
        """Handle selection change"""
        self._properties_panel.update_selection(selected_primitives)
        self._status_bar.update_selection(len(selected_primitives))
    
    def _on_cursor_moved(self, x: float, y: float, snap_type):
        """Handle cursor movement"""
        self._status_bar.update_coordinates(x, y, snap_type)
    
    def _on_view_changed(self):
        """Handle view change"""
        zoom = self._cad_canvas.navigation.get_zoom_percent()
        rotation = self._cad_canvas.navigation.get_rotation_degrees()
        self._status_bar.update_zoom(zoom)
        self._status_bar.update_rotation(rotation)
        self._cad_canvas.redraw()
    
    def _on_settings_changed(self, setting_name: str, value):
        """Handle settings change"""
        if setting_name == "grid_visible":
            self._cad_canvas.grid.visible = value
            self._cad_canvas.redraw()
        elif setting_name == "grid_step":
            self._cad_canvas.grid.set_step(value)
            self._cad_canvas.redraw()
        elif setting_name == "grid_color":
            self._cad_canvas.grid.color = value
            self._cad_canvas.redraw()
        elif setting_name == "background_color":
            self._cad_canvas.canvas.config(bg=value)
            self._cad_canvas.redraw()
        elif setting_name == "angle_unit":
            self._status_bar.set_angle_unit(value)
        elif setting_name == "snaps":
            from .primitives.base import SnapType
            snap_map = {
                "endpoint": SnapType.ENDPOINT,
                "midpoint": SnapType.MIDPOINT,
                "center": SnapType.CENTER,
                "intersection": SnapType.INTERSECTION,
                "perpendicular": SnapType.PERPENDICULAR,
            }
            enabled = {snap_map[s] for s in value if s in snap_map}
            self._cad_canvas.snap_manager.set_enabled_snaps(enabled)
    
    def _on_style_changed(self, style_id: str):
        """Handle style change"""
        self._cad_canvas.redraw()
    
    def _on_property_changed(self):
        """Handle property change"""
        self._cad_canvas.redraw()
    
    def _on_point_entered(self, x: float, y: float):
        """Handle point entered from input panel"""
        current_tool = self._cad_canvas.get_tool()
        if current_tool:
            sx, sy = self._cad_canvas.navigation.world_to_screen(x, y)
            current_tool.on_left_click(sx, sy, x, y)
            self._cad_canvas.redraw()
            self._input_panel.set_last_point(x, y)
    
    def _on_base_point_set(self, x: float, y: float):
        """Handle base point set from canvas"""
        if x is not None and y is not None:
            self._input_panel.set_base_point(x, y, enable=True)
        else:
            self._input_panel.clear_base_point()
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo("О программе",
                           "GeomModel CAD\n\n"
                           "Система геометрического моделирования\n\n"
                           "Реализованный функционал:\n"
                           "• ЛР1: Отрезки в декартовых и полярных координатах\n"
                           "• ЛР2: Навигация (pan, zoom, rotate)\n"
                           "• ЛР3: Стили линий по ГОСТ 2.303-68\n"
                           "• ЛР4: Геометрические примитивы и привязки\n"
                           "• ЛР5: Экспорт в DXF (R12/R2000)\n"
                           "• ЛР6: Импорт из DXF\n"
                           "• ЛР7: Размерные линии (ГОСТ 2.307-2011)\n\n"
                           "Версия 1.3.0")
    
    def _on_close(self):
        """Handle window close"""
        if self._cad_canvas.primitives:
            if not messagebox.askyesno("Выход", "Выйти без сохранения?"):
                return
        self.root.destroy()
    
    def run(self):
        """Run application main loop"""
        self.root.mainloop()
