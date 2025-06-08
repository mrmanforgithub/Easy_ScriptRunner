import ast
import time
import re
from PIL import  ImageGrab
import numpy as np
from collections import defaultdict


from PyQt5.QtCore import Qt, pyqtSignal,QThreadPool,QObject,QRunnable,QTimer,QPoint
from PyQt5.QtGui import QPixmap, QColor,QCursor
from PyQt5.QtWidgets import QWidget,QVBoxLayout, QLabel,QHBoxLayout,QFrame,QScrollArea,QSplitter,QSizePolicy
from qfluentwidgets import (Action, qrouter, PrimaryDropDownToolButton, SwitchButton, LineEdit, TransparentToolButton,
                            ProgressBar, DoubleSpinBox, SpinBox, PrimaryPushButton,setFont,TransparentPushButton,ComboBox,ToggleButton, FluentIcon,PrimaryDropDownPushButton, RoundMenu,qconfig,MessageBoxBase,SubtitleLabel,ToolTipFilter)
from qfluentwidgets import FluentIcon as FIF

from ..common.photo_tool import photo_tool
from ..common.signal_bus import signalBus
from ..common.config import cfg
from ..components.iconlabel import IconLabel
from ..common.style_sheet import StyleSheet
from ..common.modmanager import ModManager
from ..common.recognizer_registry import RECOGNIZER_REGISTRY
from .recognizer_widget import (
    ImageRecognitionWidget,
    TextRecognitionWidget,
    ColorRecognitionWidget,
    AlwaysSuccessWidget
)


