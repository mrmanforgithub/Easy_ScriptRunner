# coding:utf-8
from typing import List

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtWidgets import  QWidget, QVBoxLayout, QApplication, QFrame, QVBoxLayout, QLabel, QHBoxLayout
from qfluentwidgets import (PrimaryPushButton, FluentIcon, InfoBadge, FluentIcon, IconWidget, isDarkTheme,Theme,SmoothScrollArea, SearchLineEdit,IconWidget,ScrollArea,InfoLevel)
from qfluentwidgets import FluentIcon as FIF
from ..common.style_sheet import StyleSheet
from ..common.config import cfg,TAB_PATH
from ..common.trie import Trie
from ..components.hover_card import HoverCardWidget
from ..common.signal_bus import signalBus
from ..common.photo_tool import photo_tool



class searchLineEdit(SearchLineEdit):
    """ Search line edit """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(self.tr('查找最近打开'))
        self.setFixedWidth(304)
        self.textChanged.connect(self.search)


class IconCard(QFrame):
    """ Icon card """

    clicked = pyqtSignal(dict)  # 发射信号时传递字典数据

    def __init__(self, data: dict, parent=None):
        super().__init__(parent=parent)
        self.data = data
        self.iconview = parent
        self.isSelected = False

        self.setObjectName("iconCard")

        self.setFixedHeight(100)
        self.setMouseTracking(True)
        self.initUI()
        self.setSelected(False)

        self.badge = InfoBadge.success(self.tr('最近'),parent=self)
        self.badge.setVisible(False)
        self.updateBadgePosition()


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateBadgePosition()

    def updateBadgePosition(self):
        margin = 6  # 右边/上边留点空隙
        x = self.width() - self.badge.width() - margin
        y = margin
        self.badge.move(x, y)


    def initUI(self):
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(12, 8, 12, 8)
        self.mainLayout.setSpacing(12)

        # 左侧图标
        self.iconWidget = IconWidget(self)
        self.iconWidget.setFixedSize(40, 40)
        self.iconWidget.setIcon(FluentIcon.DOCUMENT)
        self.mainLayout.addWidget(self.iconWidget, 0, Qt.AlignTop)

        # 中间文本区域（标题 + 路径）
        self.textLayout = QVBoxLayout()
        self.textLayout.setSpacing(4)

        self.titleLabel = QLabel(self)
        self.titleLabel.setText(str(self.data.get("name", "")))
        self.textLayout.addWidget(self.titleLabel)

        self.titleLabel.setObjectName("cardTitle")

        self.bodyLabel = QLabel(self)
        self.bodyLabel.setText(str(self.data.get("path", "")))

        self.bodyLabel.setObjectName("cardBody")


        self.textLayout.addWidget(self.bodyLabel)
        self.mainLayout.addLayout(self.textLayout, 1)

        # 右下角显示打开时间
        self.timeLabel = QLabel(self)
        self.timeLabel.setText(str(self.data.get("load_time", "")))
        self.timeLabel.setAlignment(Qt.AlignRight | Qt.AlignBottom)


        # 创建一个布局包裹时间标签，使其靠右下
        timeLayout = QVBoxLayout()
        timeLayout.addStretch()
        timeLayout.addWidget(self.timeLabel, 0, Qt.AlignRight)
        self.mainLayout.addLayout(timeLayout)


    def mouseReleaseEvent(self, e):
        if not self.isSelected:
            self.clicked.emit(self.data)


    def setSelected(self, isSelected: bool, force=False):
        if isSelected == self.isSelected and not force:
            return
        self.isSelected = isSelected

        if not isSelected:
            self.iconWidget.setIcon(FluentIcon.DOCUMENT)  # 默认使用 FluentIcon.MENU
        else:
            icon = FluentIcon.DOCUMENT.icon(Theme.LIGHT if isDarkTheme() else Theme.DARK)
            self.iconWidget.setIcon(icon)

        self.setProperty('isSelected', isSelected)
        self.setStyle(QApplication.style())


    def enterEvent(self, event):
        self.setGraphicsEffect(QtWidgets.QGraphicsDropShadowEffect(blurRadius=8, xOffset=0, yOffset=2))

    def leaveEvent(self, event):
        self.setGraphicsEffect(None)


class IconInfoPanel(QFrame):
    """ Icon info panel """

    def __init__(self, data: dict, parent=None):
        super().__init__(parent=parent)
        self.iconview = parent

        self.nameLabel = QLabel(data['name'], self)
        self.iconWidget = IconWidget(FluentIcon.MENU, self)
        self.pathTitlelabel = QLabel(self.tr('路径'), self)
        self.pathlabel = QLabel(data['path'], self)  # 显示 path
        self.loadTimeTitleLabel = QLabel(self.tr('最近打开时间'), self)
        self.loadTimelabel = QLabel(data['load_time'], self)  # 显示 load_time

        # 添加打开按钮
        self.openButton = PrimaryPushButton(self.tr('打开'), self)
        self.openButton.clicked.connect(self.openFile)

        self.clearButton = PrimaryPushButton(self.tr('清除'), self)
        self.clearButton.clicked.connect(self.clearFile)


        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(16, 20, 16, 20)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.vBoxLayout.addWidget(self.nameLabel)
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.addWidget(self.iconWidget)
        self.vBoxLayout.addSpacing(45)
        self.vBoxLayout.addWidget(self.pathTitlelabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.pathlabel)
        self.vBoxLayout.addSpacing(34)
        self.vBoxLayout.addWidget(self.loadTimeTitleLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.loadTimelabel)
        self.vBoxLayout.addSpacing(25)  # 添加间距
        self.vBoxLayout.addWidget(self.openButton)  # 添加按钮
        self.vBoxLayout.addSpacing(8)  # 添加间距
        self.vBoxLayout.addWidget(self.clearButton)  # 添加按钮

        self.iconWidget.setFixedSize(48, 48)
        self.setFixedWidth(216)

        self.nameLabel.setObjectName('nameLabel')
        self.pathTitlelabel.setObjectName('subTitleLabel')
        self.loadTimeTitleLabel.setObjectName('subTitleLabel')


    def setData(self, data: dict, selected = True):
        """ 更新面板内容 """
        self.iconWidget.setIcon(FluentIcon.DOCUMENT)  # 默认使用 FluentIcon.MENU
        self.nameLabel.setText(str(data.get('name', '')))
        self.pathlabel.setText(str(data.get('path', '')))
        self.loadTimelabel.setText(str(data.get('load_time', '')))

        for i in range(self.vBoxLayout.count()):
            item = self.vBoxLayout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setVisible(selected)


    def openFile(self):
        """ 打开文件 """
        path = self.pathlabel.text().strip()
        if path:
            signalBus.load_path.emit(path)


    def clearFile(self):
        """ 打开文件 """
        path = self.pathlabel.text().strip()
        if path:
            photo_tool.remove_recent(path)



