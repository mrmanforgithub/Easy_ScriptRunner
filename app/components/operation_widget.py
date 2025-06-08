import re
import time
import random
import pyautogui
import glob
import os
import psutil
import subprocess
import webbrowser
import pyperclip
import ast


from PyQt5.QtCore import Qt,QEvent,QTimer
from PyQt5.QtGui import QIntValidator,QDoubleValidator
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel,QHBoxLayout,QFrame,QSplitter,QSizePolicy,QTableWidgetItem, QButtonGroup,QCompleter

from qfluentwidgets import (Action,RadioButton, SwitchButton, LineEdit, ComboBox,ToggleButton,FluentIcon, PrimaryDropDownToolButton, PrimaryPushButton,PrimaryToolButton, RoundMenu)
from qfluentwidgets import FluentIcon as FIF

from ..common.photo_tool import photo_tool
from ..common.signal_bus import signalBus
from ..common.config import cfg
from ..common.operation_registry import register_operation
from ..common.recognizer_registry import RECOGNIZER_REGISTRY


class BaseOperationWidget(QWidget):
    """操作控件的基类（简化版）"""
    def __init__(self,parent=None):
        super().__init__(parent)
        self.scriptpage = parent
        self.layout = QVBoxLayout(self)
        self.init_ui()

    def init_ui(self):
        """初始化UI界面"""
        pass

    def get_operation(self):
        """获取操作数据（子类必须拥有此方法）"""
        pass

    def insert_parameters(self, parameters):
        """插入参数（子类必须拥有此方法）"""
        pass



def wait_time_execution(scriptpage, parameters:list, args:list):
    """ 处理等待时间的操作 """
    wait_time = parameters[0]
    start_time = time.time()
    while time.time() - start_time < wait_time / 1000:
        if not scriptpage.scanning:
            break
        time.sleep(0.01)
    return args[0]+"-done","exe"


def check_match_execution(scriptpage, parameters:list,args:list):
    scan_image = parameters[0]  # 获取扫描target
    location = parameters[1]  # 获取扫描位置

    if isinstance(location,list):
        location = location
    elif location.startswith("(") and location.endswith(")"):
        location = scriptpage.manager.getPram(location)
    elif location.startswith("[") and location.endswith("]"):
        location = ast.literal_eval(location)
    else:
        return

    max_wait_time = parameters[2]  # 获取最大等待时间（单位：秒）

    success_action = parameters[3]
    failure_action = parameters[4]

    method = parameters[5]  #是图像/文字/颜色还是其他

    skip_num = parameters[6]
    skip_num2 = parameters[7]

    index = args[1]   #chosen_index 在这里是负数并且-1 传递过来的就已经改了
    start_time = time.time()

    target = scan_image

    result = False
    while time.time() - start_time < max_wait_time:
        if method in ["识别对象", scriptpage.tr("识别对象")]:
            result = scriptpage.result_check[target]
        else:
            result = scriptpage.check_scan(target, location, method ,index)

        if result:
            if success_action == scriptpage.tr("跳过后续操作"):
                scriptpage.logpage.update_log_signal.emit(scriptpage.tr("检查匹配成功") + "-" + scriptpage.tr("跳过后续操作"), "exe")
                return -1
            elif success_action == scriptpage.tr("跳过n个操作"):
                scriptpage.logpage.update_log_signal.emit(scriptpage.tr("检查匹配成功") + "-" + scriptpage.tr("跳过n个操作"), "exe")
                return skip_num

            if method in ["图像识别",scriptpage.tr("图像识别")]:
                scriptpage.manager.results[index]['loc'] = scriptpage.manager.results[target]['loc']
            else:
                scriptpage.manager.results[index]['loc']  = result

            scriptpage.logpage.update_log_signal.emit(scriptpage.tr("检查匹配成功") + "-" + scriptpage.tr("继续后续操作"), "exe")
            return 0

        if not scriptpage.scanning:
            break
        time.sleep(0.1)

    # 如果超时失败
    if time.time() - start_time > max_wait_time:
        if failure_action == scriptpage.tr("跳过后续操作"):
            scriptpage.logpage.update_log_signal.emit(scriptpage.tr("检查匹配失败") + "-" + scriptpage.tr("跳过后续操作"), "exe")
            return -1
        elif failure_action == scriptpage.tr("跳过n个操作"):
            scriptpage.logpage.update_log_signal.emit(scriptpage.tr("检查匹配失败") + "-" + scriptpage.tr("跳过n个操作"), "exe")
            return skip_num2
    scriptpage.logpage.update_log_signal.emit(scriptpage.tr("检查匹配失败") + "-" + scriptpage.tr("继续后续操作"), "exe")
    scriptpage.manager.results[index]['loc']  = [0, 0, 0, 0]

    return 0


def mouse_action_execution(scriptpage, parameters: list, args: list):
    mouse_button = parameters[0]  # 左键、右键、中键
    action = parameters[1]        # 单击、双击、长按
    position_str = parameters[2]  # 点击位置（字符串）
    press_time = parameters[3]    # 长按时间float
    click_times = parameters[4]   # 点击次数int

    # 提取坐标 可能是2个或4个
    position_values = list(map(int, re.findall(r"-?\d+", position_str)))

    # 获取点击偏移值
    random_range = cfg.get(cfg.offset)
    if isinstance(random_range, str) and not random_range.isdigit():
        random_range = None
    offset_x = random.randint(0, int(random_range)) if random_range else 0
    offset_y = random.randint(0, int(random_range)) if random_range else 0

    center_x = center_y = 0
    if len(position_values) == 4:
        loc = scriptpage.manager.getPram(position_values)
        if loc:
            center_x, center_y = loc
        else:
            scriptpage.logpage.update_log_signal.emit(scriptpage.tr("不存在的区域"), "error")
            return args[0] + "-Failed", "error"
    elif len(position_values) == 2:
        center_x, center_y = position_values
    else:
        return args[0] + "-Failed", "error"

    real_x = center_x + offset_x
    real_y = center_y + offset_y

    if real_x == real_y == 0:
        return args[0] + "-Failed", "error"

    # 映射按钮名称
    button_map = {
        "左键": "left", "left": "left",
        "右键": "right", "right": "right",
        "中键": "middle", "middle": "middle"
    }
    button = button_map.get(mouse_button)
    if not button:
        return args[0] + "-Failed", "error"
    try:
        if action in ["单击", "single click"]:
            pyautogui.click(real_x, real_y, clicks=int(click_times), button=button)
        elif action in ["双击", "double click"]:
            pyautogui.click(real_x, real_y, clicks=2, interval=0.1, button=button)
        elif action in ["长按", "long press"] and press_time:
            pyautogui.mouseDown(real_x, real_y, button=button)
            time.sleep(float(press_time))
            pyautogui.mouseUp(real_x, real_y, button=button)
        else:
            return args[0] + "-Failed", "error"
    except Exception as e:
        scriptpage.logpage.update_log_signal.emit(str(e), "error")
        return args[0] + "-Failed", "error"
    return args[0] + "-done", "exe"