#图文界面内容
class ScanPage(QWidget):
    """自定义扫描页面"""
    update_label_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int,str)

    def __init__(self, parent=None,graph_text = [],detail = None):
        super().__init__(parent=parent)
        # 创建最外层的水平布局
        self.pivot = parent
        #由于初始化的时候,这个scriptPage还没有创建,所以只能为None,随后会赋值
        self.scriptpage = None
        self.logpage = None
        self.upif = True
        #主题色
        self.theme_color = qconfig.themeColor.value
        #存放所有图文行的具体数据
        self.graph_text = graph_text
        self.detail = detail
        #存放所有图文行的内容
        self.rec_path = []
        #存放所有图文行的扫描地址
        self.rec_address = []

        self.RecognizeWidget = defaultdict(lambda: None)
        #线程池
        try:
            self.thread_pool = self.pivot.tabpage.tabinterface.homeInterface.thread_pool
        except:
            self.thread_pool = None
        self.main_layout = QHBoxLayout(self)

        # 左边部分的垂直布局
        self.left_layout = QVBoxLayout()
        self.splitter = QSplitter(Qt.Horizontal, self)
        # QScrollArea存放图文栏
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setWidgetResizable(True)  # 使其大小可调整
        self.scroll_content.setObjectName("view")



        # 确保更新布局
        self.scroll_area.update()  # 强制更新，确保布局正确
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.button = PrimaryDropDownPushButton(self.tr('创建识别对象'), self, FluentIcon.FINGERPRINT)
        self.button.setMinimumHeight(50)

        # 将 QScrollArea 和 PrimaryButton 添加到左侧布局
        self.left_layout.addWidget(self.scroll_area)
        self.left_layout.addWidget(self.button)



        # 右侧布局
        self.right_layout = QVBoxLayout()

        # 定时器部分
        self.timer_panel = QWidget()
        self.timer_layout = QVBoxLayout(self.timer_panel)
        # 定时器进度条
        self.progress_bar = ProgressBar(self.timer_panel)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.timer_layout.addWidget(self.progress_bar)
        # 定时器按钮
        self.timer_button = PrimaryPushButton(self.tr('设置定时器'))
        # 定时器布局面板
        self.timer_layout.addWidget(self.timer_button)
        self.timer_layout.setAlignment(Qt.AlignTop)


        #窗口选择/状态栏内容
        self.status_label = QLabel(self.tr("无窗口选择"), self)
        self.status_label.setObjectName("window_select")

        self.window_process = None

        self.status_label.setAlignment(Qt.AlignCenter)

        #扫描状态栏内容
        self.scan_status_label = QLabel(self.tr("未开始扫描"), self)
        self.scan_status_label.setObjectName("scanstatuslabel")
        self.scan_status_label.setAlignment(Qt.AlignCenter)
        self.scan_status_label.setSizePolicy(
            QSizePolicy.Minimum,  # 水平方向
            QSizePolicy.Expanding   # 垂直方向
        )
        self.scan_status_label.setWordWrap(True)



        # 相似度设置部分
        self.similarity_label = QLabel(self.tr("相似度："), self)
        self.similarity_spinbox = SpinBox(self)
        self.similarity_spinbox.setRange(0, 100)
        self.similarity_spinbox.setValue(75)  # 默认值
        self.similarity_layout = QHBoxLayout()
        self.similarity_layout.addWidget(self.similarity_label)
        self.similarity_layout.addWidget(self.similarity_spinbox)
        self.similarity_spinbox.setFixedWidth(120)


        # 扫描间隔设置部分
        self.interval_label = QLabel(self.tr("扫描间隔："), self)
        self.interval_spinbox = DoubleSpinBox(self)
        self.interval_spinbox.setRange(0.01, 100.0)
        self.interval_spinbox.setValue(0.1)  # 默认值
        self.interval_layout = QHBoxLayout()
        self.interval_layout.addWidget(self.interval_label)
        self.interval_layout.addWidget(self.interval_spinbox)
        self.interval_spinbox.setFixedWidth(120)


        #窗口选择/满足一个
        self.switchButton = SwitchButton(self.tr('全部满足'))
        self.switchButton.setChecked(True)
        self.switchButton.setText(self.tr('全部满足'))
        self.window_button = PrimaryPushButton(self.tr('设置窗口'))
        self.switch_layout = QHBoxLayout()
        self.switch_layout.addWidget(self.window_button)
        self.switch_layout.addWidget(self.switchButton)
        self.switch_layout.setAlignment(self.switchButton,Qt.AlignRight)

        # 开始扫描按钮
        self.start_scan_button = ToggleButton(self.tr('开始扫描'), self, FluentIcon.ROTATE)
        self.start_scan_button.installEventFilter(ToolTipFilter(self.start_scan_button))
        self.start_scan_button.setToolTip(self.tr('默认快捷键:')+"Alt+O/Alt+P")
        self.start_scan_button.setMinimumHeight(80)

        #添加到右布局
        self.right_layout.addWidget(self.status_label)
        self.right_layout.addWidget(self.timer_panel)
        self.right_layout.addWidget(self.scan_status_label)
        self.right_layout.addLayout(self.similarity_layout)
        self.right_layout.addLayout(self.interval_layout)
        self.right_layout.addLayout(self.switch_layout)
        self.right_layout.addWidget(self.start_scan_button)

        self.left_widget = QWidget()
        self.left_widget.setLayout(self.left_layout)

        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_layout)
        self.right_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.right_widget.setMinimumWidth(230)
        self.right_widget.setMaximumWidth(270)


        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        self.main_layout.addWidget(self.splitter)

        self.setLayout(self.main_layout)

        #尝试加载mod并且更改 RECOGNIZED注册器
        mod_manager = ModManager()
        mod_manager.load_mods()

        self.event_bind(self.button)
        self.generate_recognition_interface(self.graph_text)
        self.initdetail(self.detail)
        self.connectSignalToSlot()

        StyleSheet.SCAN_PAGE.apply(self)



