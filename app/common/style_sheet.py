# coding: utf-8
from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, qconfig, isDarkTheme


class StyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """

    HOME_INTERFACE = "home_interface"
    SETTING_INTERFACE = "setting_interface"
    GALLERY_INTERFACE = "gallery_interface"
    NAVIGATION_VIEW_INTERFACE = "navigation_view_interface"
    ICON_INTERFACE = "icon_interface"
    SCAN_PAGE = "scanpage"
    RECORD_DIALOG ="record_dialog"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f":/qss/{theme.value.lower()}/{self.value}.qss"