def keyboard_action_execution(scriptpage, parameters:list,args:list):
    mode = parameters[0]  # 操作模式
    if mode == "单点":
        key_sym = parameters[1]  # 单个按键
        pyautogui.press(key_sym)  # 按下单个按键
    elif mode == "多按":
        keys = parameters[1]  # 多个按键
        pyautogui.hotkey(*[key.strip("[]") for key in keys])  # 按下所有组合键
    elif mode == "长按":
        long_press_time = parameters[1]  # 长按时间
        key_sym = parameters[2]  # 单个按键
        key = key_sym
        pyautogui.keyDown(key)
        start_time = time.time()
        while time.time() - start_time < long_press_time:
            if not scriptpage.scanning:
                break
            time.sleep(0.1)
        pyautogui.keyUp(key)
    elif mode == "多按长按":
        long_press_time = parameters[1]  # 长按时间
        keys = parameters[2]  # 多个按键
        pyautogui.keyDown(keys[0])  # 按下第一个键
        for key in keys[1:]:
            pyautogui.press(key)  # 按下其他组合键
        time.sleep(long_press_time)  # 按键长按的时间
        pyautogui.keyUp(keys[0])  # 释放第一个键
    elif mode == "打字":
        text = parameters[1]  # 输入文本
        if text.startswith("(") and text.endswith(")"):
            try:
                param_string = text[1:-1]
                param_list = param_string.split(",")
                if len(param_list) == 4:
                    result = scriptpage.manager.getPram(param_list)  # 获取对应内容
                    if result:
                        text = result
                    else:
                        return args[0]+"-Failed","error"
            except ValueError:
                return args[0]+"-Failed","error"
        if bool(re.search('[\u4e00-\u9fa5]', text)):
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.write(text, interval=0.05)
    return args[0]+"-done","exe"


def mouse_drag_execution(scriptpage, parameters: list, args: list):
    duration = parameters[0]  # 时长（浮动类型）
    move_type = parameters[1]  # 移动类型
    points = parameters[2]  # 起始和结束坐标点

    num_points = len(points)
    if num_points < 2:
        return args[0] + "-Failed", "error"

    # 计算每次移动的时间
    time_per_move = round(duration / (num_points - 1), 3) / 2

    processed_positions = []
    # 处理坐标点，支持区域坐标映射
    for pos in points:
        if len(pos) == 4:
            loc = scriptpage.manager.getPram(pos)
            if loc and loc != (0, 0):
                processed_positions.append(loc)
            else:
                scriptpage.logpage.update_log_signal.emit(scriptpage.tr("不存在的区域"), "error")
                return args[0] + "-Failed", "error"
        else:
            processed_positions.append(pos)

    # 如果只有2个点, 插入中间点形成平滑的拖动
    if num_points == 2:
        start, end = processed_positions[0], processed_positions[1]
        intermediate_points = 28  # 根据需要调整中间点数量
        for i in range(1, intermediate_points + 1):
            x = int(start[0] + (end[0] - start[0]) * i / (intermediate_points + 1))
            y = int(start[1] + (end[1] - start[1]) * i / (intermediate_points + 1))
            processed_positions.insert(i, (x, y))
        num_points = len(processed_positions)  # 更新点数
        time_per_move = round(duration / (num_points - 1), 3) / 2  # 重新计算每次移动的时间

    # 确保处理后的坐标点有足够的点
    if len(processed_positions) < 2:
        return args[0] + "-Failed", "error"

    pyautogui.PAUSE = time_per_move  # 设置全局暂停时间

    # 函数来执行实际的鼠标移动
    def execute_move():
        pyautogui.moveTo(processed_positions[0][0], processed_positions[0][1], duration=0.005)
        if move_type == "drag":
            pyautogui.mouseDown()
        for i in range(1, num_points):
            if scriptpage.scanning:  # 确保操作可以被中断
                pyautogui.moveTo(processed_positions[i][0], processed_positions[i][1], duration=time_per_move)
        if move_type == "drag":
            pyautogui.mouseUp()

    execute_move()
    return args[0] + "-done", "exe"


def scroll_action_execution(scriptpage, parameters:list,args:list):
    scroll_time = parameters[0]  # 获取滚动步数
    pyautogui.scroll(scroll_time)  # 执行滚轮操作
    return args[0]+"-done","exe"


def program_command_execution(scriptpage, parameters:list,args:list):
    app_path = parameters[0]  # 获取执行内容
    app_exe = parameters[1]  # 获取执行的方式
    index = args[1]
    ALLOWED_COMMANDS = {
        "window_show_top": photo_tool.window_show_top,
        "figure":  photo_tool.figure_out
    }
    try:
        app_name = os.path.basename(app_path)
        if app_exe == "关闭程序":
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                if proc.info['name'] == app_name:  # 如果进程名匹配
                    proc.terminate()  # 终止进程
                    break
                elif app_path.isdigit():
                    if proc.info['pid'] == int(app_path):
                        proc.terminate()  # 终止进程
                        break
        elif app_exe == "启动程序":
            url_pattern = re.compile(r"^(http://|https://|ftp://|www\.)[^\s]+$", re.IGNORECASE)
            if url_pattern.match(app_path):
                webbrowser.open(app_path)
            else:
                for proc in psutil.process_iter(attrs=['pid', 'name']):
                    if app_name.lower() in proc.info['name'].lower():
                        continue
                os.startfile(app_path)
        elif app_exe == "系统命令":
            result = subprocess.run(app_path, shell=True, capture_output=True, text=True)
            stdout = result.stdout
            stderr = result.stderr
            if stderr:
                if scriptpage.upif:
                    signalBus.main_infobar_signal.emit(scriptpage.tr("错误"), stderr,"TOP","error")
                return args[0]+"-Failed","error"
            if scriptpage.upif:
                signalBus.main_infobar_signal.emit(scriptpage.tr("输出"), stdout,"TOP","info")
            scriptpage.manager.results[index]['command'] = stdout
        elif app_exe == "软件命令":
            app_path = app_path.strip()
            match = re.match(r"(\w+)\((.*)\)", app_path)
            if match:
                method_name = match.group(1)  # 获取方法名
                param_str = match.group(2)  # 获取参数
                if param_str.startswith("(") and param_str.endswith(")"):
                    try:
                        param_string = param_str[1:-1]
                        param_list = param_string.split(",")
                        if len(param_list) == 4:
                            result = scriptpage.manager.getPram(param_list)
                            if result:
                                params = [str(result)]
                    except:
                        pass
                else:
                    params = [p.strip() for p in param_str.split(",")] if param_str else []

                if method_name in ALLOWED_COMMANDS and params:
                    try:
                        result = ALLOWED_COMMANDS[method_name](*params)  # 调用方法
                        if result:
                            scriptpage.manager.results[index]['command'] = result
                            if scriptpage.upif:
                                signalBus.main_infobar_signal.emit(scriptpage.tr("成功"), str(result), "TOP","success")
                    except Exception as e:
                        if scriptpage.upif:
                            signalBus.main_infobar_signal.emit(scriptpage.tr("错误"), str(e), "TOP","error")
                        return args[0]+"-Failed","error"
        return args[0]+"-done","exe"
    except Exception as e:
        return args[0]+"-Failed","error"


def toggle_scan_execution(scriptpage, parameters:list,args:list):
    route_key = parameters[0]
    method = parameters[1]
    if method:
        signalBus.stop_index_signal.emit(route_key)
    else:
        signalBus.start_index_signal.emit(route_key)
    return args[0]+"-done","exe"




@register_operation("等待时间", icon=FIF.STOP_WATCH,execute_func=wait_time_execution)
class WaitOperationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scriptpage = parent
        self.layout = QVBoxLayout(self)

        # 创建时间标签
        self.time_layout = QHBoxLayout()
        self.time_label = QLabel(self.tr("等待(毫秒):"))
        self.time_button = ToggleButton(FluentIcon.STOP_WATCH,self.tr('开始计时'))
        self.time_layout.addWidget(self.time_label)
        self.time_layout.addWidget(self.time_button)
        self.time_button.toggled.connect(self.start_or_stop_timer)
        # 创建时间输入框
        self.times_entry = LineEdit()
        self.times_entry.setPlaceholderText(self.tr("输入数字"))
        self.times_entry.setClearButtonEnabled(True)
        self.times_entry.setValidator(QIntValidator())
        self.timer = QTimer(self)
        self.timer.setInterval(10)  # 100ms 触发一次
        self.timer.timeout.connect(self.update_time)
        self.start_time = 0
        self.layout.addLayout(self.time_layout)
        self.layout.addWidget(self.times_entry)
        self.setLayout(self.layout)


    def get_operation(self):
        try:
            wait_time = int(self.times_entry.text())
        except:
            signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("数字错误！"),"TOP_RIGHT","error")
            return []
        operation = {
                "operation_name": self.__class__.key,
                "parameters": [wait_time],
                "operation_text": [f"等待:{wait_time}ms",f"Wait:{wait_time}ms"]
            }
        return operation


    def insert_parameters(self,parameters):
        self.times_entry.setText(str(parameters[0]))


    def start_or_stop_timer(self,checked):
        """按下按钮时启动计时，抬起时停止"""
        if checked:
            self.time_button.setText(self.tr("停止计时"))
            self.start_time = self.getTime()
            self.timer.start()
        else:
            self.time_button.setText(self.tr("开始计时"))
            self.timer.stop()


    def update_time(self):
        """每 100ms 更新输入框的值"""
        self.start_time += 10
        self.times_entry.setText(f"{self.start_time}")


    def getTime(self):
        """获取 times_entry 的数值，默认 0"""
        text = self.times_entry.text().strip()
        try:
            return int(text) if text else 0
        except ValueError:
            return 0  # 处理非数字输入情况



