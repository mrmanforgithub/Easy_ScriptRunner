from PyQt5 import QtCore, QtGui, QtWidgets
from qfluentwidgets import ElevatedCardWidget, IconWidget, TitleLabel, BodyLabel


class HoverCardWidget(ElevatedCardWidget):
    """自定义悬停卡片控件，包含图标、标题和正文"""

    def __init__(self, icon,title,content, parent=None):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.content = content
        self.setupUi()

    def setupUi(self):
        # 设置卡片布局
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(15, 15, 15, 15)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # 图标控件
        self.IconWidget = IconWidget(self)
        self.IconWidget.setMinimumSize(QtCore.QSize(50, 50))
        self.IconWidget.setMaximumSize(QtCore.QSize(50, 50))
        self.IconWidget.setIcon(self.icon)
        self.horizontalLayout.addWidget(self.IconWidget)

        # 垂直布局（标题和正文）
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName("verticalLayout")

        # 标题
        self.TitleLabel = TitleLabel(self)
        self.TitleLabel.setText(self.title)
        self.TitleLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.verticalLayout.addWidget(self.TitleLabel)

        # 正文
        self.BodyLabel = BodyLabel(self)
        self.BodyLabel.setText(self.content)
        self.BodyLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.verticalLayout.addWidget(self.BodyLabel)

        self.horizontalLayout.addLayout(self.verticalLayout)

        # 设置悬停效果
        self.setHoverEffect(True)

    def setHoverEffect(self, enable: bool):
        """启用或禁用悬停效果"""
        if enable:
            self.setProperty("hover", True)
            self.setStyle(QtWidgets.QApplication.style())
        else:
            self.setProperty("hover", False)
            self.setStyle(QtWidgets.QApplication.style())