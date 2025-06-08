import re
import time
import numpy as np
import pyautogui
from PIL import  ImageGrab
import pygetwindow as gw
import pyperclip
from collections import defaultdict
from typing import List, Dict, Union, Optional

from PyQt5.QtCore import Qt,QEvent,pyqtSignal,QTimer
from PyQt5.QtGui import QIntValidator,QDoubleValidator
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel,QHBoxLayout,QFrame,QSplitter,QSizePolicy,QTableWidgetItem

from qfluentwidgets import (Action,RadioButton, SwitchButton, LineEdit, ComboBox,ToggleButton,MessageBoxBase,         SubtitleLabel,FluentIcon, PrimaryDropDownToolButton, PrimaryPushButton,setFont,PrimaryToolButton,TableWidget,qconfig,TransparentPushButton, RoundMenu,CommandBar,TransparentDropDownPushButton,BodyLabel,ToolTipFilter)
from qfluentwidgets import FluentIcon as FIF

from ..common.style_sheet import StyleSheet
from ..common.photo_tool import photo_tool
from ..common.signal_bus import signalBus
from ..common.config import cfg
from ..common.scripticon import ScriptIcon
from ..components.iconlabel import IconLabel
from ..components.recorddialog import RecordingDialog

from ..common.operation_registry import OPERATION_REGISTRY
from .operation_widget import (
    WaitOperationWidget,
    CheckOperationWidget,
    MouseOperationWidget,
    KeyboardOperationWidget,
    DragOperationWidget,
    WheelOperationWidget,
    OpenOperationWidget,
    StartOperationWidget
)

from ..common.recognizer_registry import RECOGNIZER_REGISTRY
from .recognizer_widget import (
    ImageRecognitionWidget,
    TextRecognitionWidget,
    ColorRecognitionWidget,
    AlwaysSuccessWidget
)



#操作界面内容
class ScriptPage(QWidget):
    """自定义操作页面"""

    def __init__(self, parent=None, operations = []):
        super().__init__(parent=parent)
        self.pivot = parent
        self.scanpage = self.pivot.scanInterface
        self.logpage = None
        self.upif = False
        self.theme_color = qconfig.themeColor.value  #主题色


        self.operations = operations  #执行的操作内容

        self.start_time = None  # 开始时间
        self.time_count = 0  #当前扫描时间
        self.time_limit = None  #自动结束时间

        self.scan_count= 0  #当前扫描次数
        self.scan_limit= None  #扫描次数上限

        self.execution_count = 0  #当前执行次数
        self.execution_limit = None  #执行次数上限

        # 参数的初始化
        self.process_name = None
        self.scanning = False
        self.is_executing = False  #是否执行

        self.result_check = defaultdict(lambda: True)  # 全为是通过检查/一个是就通过

        self.manager = ParametersManager(self)

        # 默认的扫描相似度阈值 和扫描间隔
        self.check_similar = 0.75
        self.scan_interval = 0.1

        #主体部分 水平布局 分为左右
        self.main_layout = QHBoxLayout(self)
        StyleSheet.HOME_INTERFACE.apply(self)
        # 创建 QSplitter 设置为水平分割线
        self.splitter = QSplitter(Qt.Horizontal, self)

        # 左边部分 垂直布局
        self.left_layout = QVBoxLayout()
        #下半部分是一个table
        self.operation_table =TableFrame(self)
        #左边上半部分是命令条
        self.commandbar = self.createCommandBar()

        #添加到左侧布局
        self.left_layout.addWidget(self.commandbar)
        self.left_layout.addWidget(self.operation_table)
        self.left_layout.setAlignment(Qt.AlignTop)


        #右边部分 垂直布局
        self.right_layout = QVBoxLayout()
        # 当前操作标签
        self.operation_label = IconLabel(icon=FluentIcon.INFO, text= self.tr("无选中操作"), parent= self, reverse=True)
        self.operation_label.setObjectName("operationlabel")
        self.operation_label.setAlignment(Qt.AlignCenter)
        self.operation_label.setMinimumHeight(40)
        self.right_layout.addWidget(self.operation_label)

        # 填充区域（暂时为空）
        self.fill_area = QWidget()
        self.fill_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.fill_layout = QVBoxLayout()
        self.fill_layout.setAlignment(Qt.AlignTop)
        self.fill_area.setLayout(self.fill_layout)
        self.right_layout.addWidget(self.fill_area)

        # 提交和取消按钮
        button_layout = QHBoxLayout()
        self.submit_button = PrimaryPushButton(self.tr("提交"))
        self.cancel_button = TransparentPushButton(self.tr("取消"))
        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.setAlignment(Qt.AlignBottom)
        self.right_layout.addLayout(button_layout)

        self.left_widget = QWidget()
        self.left_widget.setLayout(self.left_layout)
        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_layout)

        # 向 QSplitter 添加左右控件
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)

        # 将左右布局添加到最外层的水平布局
        self.main_layout.addWidget(self.splitter)
        self.operation_table.showoperation(self.operations)
        self.setLayout(self.main_layout)
        self.connectSignalToSlot()
        self.operation_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.operation_table.customContextMenuRequested.connect(self.init_menu)


    def connectSignalToSlot(self):
        # 连接信号到槽函数
        self.operation_table.selection_changed_signal.connect(self.handle_selection_change)