@register_operation("检查匹配",icon=FIF.FLAG,execute_func=check_match_execution,fields=["loc","text"])
class CheckOperationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scriptpage = parent
        self.manager = self.scriptpage.manager
        self.layout = QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 图文输入框和浏览按钮
        self.scan_combobox = ComboBox()
        for key, item in RECOGNIZER_REGISTRY.items():
            self.scan_combobox.addItem(self.tr(key),userData=key)
        self.scan_combobox.addItem(self.tr("识别对象"))

        self.scan_combobox.setCurrentIndex(0)  # 默认值
        self.scan_entry = LineEdit()
        None_options = [self.tr("无识别对象")]
        label_data = self.manager.get_labels(stand_options = None_options, fields = ["text","loc"])
        self.combobox = ComboBox(self)
        for item in label_data:
            self.combobox.addItem(item["text"], userData=item["real_index"])
        self.combobox.setCurrentIndex(0)
        self.combobox.setVisible(False)

        self.browse_button = PrimaryToolButton(FluentIcon.FOLDER, self)
        self.browse_button.clicked.connect(lambda: self.check_scan_method(self.scan_combobox.currentText()))

        self.scan_input_layout = QHBoxLayout()
        self.scan_input_layout.addWidget(self.scan_combobox)
        self.scan_input_layout.addWidget(self.scan_entry)
        self.scan_input_layout.addWidget(self.combobox)
        self.scan_input_layout.addWidget(self.browse_button)

        self.layout.addLayout(self.scan_input_layout)

        # 地址输入框和框选按钮
        self.location_label = QLabel(self.tr("地址:"))
        self.location_entry = LineEdit()
        self.location_layout = QHBoxLayout()
        self.location_layout.addWidget(self.location_label)
        self.location_layout.addWidget(self.location_entry)

        # 添加框选和截图按钮
        self.menu = RoundMenu(parent=self)
        self.cut_action = Action(FluentIcon.CUT, self.tr('框选'))
        self.grab_action = Action(FluentIcon.CAMERA, self.tr('截图'))
        self.show_action = Action(FluentIcon.HIGHTLIGHT,self.tr('显示'))
        self.cut_action.triggered.connect(lambda: photo_tool.select_scan_region(self.location_entry))  # 绑定框选
        self.grab_action.triggered.connect(lambda: photo_tool.select_scan_region(self.location_entry, path_entry=self.scan_entry, grab=True))  # 绑定截图
        self.show_action.triggered.connect(lambda: photo_tool.show_address(self.location_entry.text()))
        self.menu.addAction(self.cut_action)
        self.menu.addAction(self.grab_action)
        self.menu.addAction(self.show_action)

        self.select_button = PrimaryDropDownToolButton(FluentIcon.CUT, self)
        self.select_button.setMenu(self.menu)
        self.location_layout.addWidget(self.select_button)

        self.layout.addLayout(self.location_layout)

        # 最长等待时间
        self.time_label = QLabel(self.tr("最长等待(秒):"))
        self.time_entry = LineEdit()
        self.time_entry.setValidator(QDoubleValidator())
        self.time_entry.setText("10")  # 默认值为10秒
        self.time_layout = QHBoxLayout()
        self.time_layout.addWidget(self.time_label)
        self.time_layout.addWidget(self.time_entry)

        self.layout.addLayout(self.time_layout)

        # 如果成功下拉框
        self.success_label = QLabel(self.tr("如果成功:"))
        self.success_combobox = ComboBox()
        self.success_combobox.addItems([self.tr("继续后续操作"), self.tr("跳过后续操作"),self.tr("跳过n个操作")])
        self.success_combobox.setCurrentIndex(0)  # 默认值
        self.skip_operations_input = LineEdit()
        self.skip_operations_input.setVisible(False)
        self.skip_operations_input.setValidator(QIntValidator())
        self.skip_operations_input.setText("0")
        self.success_layout = QHBoxLayout()
        self.success_layout.addWidget(self.success_label)
        self.success_layout.addWidget(self.success_combobox)
        self.success_layout.addWidget(self.skip_operations_input)

        self.layout.addLayout(self.success_layout)

        # 如果失败下拉框
        self.failure_label = QLabel(self.tr("如果失败:"))
        self.failure_combobox = ComboBox()
        self.failure_combobox.addItems([self.tr("继续后续操作"), self.tr("跳过后续操作"),self.tr("跳过n个操作")])
        self.failure_combobox.setCurrentIndex(0)  # 默认值
        self.skip_operations_failure_input= LineEdit()
        self.skip_operations_failure_input.setVisible(False)
        self.skip_operations_failure_input.setValidator(QIntValidator())
        self.skip_operations_failure_input.setText("0")
        self.failure_layout = QHBoxLayout()
        self.failure_layout.addWidget(self.failure_label)
        self.failure_layout.addWidget(self.failure_combobox)
        self.failure_layout.addWidget(self.skip_operations_failure_input)

        self.layout.addLayout(self.failure_layout)
        self.scan_combobox.currentIndexChanged.connect(self.update_scan_input_visibility)
        self.success_combobox.currentIndexChanged.connect(self.update_skip_input_visibility)
        self.failure_combobox.currentIndexChanged.connect(self.update_skip_input_visibility)


    def get_operation(self):
        try:
            scan_method = self.scan_combobox.currentData()
            scan_image = self.scan_entry.text() if scan_method != self.tr("识别对象") else self.combobox.currentIndex()
            location = self.location_entry.text() if scan_method != self.tr("识别对象") else [0, 0, 0, 0]
            max_wait_time = float(self.time_entry.text())
            success_action = self.success_combobox.currentText()
            failure_action = self.failure_combobox.currentText()
            try:
                if self.success_combobox.currentText() == self.tr("跳过n个操作"):
                    skip_success_operations = int(self.skip_operations_input.text())  # 获取跳过的操作数
                else:
                    skip_success_operations = 0
                if self.failure_combobox.currentText() == self.tr("跳过n个操作"):
                    skip_failure_operations = int(self.skip_operations_failure_input.text())  # 获取跳过的操作数
                else:
                    skip_failure_operations = 0
            except:
                skip_success_operations = 0
                skip_failure_operations = 0
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"), f"{e}", "TOP_RIGHT","error")
            return []
        operation = {
            "operation_name": self.__class__.key,
            "parameters": [scan_image, location, max_wait_time, success_action, failure_action, scan_method, skip_success_operations, skip_failure_operations],
            "operation_text": [f"检查匹配 {scan_image}-{location}",f"Check-Match {scan_image}-{location}"]
        }
        return operation


    def insert_parameters(self,parameters):
        self.scan_entry.setText(str(parameters[0]))
        self.location_entry.setText(str(parameters[1]))
        self.time_entry.setText(str(parameters[2]))
        self.success_combobox.setCurrentText(parameters[3])
        self.failure_combobox.setCurrentText(parameters[4])
        self.skip_operations_input.setText(str(parameters[6]))
        self.skip_operations_failure_input.setText(str(parameters[7]))
        self.scan_combobox.setCurrentText(parameters[5])
        if parameters[5] == self.tr("识别对象"):
            self.combobox.setCurrentIndex(parameters[0])


    def update_scan_input_visibility(self):
        if self.scan_combobox.currentText() == self.tr("颜色识别"):
            self.show_address_edit(True)
            self.browse_button.setIcon(FluentIcon.PALETTE)
        elif self.scan_combobox.currentText() == self.tr("图像识别"):
            self.show_address_edit(True)
            self.browse_button.setIcon(FluentIcon.FOLDER)
        elif self.scan_combobox.currentText() == self.tr("识别对象"):
            self.show_address_edit(False)
        else:
            self.show_address_edit(True)
            self.browse_button.setVisible(False)


    def check_scan_method(self,method):
        if method == self.tr("图像识别"):
            photo_tool.browse_file(self.scan_entry)
        elif method == self.tr("颜色识别"):
            photo_tool.select_color(self.scan_entry)
        else:
            pass


    def show_address_edit(self,show):
        self.browse_button.setVisible(show)
        self.scan_entry.setVisible(show)
        self.location_label.setVisible(show)
        self.location_entry.setVisible(show)
        self.select_button.setVisible(show)
        self.combobox.setVisible(not show)


    def update_skip_input_visibility(self):
        if self.success_combobox.currentText() == self.tr("跳过n个操作"):
            self.skip_operations_input.setVisible(True)
        else:
            self.skip_operations_input.setVisible(False)

        if self.failure_combobox.currentText() == self.tr("跳过n个操作"):
            self.skip_operations_failure_input.setVisible(True)
        else:
            self.skip_operations_failure_input.setVisible(False)