#事件绑定和界面生成

    #根据识别参数填充界面
    def initdetail(self,detail):
        try:
            window_process = detail["window_process"]
            switch_method = detail["switch_method"]
            similar = detail["similar"]
            scan_interval = detail["scan_interval"]
        except:
            return
        if window_process:
            self.status_label.setText(window_process)
            self.window_process = window_process
        if switch_method is True:
            self.switchButton.setChecked(True)
            self.switchButton.setText(self.tr('全部满足'))
        else:
            self.switchButton.setChecked(False)
            self.switchButton.setText(self.tr('满足一个'))
        if similar:
            self.similarity_spinbox.setValue(similar)
        if scan_interval:
            self.interval_spinbox.setValue(scan_interval)


    #获取识别参数
    def getdetail(self):
        detail = {}
        # 获取窗口进程
        detail["window_process"] = self.window_process if hasattr(self, 'window_process') else ""
        # 获取切换方式
        detail["switch_method"] = self.switchButton.isChecked()
        # 获取相似度
        detail["similar"] = self.similarity_spinbox.value()
        # 获取扫描间隔
        detail["scan_interval"] = self.interval_spinbox.value()
        return detail


    #连接到槽函数
    def connectSignalToSlot(self):
        # 连接信号到槽函数
        self.update_label_signal.connect(self.update_ui_label)
        self.update_progress_signal.connect(self.update_progress)
        self.similarity_spinbox.valueChanged.connect(self.update_similar)
        self.interval_spinbox.valueChanged.connect(self.update_interval)
        signalBus.stop_scan_signal.connect(self.stop_scanning)
        signalBus.start_scan_signal.connect(self.start_scanning)


    #按下开始扫描后，切换按钮状态和启动函数
    def on_start_scan_toggled(self, checked):
        """按下开始扫描的切换函数"""
        if checked:
            try:
                graph_count = sum(1 for _ in self.graph_text)
                if graph_count:
                    self.start_scanning()
                else:
                    raise ValueError
            except:
                signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("页面无图文栏！"),"TOP","error")
                self.stop_scanning()
        else:
            try:
                self.stop_scanning()
            except:
                signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("关闭扫描时出现错误"),"TOP","error")


    #切换满足方式  全部满足/满足一个
    def onSwitchCheckedChanged(self, isChecked):
        """切换满足方式的函数"""
        if isChecked:
            self.switchButton.setText(self.tr('全部满足'))
        else:
            self.switchButton.setText(self.tr('满足一个'))


    #事件绑定,主要绑定添加识别目标的按钮的事件
    def event_bind(self,widget):
        """绑定各类触发函数"""
        self.switchButton.checkedChanged.connect(self.onSwitchCheckedChanged)
        self.status_label.mouseDoubleClickEvent =  lambda event: self.open_window_selection()
        self.window_button.clicked.connect(self.open_window_selection)
        self.start_scan_button.toggled.connect(self.on_start_scan_toggled)
        self.timer_button.clicked.connect(self.open_timer_set)

        menu = RoundMenu(parent=self)
        for category, item in RECOGNIZER_REGISTRY.items():
            icon = item.icon
            action = Action(icon, self.tr(category))
            action.triggered.connect(lambda _, category=category: self.handle_recognition(category))
            menu.addAction(action)

        widget.setMenu(menu)



#槽函数

    # 用于修改label内容
    def update_ui_label(self, text):
        """槽函数,用于修改扫描状态栏内容"""
        if self.upif:
            self.scan_status_label.setText(text)


    # 用于修改进度条
    def update_progress(self, value, str):
        """槽函数,用于修改定时器progressbar内容"""
        if self.upif:
            self.timer_button.setText(str)
            self.progress_bar.setValue(value)


    #用于修改相似度
    def update_similar(self,value:int):
        self.scriptpage.check_similar = value/100


    #用于修改扫描间隔
    def update_interval(self,value:float):
        self.scriptpage.scan_interval = value


