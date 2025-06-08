from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel
from qfluentwidgets import (qrouter, SegmentedWidget)
from ..common.style_sheet import StyleSheet
from qfluentwidgets import FluentIcon as FIF
from ..components import scanpage,scriptpage,logpage
from ..common.signal_bus import signalBus


#单独page
class TabPage(QWidget):
    """单个Tab页面"""
    def __init__(self, parent=None,title = [], graph_text = [], operations = [] , detail = None):
        super().__init__(parent=parent)
        self.tabinterface = parent
        self.title = title
        self.layout = QVBoxLayout(self)
        self.pivotInterface = PivotInterface(self,graph_text = graph_text,operations = operations , detail = detail)
        self.layout.addWidget(self.pivotInterface)  # 导航栏
        self.setLayout(self.layout)

#上方导航栏
class PivotInterface(QWidget):
    """ Pivot interface """
    Nav = SegmentedWidget
    def __init__(self, parent=None, graph_text = [], operations = [] , detail = None):
        super().__init__(parent=parent)
        self.tabpage = parent
        self.pivot = self.Nav(self)
        self.upif = True

        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)
        self.scanInterface = scanpage.ScanPage(self,graph_text = graph_text , detail = detail)
        self.scriptInterface = scriptpage.ScriptPage(self,operations = operations)
        self.logInterface = logpage.LogPage(self)
        self.scanInterface.scriptpage = self.scriptInterface
        self.scanInterface.logpage = self.logInterface
        self.scriptInterface.logpage = self.logInterface
        # add items to pivot
        self.addSubInterface(self.scanInterface, 'scanInterface', self.tr('识别对象'))
        self.addSubInterface(self.scriptInterface, 'scriptInterface', self.tr('操作内容'))
        self.addSubInterface(self.logInterface, 'logInterface', self.tr('运行日志'))
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignTop)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        StyleSheet.NAVIGATION_VIEW_INTERFACE.apply(self)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.scanInterface)
        self.pivot.setCurrentItem(self.scanInterface.objectName())
        qrouter.setDefaultRouteKey(self.stackedWidget, self.scanInterface.objectName())
        self.connectSignalToSlot()


    #连接到槽函数
    def connectSignalToSlot(self):
        # 连接信号到槽函数
        signalBus.is_minimize.connect(lambda: self.up_load(False))
        signalBus.is_normal.connect(lambda: self.up_load(True))
        pass


    def addSubInterface(self, widget: QLabel, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )


    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())
        if self.upif:
            for i in range(self.stackedWidget.count()):
                w = self.stackedWidget.widget(i)
                w.upif = bool(w == widget)
            if widget.objectName() == "logInterface":
                widget.logtable.showlogs(widget.scan_log)


    def up_load(self,method):
        try:
            if method or self.upif:
                current_widget = self.stackedWidget.currentWidget()
                current_widget.upif = True
            else:
                self.scanInterface.upif = False
                self.scriptInterface.upif = False
                self.logInterface.upif = False
        except:
            pass