#操作移动与修改

    def createCommandBar(self):
        bar = CommandBar(self)
        # 添加删除按钮，并绑定到 deloperation 方法
        delete_action = Action(FIF.DELETE, self.tr('删除'))
        self.change_action = Action(FIF.EDIT, self.tr('修改'), checkable=True)
        up_action = Action(FIF.UP, self.tr('上移'))
        down_action =Action(FIF.DOWN, self.tr('下移'))
        copy_action =Action(FIF.COPY, self.tr('复制'))
        select_action =Action(FIF.ACCEPT, self.tr('全选'))
        exe_action =Action(FIF.DEVELOPER_TOOLS, self.tr('执行'))
        pram_action =Action(FIF.EMOJI_TAB_SYMBOLS, self.tr('获取参数'))
        record_action =Action(ScriptIcon.RECORD, self.tr('录制'))


        delete_action.triggered.connect(self.operation_delete)  # 绑定删除功能
        self.change_action.triggered.connect(self.operation_change)  # 绑定修改功能
        up_action.triggered.connect(self.operation_move_up)  # 绑定上移功能
        down_action.triggered.connect(self.operation_move_down)  # 绑定下移功能
        copy_action.triggered.connect(self.operation_copy_paste)  # 绑定复制功能
        select_action.triggered.connect(self.operation_table.selectAll)  # 绑定全选功能
        exe_action.triggered.connect(self.operation_execute)  # 绑定执行功能
        pram_action.triggered.connect(self.operation_pram)  # 绑定参数面板
        record_action.triggered.connect(self.open_recording_dialog)  # 绑定参数面板


        bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button = TransparentDropDownPushButton(self.tr('添加'), self, FIF.ADD)
        button.setMenu(self.createCheckableMenu())
        button.setFixedHeight(34)
        setFont(button, 12)
        bar.addWidget(button)

        bar.addActions([
            delete_action,
            self.change_action
        ])
        bar.addSeparator()
        bar.addActions([
            up_action,
            down_action,
            record_action,
            copy_action,
            exe_action,
            pram_action,
            select_action
        ])
        return bar


    #删除操作
    def operation_delete(self):
        selected_rows = set()
        # 获取所有选中的行
        for index in self.operation_table.selectedIndexes():
            selected_rows.add(index.row())
        # 按从大到小的顺序删除选中的行
        for row in sorted(selected_rows, reverse=True):
            del self.operations[row]
            self.operation_table.showoperation(self.operations)
        self.operation_table.clearSelection()


    #修改操作
    def operation_change(self):
        # 获取当前 submit_button 的启用状态
        is_button_enabled = self.submit_button.isEnabled()
        # 判断 change_action 是否被选中
        if self.change_action.isChecked():
            # 如果 change_action 被选中，且按钮当前不可用，则启用按钮
            if not is_button_enabled:
                self.submit_button.setEnabled(True)
            else:
                self.change_action.setChecked(False)
        else:
            # 如果 change_action 没有被选中，且按钮当前可用，则禁用按钮
            if is_button_enabled:
                self.submit_button.setEnabled(False)


    #上移操作
    def operation_move_up(self):
        selected_rows = list(self.operation_table.selectedIndexes())  # 获取所有选中的索引
        if not selected_rows:
            return  # 如果没有选中行，直接返回
        # 获取最后一个选中的行（最后被点击的行）
        last_selected_index = selected_rows[-1]
        last_selected_row = last_selected_index.row()

        # 如果选中的行不是第一行，才可以移动
        if last_selected_row > 0:
            # 获取上面一行的数据
            self.operations[last_selected_row - 1], self.operations[last_selected_row] = self.operations[last_selected_row], self.operations[last_selected_row - 1]
            self.operation_table.showoperation(self.operations)
            # 重新设置选择
            self.operation_table.selectRow(last_selected_row - 1)


    #下移操作
    def operation_move_down(self):
        selected_rows = list(self.operation_table.selectedIndexes())  # 获取所有选中的索引
        if not selected_rows:
            return  # 如果没有选中行，直接返回

        # 获取最后一个选中的行（最后被点击的行）
        last_selected_index = selected_rows[-1]
        last_selected_row = last_selected_index.row()

        # 如果选中的行不是最后一行，才可以移动
        if last_selected_row < self.operation_table.rowCount() - 1:
            self.operations[last_selected_row], self.operations[last_selected_row + 1] = self.operations[last_selected_row + 1], self.operations[last_selected_row]
            self.operation_table.showoperation(self.operations)
            self.operation_table.selectRow(last_selected_row + 1)


    #复制到最后
    def operation_copy_paste(self):
        selected_rows = list(self.operation_table.selectedIndexes())  # 获取所有选中的索引
        if not selected_rows:
            return
        # 获取选中行的索引
        selected_rows_indices = sorted(set(index.row() for index in selected_rows))  # 去重并排序行号
        for row_index in selected_rows_indices:
            operation_data = self.operations[row_index]  # 获取当前行的数据
            self.operations.append(operation_data)  # 将数据添加到操作列表末尾
        self.operation_table.showoperation(self.operations)


    #执行选中行操作一次
    def operation_execute(self):
        selected_rows = list(self.operation_table.selectedIndexes())  # 获取所有选中的索引
        if not selected_rows:
            return
        # 获取选中行的索引
        exe_operation = []
        selected_rows_indices = sorted(set(index.row() for index in selected_rows))
        for row_index in selected_rows_indices:
            operation_data = self.operations[row_index]
            exe_operation.append(operation_data)
        self.execute_operations(operations=exe_operation)


    #获取参数
    def operation_pram(self):
        operation_widget = PramOperationBox(parent= self.window(),scriptpage=self)
        if operation_widget.exec_():
            pass


    #打开录制窗口进行操作录制
    def open_recording_dialog(self):
        self.dialog = RecordingDialog()
        self.dialog.show()
        self.dialog.recording_finished.connect(self.handle_recording_data)

    def handle_recording_data(self, data:list):
        if data:
            self.operations = data
            self.operation_table.showoperation(self.operations)
        signalBus.maximizeSignal.emit()


    #为table添加右键菜单
    def init_menu(self,pos):
        index = self.operation_table.indexAt(pos)
        table_menu = RoundMenu()
        change_actions = None
        if index.isValid():
            row = index.row()
            self.operation_table.selectRow(row)
            change_actions = self.createCheckableMenu(right=True,position=row)

        actions = self.createCheckableMenu(right=True)
        submenu = RoundMenu(self.tr("添加操作"), self)
        submenu.setIcon(FIF.ADD)
        submenu.addActions(actions)

        dele_action = Action(FIF.DELETE,self.tr("删除操作"))
        dele_action.triggered.connect(self.operation_delete)

        move_up_action = Action(FIF.UP,self.tr("操作上移"))
        move_up_action.triggered.connect(self.operation_move_up)

        move_down_action = Action(FIF.DOWN,self.tr("操作下移"))
        move_down_action.triggered.connect(self.operation_move_down)

        copy_action = Action(FIF.COPY,self.tr("复制操作"))
        copy_action.triggered.connect(self.operation_copy_paste)

        select_action =  Action(FIF.ACCEPT,self.tr("全选操作"))
        select_action.triggered.connect(self.operation_table.selectAll)

        exe_action =  Action(FIF.DEVELOPER_TOOLS,self.tr("调试执行"))
        exe_action.triggered.connect(self.operation_execute)

        # 将菜单项添加到右键菜单
        selected_indexes = self.operation_table.selectedIndexes()
        table_menu.addMenu(submenu)
        if change_actions:
            submenu2 = RoundMenu(self.tr("修改操作"), self)
            submenu2.setIcon(FIF.EDIT)
            submenu2.addActions(change_actions)
            table_menu.addMenu(submenu2)
        if selected_indexes:
            table_menu.addAction(dele_action)
            if len(set(index.row() for index in selected_indexes)) == 1:
                table_menu.addAction(move_up_action)
                table_menu.addAction(move_down_action)
            table_menu.addAction(copy_action)
            table_menu.addAction(exe_action)
        table_menu.addAction(select_action)
        table_menu.exec_(self.operation_table.mapToGlobal(pos))


