# coding:utf-8
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QEvent
from PyQt5.QtGui import QDesktopServices, QPainter, QPen, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,QLayout

from qfluentwidgets import (ScrollArea, PushButton, ToolButton, FluentIcon,
                            isDarkTheme, IconWidget, Theme, ToolTipFilter, TitleLabel, CaptionLabel,
                            StrongBodyLabel, BodyLabel, toggleTheme)
from ..common.config import cfg, FEEDBACK_URL, HELP_URL
from ..common.style_sheet import StyleSheet
from ..common.signal_bus import signalBus


class ToolBar(QWidget):
    """ Tool bar """

    def __init__(self, title, subtitle, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = TitleLabel(self.tr(title), self)
        self.subtitleLabel = CaptionLabel(self.tr(subtitle), self)

        self.themeButton = ToolButton(FluentIcon.CONSTRACT, self)
        self.supportButton = ToolButton(FluentIcon.HEART, self)
        self.feedbackButton = ToolButton(FluentIcon.FEEDBACK, self)

        self.vBoxLayout = QVBoxLayout(self)
        self.buttonLayout = QHBoxLayout()

        self.__initWidget()

    def __initWidget(self):
        self.setFixedHeight(138)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(36, 22, 36, 12)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.addSpacing(4)
        self.vBoxLayout.addLayout(self.buttonLayout, 1)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.buttonLayout.setSpacing(4)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.addStretch(1)
        self.buttonLayout.addWidget(self.themeButton, 0, Qt.AlignRight)
        self.buttonLayout.addWidget(self.supportButton, 0, Qt.AlignRight)
        self.buttonLayout.addWidget(self.feedbackButton, 0, Qt.AlignRight)
        self.buttonLayout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.themeButton.installEventFilter(ToolTipFilter(self.themeButton))
        self.supportButton.installEventFilter(ToolTipFilter(self.supportButton))
        self.feedbackButton.installEventFilter(
            ToolTipFilter(self.feedbackButton))
        self.themeButton.setToolTip(self.tr('切换主题'))
        self.supportButton.setToolTip(self.tr('支持作者🥰'))
        self.feedbackButton.setToolTip(self.tr('提供反馈'))

        self.themeButton.clicked.connect(lambda: toggleTheme(True))
        self.supportButton.clicked.connect(signalBus.supportSignal.emit)
        self.feedbackButton.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))

        self.subtitleLabel.setTextColor(QColor(96, 96, 96), QColor(216, 216, 216))



class NolinkCard(QWidget):
    """ Example card with dynamic widget or layout handling """

    def __init__(self,widget, parent=None):
        super().__init__(parent=parent)
        self.widget = widget
        self.card = QFrame(self)

        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = QVBoxLayout(self.card)
        self.topLayout = QHBoxLayout()

        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()
        self.card.setObjectName('card')

    def __initLayout(self):
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.cardLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.topLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        self.vBoxLayout.setSpacing(12)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.setContentsMargins(12, 12, 12, 12)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.card, 0, Qt.AlignTop)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.cardLayout.setSpacing(0)
        self.cardLayout.setAlignment(Qt.AlignTop)
        self.cardLayout.addLayout(self.topLayout, 0)

        if isinstance(self.widget, QLayout):
            self.cardLayout.addLayout(self.widget)
        else:
            self.widget.setParent(self.card)
            self.topLayout.addWidget(self.widget)
            self.widget.show()



class GalleryInterface(ScrollArea):
    """ Gallery interface """

    def __init__(self, title: str, subtitle: str, parent=None):
        """
        Parameters
        ----------
        title: str
            The title of gallery

        subtitle: str
            The subtitle of gallery

        parent: QWidget
            parent widget
        """
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.toolBar = ToolBar(title, subtitle, self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, self.toolBar.height(), 0, 0)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.vBoxLayout.setSpacing(30)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)

        self.view.setObjectName('view')
        StyleSheet.GALLERY_INTERFACE.apply(self)


    def addNolinkLayout(self, widget):
        card = NolinkCard(widget, self.view)
        self.vBoxLayout.addWidget(card, 0, Qt.AlignTop)
        return card



    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.toolBar.resize(self.width(), self.toolBar.height())