@register_operation("鼠标操作", icon=FIF.TAG, execute_func=mouse_action_execution)
class MouseOperationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scriptpage = parent
        self.manager = self.scriptpage.manager
        self.layout = QVBoxLayout(self)

        # 点击位置输入框
        self.position_label = QLabel(self.tr("点击位置:"), self)
        self.click_position_var = LineEdit(self)
        self.click_position_var.setPlaceholderText("(x,y)")
        self.layout.addWidget(self.position_label)
        self.layout.addWidget(self.click_position_var)

        # 操作类型单选框 (单击、双击、长按)
        self.radioWidget = QWidget(self)
        self.radioLayout = QHBoxLayout(self.radioWidget)
        self.click_radio_button = RadioButton(self.tr("单击"), self.radioWidget)
        self.double_click_radio_button = RadioButton(self.tr("双击"), self.radioWidget)
        self.long_press_radio_button = RadioButton(self.tr("长按"), self.radioWidget)
        self.buttonGroup = QButtonGroup(self.radioWidget)
        self.buttonGroup.addButton(self.click_radio_button)
        self.buttonGroup.addButton(self.double_click_radio_button)
        self.buttonGroup.addButton(self.long_press_radio_button)
        self.radioLayout.addWidget(self.click_radio_button)
        self.radioLayout.addWidget(self.double_click_radio_button)
        self.radioLayout.addWidget(self.long_press_radio_button)
        self.click_radio_button.click()  # 默认选中单击
        self.layout.addWidget(self.radioWidget)

        # 按钮类型单选框 (左键、右键、中键)
        self.radioWidget2 = QWidget(self)
        self.radioLayout2 = QHBoxLayout(self.radioWidget2)
        self.left_button_radio = RadioButton(self.tr("左键"), self.radioWidget2)
        self.right_button_radio = RadioButton(self.tr("右键"), self.radioWidget2)
        self.middle_button_radio = RadioButton(self.tr("中键"), self.radioWidget2)
        self.buttonGroup2 = QButtonGroup(self.radioWidget2)
        self.buttonGroup2.addButton(self.left_button_radio)
        self.buttonGroup2.addButton(self.right_button_radio)
        self.buttonGroup2.addButton(self.middle_button_radio)
        self.radioLayout2.addWidget(self.left_button_radio)
        self.radioLayout2.addWidget(self.right_button_radio)
        self.radioLayout2.addWidget(self.middle_button_radio)
        self.left_button_radio.click()  # 默认选中左键
        self.layout.addWidget(self.radioWidget2)

        # 长按时间输入框
        self.press_time_label = QLabel(self.tr("长按时间(秒):"), self)
        self.press_time_entry = LineEdit(self)
        self.press_time_entry.setValidator(QDoubleValidator())
        self.press_time_entry.setText("1.0")  # 默认1秒
        self.press_time_entry.setPlaceholderText(self.tr("输入数字"))
        self.layout.addWidget(self.press_time_label)
        self.layout.addWidget(self.press_time_entry)

        self.press_time_label.setVisible(False)
        self.press_time_entry.setVisible(False)

        self.click_times_label = QLabel(self.tr("连点次数:"), self)
        self.click_times_entry = LineEdit(self)
        self.click_times_entry.setValidator(QIntValidator())
        self.click_times_entry.setText("1")  # 默认点击一次
        self.click_times_entry.setPlaceholderText(self.tr("输入数字"))
        self.layout.addWidget(self.click_times_label)
        self.layout.addWidget(self.click_times_entry)

        # 绑定切换长按时间的显示
        self.toggle_press_time_field()
        self.click_radio_button.toggled.connect(self.toggle_press_time_field)
        self.double_click_radio_button.toggled.connect(self.toggle_press_time_field)
        self.long_press_radio_button.toggled.connect(self.toggle_press_time_field)

        # 按钮
        self.match_area_button = PrimaryPushButton(self.tr("匹配区域"), self)
        self.record_click_button = PrimaryPushButton(self.tr("录制点击"), self)

        self.match_area_button.clicked.connect(self.handle_match_area)
        self.record_click_button.clicked.connect(self.handle_record_click)

        self.layout.addWidget(self.record_click_button)
        self.layout.addWidget(self.match_area_button)


    def get_operation(self):
        """获取当前鼠标操作的数据"""
        selected_action = self.buttonGroup.checkedButton()
        action_text = selected_action.text() if selected_action else None

        selected_button = self.buttonGroup2.checkedButton()
        button_text = selected_button.text() if selected_button else None

        address = self.click_position_var.text()

        try:
            press_time = float(self.press_time_entry.text())
            click_times = int(self.click_times_entry.text())
        except:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("数据格式不符合规则！"),"TOP_RIGHT","error")
            return None
        # 格式验证
        if not self.is_valid_operation_format(address):
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("点击位置格式错误"),"TOP_RIGHT","error")
            return None

        operation = {
            "operation_name": self.__class__.key,
            "parameters": [button_text, action_text, address, press_time,click_times],
            "operation_text": [f"鼠标操作:{button_text}-{action_text}-{address}",f"Mouse action:{button_text}-{action_text}-{address}"]
        }
        return operation


    def insert_parameters(self,parameters):
        button_text, action_text, address, press_time,click_times = parameters
        for button in self.buttonGroup2.buttons():
            if self.get_standard_text(button.text()) == self.get_standard_text(button_text):
                button.setChecked(True)
                break
        for button in self.buttonGroup.buttons():
            if self.get_standard_text(button.text()) == self.get_standard_text(action_text):
                button.setChecked(True)
                break
        self.click_position_var.setText(address)
        self.press_time_entry.setText(str(press_time))
        self.click_times_entry.setText(str(click_times))


    def toggle_press_time_field(self):
        """根据操作类型选择来显示或隐藏长按时间输入框"""
        self.press_time_label.setVisible(False)
        self.press_time_entry.setVisible(False)
        self.click_times_label.setVisible(False)
        self.click_times_entry.setVisible(False)
        if self.long_press_radio_button.isChecked():
            self.press_time_label.setVisible(True)
            self.press_time_entry.setVisible(True)
        elif self.click_radio_button.isChecked():
            self.click_times_label.setVisible(True)
            self.click_times_entry.setVisible(True)


    def get_standard_text(self,text):
        """
        统一不同语言或不同别名的文本，使其匹配标准名称
        """
        mapping = {
            "左键": "left",
            "右键":"right" ,
            "中键":"middle" ,
            "单击": "single click",
            "长按": "long press",
            "双击": "double click"
        }

        # 尝试匹配标准名称
        for key, value in mapping.items():
            if text in (key, value):  # 中英文互相匹配
                return key  # 返回字典中的标准名称

        return text  # 如果没有匹配，返回原始值


    def is_valid_operation_format(self, operation_text):
        """验证操作格式"""
        result = re.match(r"^\(\d+\s*,\s*\d+\)$|^\(\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*\)$", operation_text)
        return result


    def handle_match_area(self):
        self.setVisible(False)
        pathfinding_window = QWidget(self)
        pathfinding_layout = QVBoxLayout(pathfinding_window)
        label_options = [self.tr("固定") , self.tr("当前位置")]
        label_data = self.manager.get_labels(base_options = label_options,fields = ["loc"])
        combobox_label = QLabel(self.tr("选择起始点:"), pathfinding_window)
        combobox = ComboBox(pathfinding_window)

        for item in label_data:
            combobox.addItem(item["text"], userData=item["real_index"])
        combobox.setCurrentIndex(0)

        pathfinding_layout.addWidget(combobox_label)
        pathfinding_layout.addWidget(combobox)

        x_label = QLabel("x:", pathfinding_window)
        x_entry = LineEdit(pathfinding_window)
        x_entry.setValidator(QIntValidator())
        x_entry.setText("0")
        y_label = QLabel("y:", pathfinding_window)
        y_entry = LineEdit(pathfinding_window)
        y_entry.setValidator(QIntValidator())
        y_entry.setText("0")

        pathfinding_layout.addWidget(x_label)
        pathfinding_layout.addWidget(x_entry)
        pathfinding_layout.addWidget(y_label)
        pathfinding_layout.addWidget(y_entry)

        confirm_button = PrimaryPushButton(self.tr("确认"), pathfinding_window)
        back_button = PrimaryPushButton(self.tr("返回"), pathfinding_window)
        confirm_button.clicked.connect(lambda: self.handle_pathfinding_confirm(pathfinding_window, self.manager.getvalue(combobox,x_entry,y_entry)))
        back_button.clicked.connect(lambda: self.handle_back(pathfinding_window))
        pathfinding_layout.addWidget(confirm_button)
        pathfinding_layout.addWidget(back_button)
        self.scriptpage.fill_layout.addWidget(pathfinding_window)


    def handle_back(self,pathfinding_window):
        pathfinding_window.setVisible(False)
        self.setVisible(True)


    def handle_pathfinding_confirm(self,pathfinding_window,data):
        self.click_position_var.clear()
        self.click_position_var.setText(f"({','.join(map(str, data))})")
        pathfinding_window.setVisible(False)
        self.setVisible(True)


    def handle_record_click(self):
        photo_tool.select_point(self.click_position_var)



