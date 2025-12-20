"""
Style Manager - singleton for managing line styles
Менеджер стилей - синглтон для управления стилями линий
"""

from typing import Dict, List, Optional, Callable
from .line_style import LineStyle, LineType, GOST_STYLES
import copy


class StyleManager:
    """
    Singleton style manager
    Менеджер стилей (синглтон)
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._styles: Dict[str, LineStyle] = {}
        self._current_style_id: str = "solid_main"
        self._listeners: List[Callable] = []
        self._load_gost_styles()
    
    def _load_gost_styles(self):
        """Load GOST styles"""
        for style_id, style in GOST_STYLES.items():
            self._styles[style_id] = style.copy()
    
    def get_style(self, style_id: str) -> Optional[LineStyle]:
        """Get style by ID"""
        return self._styles.get(style_id)
    
    def get_all_styles(self) -> Dict[str, LineStyle]:
        """Get all styles"""
        return self._styles.copy()
    
    def get_style_list(self) -> List[tuple]:
        """Get list of (style_id, style_name) tuples"""
        return [(sid, style.name) for sid, style in self._styles.items()]
    
    def get_current_style(self) -> LineStyle:
        """Get current style"""
        return self._styles.get(self._current_style_id, self._styles["solid_main"])
    
    def get_current_style_id(self) -> str:
        """Get current style ID"""
        return self._current_style_id
    
    def set_current_style(self, style_id: str):
        """Set current style"""
        if style_id in self._styles:
            self._current_style_id = style_id
            self._notify_listeners()
    
    def add_style(self, style_id: str, style: LineStyle) -> bool:
        """Add new style"""
        if style_id in self._styles:
            return False
        new_style = style.copy()
        new_style.is_system = False
        self._styles[style_id] = new_style
        self._notify_listeners()
        return True
    
    def update_style(self, style_id: str, **kwargs) -> bool:
        """Update style properties"""
        if style_id not in self._styles:
            return False
        style = self._styles[style_id]
        for key, value in kwargs.items():
            if hasattr(style, key):
                setattr(style, key, value)
        self._notify_listeners()
        return True
    
    def delete_style(self, style_id: str) -> bool:
        """Delete style (cannot delete system styles)"""
        if style_id not in self._styles:
            return False
        if self._styles[style_id].is_system:
            return False
        del self._styles[style_id]
        if self._current_style_id == style_id:
            self._current_style_id = "solid_main"
        self._notify_listeners()
        return True
    
    def create_custom_style(self, name: str, base_style_id: str = "solid_main", **kwargs) -> Optional[str]:
        """Create custom style based on base style"""
        if base_style_id not in self._styles:
            return None
        base = self._styles[base_style_id]
        new_style = base.copy()
        new_style.name = name
        new_style.is_system = False
        for key, value in kwargs.items():
            if hasattr(new_style, key):
                setattr(new_style, key, value)
        style_id = f"custom_{len([s for s in self._styles if s.startswith('custom_')])}"
        self._styles[style_id] = new_style
        self._notify_listeners()
        return style_id
    
    def add_listener(self, callback: Callable):
        """Add listener for style changes"""
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """Remove listener"""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self):
        """Notify all listeners about style changes"""
        for callback in self._listeners:
            try:
                callback()
            except Exception:
                pass
    
    def reset_to_defaults(self):
        """Reset to default GOST styles"""
        self._styles.clear()
        self._load_gost_styles()
        self._current_style_id = "solid_main"
        self._notify_listeners()
