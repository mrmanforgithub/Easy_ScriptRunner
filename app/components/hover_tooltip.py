from PyQt5.QtCore import QObject, QEvent, QTimer
from PyQt5.QtWidgets import QWidget

class HoverTrigger(QObject):
    """
    鼠标悬停一定时间后触发 `hover_callback`，离开时触发 `leave_callback`
    """
    def __init__(self, parent: QWidget, hover_callback=None, leave_callback=None, hover_delay=500):
        """
        :param parent: 需要监听的控件
        :param hover_callback: 鼠标悬停后触发的回调
        :param leave_callback: 鼠标离开时触发的回调
        :param hover_delay: 悬停触发延迟（毫秒）
        """
        super().__init__(parent)
        self.parent_widget = parent
        self.hover_callback = hover_callback
        self.leave_callback = leave_callback
        self.hover_delay = hover_delay

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.triggerHoverCallback)

        self.parent_widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.parent_widget:
            if event.type() == QEvent.Enter:
                self.timer.start(self.hover_delay)  # 开始计时
            elif event.type() == QEvent.Leave:
                self.timer.stop()  # 停止悬停计时
                self.triggerLeaveCallback()  # 执行离开回调
        return super().eventFilter(obj, event)

    def triggerHoverCallback(self):
        """ 悬停达到时间后执行回调 """
        if self.hover_callback:
            self.hover_callback()

    def triggerLeaveCallback(self):
        """ 鼠标离开时执行回调 """
        if self.leave_callback:
            self.leave_callback()