#操作添加

    # 创建添加操作的菜单
    def createCheckableMenu(self, pos=None, right=None, position=None):
        menu = RoundMenu(parent=self)

        actions = []  # 用于存储所有 Action
        for text, item in OPERATION_REGISTRY.items():
            icon = item.icon
            action = Action(icon, self.tr(text))
            action.triggered.connect(lambda checked=False, name=text: self.add_operation_widget(name, position))
            actions.append(action)

        # 按照原来的分组方式添加到菜单
        menu.addActions(actions)  # [等待时间, 检查匹配]

        if right is not None:
            return actions

        if pos is not None:
            menu.exec(pos, ani=True)
        return menu


    # 添加操作
    def add_operation_widget(self, operation_name, position=None, parameters=None):
        if position is None:
            position = self.operation_table.rowCount()
        self.clear_bind()
        item = OPERATION_REGISTRY.get(operation_name)
        widget_factory = item.cls if item else None

        if widget_factory is None:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("未知的操作"), "TOP_RIGHT","error")
            return

        if callable(widget_factory):
            operation_widget = widget_factory(self)
        else:
            operation_widget = widget_factory(self)

        self.fill_layout.addWidget(operation_widget)
        operation_widget.setFocus()
        self.set_operation_label(operation_widget, position, parameters)
        if parameters:
            self.submit_button.setEnabled(False)
            operation_widget.insert_parameters(parameters)
        else:
            self.submit_button.setEnabled(True)
        self.submit_button.clicked.connect(lambda: self.confirm_click(position, operation_widget.get_operation()))
        self.cancel_button.clicked.connect(self.cancel_click)



