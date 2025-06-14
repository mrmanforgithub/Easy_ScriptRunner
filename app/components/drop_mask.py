"""
这是一个文件拖入窗口的全屏遮罩，同时会显示图标和文字，请在主窗口内实例化 DropMask
注意该窗口实例化需要在窗体 setupUi 之后

"""
from typing import Optional

from PyQt5.QtCore import QEasingCurve, QEvent, QPropertyAnimation, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QDragLeaveEvent, QResizeEvent, QDragEnterEvent
from PyQt5.QtWidgets import (QDialog, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
                            QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets.components import IconWidget, TitleLabel


class DropMask(QDialog):
    """ Dialog box base class with a mask """
    droped_file_url = pyqtSignal(str)

    def __init__(self, parent, title: str, icon: Optional[FIF] = None):
        super().__init__(parent=parent)
        self._hBoxLayout = QHBoxLayout(self)
        self.windowMask = QWidget(self)
        self.setAcceptDrops(True)

        # 设置在最顶层
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # dialog box in the center of mask, all widgets take it as parent
        self.widget = QFrame(self)
        self.v_layout = QVBoxLayout()
        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_layout2 = QVBoxLayout()
        self.v_layout2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.biggest_layout = QVBoxLayout()

        self.icon_widget = IconWidget()
        self.icon_widget.setIcon(icon)
        self.icon_widget.setFixedSize(108, 108)
        self.icon_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.title_label = TitleLabel()
        self.title_label.setText(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.v_layout.addWidget(self.icon_widget)
        self.v_layout2.addWidget(self.title_label)

        self.biggest_layout.addLayout(self.v_layout)
        self.biggest_layout.addLayout(self.v_layout2)

        self.widget.setLayout(self.biggest_layout)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(0, 0, parent.width(), parent.height())

        self.windowMask.resize(self.size())

        self._hBoxLayout.addWidget(self.widget, 1, Qt.AlignmentFlag.AlignCenter)
        self.set_shadow_effect()
        self.set_mask_color(QColor(0, 0, 0, 75))

        self.window().installEventFilter(self)

    def set_shadow_effect(self, blur_radius=60, offset=(0, 10), color=QColor(0, 0, 0, 50)):
        """ add shadow to dialog """
        shadow_effect = QGraphicsDropShadowEffect(self.widget)
        shadow_effect.setBlurRadius(blur_radius)
        shadow_effect.setOffset(*offset)
        shadow_effect.setColor(color)
        # self.widget.setGraphicsEffect(None)
        self.widget.setGraphicsEffect(shadow_effect)

    def set_mask_color(self, color: QColor):
        """ set the color of mask """
        self.windowMask.setStyleSheet(f"""
            background: rgba({color.red()}, {color.blue()}, {color.green()}, {color.alpha()})
        """)

    def showEvent(self, e):
        """ fade in """
        opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacity_effect)
        opacity_ani = QPropertyAnimation(opacity_effect, b'opacity', self)
        opacity_ani.setStartValue(0)
        opacity_ani.setEndValue(1)
        opacity_ani.setDuration(200)
        opacity_ani.setEasingCurve(QEasingCurve.Type.InSine)
        opacity_ani.finished.connect(opacity_effect.deleteLater)
        opacity_ani.start()
        super().showEvent(e)

    def closeEvent(self, e):
        """ fade out """
        # self.widget.setGraphicsEffect(None)
        opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacity_effect)
        opacity_ani = QPropertyAnimation(opacity_effect, b'opacity', self)
        opacity_ani.setStartValue(1)
        opacity_ani.setEndValue(0)
        opacity_ani.setDuration(100)
        opacity_ani.setEasingCurve(QEasingCurve.Type.OutCubic)
        opacity_ani.finished.connect(self.deleteLater)
        opacity_ani.start()
        e.ignore()

    def resizeEvent(self, e):
        self.windowMask.resize(self.size())

    def eventFilter(self, obj, e: QEvent):
        if obj is self.window():
            if e.type() == QEvent.Type.Resize:
                re = QResizeEvent(e)
                self.resize(re.size())

        return super().eventFilter(obj, e)

    def dragEnterEvent(self, e):
        file_text: str = e.mimeData().text()
        if e.mimeData().hasText():
            if file_text.endswith('.json'):
                self.icon_widget.setIcon(FIF.ZIP_FOLDER)
                # 将图标设置为居中
                self.icon_widget.setFixedSize(108, 108)
                self.title_label.setText(self.tr('松开鼠标放入文件'))
            else:
                self.icon_widget.setIcon(FIF.REMOVE_FROM)
                self.icon_widget.setFixedSize(108, 108)
                self.title_label.setText(self.tr('文件必须是.json文件'))
            e.accept()
        else:
            self.hide()
            e.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        # 当文件移动出窗口的时候，隐藏窗口
        self.hide()

    def dropEvent(self, e):
        path = e.mimeData().urls()[0].toLocalFile()
        self.droped_file_url.emit(path)
        self.hide()


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    class MyWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.resize(800, 600)
            self.setAcceptDrops(True)
            self.setWindowTitle('DropMask Test')
            self.dialog_mask = DropMask(self, '拖入文件', FIF.ZIP_FOLDER)
            self.dialog_mask.droped_file_url.connect(lambda x: print(x))
            self.dialog_mask.hide()

        def dragEnterEvent(self, e: QDragEnterEvent):
            if e.mimeData().hasText():
                self.dialog_mask.show()

        # 窗体大小发生改变触发事件
        def resizeEvent(self, event):
            self.resize_mask()

        def resize_mask(self) -> None:
            self.dialog_mask.resize(self.width(), self.height())

    app = QApplication([])
    mask = MyWindow()
    mask.show()
    app.exec()