@register_operation("键盘操作", icon=FIF.LABEL, execute_func=keyboard_action_execution)
class KeyboardOperationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scriptpage = parent
        self.manager = self.scriptpage.manager
        self.key_bind = True
        self.key_map = {
        Qt.Key_Control: "ctrl",
        Qt.Key_Shift: "shift",
        Qt.Key_Alt: "alt",
        Qt.Key_Space: "space",  # 空格键映射为空格字符
        Qt.Key_Return: "enter",
        Qt.Key_Escape: "escape",
        Qt.Key_Tab: "tab",
        Qt.Key_Up: "up",  # 上箭头
        Qt.Key_Down: "down",  # 下箭头
        Qt.Key_Left: "left",  # 左箭头
        Qt.Key_Right: "right",  # 右箭头
        Qt.Key_PageUp: "pageup",
        Qt.Key_End: "end",
        Qt.Key_Home:"home"
        }
        self.layout = QVBoxLayout(self)


        self.button = ComboBox()
        self.button.addItems([self.tr('单点'), self.tr('多按'),self.tr("长按"),self.tr('多按长按'),self.tr('打字')])
        self.button.setCurrentIndex(0)  # 默认值
        self.button.currentTextChanged.connect(self.handle_choice)
        self.button.setFocusPolicy(Qt.NoFocus)
        self.layout.addWidget(self.button)

        # 用于显示按键的文本框
        self.input_entry = LineEdit(self)
        self.input_entry.setClearButtonEnabled(True)
        self.input_entry.setReadOnly(True)
        self.input_entry.setFocusPolicy(Qt.NoFocus)
        self.input_entry.setPlaceholderText(self.tr("输入按键名"))
        self.layout.addWidget(self.input_entry)

        # 自动输入 / 手动输入的按钮
        self.input_method_Button = SwitchButton(self.tr('自动输入'))
        self.input_method_Button.checkedChanged.connect(self.onSwitchCheckedChanged)
        self.input_method_Button.setFocusPolicy(Qt.NoFocus)
        self.layout.addWidget(self.input_method_Button)

        self.input_clear_Button = PrimaryPushButton(self.tr("清空内容"))
        self.input_clear_Button.clicked.connect(self.clearinput)
        self.input_clear_Button.setFocusPolicy(Qt.NoFocus)
        self.layout.addWidget(self.input_clear_Button)

        # 长按时间文本框
        long_press_frame = QFrame(self)
        long_press_layout = QHBoxLayout(long_press_frame)

        long_press_label = QLabel(self.tr("长按时间(秒):"), self)
        long_press_layout.addWidget(long_press_label)

        self.long_press_entry = LineEdit(self)
        self.long_press_entry.setValidator(QDoubleValidator())
        self.long_press_entry.setPlaceholderText(self.tr("输入数字"))
        long_press_layout.addWidget(self.long_press_entry)

        long_press_frame.setLayout(long_press_layout)
        long_press_frame.setVisible(False)  # 默认不显示长按时间框
        self.layout.addWidget(long_press_frame)

        # 设置长按时间框的显示与否
        self.long_press_frame = long_press_frame

        self.text_mode_button = PrimaryPushButton(self.tr("匹配文字"))
        self.text_mode_button.clicked.connect(self.handle_match_area)

        self.text_mode_button.setVisible(False)
        self.layout.addWidget(self.text_mode_button)



    def get_operation(self):
        try:
            formatted_keys = None
            current_mode = self.button.text()
            key_sym = self.input_entry.text()
            if current_mode == self.tr("单点"):
                formatted_keys = ["单点", key_sym]
            elif current_mode == self.tr("多按"):
                parts = re.findall(r'\[(.+?)\]', key_sym)
                formatted_keys = ["多按", parts]
            elif current_mode == self.tr("长按"):
                formatted_keys = ["长按", float(self.long_press_entry.text()), key_sym]
            elif current_mode == self.tr("多按长按"):
                parts = re.findall(r'\[(.+?)\]', key_sym)
                formatted_keys = ["多按长按", float(self.long_press_entry.text()), parts ]
            elif current_mode == self.tr("打字"):
                formatted_keys = ["打字", key_sym]
        except:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("输入有误，请检查！"),"TOP_RIGHT","error")
            return []
        operation ={
        "operation_name": self.__class__.key,
        "parameters": formatted_keys,
        "operation_text":[f"键盘操作:{formatted_keys}",f"Keyboard action:{formatted_keys}"]
        }
        return operation


    def insert_parameters(self,parameters):
        if len(parameters) == 3 :
            button_text = parameters[0]
            press_time = parameters[1]
            input_keysym = parameters[2]
        else:
            button_text = parameters[0]
            press_time = None
            input_keysym = parameters[1]
        self.button.setCurrentText(self.tr(button_text))
        if isinstance(input_keysym, list):  # 检查 input_keysym 是否为列表
            for inp in input_keysym:
                self.insert_text(str(inp))
        else:
            self.insert_text(str(input_keysym))
        if press_time:
            self.long_press_entry.setText(str(press_time))


    def handle_match(self,text_mode_widget,combobox,before_entry,after_entry):
        if combobox.currentText().startswith(self.scriptpage.tr("程序命令")):
            match_result = self.manager.getvalue(combobox,before_entry,after_entry,method = 2)
        else:
            match_result = self.manager.getvalue(combobox,before_entry,after_entry,method = 1)
        self.input_entry.setText(str(match_result))
        text_mode_widget.setVisible(False)
        self.setVisible(True)


    def handle_back(self,text_mode_widget):
        text_mode_widget.setVisible(False)
        self.setVisible(True)


    def handle_match_area(self):
        self.setVisible(False)
        text_mode_widget = QWidget(self)
        text_mode_layout = QVBoxLayout(text_mode_widget)

        # 匹配文字
        match_text_label = QLabel(self.tr("匹配文字"), text_mode_widget)
        match_text_combobox = ComboBox(text_mode_widget)
        label_data = self.manager.get_labels(stand_options = ["无文字识别"],fields = ["text","command"])
        for item in label_data:
            match_text_combobox.addItem(item["text"], userData=item["real_index"])

        text_mode_layout.addWidget(match_text_label)
        text_mode_layout.addWidget(match_text_combobox)

        # 前文字
        before_text_layout = QHBoxLayout()
        before_text_label = QLabel(self.tr("前缀"), text_mode_widget)
        before_text_entry = LineEdit(text_mode_widget)
        before_text_layout.addWidget(before_text_label)
        before_text_layout.addWidget(before_text_entry)

        # 后文字
        after_text_layout = QHBoxLayout()
        after_text_label = QLabel(self.tr("后缀"), text_mode_widget)
        after_text_entry = LineEdit(text_mode_widget)
        after_text_layout.addWidget(after_text_label)
        after_text_layout.addWidget(after_text_entry)

        # 插入按钮
        text_mode_layout.addLayout(before_text_layout)
        text_mode_layout.addLayout(after_text_layout)

        confirm_button = PrimaryPushButton(self.tr("确认"), text_mode_widget)
        back_button = PrimaryPushButton(self.tr("返回"), text_mode_widget)
        confirm_button.clicked.connect(lambda: self.handle_match(text_mode_widget,match_text_combobox,before_text_entry,after_text_entry))
        back_button.clicked.connect(lambda: self.handle_back(text_mode_widget))
        text_mode_layout.addWidget(confirm_button)
        text_mode_layout.addWidget(back_button)
        text_mode_widget.setLayout(text_mode_layout)
        self.scriptpage.fill_layout.addWidget(text_mode_widget)


    def clearinput(self):
        self.input_entry.clear()


    def handle_choice(self, text):
        self.input_entry.clear()
        if text == self.tr('多按长按') or text == self.tr('长按'):
            self.long_press_frame.setVisible(True)
            self.text_mode_button.setVisible(False)
        elif text == self.tr("单点") or text == self.tr("多按"):
            self.long_press_frame.setVisible(False)
            self.text_mode_button.setVisible(False)
        else:
            self.text_mode_button.setVisible(True)
            self.long_press_frame.setVisible(False)


    def onSwitchCheckedChanged(self, isChecked):
        if isChecked:
            self.input_method_Button.setText(self.tr('手动输入'))
            self.key_bind = False
            self.input_entry.setReadOnly(False)
            self.input_entry.setFocusPolicy(Qt.ClickFocus)
        else:
            self.input_method_Button.setText(self.tr('自动输入'))
            self.key_bind = True
            self.input_entry.setReadOnly(True)
            self.input_entry.setFocusPolicy(Qt.NoFocus)
            self.setFocus()


    def keyPressEvent(self, event):
        if not self.key_bind:
            return
        key_sym =event.key()
        key_text = event.text()
        if key_sym in self.key_map:
            key_text = self.key_map[key_sym]
        self.insert_text(key_text=key_text)


    def insert_text(self,key_text):
        current_mode = self.button.text()  # 获取 button 上的文本
        if current_mode == self.tr('单点') or current_mode == self.tr('长按') or current_mode == self.tr("打字"):
            if key_text:
                self.input_entry.setReadOnly(False)
                self.input_entry.clear()
                self.input_entry.insert(key_text)
                if self.key_bind:
                    self.input_entry.setReadOnly(True)
        elif current_mode == self.tr('多按') or current_mode == self.tr('多按长按'):
            # 多按或长按多按模式
            if key_text:
                self.input_entry.setReadOnly(False)
                current_text = self.input_entry.text()
                if current_text:  # 如果输入框中已有内容
                    self.input_entry.insert(f"+[{key_text}]")  # 在现有内容后加入加号和当前按键
                else:
                    self.input_entry.insert(f"[{key_text}]")
                if self.key_bind:
                    self.input_entry.setReadOnly(True)


    def event(self, event):
        if self.key_bind:
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
                self.insert_text(key_text="tab")
                event.accept()
                return True
            elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_Backspace:
                self.insert_text(key_text="backspace")
                event.accept()
                return True
        return QWidget.event(self, event)