#操作执行

    def execute_operations(self, operations=None):
        try:
            self.is_executing = True
            skip_count = 0
            singlepass = bool(operations)
            operations = operations if singlepass else self.operations

            for i,operation in enumerate(operations):
                if skip_count > 0:
                    skip_count -= 1
                    continue

                operation_name = operation["operation_name"]
                parameters = operation["parameters"]
                operation_text = operation["operation_text"]

                if (not self.scanning or not self.is_executing) and not singlepass: #不再扫描的时候,也不再继续执行
                    break

                item = OPERATION_REGISTRY.get(operation_name)
                func = item.func if item else None
                if func is not None:
                    if operation_name !="检查匹配":
                        locale = cfg.get(cfg.language).value.name()
                        if locale == "zh_CN":
                            content,method = func(self, parameters = parameters ,args= [operation_text[0],-i-1])
                        else:
                            content,method = func(self, parameters = parameters ,args= [operation_text[1],-i-1])
                        self.logpage.update_log_signal.emit(f"{content}", method)
                    else:
                        skip_num = func(self,parameters = parameters ,args= [operation_text,-i-1])
                        if skip_num == 0:
                            pass
                        elif skip_num > 0:
                            skip_count = skip_num
                            continue
                        elif skip_num <0:
                            break
                else:
                    self.logpage.update_log_signal.emit(self.tr("未知的操作"), "error")
                    continue
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"), str(e),"TOP_RIGHT","error")
            self.logpage.update_log_signal.emit(f"{e}","error")
        finally:
            self.execution_count +=1
            self.is_executing = False  # 操作完成，设置为 False


#界面更新

    #清空控件
    def clear_layout(self, layout):
        """ 清空布局中的所有控件 """
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()  # 删除控件
            elif item.layout():
                self.clear_layout(item.layout())  # 递归删除子布局


    #清除绑定,回归最原始的状态
    def clear_bind(self):
        self.clear_layout(self.fill_layout)
        self.operation_label.setText(self.tr("无选中操作"))
        self.operation_label.icon = FluentIcon.INFO
        self.submit_button.setEnabled(True)
        self.change_action.setChecked(False)
        try:
            self.submit_button.clicked.disconnect()
        except TypeError:
            pass
        try:
            self.cancel_button.clicked.disconnect()
        except TypeError:
            pass


    # 确认提交按钮的点击事件
    def confirm_click(self,position,operation):
        if not operation:
            return
        try:
            if self.operations:
                if 0 <= position < len(self.operations):
                    self.operations.pop(position)  # 删除指定位置的数据
            self.operations.insert(position, operation)
            self.operation_table.showoperation(self.operations)
            self.clear_bind()
            self.operation_table.clearSelection()
            signalBus.main_infobar_signal.emit(self.tr("成功"), self.tr("已经成功提交"),"TOP_RIGHT","success")
        except ValueError as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("错误"),"TOP_RIGHT","error")


    # 取消按钮的点击事件
    def cancel_click(self):
        self.operation_table.clearSelection()
        self.clear_bind()


    #当选中操作的时候 在右侧显示对应的内容
    def handle_selection_change(self, selected_data):
        # 这里处理选中的数据
        try:
            position = int(selected_data[0])-1
        except:
            position = None
        if position is not None:
            try:
                operation_data = self.operations[position]
                operation_name = operation_data.get('operation_name')
                parameters = operation_data.get('parameters')
                self.add_operation_widget(operation_name, position , parameters)
            except:
                pass



#工具/造轮子代码

    #根据类别来修改label内容
    def set_operation_label(self, widget, position = 0, method = None):
        """查找当前类对应的操作名称（翻译文本）和图标"""
        if widget is None:
            self.operation_label.setText(self.tr("无选中操作"))
            self.operation_label.icon = FluentIcon.INFO
            return
        for category, item in OPERATION_REGISTRY.items():
            icon = item.icon
            cls = item.cls
            if cls == widget.__class__:  # 直接获取当前类的类型
                if method:
                    self.operation_label.setText(self.tr("修改-")+category+f"{position+1}")
                else:
                    self.operation_label.setText(self.tr("新建-")+category+f"{position+1}")
                self.operation_label.icon = icon
        return


    #单次识别函数
    def check_scan(self, load_target, address, method:str , index:int):
        screenshot=None
        if address == [0, 0, 0, 0]:
            return False
        x1, y1, x2, y2 = address
        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        result_found = False
        item = RECOGNIZER_REGISTRY.get(method)
        func = item.func if item else None
        if func:
            result = func(
                        parent = self,
                        target = load_target,
                        address_content = address,
                        chosen_index = index,
                        returnloc = True,
                        screenshot = screenshot)
        else:
            photo_tool.error_print("Not Exist Recignize Function")
            result = False

        if result:
            result_found = result
        else:
            result_found = False
        screenshot.close()
        return result_found


    #清空计时器
    def free_timer(self):
        self.scanpage.update_progress_signal.emit(100,self.tr("设置定时器"))
        self.scanpage.stop_scanning()
        photo_tool.window_show_top("ScriptRunner")