class IconCardView(QWidget):
    """ Icon card view """

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.trie = Trie()
        self.searchLineEdit = searchLineEdit(self)

        self.view = QFrame(self)
        self.scrollArea = SmoothScrollArea(self.view)
        self.scrollWidget = QWidget(self.scrollArea)
        self.infoPanel = IconInfoPanel({'name': '', 'path': '', 'load_time': ''}, self)  # 初始化为空数据

        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout(self.view)

        self.scrolllayout = QVBoxLayout(self.scrollWidget)


        self.cards = []     # type:List[IconCard]
        self.data_list = []  # 存储从 JSON 文件中读取的数据
        self.currentIndex = -1


        self.__initWidget()


    def __initWidget(self):
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setViewportMargins(0, 4, 0, 4)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.addWidget(self.searchLineEdit)
        self.vBoxLayout.addWidget(self.view)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.scrollArea)
        self.hBoxLayout.addWidget(self.infoPanel, 0, Qt.AlignRight)

        self.scrolllayout.setAlignment(Qt.AlignTop)
        self.scrolllayout.setSpacing(5)
        self.scrolllayout.setContentsMargins(7, 4, 15, 5)

        self.__setQss()

        cfg.themeChanged.connect(self.__setQss)
        self.searchLineEdit.clearSignal.connect(self.showAllIcons)
        self.searchLineEdit.searchSignal.connect(self.search)

        # 从 JSON 文件中读取数据
        signalBus.load_finished.connect(self.loadData)
        self.scrollWidget.mousePressEvent = self.clearSelection


    def clearSelection(self, event):
        """ 点击空白区域时取消选中 """
        for card in self.cards:
            card.setSelected(False)
        self.currentIndex = -1
        self.infoPanel.setData({'name': '', 'path': '', 'load_time': ''},selected=False)


    def loadData(self,dict:list):
        """ 从 JSON 文件加载数据并初始化卡片 """
        try:
            self.data_list = dict
            self.removeAllCard()

            self.cards.clear()
            self.trie.clear()

            for data in self.data_list:
                if data:
                    self.addCard(data)
            self.infoPanel.setData({'name': '', 'path': '', 'load_time': ''},selected=False)
        except:
            pass


    def removeAllCard(self):
        while self.scrolllayout.count():
            item = self.scrolllayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()


    def addCard(self, data: dict):
        """ 添加卡片 """
        card = IconCard(data, self)
        card.clicked.connect(self.setSelectedCard)

        self.trie.insert(data['name'], len(self.cards))  # 根据 name 插入到 Trie 树中
        self.cards.append(card)
        self.scrolllayout.addWidget(card,Qt.AlignTop)

        if len(self.cards) == 1:
            card.badge.setVisible(True)

        if data["path"] == TAB_PATH:
            card.badge.setVisible(True)
            card.badge.setLevel(InfoLevel.ERROR)
            card.badge.setText(self.tr("默认"))



    def setSelectedCard(self, data: dict):
        """ 设置选中的卡片 """
        index = self.data_list.index(data)
        if self.currentIndex >= 0 and self.currentIndex <= len(self.cards):
            self.cards[self.currentIndex].setSelected(False)

        self.currentIndex = index
        self.cards[index].setSelected(True)
        self.infoPanel.setData(data)


    def __setQss(self):
        self.view.setObjectName('iconView')
        self.scrollWidget.setObjectName('scrollWidget')

        StyleSheet.ICON_INTERFACE.apply(self)
        StyleSheet.ICON_INTERFACE.apply(self.scrollWidget)



    def search(self, keyWord: str):
        """ 搜索卡片 """
        items = self.trie.items(keyWord.lower())
        indexes = {i[1] for i in items}
        for i, card in enumerate(self.cards):
            isVisible = i in indexes
            card.setVisible(isVisible)



    def showAllIcons(self):
        """ 显示所有图标 """
        for card in self.cards:
            card.show()




class RecentlyOpenInterface(ScrollArea):
    """ recently open interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.view.setObjectName('view')

        StyleSheet.GALLERY_INTERFACE.apply(self)

        self.setObjectName('recentlyOpenInterface')

        self.hoverCard = HoverCardWidget(FIF.HISTORY,self.tr("最近打开"),self.tr("最近打开的脚本文件"),self)
        self.vBoxLayout.addWidget(self.hoverCard)
        self.iconView = IconCardView(self)
        self.vBoxLayout.addWidget(self.iconView)
