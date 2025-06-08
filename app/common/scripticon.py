from enum import Enum

from qfluentwidgets import getIconColor, Theme, FluentIconBase


class ScriptIcon(FluentIconBase, Enum):
    """ Custom icons """

    LOCK = "lock"
    UNLOCK = "unlock"
    RECORD = "record"
    RECORDING = "recording"
    END = "end"

    def path(self, theme=Theme.AUTO):
        return f':images/icons/{self.value}_{getIconColor(theme)}.svg'