#开始扫描
    #初始化扫描数据
    def _initialize_scan(self):
        self.scanning = True
        self.scan_count = 0
        self.time_count = 0
        self.execution_count = 0
        self.is_executing = False
        self.start_time = time.time()
        self.logpage.update_log_signal.emit(self.tr("开始扫描识别"), "end")


    #更新所有的计时器
    def _update_all_counters(self,time_used: float):
        if self.time_limit:
            self._update_scan_time(time_used)
        if self.scan_limit:
            self._update_scan_count()
        if self.execution_limit:
            self._update_execution_count()


    #更新扫描时间
    def _update_scan_time(self, time_used):
        self.time_count += time_used
        if self.scanpage.upif:
            current_time = int(self.time_limit - self.time_count)
            time_str = self.tr("定时") + f"{current_time}s"
            self.scanpage.update_progress_signal.emit(
                int((current_time / self.time_limit) * 100),
                time_str
            )
        if self.time_count >= self.time_limit:
            self.free_timer()


    #更新扫描次数
    def _update_scan_count(self):
        self.scan_count += 1
        if self.scanpage.upif:
            current_count = int(self.scan_limit - self.scan_count)
            count_str = self.tr("扫描") + f"{current_count}" + self.tr("次")
            self.scanpage.update_progress_signal.emit(int((current_count / self.scan_limit) * 100), count_str)
        if self.scan_count >= self.scan_limit:
            self.free_timer()


    #更新执行次数
    def _update_execution_count(self):
        if self.scanpage.upif:
            current_count = int(self.execution_limit - self.execution_count)
            count_str = self.tr("执行") + f"{current_count}" + self.tr("次")
            self.scanpage.update_progress_signal.emit(int((current_count / self.execution_limit) * 100), count_str)
        if self.execution_count >= self.execution_limit:
            self.free_timer()


    #执行扫描
    def _perform_scan(self, scan_list):
        self.scanpage.update_label_signal.emit(self.tr("未扫描到结果"))
        switch_status = self.scanpage.switchButton.isChecked()
        self.result_check = [False] * len(scan_list)

        for i, param in enumerate(scan_list):
            target = param["target"]
            address_content = param["address"]
            chosen_index = param["index"]
            category = param["category"]

            if address_content == [0, 0, 0, 0]:
                signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("地址栏为空"), "TOP_RIGHT", "error")
                self.scanpage.stop_scanning()
                return

            x1, y1, x2, y2 = address_content
            try:
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            except Exception as e:
                self.logpage.update_log_signal.emit(f"截图失败: {e}", "error")
                continue

            item = RECOGNIZER_REGISTRY.get(category)
            func = item.func if item else None
            if func:
                result = func(
                    parent=self,
                    target=target,
                    address_content=address_content,
                    chosen_index=chosen_index,
                    returnloc=False,
                    screenshot=screenshot,
                )
            else:
                self.logpage.update_log_signal.emit(f"识别函数未找到: {category}", "error")
                result = False

            name = self.scanpage.graph_text[chosen_index]["名称"]
            self.result_check[chosen_index] = bool(result)

            if result:
                self.logpage.update_log_signal.emit(f"{name}-" + self.tr("成功"), "success")
            else:
                self.logpage.update_log_signal.emit(f"{name}-" + self.tr("失败"), "error")

            try:
                screenshot.close()
            except Exception:
                pass

        if self._should_execute(switch_status) and not self.is_executing:
            self.scanpage.update_label_signal.emit(self.tr("识别成功"))
            self.execute_operations()


    #检查窗口是否置顶
    def _check_window_active(self, active_window):
        if not active_window:
            return True  # 不阻止扫描

        if self.process_name:
            if self.process_name.isdigit():
                hwnd = int(self.process_name)
                if hwnd != active_window._hWnd:
                    self.scanpage.update_label_signal.emit(self.tr("目标窗口未置顶"))
                    self.logpage.update_log_signal.emit(self.tr("目标窗口未置顶"), "warnning")
                    return False
            else:
                if self.process_name not in active_window.title:
                    self.scanpage.update_label_signal.emit(self.tr("目标窗口未置顶"))
                    self.logpage.update_log_signal.emit(self.tr("目标窗口未置顶"), "warnning")
                    return False
        return True


    #判断是否执行
    def _should_execute(self, switch_status):
        if switch_status:
            return all(self.result_check)
        else:
            return any(self.result_check)


    #结束扫描
    def _finalize_scan(self):
        self._reset_state()
        self.scanpage.update_progress_signal.emit(100, self.tr("设置定时器"))
        self.logpage.update_log_signal.emit(self.tr("关闭扫描识别"), "end")
        self.scanpage.stop_scanning()


    #重置扫描状态
    def _reset_state(self):
        self.start_time = None
        self.time_limit = None
        self.scan_limit = None
        self.execution_limit = None
        self.scan_count = 0
        self.time_count = 0
        self.execution_count = 0
        self.manager.clear()


    def scan_loop(self, scan_list: list, max_loop=None):
        self._initialize_scan()
        ex_time = time.time()
        try:
            while self.scanning:
                if max_loop is not None:
                    if max_loop <= 0:
                        break
                    max_loop -= 1
                time_now = time.time()
                if not self.is_executing:
                    active_window = gw.getActiveWindow()
                    if not self._check_window_active(active_window):
                        time.sleep(self.scan_interval)
                        continue
                    self._perform_scan(scan_list)
                    time_used = time_now - ex_time
                    ex_time = time_now
                    self._update_all_counters(time_used)
                    time.sleep(self.scan_interval)

            self._finalize_scan()
        except Exception as e:
            self.logpage.update_log_signal.emit(f"扫描出错: {e}", "error")
            photo_tool.error_print(e)



