import keyboard
import mouse
import ast

from PyQt5.QtWidgets import  QDialog, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt,QElapsedTimer,pyqtSignal
from PyQt5.QtGui import QIcon,QIcon

from qfluentwidgets import (ToggleButton,ToggleToolButton,ToolTipFilter,PushButton)
from qfluentwidgets import FluentIcon as FIF

from ..common.photo_tool import photo_tool
from ..common.scripticon import ScriptIcon
from ..common.style_sheet import StyleSheet


class RecordingDialog(QDialog):
    recording_finished = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("录制操作"))
        self.setWindowIcon(QIcon(':/images/logo.png'))
        self.setObjectName("view")
        screen_geometry = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()

        # 计算窗口新的左上角位置，使其居中
        screen_geometry.moveCenter(screen_center)
        self.setGeometry(screen_geometry.x(), screen_geometry.y(), 320, 80)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # 设置为工具窗口

        self.record_count = 0
        self.recording = False
        self.drag_include = False
        self.actions = []  # 用于存储用户操作
        self.timer = QElapsedTimer()  # 用于记录时间

        self.start_time = 0

        self.double_click_threshold = 0.4  # 双击时间阈值（秒）
        self.long_press_threshold = 0.35  # 长按时间阈值（秒）

        self.operations = []

        # 创建主布局
        main_layout = QVBoxLayout()

        # 创建水平布局用于放置按钮
        button_layout = QHBoxLayout()


        # 创建切换锁定按钮
        self.toggle_topmost_button = ToggleToolButton(ScriptIcon.LOCK, self)
        self.toggle_topmost_button.installEventFilter(ToolTipFilter(self.toggle_topmost_button))
        self.toggle_topmost_button.setToolTip(self.tr('切换是否显示在顶端'))
        self.toggle_topmost_button.toggled.connect(self.toggle_topmost)
        self.toggle_topmost_button.setChecked(True)
        button_layout.addWidget(self.toggle_topmost_button)

        # 是否录制鼠标移动的按钮
        self.drag_include_button = ToggleToolButton(FIF.CLEAR_SELECTION, self)
        self.drag_include_button.installEventFilter(ToolTipFilter(self.drag_include_button))
        self.drag_include_button.setToolTip(self.tr('切换录制鼠标移动'))
        self.drag_include_button.toggled.connect(self.toggle_drag_include)
        button_layout.addWidget(self.drag_include_button)


        # 创建开始录制按钮
        self.start_recording_button = ToggleButton(self.tr("开启录制(F10)"), self, ScriptIcon.RECORD)
        self.start_recording_button.installEventFilter(ToolTipFilter(self.start_recording_button))
        self.start_recording_button.setToolTip(self.tr('开启录制/关闭录制'))
        self.start_recording_button.toggled.connect(self.start_recording)
        button_layout.addWidget(self.start_recording_button)
        self.start_recording_button.setDefault(False)
        self.start_recording_button.setAutoDefault(False)


        self.pause_record_button = ToggleButton(self.tr("暂停(F11)"), self, FIF.PAUSE)
        self.pause_record_button.installEventFilter(ToolTipFilter(self.pause_record_button))
        self.pause_record_button.setToolTip(self.tr('暂停录制'))
        self.pause_record_button.toggled.connect(self.pause_recording)
        button_layout.addWidget(self.pause_record_button)
        self.pause_record_button.setDisabled(True)
        self.pause_record_button.setDefault(False)
        self.pause_record_button.setAutoDefault(False)


        # 创建结束录制按钮
        self.stop = ScriptIcon.END.icon(color=Qt.red)
        self.end_recording_button = PushButton(self.tr("结束录制(F12)"), self, self.stop)
        self.end_recording_button.installEventFilter(ToolTipFilter(self.end_recording_button))
        self.end_recording_button.setToolTip(self.tr('结束录制并且提交'))
        self.end_recording_button.clicked.connect(self.end_recording)
        button_layout.addWidget(self.end_recording_button)


        # 将按钮布局添加到主布局
        main_layout.addLayout(button_layout)

        # 创建显示录制操作数量的 QLabel
        record_layout = QHBoxLayout()

        self.record_label = QLabel(self.tr("当前录制操作数量:"), self)
        self.record_count_label = QLabel(f"{self.record_count}", self)
        record_layout.addWidget(self.record_label)
        record_layout.addWidget(self.record_count_label)

        main_layout.addLayout(record_layout)

        # 设置主布局
        self.setLayout(main_layout)


        # 绑定快捷键
        self.hotkey1 = keyboard.add_hotkey("F10", lambda: self.start_recording_button.setChecked(not self.start_recording_button.isChecked()))
        self.hotkey2 = keyboard.add_hotkey("F11", lambda: self.pause_record_button.setChecked(not self.pause_record_button.isChecked()))
        self.hotkey3 = keyboard.add_hotkey("F12", self.end_recording)

        StyleSheet.RECORD_DIALOG.apply(self)


    def toggle_topmost(self, checked):
        if checked:
            # 设置为置顶
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.toggle_topmost_button.setIcon(ScriptIcon.UNLOCK)
        else:
            # 取消置顶
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.toggle_topmost_button.setIcon(ScriptIcon.LOCK)
        self.show()


    def toggle_drag_include(self, checked):
        self.drag_include = checked


    def start_recording(self, checked):
        self.recording = checked
        self.pause_record_button.setDisabled(not checked)
        if checked:
            # 开始录制
            self.start_recording_button.setIcon(ScriptIcon.RECORDING)
            self.start_recording_button.setText(self.tr("停止录制(F10)"))
            self.start_time = self.timer.elapsed()  # 记录开始时间
            self.actions = []  # 清空之前的操作记录
            self.operations = []   # 清空被创建的操作
            self.start_listening()  # 开始监听鼠标和键盘事件
        else:
            # 停止录制
            self.start_recording_button.setIcon(ScriptIcon.RECORD)
            self.start_recording_button.setText(self.tr("开启录制(F10)"))
            self.stop_listening()  # 停止监听鼠标和键盘事件
            self.save_actions()  # 保存操作记录


    def pause_recording(self,checked):
        if checked:
            self.pause_record_button.setText(self.tr("恢复(F11)"))
            self.recording = False
        else:
            self.pause_record_button.setText(self.tr("暂停(F11)"))
            self.recording = self.start_recording_button.isChecked()



    def start_listening(self):
        """开始监听鼠标和键盘事件"""
        # 监听键盘事件
        self.keyboard_handler =keyboard.hook(self.on_keyboard_event)
        # 监听鼠标事件
        self.mouse_handler = mouse.hook(self.on_mouse_event)


    def stop_listening(self):
        """停止监听鼠标和键盘事件"""
        if hasattr(self, "keyboard_handler"):
            keyboard.unhook(self.keyboard_handler)  # 仅解绑自己的键盘监听器
        if hasattr(self, "mouse_handler"):
            mouse.unhook(self.mouse_handler)  # 仅解绑自己的鼠标监听器



    def updateLabel(self):
        self.record_count = len(self.actions)
        self.record_count_label.setText(f"{self.record_count}")



    def on_keyboard_event(self, event):
        """处理键盘事件"""
        if self.recording:
            action = {
                "type": "keyboard",
                "event": event.event_type,  # 事件类型（按下或释放）
                "key": event.name,  # 按键名称
                "time": self.timer.elapsed() - self.start_time,  # 事件发生时间（相对于录制开始）
            }
            self.actions.append(action)
            self.updateLabel()



    def on_mouse_event(self, event):
        """处理鼠标事件"""
        if self.recording:
            if isinstance(event, mouse.ButtonEvent):  # 鼠标点击事件
                x, y = mouse.get_position()
                action = {
                    "type": "mouse",
                    "event": "click",
                    "button": str(event.button),  # 鼠标按键（左键、右键等）
                    "address": (x, y),
                    "pressed": event.event_type in ["down","double"],  # 按下或释放
                    "time": self.timer.elapsed() - self.start_time,  # 事件发生时间
                }
                self.actions.append(action)

            elif isinstance(event, mouse.MoveEvent):  # 鼠标移动事件
                if self.actions and self.actions[-1]["event"] == "move":
                    last_address = self.actions[-1]["address"]
                    new_point = (event.x, event.y)
                    if not last_address or last_address[-1] != new_point:
                        last_address.append(new_point)
                        self.actions[-1]["past"] += (self.timer.elapsed() - self.start_time) - self.actions[-1]["time"]
                        self.actions[-1]["time"] = self.timer.elapsed() - self.start_time
                else:
                    action = {
                        "type": "mouse",
                        "event": "move",
                        "address": [(event.x, event.y)],  # 当前的 (event.x, event.y) 作为地址
                        "past": 0,
                        "time": self.timer.elapsed() - self.start_time,  # 事件发生时间
                    }
                    self.actions.append(action)

            elif isinstance(event, mouse.WheelEvent):  # 鼠标滚轮事件
                if self.actions and self.actions[-1]["event"] == "wheel":
                    self.actions[-1]["delta"] += event.delta
                else:
                    action = {
                        "type": "mouse",
                        "event": "wheel",
                        "delta": event.delta,  # 当前滚动量
                        "time": self.timer.elapsed() - self.start_time,  # 事件发生时间
                    }
                    self.actions.append(action)
            self.updateLabel()



    def is_address_similar(self, address1, address2, threshold=5):
        """
        判断两个地址是否相似 允许x、y偏差小于等于threshold。
        """
        def parse_address(address):
            """尝试将字符串转换为 tuple 或 list"""
            if isinstance(address, str):
                try:
                    parsed = ast.literal_eval(address)  # 安全解析字符串
                    if isinstance(parsed, (tuple, list)) and len(parsed) == 2:
                        return parsed
                except (ValueError, SyntaxError):
                    return None
            return address if isinstance(address, (tuple, list)) and len(address) == 2 else None

        address1 = parse_address(address1)
        address2 = parse_address(address2)

        if address1 is None or address2 is None:
            return False  # 无法解析时返回 False
        x_diff = abs(address1[0] - address2[0])
        y_diff = abs(address1[1] - address2[1])
        return x_diff <= threshold and y_diff <= threshold



    def save_actions(self):
        """保存操作记录"""

        last_down_event = None  # 上一个鼠标按下事件

        last_key_event = None

        operations = []

        for i, action in enumerate(self.actions):
            if action:
                if last_down_event and not (action["type"] == "mouse" and action["event"] == "click" and not action["pressed"]):
                    continue

                # 判断按下事件
                if action["type"] == "mouse":
                    if action["event"] == "click" and action["pressed"]:
                        last_down_event = {
                            "action": action,  # 记录按下事件的具体内容
                            "index": i  # 记录按下事件的索引
                        }

                    # 判断释放事件, 释放事件才是添加的关键
                    elif action["event"] == "click" and not action["pressed"]:
                        if last_down_event:
                            # 获取按下和释放的时间差
                            last_action = last_down_event["action"]
                            time_diff = (action["time"] - last_action["time"])/1000

                            # 按下抬起间隔比较长 视为长按
                            if i - last_down_event["index"] == 1 or self.is_address_similar(last_action["address"],action["address"]):
                                if time_diff > self.long_press_threshold:  # 长按
                                    operation = {
                                        "operation_name": "鼠标操作",
                                        "parameters": [action["button"], "长按", str(last_action["address"]), time_diff  , 1],
                                        "operation_text": [
                                            f"鼠标操作:{action['button']}-长按-{last_action['address']}-{time_diff}秒",
                                            f"Mouse action:{action['button']}-long press-{last_action['address']}-{time_diff} sec"
                                        ],
                                        "action_time":[action["time"],time_diff]
                                    }
                                    operations.append(operation)

                                # 按下抬起间隔短,且位置差异小，则判断为单击/双击
                                else:
                                    operation = {
                                        "operation_name": "鼠标操作",
                                        "parameters": [action["button"], "单击", str(last_action["address"]), time_diff , 1],
                                        "operation_text": [
                                            f"鼠标操作:{action['button']}-单击-{last_action['address']}",
                                            f"Mouse action:{action['button']}-single click-{last_action['address']}"
                                        ],
                                        "action_time":[action["time"],time_diff]
                                    }
                                    operations.append(operation)

                            # 位置差异较大，则认为是拖动
                            else:
                                address = []
                                for action_idx in range(last_down_event["index"] + 1, i):
                                    action = self.actions[action_idx]
                                    if action["type"] == "mouse" and action["event"] == "move":
                                        address = action["address"]
                                        break
                                operation = {
                                    "operation_name": "鼠标拖动",
                                    "parameters": [time_diff, "drag", address],
                                    "operation_text": [
                                        f"鼠标拖动-拖动-{time_diff}",
                                        f"Mouse drag-drag-{time_diff}"
                                    ],
                                    "action_time":[action["time"],time_diff]
                                }
                                operations.append(operation)

                            last_down_event = None  # 重置按下事件，准备下一个事件


                    # 判断移动事件
                    elif action["event"] == "move" and self.drag_include:
                        time = action["past"] / 1000
                        address = action["address"]
                        operation = {
                            "operation_name": "鼠标拖动",
                            "parameters": [time, "move", address],
                            "operation_text": [
                                f"鼠标拖动-移动-{time}",
                                f"Mouse drag-move-{time}"
                            ],
                            "action_time":[action["time"],time]
                        }
                        operations.append(operation)
                        continue


                    # 判断滚轮事件
                    elif action["event"] == "wheel":
                        scroll_time = action["delta"]
                        operation = {
                            "operation_name": "鼠标滚动",
                            "parameters": [scroll_time],
                            "operation_text": [
                                f"滚轮{scroll_time}步",
                                f"Roll {scroll_time} steps"
                            ],
                            "action_time":[action["time"],0.1]
                        }
                        operations.append(operation)


                # 判断键盘事件
                elif action["type"] == "keyboard":
                    key_sym = action["key"]

                    if action["event"] == "down":
                        if last_key_event is None:
                            last_key_event = {
                                "action": action,  # 记录按下事件
                                "keys_pressed": [key_sym],  # 记录按下顺序
                            }
                        else:
                            if key_sym not in last_key_event["keys_pressed"]:  # 避免重复记录
                                last_key_event["keys_pressed"].append(key_sym)

                    elif action["event"] == "up":
                        if last_key_event:
                            last_action = last_key_event["action"]
                            time_diff = (action["time"] - last_action["time"]) / 1000
                            keys_sequence = last_key_event["keys_pressed"]  # 读取按键顺序

                            # 处理不同模式
                            if len(keys_sequence) == 1:  # 只有一个键
                                if time_diff > self.long_press_threshold:
                                    formatted_keys = ["长按", time_diff, keys_sequence[0]]
                                else:
                                    formatted_keys = ["单点", keys_sequence[0]]
                            else:  # 多个按键
                                if time_diff > self.long_press_threshold:
                                    formatted_keys = ["多按长按", time_diff, keys_sequence]
                                else:
                                    formatted_keys = ["多按", keys_sequence]

                            operation = {
                                "operation_name": "键盘操作",
                                "parameters": formatted_keys,
                                "operation_text": [f"键盘操作:{formatted_keys}", f"Keyboard action:{formatted_keys}"],
                                "action_time": [action["time"],time_diff]
                            }
                            operations.append(operation)

                            last_key_event = None  # 释放后重置


                else:
                    continue

        operations = self.process_operations(operations)
        operations = self.insertWait(operations)
        if operations:
            operations = operations[:-1]  #自动把最后点击关闭按钮的操作给删掉
        self.operations = operations



    def process_operations(self,operations):
        new_operations = []  # 新的操作列表，用于保存处理后的操作
        last_wheel_operation = None  # 用于保存上一个滚轮操作
        last_click_operation = None  # 用于保存上一个单击操作


        for operation in operations:
            if operation["operation_name"] == "鼠标滚动":
                if last_wheel_operation and last_wheel_operation["operation_name"] == "鼠标滚动":
                    # 累加滚轮步数
                    last_wheel_operation["parameters"][0] += operation["parameters"][0]
                    last_wheel_operation["operation_text"] = [
                        f"滚轮{last_wheel_operation['parameters'][0]}步",
                        f"Roll {last_wheel_operation['parameters'][0]} steps"
                    ]
                    continue

                last_wheel_operation = operation  # 记录上次滚动操作
                new_operations.append(operation)
                continue

            if operation["operation_name"] == "鼠标操作":
                button,action_type, address, time_diff, click_count = operation["parameters"]

                # 处理鼠标单击
                if action_type == "单击" and last_click_operation:
                    last_button, last_address, last_time_diff, last_click_count = last_click_operation["parameters"][0], \
                                                                                last_click_operation["parameters"][2], \
                                                                                last_click_operation["parameters"][3], \
                                                                                last_click_operation["parameters"][4]

                    if (
                        self.is_address_similar(last_address, address) and
                        last_button == button
                    ):
                        past_time = (operation["action_time"] - last_click_operation["action_time"]) / 1000
                        if past_time <= self.double_click_threshold:  # 如果时间间隔很小，合并为连续点击
                            total_time_diff = last_time_diff + time_diff
                            last_click_operation["parameters"][3] = total_time_diff  # 更新时间
                            last_click_operation["parameters"][4] += 1  # 更新点击次数
                            last_click_operation["action_time"] = operation["action_time"]

                            last_click_operation["operation_text"] = [
                                f"鼠标操作:{last_button}-单击-{address}",
                                f"Mouse action:{button}-single click-{address}"
                            ]
                            continue  # 合并后，不需要再加入 new_operations

                # 记录新的点击事件
                last_click_operation = operation
                new_operations.append(operation)
                continue

            # 其他类型的操作，直接加入
            new_operations.append(operation)


        return new_operations



    def insertWait(self,operations):
        last_action_time = None  # 记录上一个操作的时间
        new_operations = []  # 存放最终优化后的操作

        for operation in operations:
            current_time,duration = operation["action_time"]  # 取出当前操作的时间

            # 如果之前有记录的时间，计算间隔
            if last_action_time is not None:
                wait_time = current_time - last_action_time - duration*1000
                if wait_time >= 100:  # 只插入大于100ms的等待
                    wait_operation = {
                        "operation_name": "等待时间",
                        "parameters": [wait_time],
                        "operation_text": [f"等待:{wait_time}ms", f"Wait:{wait_time}ms"]
                    }
                    new_operations.append(wait_operation)  # 插入等待操作

            # 删除 action_time
            del operation["action_time"]

            new_operations.append(operation)  # 加入当前操作
            last_action_time = current_time  # 更新上一个时间
        return new_operations


    def closeEvent(self, event):
        """窗口关闭时停止监听"""
        if self.recording:
            self.stop_listening()

        if self.hotkey1:
            keyboard.remove_hotkey("F10")  # 解除 F10 热键
        if self.hotkey2:
            keyboard.remove_hotkey("F11")  # 解除 F11 热键
        if self.hotkey3:
            keyboard.remove_hotkey("F12")  # 解除 F12 热键
        super().closeEvent(event)


    def end_recording(self):
        self.recording =  False
        self.save_actions()
        self.recording_finished.emit(self.operations)
        self.close()

