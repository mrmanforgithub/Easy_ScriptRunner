
from PyQt5.QtCore import Qt,QRectF,QRect
from PyQt5.QtGui import QPainter,QPalette
from PyQt5.QtWidgets import QLabel

from qfluentwidgets import icon,Theme,qconfig,isDarkTheme


class IconLabel(QLabel):
    def __init__(self, icon, text,parent=None, reverse=False):
        super().__init__(text,parent)
        self._icon = icon
        self._icon_size = 20
        self._text = text
        self._padding = 10
        self._reverse = reverse
        self._theme = (
            Theme.DARK if isDarkTheme() != self._reverse else Theme.LIGHT
        )
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        qconfig.themeChanged.connect(self.change_theme)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        icon_rect = QRectF(10, (self.height() - self._icon_size) / 2, self._icon_size, self._icon_size)
        icon.drawIcon(self._icon, painter, icon_rect, theme= self._theme)  # 调用你的 drawIcon 函数绘制图标


        text_x = self._icon_size + self._padding + 5  # 5 是左侧边距
        text_rect = QRect(text_x, 0, self.width() - text_x, self.height())

        # 设置文本颜色
        painter.setPen(self.palette().color(QPalette.Text))
        painter.drawText(text_rect, self.alignment(), self._text)  # 重新绘制文本


    def change_theme(self,theme):
        self._theme = (
            Theme.DARK if isDarkTheme() != self._reverse else Theme.LIGHT
        )
        self.update()


    def setText(self, new_text):
        """设置文本，并触发界面更新"""
        self._text = new_text
        self.update()  # 触发重绘

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, new_icon):
        self._icon = new_icon
        self.update()  # 触发重绘


    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        self._text = new_text
        self.update()  # 触发重绘