class ParametersManager(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.scriptpage = parent
        self.results = defaultdict(lambda: {
            "loc": [0, 0, 0, 0],      # 匹配成功区域坐标
            "text": "",               # 识别文本
            "command": ""             # 命令执行结果
        })



    def clear(self):
        self.results.clear()



    def sele_operation(self, names: list):
        # 获取操作名不在 names 列表中的操作位置
        for category, item in OPERATION_REGISTRY.items():
            if not item.fields:
                names.append(category)

        operation_positions = [
            (index + 1, operation.get("operation_name"))
            for index, operation in enumerate(self.scriptpage.operations)
            if operation.get("operation_name") not in names  # 检查操作名是否不在 names 列表中
        ]
        return operation_positions



    def get_labels(
        self,
        stand_options: Optional[List[str]] = None,
        base_options: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Union[str, int]]]:
        """
        获取标签选项，返回包含显示文本和真实值的字典列表

        参数:
            stand_options: 默认选项列表
            base_options: 基础选项列表
            fields:筛选包含这些值的选项[loc,text,command]

        返回:
            包含显示文本和真实值的字典列表
            [{"text": "显示文本", "real_index": 实值}, ...]
        """
        label_options = []

        # 添加基础选项
        if base_options:
            for opt in base_options:
                real_index = 0
                if opt == self.tr("固定"):
                    real_index = None
                label_options.append({"text": opt, "real_index": real_index})  # 0表示当前位置


        # 添加图形文本选项
        graph_text = self.scriptpage.scanpage.graph_text
        if graph_text:
            for i, item in enumerate(graph_text):
                category = item.get("类别", "未知类别")
                name = item.get("名称", "未命名")

                recognizer_item = RECOGNIZER_REGISTRY.get(category)
                if not recognizer_item:
                    continue

                if fields and not any(f in recognizer_item.fields for f in fields):
                    continue

                label_options.append({
                    "text": f"{name}-{i + 1}",
                    "real_index": i + 1
                })

        # ✅ 操作筛选
        for idx, operation in enumerate(self.scriptpage.operations):
            op_name = operation.get("operation_name")
            item = OPERATION_REGISTRY.get(op_name)

            if not item:
                continue

            if fields and not any(f in item.fields for f in fields):
                continue

            label_options.append({
                "text": f"{self.scriptpage.tr(op_name)}-{idx + 1}",
                "real_index": -(idx + 1)
            })

        if label_options:
            return label_options
        elif stand_options:
            return [{"text": opt, "real_index": 0} for opt in stand_options]
        else:
            return []



    def getPram(self, param):
        """解析输入参数并返回相应的值"""
        if not param:
            return None
        elif isinstance(param, str):
            param = param.strip("[]")
            param = param.strip("()")
            param = param.split(",")
            param = [p.strip() for p in param]
        elif isinstance(param, tuple):
            param = list(param)
        elif isinstance(param, list):
            param = param
        else:
            return None

        if len(param) < 4:  # 至少需要 index 和 method 两个参数
            return None

        index, x, y , method = param
        index = int(index)  # 序号 大于0 是识别对象 小于0是操作结果  等于0是当前位置
        method = int(method)   # 方法 0是识别坐标中心 1是识别文字 2是 命令结果 3是完整识别坐标区域

        if method == 0:
            if index > 0:
                rect = self.results[index-1].get("loc", [0, 0, 0, 0])
            elif index < 0:
                rect = self.results[index].get("loc", [0, 0, 0, 0])
            elif index == 0:
                rect = [0, 0, 0, 0]

            if rect !=[0, 0, 0, 0]:
                center_x = (rect[0][0] + rect[1][0]) // 2
                center_y = (rect[0][1] + rect[1][1]) // 2
                return (center_x + int(x), center_y + int(y))
            elif index == 0:
                center_x,center_y = pyautogui.position()
                return (center_x + int(x), center_y + int(y))
            else:
                return None

        elif method == 1:
            if index > 0:
                body = self.results[index-1].get("text", "")
            elif index < 0:
                body = self.results[index].get("text", "")
            elif index == 0:
                body = None

            if body:
                return  f"{x}{body}{y}"

        elif method == 2:
            body = self.results[index].get("command", "")
            if body:
                return  f"{x}{body}{y}"

        if method == 3:
            if index > 0:
                rect = self.results[index-1].get("loc", [0, 0, 0, 0])
            elif index < 0:
                rect = self.results[index].get("loc", [0, 0, 0, 0])
            elif index == 0:
                rect = [0, 0, 0, 0]

            if rect !=[0, 0, 0, 0]:
                x1 = rect[0][0] + int(x)
                x2 = rect[1][0] + int(x)
                y1 = rect[0][1] + int(y)
                y2 = rect[1][1] + int(y)
                return [x1,y1,x2,y2]
            elif index == 0:
                center_x,center_y = pyautogui.position()
                x1 = center_x - int(x)
                x2 = center_x + int(x)
                y1 = center_y - int(y)
                y2 = center_y + int(y)
                return [x1,y1,x2,y2]
            else:
                return None

        return None



    def getvalue(self, combobox, x_entry, y_entry, method = 0):
        """
        解析 combobox 选项，获取 x/y 偏移量，并根据 method 控制返回格式字符串

        method == 0 的时候 为匹配区域坐标中心

        method == 1 的时候 为文字识别内容

        method == 2 的时候 为操作执行返回数据

        method == 3 的时候 为完整匹配区域坐标

        返回值为元组tuple (a,b,c,d)

        """
        try:
            real_index = combobox.currentData()

            # 解析 x/y 偏移量
            x_plus = x_entry.text().strip()
            y_plus = y_entry.text().strip()

            # 处理数值转换
            if method in [0, 3]:
                x_plus = int(x_plus) if x_plus else 0
                y_plus = int(y_plus) if y_plus else 0

        except Exception:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("数据格式不符合规则！"), "TOP_RIGHT","error")
            return None

        if real_index is not None:
            if method in [0, 3]:  # 坐标相关方法
                return (real_index, x_plus, y_plus, method)
            elif method in [1, 2]:  # 文本/命令方法
                return f"({real_index},{x_plus},{y_plus},{method})"
            else:
                return None
        else:
            return (x_plus, y_plus)