@register_operation("鼠标拖动", icon=FIF.CLEAR_SELECTION, execute_func=mouse_drag_execution)
class DragOperationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scriptpage = parent
        self.manager = self.scriptpage.manager
        self.duration = 0.5
        self.points = []
        self.op_points = []

        # Layout
        layout = QVBoxLayout(self)

        lineWidget = QWidget()
        line_layout = QHBoxLayout(lineWidget)
        click_radio_button = RadioButton(self.tr("曲线"), lineWidget)
        double_click_radio_button = RadioButton(self.tr("直线"),lineWidget)

        self.line_group = QButtonGroup(lineWidget)
        self.line_group.addButton(click_radio_button)
        self.line_group.addButton(double_click_radio_button)

        line_layout.addWidget(click_radio_button)
        line_layout.addWidget(double_click_radio_button)

        click_radio_button.click()
        layout.addWidget(lineWidget)

        # Separator
        separator1 = QFrame(self)
        separator1.setFrameShape(QFrame.HLine)
        separator1.setStyleSheet("color:#009FAA")
        layout.addWidget(separator1)

        moveWidget = QWidget()
        move_layout = QHBoxLayout(moveWidget)
        self.drag_button_radio = RadioButton(self.tr("拖动"), moveWidget)
        self.move_button_radio = RadioButton(self.tr("移动"), moveWidget)
        self.move_group = QButtonGroup(moveWidget)
        self.move_group.addButton(self.drag_button_radio)
        self.move_group.addButton(self.move_button_radio)
        move_layout.addWidget(self.drag_button_radio)
        move_layout.addWidget(self.move_button_radio)

        self.drag_button_radio.click()
        layout.addWidget(moveWidget)

        self.input_label = QLabel(self.tr("轨迹(起始点-终止点)"), self)
        layout.addWidget(self.input_label)

        self.input_entry = LineEdit(self)
        self.input_entry.setPlaceholderText("[(x1,y1),(x2,y2)]")
        self.input_entry.textEdited.connect(self.handle_input)
        layout.addWidget(self.input_entry)

        # Recording button for curve
        self.record_button = PrimaryPushButton(self.tr("录制曲线"), self)
        layout.addWidget(self.record_button)
        self.record_button.clicked.connect(self.record_curve)

        # Pathfinding button
        self.path_button = PrimaryPushButton(self.tr("手动输入"), self)
        layout.addWidget(self.path_button)
        self.path_button.clicked.connect(self.handle_match_area)

        self.time_label = QLabel(self.tr("拖动时间"), self)
        layout.addWidget(self.time_label)

        self.time_entry = LineEdit(self)
        self.time_entry.setValidator(QDoubleValidator())
        self.time_entry.setPlaceholderText("输入数字")
        self.time_entry.setText("0.5")
        layout.addWidget(self.time_entry)



    def get_operation(self):
        try:
            selected_action = self.move_group.checkedButton()
            if selected_action.text() == self.tr("拖动"):
                move_type = 'drag'
            elif selected_action.text() == self.tr("移动"):
                move_type = "move"
            duration = round(float(self.time_entry.text()), 3)
            points = self.op_points
        except:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("数据格式不符合规则！"),"TOP_RIGHT","error")
            return []
        operation = {
                "operation_name": self.__class__.key,
                "parameters": [duration, move_type, points],
                "operation_text": [f"鼠标拖动-{move_type}-{duration}",f"Mouse drag-{move_type}-{duration}"]
            }
        return operation


    def insert_parameters(self,parameters):
        if parameters[1] == "move":
            self.move_button_radio.setChecked(True)
        else:
            self.drag_button_radio.setChecked(True)
        self.duration = parameters[0]
        self.op_points = parameters[2]
        self.time_entry.setText(str(parameters[0]))
        self.input_entry.setText(str(parameters[2]))



    def handle_input(self, text):
        try:
            text = text.strip()
            if not text:
                return
            pattern = r"\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)|\(\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\)"
            matches = re.findall(pattern, text)
            points = []
            for match in matches:
                if match[0] and match[1]:  # 二维元组
                    points.append((int(match[0]), int(match[1])))  # 二维元组
                elif match[2] and match[3] and match[4]:  # 三维元组
                    points.append((int(match[2]), int(match[3]), int(match[4])))  # 三维元组
            # 确保至少有一个有效点
            if len(points)>=2:
                self.points = points
                self.op_points = self.points
            else:
                pass
        except Exception as e:
            pass


    def record_curve(self):
        selected_action = self.line_group.checkedButton()
        if selected_action:
            if selected_action.text() == self.tr("直线"):
                self.points,self.duration = photo_tool.select_line("line")
            elif selected_action.text() == self.tr("曲线"):
                self.points,self.duration = photo_tool.select_line("curve")
        self.input_entry.clear()
        self.input_entry.insert(str(self.points))
        self.time_entry.clear()
        self.time_entry.insert(str(round(self.duration, 3)))
        self.op_points = self.points
        self.points = []


    def handle_match_area(self):
        self.points = []
        self.setVisible(False)
        pathfinding_window = QWidget(self)
        pathfinding_layout = QVBoxLayout(pathfinding_window)
        label_data = [self.tr("固定"), self.tr("当前位置")]
        label_data = self.manager.get_labels(base_options = label_data,fields = ["loc"])
        combobox_label = QLabel(self.tr("选择起始点:"), pathfinding_window)
        combobox_label.setObjectName("combobox_label")
        combobox = ComboBox(pathfinding_window)
        for item in label_data:
            combobox.addItem(item["text"], userData=item["real_index"])
        combobox.setCurrentIndex(0)
        combobox.setObjectName("combobox")

        pathfinding_layout.addWidget(combobox_label)
        pathfinding_layout.addWidget(combobox)

        x_label = QLabel("x:", pathfinding_window)
        x_entry = LineEdit(pathfinding_window)
        x_entry.setValidator(QIntValidator())
        x_entry.setText("0")
        x_entry.setObjectName("x_entry")
        y_label = QLabel("y:", pathfinding_window)
        y_entry = LineEdit(pathfinding_window)
        y_entry.setValidator(QIntValidator())
        y_entry.setText("0")
        y_entry.setObjectName("y_entry")

        pathfinding_layout.addWidget(x_label)
        pathfinding_layout.addWidget(x_entry)
        pathfinding_layout.addWidget(y_label)
        pathfinding_layout.addWidget(y_entry)

        confirm_button = PrimaryPushButton(self.tr("确认"), pathfinding_window)
        back_button = PrimaryPushButton(self.tr("返回"), pathfinding_window)
        confirm_button.clicked.connect(lambda: self.handle_pathfinding_confirm(pathfinding_window,self.manager.getvalue(combobox,x_entry,y_entry)))
        back_button.clicked.connect(lambda: self.handle_back(pathfinding_window))
        pathfinding_layout.addWidget(confirm_button)
        pathfinding_layout.addWidget(back_button)
        self.scriptpage.fill_layout.addWidget(pathfinding_window)


    def handle_back(self,pathfinding_window):
        pathfinding_window.setVisible(False)
        self.setVisible(True)
        self.points = []


    def handle_pathfinding_confirm(self,pathfinding_window,data):
        if not self.points:
            self.points = [tuple(data)]
            label = pathfinding_window.findChild(QLabel, "combobox_label")
            x_entry = pathfinding_window.findChild(LineEdit, "x_entry")
            y_entry = pathfinding_window.findChild(LineEdit, "y_entry")
            combobox =  pathfinding_window.findChild(ComboBox, "combobox")
            label.setText(self.tr("选择终止点:"))
            x_entry.clear()
            x_entry.setText("0")
            y_entry.clear()
            y_entry.setText("0")
            combobox.setCurrentIndex(0)
        else:
            self.points.extend([tuple(data)])
            self.input_entry.clear()
            self.input_entry.setText(str(self.points))
            pathfinding_window.setVisible(False)
            self.setVisible(True)
            self.op_points = self.points
            self.points = []



