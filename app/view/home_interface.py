# coding:utf-8
from pathlib import Path
from typing import Optional
from PyQt5.QtGui import QDragEnterEvent
from PyQt5.QtCore import Qt,QThread,QTimer,QThreadPool
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout,QHBoxLayout
from qfluentwidgets import (qrouter,TabBar,SubtitleLabel,LineEdit,MessageBoxBase)

from ..common.config import cfg,ADD_PATH,TAB_PATH
from ..common.style_sheet import StyleSheet
from ..components.tabpage import TabPage
from ..common.signal_bus import signalBus
from ..common.photo_tool import photo_tool
from ..components.drop_mask import DropMask


class HomeInterface(QWidget):
    """ Home interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tabs = TabInterface(self)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)
        #创建所有子页面共享的单个ocr实例
        self.ocr = None
        self.ocr_thread = OcrThread(self)
        self.ocr_thread.start()  # 启动线程
        self.thread_pool = QThreadPool.globalInstance()


        self.__initWidget()
        self.ocr_thread.finished.connect(self.on_thread_finished)

        self.dialog_mask = DropMask(self, '文件拖入')
        self.dialog_mask.hide()
        self.dialog_mask.droped_file_url.connect(self.on_file_dropped)
        self.setAcceptDrops(True)


    def __initWidget(self):
        self.view.setObjectName('view')
        self.setObjectName('homeInterface')
        StyleSheet.HOME_INTERFACE.apply(self)
        self.setLayout(self.vBoxLayout)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.addWidget(self.tabs)
        self.vBoxLayout.setAlignment(Qt.AlignTop)


    def on_file_dropped(self, file_url: str):
        """文件拖入后触发的槽方法"""
        try:
            path = self.get_source_script_path(file_url)
            if path:
                data = photo_tool.loadDataFromPath(path)
                if isinstance(data, dict):
                    self.tabs.addAllDataTab(data,True)
        except Exception as e:
            photo_tool.error_print(e)


    def get_source_script_path(self, file_url: str) -> Optional[Path]:
        """ 获取 Python 脚本的路径，确保路径有效且是文件 """
        path = Path(file_url)
        if not path.exists() or not path.is_file():
            return None
        if path.suffix.lower() != '.json':
            return None  # 如果不是 JSON 文件，返回 None
        return path


    def get_mask(self) -> DropMask:
        """获取遮罩"""
        return self.dialog_mask


    def resize_mask(self) -> None:
        self.get_mask().resize(self.width(), self.height())


    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasText():
            self.dialog_mask.show()


    # 窗体大小发生改变触发事件
    def resizeEvent(self, event):
        self.resize_mask()


        #读取完成ocr后关闭线程
    def on_thread_finished(self):
        try:
            if self.ocr_thread and self.ocr_thread.isRunning():
                self.ocr_thread.quit()
                self.ocr_thread.wait()
            self.ocr_thread.deleteLater()
            self.ocr_thread = None
        except:
            pass


class OcrThread(QThread):
    # 可以添加信号用于线程完成通知主线程
    def __init__(self, parent=None):
        super().__init__(parent)
        self.HomeInterface = parent  # 将主类实例传递给线程

    def run(self):
        try:
            from ..common.PPOCR_api import GetOcrApi
            self.HomeInterface.ocr = GetOcrApi("app/tool/PaddleOCR-json_v1.4.1/PaddleOCR-json.exe")
        except Exception as e:
            photo_tool.error_print(e)
        finally:
            self.finished.emit()


class TabInterface(QWidget):
    """ Tab interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tabCount = 1
        self.homeInterface = parent

        self.widgets = []
        self.current_index = 0
        self.is_cycling = False

        self.tabBar = TabBar(self)
        self.stackedWidget = QStackedWidget(self)
        self.tabView = QWidget(self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout(self.tabView)

        self.__initWidget()


    def __initWidget(self):
        self.initLayout()
        self.tabBar.setMovable(True)
        self.tabBar.setScrollable(True)
        self.tabBar.setTabShadowEnabled(True)
        self.connectSignalToSlot()


    def connectSignalToSlot(self):
        signalBus.save_scan_signal.connect(self.saveAllDataTab)
        signalBus.load_scan_signal.connect(self.loadAllDataTab)
        signalBus.load_path.connect(self.loadAllFromPath)
        signalBus.start_index_signal.connect(self.start_tab_scan_by_route_key)
        signalBus.stop_index_signal.connect(self.stop_tab_scan_by_route_key)
        signalBus.cycle_start_signal.connect(self.start_cycle_scan)
        signalBus.stop_scan_signal.connect(self.stop_cycle_scan)
        self.tabBar.tabAddRequested.connect(self.on_add_button_clicked)
        self.tabBar.tabCloseRequested.connect(self.removeTab)
        self.tabBar.mouseDoubleClickEvent = self.on_tab_double_click
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)


    def initLayout(self):
        self.tabBar.setTabMaximumWidth(150)
        # Layout setup
        self.tabBar.setContentsMargins(0, 0, 0, 0)
        self.tabView.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.hBoxLayout.addWidget(self.tabView, 1)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.tabBar)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignTop)


    def addSubInterface(self, widget: TabPage, objectName, text, icon):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.tabBar.addTab(
            routeKey=objectName,
            text=text,
            icon=icon,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )


    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        if not widget:
            return
        self.tabBar.setCurrentTab(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())
        for i in range(self.stackedWidget.count()):
            w = self.stackedWidget.widget(i)
            is_current_widget = bool(w == widget)
            w.pivotInterface.upif = is_current_widget
            w.pivotInterface.up_load(is_current_widget)


    def on_add_button_clicked(self):
        # 弹出输入对话框让用户输入页面的标题
        w = CustomMessageBox(self.window(),self.tabCount)
        if w.exec():
            title = w.titleLineEdit.text()
            self.addNewTab(title)


    def get_all_route_keys(self):
        """
        获取所有已存在的 route_key
        """
        route_keys = set()
        for index in range(self.tabBar.count()):
            try:
                item = self.tabBar.tabItem(index)
                route_key = item.routeKey()
                route_keys.add(route_key)
            except Exception as e:
                print(f"Error getting route_key for tab {index}: {e}")
        return route_keys

    def get_unique_route_key(self, base_key):
        """
        生成唯一的 route_key
        :param base_key: 原始的 route_key
        :return: 唯一的 route_key
        """
        route_keys = self.get_all_route_keys()  # 获取所有已存在的 route_key
        new_key = base_key
        counter = 1
        while new_key in route_keys:
            new_key = f"{base_key}_{counter}"
            counter += 1
        return new_key



    def addNewTab(self,title):
        unique_route_key = self.get_unique_route_key(title)
        tabtitle = {
        "tab_name": unique_route_key,
        "route_key": unique_route_key,
        }
        defaultAdd =  cfg.get(cfg.defaultAdd)
        newTab = TabPage(self,title= tabtitle, graph_text=[],operations=[],detail=None)
        if defaultAdd == "Custom":
            data = photo_tool.loadDataFromPath(ADD_PATH)
            newTab = TabPage(self,title= tabtitle, graph_text=data["graph_text"],operations=data["operations"],detail=data["detail"])
        try:
            self.addSubInterface(newTab, unique_route_key , unique_route_key, ':/images/logo.png')
            self.tabCount += 1
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("重复的tab名称:")+f"{str(e)}","TOP","error")



    def addDataTab(self, tabData , default = False):
        # 通过传入的 tabData 创建新的 TabPage
        try:
            if default:
                base_key = "defaultscan"
            else:
                base_key = tabData['tab']['route_key']
            unique_route_key = self.get_unique_route_key(base_key)

            if default:
                tabtitle = {
                    "tab_name": self.tr("默认扫描"),
                    "route_key": unique_route_key,
                }
            else:
                tabtitle = tabData['tab']
                tabtitle["route_key"] = unique_route_key

            newTab = TabPage(self, tabtitle, tabData['graph_text'], tabData['operations'], tabData['detail'])

            title = tabtitle['tab_name']
            objectName = tabtitle['route_key']
            self.addSubInterface(newTab, objectName, title, ':/images/logo.png')
            self.tabCount += 1
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("重复的tab名称:")+f"{str(e)}","TOP","error")



    #保存所有页面的dataTab
    def saveAllDataTab(self):
        try:
            photo_tool.saveDataToJson(self.getAllDataTab())
        except Exception as e:
            photo_tool.error_print(e)


    #获取所有页面的dataTab,可以用于保存
    def getAllDataTab(self):
        all_tab_content = {}
        tab_count = self.tabBar.count()  # 获取 tab 的数量
        for index in range(tab_count):
            try:
                # 获取 tab 的 route_key 作为唯一标识
                item = self.tabBar.tabItem(index)
                route_key = item.routeKey()
                # 根据 route_key 查找对应的 TabPage
                tab_page = self.stackedWidget.findChild(TabPage, route_key)
                # 获取 TabPage 中的相关信息
                title = tab_page.title
                detail = tab_page.pivotInterface.scanInterface.getdetail()
                graph_text = tab_page.pivotInterface.scanInterface.get_graph()
                operations = tab_page.pivotInterface.scriptInterface.operations

                # 将 tab 页的信息保存到字典
                single_content = {
                    'tab': title,
                    'detail': detail,
                    'graph_text': graph_text,
                    'operations': operations
                }
                # 根据 route_key 保存内容
                all_tab_content[route_key] = single_content
            except Exception as e:
                photo_tool.error_print(e)
        return all_tab_content


    #打开文件浏览器,加载页面
    def loadAllDataTab(self,method):
        datatab = {}
        datatab = photo_tool.loadDataFromJson()
        if datatab:
            self.addAllDataTab(datatab,method)



    #读取dataTab,加载页面
    def loadAllFromPath(self, filepath):
        datatab = {}
        datatab = photo_tool.loadDataFromPath(filepath)
        if datatab:
            if filepath == TAB_PATH:
                self.clearAllTabs()
                self.addDataTab(datatab, default=True)
            else:
                self.addAllDataTab(datatab, True)



    #通过dataTab来生成所有的tab
    def addAllDataTab(self, datatab:dict, method:bool):
        try:
            if method:
                self.clearAllTabs()
            for (route_key, tab_data) in datatab.items():
                self.addDataTab(tab_data)
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("添加所有tab时出现错误:")+f"{str(e)}","TOP","error")
            photo_tool.error_print(e)
        self.update()
        signalBus.switchToInterface.emit('home')


    def clearAllTabs(self):
        # 获取所有的 TabPage
        tab_count = self.tabBar.count()
        widget_count = self.stackedWidget.count()
        try:
            for _ in range(tab_count):
                self.tabBar.removeTab(0)
            for _ in range(widget_count):
                widget = self.stackedWidget.widget(0)
                if widget:
                    self.stackedWidget.removeWidget(widget)
                    widget.deleteLater()
            self.tabCount = 0
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("删除tab时出现错误")+f"{str(e)}","TOP","error")
            photo_tool.error_print(e)


    def removeTab(self, index):
        try:
            item = self.tabBar.tabItem(index)
            widget = self.stackedWidget.findChild(TabPage, item.routeKey())
            if self.stackedWidget.count() == 1 :
                signalBus.main_infobar_signal.emit(self.tr("警告"), self.tr("删除全部可能出现错误"),"TOP","warning")
            self.stackedWidget.removeWidget(widget)
            self.tabBar.removeTab(index)
            widget.deleteLater()
            self.tabBar.update()
            self.stackedWidget.update()
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("删除tab时出现错误"),"TOP","error")
            photo_tool.error_print(e)


    def get_all_tab_texts(self):
        tab_texts = []
        for index in range(self.tabBar.count()):  # 遍历所有标签
            tab_text = self.tabBar.tabText(index)  # 获取当前标签的文本
            tab_texts.append(tab_text)
        return tab_texts


    def get_all_tab_route_keys(self):
        route_keys = []
        for index in range(self.tabBar.count()):  # 遍历所有标签
            tab_item = self.tabBar.tabItem(index)  # 获取当前标签项
            route_key = tab_item.routeKey()  # 获取当前标签的 routeKey
            route_keys.append(route_key)
        return route_keys


    def get_tab_name_by_route_key(self, route_key):
        # 遍历所有标签，查找匹配的 route_key
        for index in range(self.tabBar.count()):
            tab_item = self.tabBar.tabItem(index)
            if tab_item.routeKey() == route_key:  # 如果找到匹配的 route_key
                tab_name = tab_item.text()  # 获取标签的名称
                return tab_name, index  # 返回标签的名称和位置（索引）
        return None, None


    def start_tab_scan_by_route_key(self, route_key):
        # 遍历所有标签，查找匹配的 route_key
        widget = self.stackedWidget.findChild(TabPage, route_key)
        if widget:
            widget.pivotInterface.scanInterface.start_scanning()
        else:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("出现了不存在的页面"),"TOP","error")


    def stop_tab_scan_by_route_key(self, route_key):
        # 遍历所有标签，查找匹配的 route_key
        widget = self.stackedWidget.findChild(TabPage, route_key)
        if widget:
            widget.pivotInterface.scanInterface.stop_scanning()
        else:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("出现了不存在的页面"),"TOP","error")


    def start_cycle_scan(self):
        """ 启动循环扫描 """
        self.widgets = self.stackedWidget.findChildren(TabPage)
        if not self.widgets:
            return
        self.current_index = 0  # 当前扫描的部件索引
        self.is_cycling = True
        self.start_next_scan()


    def start_next_scan(self):
        """ 启动当前部件的扫描 """
        if not self.is_cycling:  # 如果循环已停止，则退出
            return
        if self.current_index >= len(self.widgets):
            self.current_index = 0  # 重置索引，实现循环

        widget = self.widgets[self.current_index]
        widget.pivotInterface.scanInterface.start_scanning(1)

        # 创建定时器（如果尚未创建）
        if not hasattr(self, 'scan_timer'):
            self.scan_timer = QTimer()
            self.scan_timer.timeout.connect(self.check_scan_status)
        self.scan_timer.start(100)

    def check_scan_status(self):
        """ 检查当前部件的扫描状态 """
        if not self.is_cycling:  # 如果循环已停止，则退出
            return
        widget = self.widgets[self.current_index]
        if widget.pivotInterface.scriptInterface.scanning:
            return
        self.current_index += 1
        if self.current_index >= len(self.widgets):
            self.current_index = 0  # 重置索引，实现循环
        self.start_next_scan()

    def stop_cycle_scan(self):
        """ 停止循环扫描 """
        self.is_cycling = False  # 停止循环标志
        try:
            if self.scan_timer and self.scan_timer.isActive():
                self.scan_timer.stop()  # 停止定时器
        except:
            pass



    def on_tab_double_click(self, event):
        # 获取双击的 tab 索引
        tab_index = self.tabBar.currentIndex()
        if tab_index == -1:
            return
        object_name = self.tabBar.tabText(tab_index)
        w = CustomMessageBox(self.window())
        w.titleLineEdit.setText(object_name)
        new_title = None
        if w.exec():
            new_title = w.titleLineEdit.text()
        if new_title:
            self.tabBar.setTabText(tab_index,new_title)


class CustomMessageBox(MessageBoxBase):
    """ 扫描页名称 """

    def __init__(self, parent=None,tabCount = None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(self.tr('扫描页名称'), self)
        self.titleLineEdit = LineEdit(self)

        self.titleLineEdit.setPlaceholderText(self.tr('输入标题(最好英文,不能重复)'))
        self.titleLineEdit.setClearButtonEnabled(True)


        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.titleLineEdit)

        self.yesButton.setText(self.tr('确定'))
        self.cancelButton.setText(self.tr('取消'))

        self.widget.setMinimumWidth(360)
        self.yesButton.setDisabled(True)
        self.titleLineEdit.textChanged.connect(self._validateUrl)
        if tabCount:
            self.titleLineEdit.setText(f"scan{tabCount}")
            self.yesButton.setDisabled(False)

    def _validateUrl(self, text):
        if text and self._is_valid_object_name(text):
            self.yesButton.setEnabled(True)
        else:
            self.yesButton.setEnabled(False)

    def _is_valid_object_name(self, text):
        # 判断 text 是否不以数字开头
        return not text[0].isdigit()