class TableFrame(TableWidget):
    selection_changed_signal = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scriptpage = parent

        self.verticalHeader().hide()
        self.setBorderRadius(8)
        self.setBorderVisible(True)

        self.setColumnCount(4)
        self.setHorizontalHeaderLabels([
            self.tr('id'), self.tr('操作名称'), self.tr('操作参数'),
            self.tr('操作内容')
        ])
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)


    #根据operations来动态生成表格内容
    def showoperation(self,operations):
        if operations is None:
            return
        self.setRowCount(0)
        for i, operation in enumerate(operations):
            operation_name = operation.get('operation_name', '')
            trans_operation = self.scriptpage.tr(operation_name)
            parameters = operation.get('parameters', [])
            operation_text = operation.get('operation_text', '')
            locale = cfg.get(cfg.language).value.name()
            if locale == "zh_CN":
                operation_text = operation_text[0]
            else:
                operation_text = operation_text[1]
            self.insertRow(i)
            new_row = [
            i + 1,  # id 就是当前表格行数 + 1
            trans_operation,
            str(parameters),  # 将参数转为字符串，以便显示
            operation_text
            ]
            for column, value in enumerate(new_row):
                text = str(value)
                if len(text) > 50:
                    text = text[:47] + "..."
                self.setItem(i, column, QTableWidgetItem(text))
        self.resizeColumnsToContents()


    def on_selection_changed(self):
        # 获取当前选中的索引
        selected_indexes = self.selectedIndexes()
        selected_data = []
        if selected_indexes:
            # 打印当前选中的内容
            for index in selected_indexes:
                row = index.row()
                column = index.column()
                item = self.item(row, column)
                selected_data.append(item.text())
        self.selection_changed_signal.emit(selected_data)