@register_operation("鼠标滚动", icon=FIF.ASTERISK, execute_func=scroll_action_execution)
class WheelOperationWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.scroll_steps = 0
        self.scriptpage = parent
        # 设置控件和布局
        self.layout = QVBoxLayout(self)

        self.scroll_label = QLabel(self.tr("滚轮步数(正数向上)"))
        self.scroll_entry = LineEdit(self)
        self.scroll_entry.setValidator(QIntValidator())
        self.scroll_entry.setPlaceholderText(self.tr("输入数字"))
        self.scroll_entry.setText("0")

        self.layout.addWidget(self.scroll_label)
        self.layout.addWidget(self.scroll_entry)

        self.setLayout(self.layout)
        # 鼠标滚轮事件绑定
        self.setMouseTracking(True)


    def get_operation(self):
        try:
            scroll_time = int(self.scroll_entry.text())
        except ValueError:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("数据格式不符合规则！"),"TOP_RIGHT","error")
            return []
        operation = {
            "operation_name": self.__class__.key,
            "parameters": [scroll_time],
            "operation_text": [f"滚轮{scroll_time}步",f"Roll {scroll_time} steps"]
        }
        return operation


    def insert_parameters(self,parameters):
        self.scroll_entry.setText(str(parameters[0]))


    def wheelEvent(self, event):
        direction = event.angleDelta().y() // 120  # 正数表示向上滚动,负数表示向下滚动
        current_value = int(self.scroll_entry.text()) if self.scroll_entry.text() else 0
        self.scroll_steps = current_value + direction
        self.scroll_entry.setText(str(self.scroll_steps))  # 更新滚轮步数