#工具函数/轮子


    #获取一个颜色的反色
    def getInversedcolor(self,color):
        color = QColor(color)
        inverted_color = color.rgb() ^ 0xFFFFFF
        inverted_qcolor = QColor(inverted_color)
        inverted_hex = inverted_qcolor.name()
        return inverted_hex


    #添加识别操作
    def handle_recognition(self, category):
        """添加图文识别"""
        self.save_graph()
        count = sum(1 for _ in self.graph_text) + 1
        name = f"{self.tr(category)} {count}"
        recognition_data = {
            "类别": category,
            "名称": name,
            "识别内容": "",  # 可以在之后动态填充识别内容
            "识别区域": [0, 0, 0, 0]  # 识别区域（可以根据实际情况修改）
        }
        self.graph_text.append(recognition_data)
        self.generate_recognition_interface(self.graph_text)


    #根据graph_text动态生成左边的scroll界面
    def generate_recognition_interface(self, data):
        """根据本地图文列生成对应图文界面"""
        for widget in self.scroll_content.findChildren(QWidget):
            self.scroll_layout.removeWidget(widget)
            widget.deleteLater()
        self.rec_path.clear()
        self.rec_address.clear()
        self.scroll_layout.update()
        if not data:
            return
        for i, item in enumerate(data):
            widget_data = RECOGNIZER_REGISTRY.get(item["类别"])  # 根据类别获取 Widget 类
            if widget_data:
                widget_class = widget_data.cls
                icon = widget_data.icon
                widget = widget_class(self)
                if item["类别"] =="图像识别":
                    widget.photo_base = item["识别内容"]
                self.RecognizeWidget[i] = widget
                if item["类别"] !="必定成功":
                    if "识别内容" in item and item["识别内容"]:
                        widget.line_edit.setText(item["识别内容"])
                    if "识别区域" in item and item["识别区域"]!=[0,0,0,0]:
                        widget.address_edit.setText(str(item["识别区域"]))
                self.rec_path.append(widget.line_edit)
                self.rec_address.append(widget.address_edit)
            else:
                signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("无法识别的类型"), "TOP","error")
                continue
            name_label = IconLabel(icon=icon, text=item.get("名称", "未命名"+f"{i+1}"), parent=self)
            name_label.setStyleSheet("font-weight: bold;padding-top:10px;")  # 加粗字体
            menu_button = TransparentToolButton(FIF.MENU)

            title_layout = QHBoxLayout()
            title_layout.addWidget(name_label)
            title_layout.addWidget(menu_button)

            close_button = TransparentToolButton(FluentIcon.CLOSE, self)
            horizontal_layout = QHBoxLayout()
            horizontal_layout.addWidget(widget)
            horizontal_layout.addWidget(close_button, alignment=Qt.AlignRight)

            vertical_layout = QVBoxLayout()
            vertical_layout.addLayout(title_layout)
            vertical_layout.addLayout(horizontal_layout)
            container = QWidget(self)
            container.setObjectName("Container")

            container.setLayout(vertical_layout)
            menu_button.clicked.connect(lambda _, menu_button=menu_button, index=i, : self.show_recognition_menu(menu_button.mapToGlobal(QPoint(menu_button.width()+10, -20)), index, menu_button))
            close_button.clicked.connect(lambda _, index=i: self.remove_recognition(index))
            name_label.mouseDoubleClickEvent = lambda _,index = i :self.start_edit_name(index)
            container.setContextMenuPolicy(Qt.CustomContextMenu)
            container.customContextMenuRequested.connect(
                lambda _,index=i, container=container: self.show_recognition_menu(QCursor.pos(), index, container)
            )

            self.scroll_layout.addWidget(container)
            self.scroll_area.setWidgetResizable(True)


    #移动识别对象的顺序
    def moveTarget(self,index:int,step:int):
        try:
            self.graph_text[index + step], self.graph_text[index] = self.graph_text[index], self.graph_text[index  + step]
            self.generate_recognition_interface(self.graph_text)
        except:
            pass


    #修改识别对象的名称
    def start_edit_name(self,index):
        targetname = TargetNameBox(self.window())
        self.save_graph()
        name = self.graph_text[index].get("名称", "未命名"+f"{index+1}")
        targetname.titleLineEdit.setText(name)
        if targetname.exec_():
            window_name = targetname.titleLineEdit.text()
            self.graph_text[index]["名称"] = window_name
            self.generate_recognition_interface(self.graph_text)


    #显示右键菜单(调试识别)
    def show_recognition_menu(self, pos, index ,container):
        """显示右键菜单"""
        try:
            context_menu = RoundMenu("",container)
            up_action = Action(FIF.UP,self.tr("上移识别对象"), self)
            up_action.triggered.connect(lambda: self.moveTarget(index,-1))
            down_action = Action(FIF.DOWN,self.tr("下移识别对象"), self)
            down_action.triggered.connect(lambda: self.moveTarget(index,1))
            close_action = Action(FIF.DELETE,self.tr("删除识别对象"), self)
            close_action.triggered.connect(lambda: self.remove_recognition(index))
            exe_action = Action(FIF.DEVELOPER_TOOLS,self.tr("调试执行识别"), self)
            exe_action.triggered.connect(lambda: self.recognize(self.graph_text[index]))
            show_action = Action(FIF.DEVELOPER_TOOLS,self.tr("识别并显示区域"), self)
            show_action.triggered.connect(lambda: self.recognize(self.graph_text[index],show=True))
            context_menu.addAction(up_action)
            context_menu.addAction(down_action)
            context_menu.addAction(close_action)
            context_menu.addAction(exe_action)
            context_menu.addAction(show_action)
            context_menu.exec_(pos)
        except Exception as e:
            photo_tool.error_print(e)


    #删除指定index的graph_text
    def remove_recognition(self, index:int):
        """删除图像识别的控件和相关容器"""
        self.save_graph()
        if 0 <= index < len(self.graph_text):
            self.graph_text.pop(index)
        self.generate_recognition_interface(self.graph_text)


    #单次调试识别
    def recognize(self, data:dict ,show = False):
        try:
            if show and data["类别"] != "必定成功":
                signalBus.hideSignal.emit()
                time.sleep(0.15)
            start_time = time.time()
            address = data["识别区域"]
            x1, y1, x2, y2 = address
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            method = data["类别"]
            target = data["识别内容"]
            item = RECOGNIZER_REGISTRY.get(method)
            func = item.func if item else None
            if func:
                result = func(
                    parent=self.scriptpage,
                    target=target,
                    address_content=address,
                    chosen_index=None,
                    returnloc=True,
                    screenshot=screenshot
                )
            else:
                photo_tool.error_print("Not Exist Recignize Function")
                result = False

            if bool(result):
                if not isinstance(result,bool):
                    result_ev= [result[0][0],result[0][1],result[1][0],result[1][1]]
                past_time = round(time.time()-start_time,2)
                signalBus.main_infobar_signal.emit(self.tr("成功"),self.tr("识别成功")+f"{str(result)}"+f"{past_time}s","TOP","success")
                if show and result_ev:
                    photo_tool.show_address(str(result_ev))
            else:
                signalBus.main_infobar_signal.emit(self.tr("失败"),self.tr("识别失败"),"TOP","error")
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"),str(e),"TOP_RIGHT","error")
        finally:
            signalBus.maximizeSignal.emit()


    #将当前的内容保存到 graph_text中去(图文详情)
    def save_graph(self):
        """将当前的内容保存到本地graph_text中去(图文详情)"""
        if self.graph_text is not None:
            for i,content in enumerate(self.graph_text):
                try:
                    if content["类别"] == "图像识别":
                        content["识别内容"] = self.RecognizeWidget[i].photo_base
                    else:
                        content["识别内容"] = self.rec_path[i].text()
                    parsed_content = ast.literal_eval(self.rec_address[i].text())
                    if isinstance(parsed_content, list) and len(parsed_content) == 4:
                        content["识别区域"] = parsed_content
                    else:
                        raise ValueError
                except ValueError:
                    content["识别区域"] = [0,0,0,0]
                except Exception:
                    pass


    #获取当前页面的graph_text,用于写入文件
    def get_graph(self):
        self.save_graph()
        return self.graph_text



