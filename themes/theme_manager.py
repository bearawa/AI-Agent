"""
AIZS 主题管理器
提供企业级设计系统支持，包括颜色、字体、间距、圆角等设计令牌。
支持主题切换和动态样式管理。
"""
from typing import Dict, Any, Optional


class ThemeManager:
    """
    主题管理器，负责管理设计令牌和主题切换。
    """

    DEFAULT_THEME = "light"

    LIGHT_THEME = {
        "name": "light",
        "display_name": "浅色主题",
        "colors": {
            "primary": "#10a37f",
            "primary_hover": "#0e906f",
            "primary_active": "#0c7a5f",
            "primary_text": "#ffffff",
            
            "secondary": "#0d0d0d",
            "secondary_hover": "#2f2f2f",
            "secondary_active": "#1f1f1f",
            
            "success": "#10a37f",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "info": "#3b82f6",
            
            "bg_page": "#ffffff",
            "bg_container": "#ffffff",
            "bg_card": "#ffffff",
            "bg_hover": "#f4f4f4",
            
            "text_primary": "#0d0d0d",
            "text_secondary": "#5e5e5e",
            "text_tertiary": "#8e8e8e",
            "text_disabled": "#ececec",
            
            "border": "#e5e5e5",
            "border_light": "#ececec",
            "border_focus": "#10a37f",
            
            "shadow": "0 1px 2px rgba(0, 0, 0, 0.05)",
            "shadow_hover": "0 2px 4px rgba(0, 0, 0, 0.1)",
            "shadow_card": "0 1px 2px rgba(0, 0, 0, 0.05)",
            
            "gradient_primary": "#10a37f",
            "gradient_success": "#10a37f",
        },
        "typography": {
            "font_family": "'PingFang SC', 'Microsoft YaHei', sans-serif",
            "font_size_xs": "10px",
            "font_size_sm": "12px",
            "font_size_base": "14px",
            "font_size_lg": "16px",
            "font_size_xl": "18px",
            "font_size_xxl": "24px",
            "font_weight_normal": 400,
            "font_weight_medium": 500,
            "font_weight_bold": 600,
            "line_height_base": 1.5,
            "line_height_lg": 1.8,
            "letter_spacing_normal": "0",
            "letter_spacing_wide": "0.5px",
        },
        "spacing": {
            "spacing_xxs": "4px",
            "spacing_xs": "8px",
            "spacing_sm": "12px",
            "spacing_base": "16px",
            "spacing_md": "24px",
            "spacing_lg": "32px",
            "spacing_xl": "48px",
            "spacing_xxl": "64px",
        },
        "radius": {
            "radius_xxs": "2px",
            "radius_xs": "4px",
            "radius_sm": "6px",
            "radius_base": "8px",
            "radius_md": "12px",
            "radius_lg": "16px",
            "radius_xl": "24px",
            "radius_round": "9999px",
        },
        "shadows": {
            "shadow_xs": "0 1px 2px rgba(0, 0, 0, 0.05)",
            "shadow_sm": "0 2px 4px rgba(0, 0, 0, 0.06)",
            "shadow_base": "0 2px 8px rgba(0, 0, 0, 0.08)",
            "shadow_md": "0 4px 12px rgba(0, 0, 0, 0.1)",
            "shadow_lg": "0 8px 24px rgba(0, 0, 0, 0.12)",
            "shadow_xl": "0 12px 32px rgba(0, 0, 0, 0.15)",
        },
        "z_index": {
            "z_index_base": 0,
            "z_index_dropdown": 1000,
            "z_index_sticky": 1020,
            "z_index_fixed": 1030,
            "z_index_modal_backdrop": 1040,
            "z_index_modal": 1050,
            "z_index_popover": 1060,
            "z_index_tooltip": 1070,
            "z_index_notification": 1080,
            "z_index_page_header": 1090,
        },
        "transitions": {
            "transition_fast": "0.15s ease",
            "transition_base": "0.2s ease",
            "transition_slow": "0.3s ease",
            "transition_duration_fast": "150ms",
            "transition_duration_base": "200ms",
            "transition_duration_slow": "300ms",
            "transition_ease": "cubic-bezier(0.4, 0, 0.2, 1)",
        },
        "breakpoints": {
            "xs": "480px",
            "sm": "576px",
            "md": "768px",
            "lg": "992px",
            "xl": "1200px",
            "xxl": "1600px",
        },
    }

    DARK_THEME = {
        "name": "dark",
        "display_name": "深色主题",
        "colors": {
            "primary": "#10a37f",
            "primary_hover": "#11b990",
            "primary_active": "#0e906f",
            "primary_text": "#ffffff",
            
            "secondary": "#ececec",
            "secondary_hover": "#f4f4f4",
            "secondary_active": "#ffffff",
            
            "success": "#10a37f",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "info": "#3b82f6",
            
            "bg_page": "#212121",
            "bg_container": "#2f2f2f",
            "bg_card": "#212121",
            "bg_hover": "#2f2f2f",
            
            "text_primary": "#ececec",
            "text_secondary": "#b4b4b4",
            "text_tertiary": "#8e8e8e",
            "text_disabled": "#424242",
            
            "border": "#424242",
            "border_light": "#2f2f2f",
            "border_focus": "#10a37f",
            
            "shadow": "0 1px 2px rgba(0, 0, 0, 0.4)",
            "shadow_hover": "0 2px 4px rgba(0, 0, 0, 0.5)",
            "shadow_card": "0 1px 2px rgba(0, 0, 0, 0.4)",
            
            "gradient_primary": "#10a37f",
            "gradient_success": "#10a37f",
        },
        "typography": {
            "font_family": "'PingFang SC', 'Microsoft YaHei', sans-serif",
            "font_size_xs": "10px",
            "font_size_sm": "12px",
            "font_size_base": "14px",
            "font_size_lg": "16px",
            "font_size_xl": "18px",
            "font_size_xxl": "24px",
            "font_weight_normal": 400,
            "font_weight_medium": 500,
            "font_weight_bold": 600,
            "line_height_base": 1.5,
            "line_height_lg": 1.8,
            "letter_spacing_normal": "0",
            "letter_spacing_wide": "0.5px",
        },
        "spacing": {
            "spacing_xxs": "4px",
            "spacing_xs": "8px",
            "spacing_sm": "12px",
            "spacing_base": "16px",
            "spacing_md": "24px",
            "spacing_lg": "32px",
            "spacing_xl": "48px",
            "spacing_xxl": "64px",
        },
        "radius": {
            "radius_xxs": "2px",
            "radius_xs": "4px",
            "radius_sm": "6px",
            "radius_base": "8px",
            "radius_md": "12px",
            "radius_lg": "16px",
            "radius_xl": "24px",
            "radius_round": "9999px",
        },
        "shadows": {
            "shadow_xs": "0 1px 2px rgba(0, 0, 0, 0.3)",
            "shadow_sm": "0 2px 4px rgba(0, 0, 0, 0.35)",
            "shadow_base": "0 2px 8px rgba(0, 0, 0, 0.4)",
            "shadow_md": "0 4px 12px rgba(0, 0, 0, 0.45)",
            "shadow_lg": "0 8px 24px rgba(0, 0, 0, 0.5)",
            "shadow_xl": "0 12px 32px rgba(0, 0, 0, 0.6)",
        },
        "z_index": {
            "z_index_base": 0,
            "z_index_dropdown": 1000,
            "z_index_sticky": 1020,
            "z_index_fixed": 1030,
            "z_index_modal_backdrop": 1040,
            "z_index_modal": 1050,
            "z_index_popover": 1060,
            "z_index_tooltip": 1070,
            "z_index_notification": 1080,
            "z_index_page_header": 1090,
        },
        "transitions": {
            "transition_fast": "0.15s ease",
            "transition_base": "0.2s ease",
            "transition_slow": "0.3s ease",
            "transition_duration_fast": "150ms",
            "transition_duration_base": "200ms",
            "transition_duration_slow": "300ms",
            "transition_ease": "cubic-bezier(0.4, 0, 0.2, 1)",
        },
        "breakpoints": {
            "xs": "480px",
            "sm": "576px",
            "md": "768px",
            "lg": "992px",
            "xl": "1200px",
            "xxl": "1600px",
        },
    }

    THEMES = {
        "light": LIGHT_THEME,
        "dark": DARK_THEME,
    }

    def __init__(self):
        self._current_theme_name = self.DEFAULT_THEME
        self._current_theme = self.THEMES[self.DEFAULT_THEME]
        self._theme_callbacks = []

    @property
    def current_theme(self) -> Dict[str, Any]:
        """获取当前主题配置"""
        return self._current_theme

    @property
    def current_theme_name(self) -> str:
        """获取当前主题名称"""
        return self._current_theme_name

    def set_theme(self, theme_name: str) -> bool:
        """
        设置主题

        :param theme_name: 主题名称
        :return: 是否设置成功
        """
        if theme_name not in self.THEMES:
            return False
        
        self._current_theme_name = theme_name
        self._current_theme = self.THEMES[theme_name]
        
        for callback in self._theme_callbacks:
            callback(theme_name, self._current_theme)
        
        return True

    def toggle_theme(self) -> str:
        """
        切换主题（浅色/深色）

        :return: 新的主题名称
        """
        new_theme = "dark" if self._current_theme_name == "light" else "light"
        self.set_theme(new_theme)
        return new_theme

    def get_color(self, key: str) -> Optional[str]:
        """
        获取颜色值

        :param key: 颜色键名
        :return: 颜色值或 None
        """
        return self._current_theme.get("colors", {}).get(key)

    def get_typography(self, key: str) -> Optional[str]:
        """
        获取字体配置

        :param key: 字体配置键名
        :return: 字体配置值或 None
        """
        return self._current_theme.get("typography", {}).get(key)

    def get_spacing(self, key: str) -> Optional[str]:
        """
        获取间距配置

        :param key: 间距配置键名
        :return: 间距配置值或 None
        """
        return self._current_theme.get("spacing", {}).get(key)

    def get_radius(self, key: str) -> Optional[str]:
        """
        获取圆角配置

        :param key: 圆角配置键名
        :return: 圆角配置值或 None
        """
        return self._current_theme.get("radius", {}).get(key)

    def get_shadow(self, key: str) -> Optional[str]:
        """
        获取阴影配置

        :param key: 阴影配置键名
        :return: 阴影配置值或 None
        """
        return self._current_theme.get("shadows", {}).get(key)

    def get_z_index(self, key: str) -> Optional[int]:
        """
        获取 z-index 配置

        :param key: z-index 配置键名
        :return: z-index 值或 None
        """
        return self._current_theme.get("z_index", {}).get(key)

    def get_transition(self, key: str) -> Optional[str]:
        """
        获取过渡动画配置

        :param key: 过渡动画配置键名
        :return: 过渡动画配置值或 None
        """
        return self._current_theme.get("transitions", {}).get(key)

    def get_breakpoint(self, key: str) -> Optional[str]:
        """
        获取响应式断点配置

        :param key: 断点配置键名
        :return: 断点配置值或 None
        """
        return self._current_theme.get("breakpoints", {}).get(key)

    def register_callback(self, callback):
        """
        注册主题切换回调

        :param callback: 回调函数，签名: callback(theme_name, theme_config)
        """
        if callback not in self._theme_callbacks:
            self._theme_callbacks.append(callback)

    def unregister_callback(self, callback):
        """
        注销主题切换回调

        :param callback: 回调函数
        """
        if callback in self._theme_callbacks:
            self._theme_callbacks.remove(callback)

    def list_themes(self) -> list:
        """
        获取所有可用主题列表

        :return: 主题列表，每个元素包含 name 和 display_name
        """
        return [
            {"name": name, "display_name": theme["display_name"]}
            for name, theme in self.THEMES.items()
        ]

    def generate_css_variables(self) -> str:
        """
        生成 CSS 变量字符串

        :return: CSS 变量定义字符串
        """
        css = ":root {\n"
        
        for category, values in self._current_theme.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    css_var_name = f"--{category}-{key}"
                    css += f"  {css_var_name}: {value};\n"
        
        css += "}"
        return css


# 创建全局主题管理器实例
theme_manager = ThemeManager()