@register_operation("程序命令", icon=FIF.COMMAND_PROMPT, execute_func=program_command_execution,fields=["command"])
class OpenOperationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scriptpage = parent
        # 设置控件和布局
        self.layout = QVBoxLayout(self)

        self.intro_label = QLabel(self.tr("启动可执行文件或者打开文件/网址"))
        self.path_entry = LineEdit(self)
        self.path_entry.setPlaceholderText(self.tr("C:\\Program Files\\QQ.exe"))
        self.command = [
        "dir", "cd", "copy", "del", "ren", "move", "mkdir", "rmdir", "cls", "exit", "echo",
        "tasklist", "taskkill", "ping", "ipconfig", "netstat", "tracert", "arp", "nslookup",
        "set", "shutdown", "start", "assoc", "attrib", "chkdsk", "chkntfs", "clip", "color",
        "comp", "compact", "convert", "date", "defrag", "diskpart", "driverquery", "fc",
        "find", "findstr", "format", "fsutil", "hostname", "label", "mode", "more", "pathping",
        "pause", "powercfg", "print", "prompt", "recover", "replace", "sc", "sfc", "shutdown",
        "sort", "subst", "systeminfo", "taskmgr", "timeout", "title", "tree", "type", "ver", "vol",
        "wmic", "xcopy","time","echo %date% %time%"
        ]
        self.soft_command = ["window_show_top(window_name)","figure(expression)"]

        self.completer = QCompleter([], self.path_entry)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setMaxVisibleItems(10)
        self.path_entry.setCompleter(self.completer)

        self.radioWidget = QWidget(self)
        self.radioLayout = QVBoxLayout(self.radioWidget)  # 改为垂直布局

        # 第一行：启动程序、关闭程序
        self.firstRowLayout = QHBoxLayout()
        self.open_button = RadioButton(self.tr("启动程序"), self.radioWidget)
        self.close_button = RadioButton(self.tr("关闭程序"), self.radioWidget)
        self.firstRowLayout.addWidget(self.open_button)
        self.firstRowLayout.addWidget(self.close_button)

        # 第二行：系统命令、软件命令
        self.secondRowLayout = QHBoxLayout()
        self.system_button = RadioButton(self.tr("系统命令"), self.radioWidget)
        self.software_button = RadioButton(self.tr("软件命令"), self.radioWidget)
        self.secondRowLayout.addWidget(self.system_button)
        self.secondRowLayout.addWidget(self.software_button)

        # 按钮分组
        self.buttonGroup = QButtonGroup(self.radioWidget)
        self.buttonGroup.addButton(self.open_button)
        self.buttonGroup.addButton(self.close_button)
        self.buttonGroup.addButton(self.system_button)
        self.buttonGroup.addButton(self.software_button)

        # 组合布局
        self.radioLayout.addLayout(self.firstRowLayout)
        self.radioLayout.addLayout(self.secondRowLayout)

        self.open_button.click()  # 默认选中启动程序

        self.layout.addWidget(self.intro_label)
        self.layout.addWidget(self.radioWidget)
        self.layout.addWidget(self.path_entry)
        self.setLayout(self.layout)
        self.path_entry.textEdited.connect(self.update_completer)
        self.system_button.toggled.connect(self.update_placeholder)
        self.software_button.toggled.connect(self.update_placeholder)
        self.open_button.toggled.connect(self.update_placeholder)


    def get_operation(self):
        try:
            app_path = self.path_entry.text()
            if app_path.startswith('"') and app_path.endswith('"'):
                app_path = app_path[1:-1]
        except ValueError:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("数据格式不符合规则！"),"TOP_RIGHT","error")
            return []
        selected_action = self.buttonGroup.checkedButton()
        action_text = selected_action.text() if selected_action else None
        if action_text == self.tr("启动程序"):
            operation = {
                "operation_name": self.__class__.key,
                "parameters": [app_path,action_text],
                "operation_text": [f"启动{app_path}",f"Open {app_path}"]
            }
        elif action_text == self.tr("关闭程序"):
            operation = {
                "operation_name": self.__class__.key,
                "parameters": [app_path,action_text],
                "operation_text": [f"关闭{app_path}",f"Close {app_path}"]
            }
        elif action_text == self.tr("系统命令") or action_text == self.tr("软件命令"):
            operation = {
                "operation_name": self.__class__.key,
                "parameters": [app_path,action_text],
                "operation_text": [f"命令{app_path}",f"Command {app_path}"]
            }
        return operation


    def insert_parameters(self,parameters):
        self.path_entry.setText(parameters[0])
        for button in self.buttonGroup.buttons():
            if button.text() == self.tr(parameters[1]):
                button.setChecked(True)  # 选中对应的按钮
                break


    def update_placeholder(self):
        if self.system_button.isChecked():
            self.intro_label.setText(self.tr("执行系统命令,如cmd命令"))
            self.path_entry.setPlaceholderText(self.tr("system command(cmd)"))
        elif self.software_button.isChecked():
            self.intro_label.setText(self.tr("执行本软件定义的其他命令"))
            self.path_entry.setPlaceholderText(self.tr("software command"))
        elif self.open_button.isChecked():
            self.intro_label.setText(self.tr("启动可执行文件或者打开文件/网址"))
            self.path_entry.setPlaceholderText(self.tr("C:\\Program Files\\QQ.exe"))
        else:
            self.intro_label.setText(self.tr("关闭正在进行的程序或者打开的文件"))
            self.path_entry.setPlaceholderText(self.tr("C:\\Program Files\\QQ.exe"))


    def update_completer(self):
        if self.system_button.isChecked():
            self.completer.model().setStringList(self.command)
            return
        elif self.software_button.isChecked():
            self.completer.model().setStringList(self.soft_command)
            return
        text = self.path_entry.text()
        if text.endswith("/") or text.endswith("\\"):
            suggestions = glob.glob(text + "*")
            self.completer.model().setStringList(suggestions)
        elif os.path.isdir(text):
            suggestions = glob.glob(text + "/*")
            self.completer.model().setStringList(suggestions)
        elif text:
            drive_suggestion = glob.glob(text + "*")
            self.completer.model().setStringList(drive_suggestion)
        else:
            self.completer.model().setStringList([])



@register_operation("开关扫描", icon=FIF.PLAY, execute_func=toggle_scan_execution)
class StartOperationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scriptpage = parent

        # 设置控件和布局
        self.layout = QVBoxLayout(self)
        self.start_label = QLabel(self.tr("请选择需要开启的标签"))

        self.layout.addWidget(self.start_label)

        self.switch_button = SwitchButton(self.tr("开启扫描"))
        self.layout.addWidget(self.switch_button)
        self.switch_button.checkedChanged.connect(self.switchChanged)

        # 获取标签名
        tab_names = self.scriptpage.pivot.tabpage.tabinterface.get_all_tab_texts()
        self.tab_objname = self.scriptpage.pivot.tabpage.tabinterface.get_all_tab_route_keys()

        self.tab_combobox = ComboBox(self)
        if tab_names:
            self.tab_combobox.addItems(tab_names)
        else:
            self.tab_combobox.addItem("No tabs available")

        self.layout.addWidget(self.tab_combobox)
        self.setLayout(self.layout)


    def get_operation(self):
        try:
            chosen_index = self.tab_combobox.currentIndex()
            if self.tab_combobox.currentText == "No tabs available":
                raise ValueError
        except ValueError:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("数据格式不符合规则！"),"TOP_RIGHT","error")
            return []
        if self.switch_button.isChecked():
            operation = {
                "operation_name": self.__class__.key,
                "parameters": [self.tab_objname[chosen_index],True],
                "operation_text": [f"关闭{self.tab_objname[chosen_index]}",f"Stop{self.tab_objname[chosen_index]}"]
            }
        else:
            operation = {
                "operation_name": self.__class__.key,
                "parameters": [self.tab_objname[chosen_index],False],
                "operation_text": [f"开启{self.tab_objname[chosen_index]}",f"Start{self.tab_objname[chosen_index]}"]
            }
        return operation


    def insert_parameters(self,parameters):
        self.set_selection(parameters[0])
        self.switch_button.setChecked(parameters[1])


    def switchChanged(self,is_checked):
        if is_checked:
            self.switch_button.setText(self.tr("关闭扫描"))
            self.start_label = QLabel(self.tr("请选择需要关闭的标签"))
        else:
            self.switch_button.setText(self.tr("开启扫描"))
            self.start_label = QLabel(self.tr("请选择需要开启的标签"))


    def set_selection(self,route_key):
        tab_name, index = self.scriptpage.pivot.tabpage.tabinterface.get_tab_name_by_route_key(route_key)
        if index is not None:
            self.tab_combobox.setCurrentIndex(index)
        else:
            signalBus.main_infobar_signal.emit(self.tr("错误"), self.tr("对应页面不存在！"),"TOP_RIGHT","error")