class PramOperationBox(MessageBoxBase):
    """ 参数操作窗口 """

    def __init__(self, parent=None, scriptpage=None):
        super().__init__(parent)
        self.scriptpage = scriptpage
        self.manager = self.scriptpage.manager

        self.titleLabel = SubtitleLabel(self.tr('获取变动参数'), self)
        self.viewLayout.addWidget(self.titleLabel)

        # 参数字符串输入框
        self.pram_layout = QHBoxLayout()
        self.pram_entry = LineEdit()
        self.pram_entry.setClearButtonEnabled(True)
        self.pram_entry.setPlaceholderText(self.tr("参数字符串"))
        self.pram_entry.textChanged.connect(self.handle_text_change)

        self.switchButton = SwitchButton(self.tr("翻译参数"))
        self.switchButton.installEventFilter(ToolTipFilter(self.switchButton))
        self.switchButton.setToolTip(self.tr('是否根据用户输入,反向翻译参数来源'))
        self.switchButton.checkedChanged.connect(self.onSwitchCheckedChanged)
        self.switchButton.setChecked(True)

        self.pram_layout.addWidget(self.pram_entry)
        self.pram_layout.addWidget(self.switchButton)

        self.viewLayout.addLayout(self.pram_layout)

        self.label_data = [self.tr("当前位置")]
        self.label_data = self.manager.get_labels(
            stand_options=[self.tr("无参数对象")],
            base_options=self.label_data,
            fields = ["text","loc","command"]
        )

        self.combobox = ComboBox()
        for item in self.label_data:
            self.combobox.addItem(item["text"], userData=item["real_index"])
        self.combobox.setCurrentIndex(0)
        self.combobox.currentIndexChanged.connect(self.handle_label_change)
        self.viewLayout.addWidget(self.combobox)

        self.method_data = {
            self.tr("区域坐标中心"): 0,
            self.tr("文字识别内容"): 1,
            self.tr("操作返回结果"): 2,
            self.tr("区域完整坐标"): 3
        }

        self.method_options = list(self.method_data.keys())
        self.method_combobox = ComboBox()
        self.method_combobox.addItems(self.method_options)
        self.method_combobox.setCurrentIndex(0)
        self.method_combobox.currentIndexChanged.connect(self.handle_method_change)
        self.viewLayout.addWidget(self.method_combobox)

        # X 轴输入
        self.x_label = BodyLabel("x:")
        self.x_entry = LineEdit()
        self.x_entry.setValidator(QIntValidator())
        self.x_entry.setText("0")
        self.x_entry.textChanged.connect(self.update_parameter_string)
        self.x_layout = QHBoxLayout()
        self.x_layout.addWidget(self.x_label)
        self.x_layout.addWidget(self.x_entry)

        # Y 轴输入
        self.y_label = BodyLabel("y:")
        self.y_entry = LineEdit()
        self.y_entry.setValidator(QIntValidator())
        self.y_entry.setText("0")
        self.y_entry.textChanged.connect(self.update_parameter_string)
        self.y_layout = QHBoxLayout()
        self.y_layout.addWidget(self.y_label)
        self.y_layout.addWidget(self.y_entry)

        self.viewLayout.addLayout(self.x_layout)
        self.viewLayout.addLayout(self.y_layout)

        self.widget.setMinimumWidth(300)

        # 适配 MessageBoxBase 按钮
        self.yesButton.setText(self.tr("确认并复制"))
        self.cancelButton.setText(self.tr("取消并退出"))

        self.yesButton.clicked.connect(self.handle_confirm)



    def handle_label_change(self):
        self.update_options_based_on_selection()
        self.update_parameter_string()



    def update_options_based_on_selection(self):
        real_index = self.combobox.currentData()
        reg_item = None
        methods = []

        if real_index == 0:
            methods = [self.tr("区域坐标中心"), self.tr("区域完整坐标")]
        elif real_index < 0:
            op_index = -real_index - 1
            operation = self.scriptpage.operations[op_index]
            operation_type = operation.get("operation_name", "未知类别")
            reg_item = OPERATION_REGISTRY.get(operation_type)
        elif real_index > 0:
            item = self.scriptpage.scanpage.graph_text[real_index - 1]
            category = item.get("类别")
            reg_item = RECOGNIZER_REGISTRY.get(category)


        if reg_item:
            methods = []
            fields = reg_item.fields
            field_to_label = {
                "loc": [self.tr("区域坐标中心"), self.tr("区域完整坐标")],
                "text":[self.tr("文字识别内容")],
                "command":[self.tr("操作返回结果")]
            }
            for field in fields:
                methods.extend(field_to_label.get(field, []))

        self.method_combobox.clear()
        self.method_combobox.addItems(methods)




    def handle_method_change(self, index):

        current_method = self.method_combobox.currentText()
        x_value = self.x_entry.text().strip()
        y_value = self.y_entry.text().strip()

        if current_method in [self.tr("区域坐标中心"), self.tr("区域完整坐标")]:
            self.x_entry.setValidator(QIntValidator())
            self.y_entry.setValidator(QIntValidator())
            if x_value == "":
                self.x_entry.setText("0")
            if y_value == "":
                self.y_entry.setText("0")
        else:
            self.x_entry.setValidator(None)
            self.y_entry.setValidator(None)
        self.update_parameter_string()



    def onSwitchCheckedChanged(self, isChecked):
        """切换是否反向翻译的函数"""
        if isChecked:
            self.switchButton.setText(self.tr("获取参数"))
            try:
                self.pram_entry.textChanged.disconnect(self.handle_text_change)
            except TypeError:
                pass
            self.pram_entry.textChanged.connect(self.handle_text_change)
        else:
            self.switchButton.setText(self.tr("翻译参数"))
            try:
                self.pram_entry.textChanged.disconnect(self.handle_text_change)
            except TypeError:
                pass



    def update_parameter_string(self):
        """ 根据当前选择的参数更新 LineEdit 显示内容 """
        try:
            method_str = self.method_combobox.currentText()
            method = self.method_data.get(method_str)
            data = self.manager.getvalue(self.combobox, self.x_entry, self.y_entry, method)
            self.pram_entry.setText(str(data))
        except:
            pass



    def handle_text_change(self):

        """
        解析参数字符串并更新 UI 组件
        """

        text = self.pram_entry.text().strip()

        # 解析数据
        try:
            if text.startswith("[") and text.endswith("]"):  # 处理 method 1, 2
                content = text[1:-1].strip()
            elif text.startswith("(") and text.endswith(")"):  # 处理 method 0, 3
                content = text[1:-1].strip()
            else:
                return  # 无法解析，直接返回


            split_data = re.split(r",\s*", content)

            if len(split_data) != 4:
                return

            method = int(split_data[3])

            # 根据 method 决定默认值
            default_value = "" if method in [1, 2] else 0

            # 解析数据，保持空值或默认值
            parsed_data = [item.strip() if item.strip() else default_value for item in split_data]

            if len(parsed_data) < 4:
                return  # 格式错误，直接返回

            # 解析数值
            real_index = int(parsed_data[0])
            x_plus = parsed_data[1]
            y_plus = parsed_data[2]
            method = int(parsed_data[3])

            # 直接通过 real_index 查找 ComboBox 选项
            found = False
            for i in range(self.combobox.count()):
                if self.combobox.itemData(i) == real_index:  # 关键修改：直接比较 real_index
                    self.combobox.setCurrentIndex(i)
                    found = True
                    break

            if not found:
                return  # 未找到匹配项


            # 反向查找 Method ComboBox 选项

            key = next((k for k, v in self.method_data.items() if v == method), None)
            if key:

                self.method_combobox.setCurrentText(key)


            # 更新 x/y 坐标
            self.x_entry.setText(str(x_plus))
            self.y_entry.setText(str(y_plus))

        except Exception as e:
            return  # 解析失败，不做任何更改



    def handle_confirm(self):
        """ 复制参数到剪贴板 """
        text = self.pram_entry.text().strip()
        if text:
            pyperclip.copy(text)