#界面设置函数

    #选择窗口
    def open_window_selection(self):
        window_selection = WindowSelectionBox(self.window())
        if window_selection.exec_():
            window_name = window_selection.windowLineEdit.text()
            if window_name == "ScriptRunner" or not window_name:
                self.scriptpage.process_name = None
                self.window_process = None
                self.status_label.setText(self.tr("无窗口选择"))
            else:
                self.scriptpage.process_name = window_name
                self.window_process = window_name
                self.status_label.setText(window_name)


    #选择定时器
    def open_timer_set(self):
        self.scriptpage.time_limit = None
        self.scriptpage.scan_limit = None
        self.scriptpage.execution_limit = None
        timer = TimerSetBox(self.window())
        if timer.exec_():
            time_count = timer.timeLineEdit.text()
            timer_type = timer.comboBox.text()
            if timer_type == self.tr("定时"):
                self.scriptpage.time_limit = int(time_count)
                self.timer_button.setText(self.tr("定时")+f"{time_count}s")
            elif timer_type == self.tr("扫描次数"):
                self.scriptpage.scan_limit = int(time_count)
                self.timer_button.setText(self.tr("扫描")+f"{time_count}"+self.tr("次"))
            elif timer_type == self.tr("执行成功次数"):
                self.scriptpage.execution_limit = int(time_count)
                self.timer_button.setText(self.tr("执行")+f"{time_count}"+self.tr("次"))
        else:
            self.timer_button.setText(self.tr("设置定时器"))




#扫描函数

    # 开始扫描
    def start_scanning(self,max_loop = None):
        """ 启动扫描 """
        if self.scriptpage.scanning:
            return
        # 第一部分 GUI 变动
        self.update_gui_for_scan_start()
        # 第二部分 参数归零和初始化
        self.reset_and_initialize_parameters()
        # 第三部分 提炼 scan_list
        scan_list = self.prepare_scan_list()
        if scan_list is None:  # 如果 scan_list 无效，直接返回
            return
        # 第四部分：提交 ScanTask 到线程池并运行
        self.submit_scan_task(scan_list,max_loop)


    def update_gui_for_scan_start(self):
        """ 更新 GUI 以反映扫描开始 """
        self.start_scan_button.setChecked(True)
        if self.upif:
            self.start_scan_button.setText(self.tr('关闭扫描'))
            self.scan_status_label.setText(self.tr("准备提交识别"))
            invered_color = self.getInversedcolor(qconfig.themeColor.value)
            self.scan_status_label.setStyleSheet(f"color:{invered_color}")


    def reset_and_initialize_parameters(self):
        """ 参数归零和初始化 """
        similarity_value = self.similarity_spinbox.value() / 100
        self.scriptpage.check_similar = similarity_value
        interval_value = self.interval_spinbox.value()
        self.scriptpage.scan_interval = interval_value
        self.scriptpage.process_name = self.window_process
        self.save_graph()
        # 归零计数器
        self.scriptpage.time_count = 0
        self.scriptpage.scan_count = 0
        self.scriptpage.execution_count = 0
        # 清空日志
        if self.logpage.scan_log:
            self.logpage.scan_log.clear()


    def prepare_scan_list(self):
        """ 提炼 scan_list """
        total_count = sum(1 for _ in self.graph_text)
        # 初始化 result_check
        button_status = self.switchButton.isChecked()
        self.scriptpage.result_check = [button_status] * total_count
        use_count = 0
        scan_list = []
        for i in range(total_count):

            category = self.graph_text[i]["类别"]
            rec_target = self.graph_text[i]["识别内容"]
            address = self.graph_text[i]["识别区域"]

            if not rec_target.strip():
                use_count += 1
                continue

            try:
                self.scriptpage.result_check[i] = False
                target = None

                if category == "颜色识别":
                    target = rec_target
                    if not re.match(r'^#[0-9a-fA-F]{6}$', target):  # 验证是否为十六进制颜色值
                        raise ValueError("")
                else:
                    target = rec_target

                if address == [0, 0, 0, 0]:
                    raise ValueError("")

                scan_list.append({
                    "target": target,
                    "address": address,
                    "index": i,
                    "category": category
                })

            except Exception as e:
                signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("识别内容有误"), "TOP_RIGHT","error")
                self.stop_scanning()
                return None

        if use_count >= total_count:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("无可用识别内容"), "TOP_RIGHT","error")
            self.stop_scanning()
            return None

        return scan_list


    def submit_scan_task(self, scan_list , max_loop = None):
        """ 提交 ScanTask 到线程池并运行 """
        task = ScanTask(self.scriptpage, scan_list, self ,max_loop=max_loop)
        self.thread_pool.start(task)


    #停止扫描
    def stop_scanning(self):
        self.start_scan_button.setChecked(False)
        if self.upif:
            self.start_scan_button.setText(self.tr("开始扫描"))
            self.scan_status_label.setText(self.tr("未开始扫描"))
            self.scan_status_label.setStyleSheet(f"color: --ThemeColorPrimary")

        self.scriptpage.scanning = False
        self.scriptpage.is_executing = False





#扫描任务线程
class ScanTask(QRunnable):
    def __init__(self, scriptpage, scan_list:list ,scanpage , max_loop = None):
        super().__init__()
        self.scriptpage = scriptpage
        self.scanpage = scanpage
        self.scan_list = scan_list
        self.max_loop = max_loop

    def run(self):
        try:
            self.scriptpage.scan_loop(self.scan_list ,max_loop = self.max_loop)
        except Exception as e:
            signalBus.main_infobar_signal.emit("错误",f"{e}","TOP","error")
            self.scanpage.stop_scanning()
            photo_tool.error_print(e)
        finally:
            pass



#窗口选择
class WindowSelectionBox(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanpage = parent
        self.windowLabel = SubtitleLabel(self.tr('选择窗口'), self)
        self.hwnd_map = photo_tool.get_all_hwnd()
        self.hwnd_map = {handle: title for handle, title in self.hwnd_map.items() if title.strip()}
        self.window_items = [f"{handle}: {title}" for handle, title in self.hwnd_map.items()]
        if not self.window_items:
            self.window_items = [self.tr("没有可用窗口")]
        self.selected_window = ComboBox()
        self.selected_window.addItems(self.window_items)
        self.selected_window.setCurrentIndex(0)

        self.switchButton = SwitchButton(self)
        self.switchButton.setText(self.tr('窗口名称'))

        self.windowLineEdit = LineEdit(self)
        self.windowLineEdit.setPlaceholderText(self.tr('输入窗口名称'))
        self.windowLineEdit.setClearButtonEnabled(True)

        self.viewLayout.addWidget(self.windowLabel)
        self.viewLayout.addWidget(self.selected_window)
        self.viewLayout.addWidget(self.switchButton)
        self.viewLayout.addWidget(self.windowLineEdit)

        self.yesButton.setText(self.tr('确定'))
        self.cancelButton.setText(self.tr('取消'))
        self.widget.setMinimumWidth(360)
        self.selected_window.currentIndexChanged.connect(self._setLineEdit)
        self.switchButton.checkedChanged.connect(self._update_combobox)
        self._update_combobox()

    def _setLineEdit(self,index):
        self.windowLineEdit.setText(str(self.get_selected_window(index=index)))

    def _update_combobox(self):
        """更新ComboBox的内容 根据SwitchButton的状态"""
        if self.switchButton.isChecked():
            self.switchButton.setText(self.tr("窗口句柄"))
        else:
            self.switchButton.setText(self.tr("窗口名称"))
        self._setLineEdit(self.selected_window.currentIndex())

    def get_selected_window(self,index:int):
        """获取选中的窗口信息"""
        hwnd_items = list(self.hwnd_map.items())
        selected_handle, selected_title = hwnd_items[index]
        if selected_title == "ScriptRunner":
            return ''
        if self.switchButton.isChecked():  # 如果是句柄模式
            return selected_handle  # 返回句柄
        else:
            return selected_title  # 返回标题


#定时器设置
class TimerSetBox(MessageBoxBase):
    """ TimerSetBox"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timeLabel = SubtitleLabel(self.tr('定时器设置'), self)
        self.comboBox = ComboBox(self)
        self.comboBox.addItem(self.tr("定时"))
        self.comboBox.addItem(self.tr("扫描次数"))
        self.comboBox.addItem(self.tr("执行成功次数"))
        self.comboBox.setCurrentIndex(0)
        self.timeLineEdit = LineEdit(self)
        self.timeLineEdit.setPlaceholderText(self.tr('输入时间秒数'))
        self.timeLineEdit.setClearButtonEnabled(True)

        self.viewLayout.addWidget(self.timeLabel)
        self.viewLayout.addWidget(self.comboBox)
        self.viewLayout.addWidget(self.timeLineEdit)

        self.yesButton.setText(self.tr('确定'))
        self.cancelButton.setText(self.tr('取消'))

        self.widget.setMinimumWidth(360)
        self.yesButton.setDisabled(True)
        self.comboBox.currentTextChanged.connect(self._setPlacehoder)
        self.timeLineEdit.textChanged.connect(self._validateUrl)

    def _validateUrl(self, text):
        if text and self._is_valid_object_name(text):
            self.yesButton.setEnabled(True)
        else:
            self.yesButton.setEnabled(False)

    def _is_valid_object_name(self, text):
        return text.isdigit()

    def _setPlacehoder(self,text):
        if text == self.tr("定时"):
            self.timeLineEdit.setPlaceholderText(self.tr('输入时间秒数'))
        elif text == self.tr("扫描次数"):
            self.timeLineEdit.setPlaceholderText(self.tr('输入扫描次数'))
        elif text == self.tr("执行成功次数"):
            self.timeLineEdit.setPlaceholderText(self.tr('输入执行成功次数'))


#识别对象名称设置
class TargetNameBox(MessageBoxBase):
    """ 识别对象名称 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(self.tr('识别对象名称'), self)
        self.titleLineEdit = LineEdit(self)

        self.titleLineEdit.setPlaceholderText(self.tr('输入名称(最好不重复)'))
        self.titleLineEdit.setClearButtonEnabled(True)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.titleLineEdit)

        self.yesButton.setText(self.tr('确定'))
        self.cancelButton.setText(self.tr('取消'))

        self.widget.setMinimumWidth(360)
        self.yesButton.setDisabled(True)
        self.titleLineEdit.textChanged.connect(self._validateUrl)

    def _validateUrl(self, text):
        if text and self._is_valid_object_name(text):
            self.yesButton.setEnabled(True)
        else:
            self.yesButton.setEnabled(False)

    def _is_valid_object_name(self, text):
        # 判断 text 是否不以数字开头
        return not text[0].isdigit()
