import concurrent.futures
import json
import os
import shutil
import time
import tkinter as tk
from tkinter import filedialog, ttk
import cv2
import numpy as np
import pyautogui
from PIL import Image, ImageGrab
from datetime import datetime
import subprocess
import re
import io
import pygetwindow as gw
import threading
from pypinyin import lazy_pinyin

class TabController:
    # 导入UI类后,替换以下的 object 类型,将获得 IDE 属性提示功能
    ui: object
    tab: object

    def __init__(self, tab):
        self.tab = tab     # 本身的tab页面,用于给自己的tab控件进行操作

        self.ocr = None  # 设置ocr模型

        self.start_time = None  # 开始时间
        self.time_count = 0  #当前扫描时间
        self.time_limit = None  #自动结束时间

        self.scan_count= 0  #当前扫描次数
        self.scan_limit= None  #扫描次数上限

        self.execution_count = 0  #当前执行次数
        self.execution_limit = None  #执行次数上限

        self.scan_interval = 100  #扫描间隔
        self.execution_method = "script_done"  #执行判断方式
        self.previous_scan_result = None

        self.photo_if = "all"  #满足策略

        self.process_name = None  #选择窗口进程名

        self.random_offset = 0  #随机偏移量

        self.default_check = "弱相似"  #相似策略

        self.key_bind = True  #专门给键盘窗口用的

        self.file_path = "setting_json/operation_cache.json"  # 缓存文件,临时记录操作数据,关闭后清空
        self.photo_path = "setting_json/photo_cache.json"  # 缓存文件,临时记录图片数据,关闭后清空
        self.default_file_path = "setting_json/default_operation.json"   # 默认文件,记录开启时导入的操作内容
        self.default_photo_path = "setting_json/default_photo.json"    # 默认文件,记录开启时导入的图片内容
        self.key_setting_path = "setting_json/key_setting.json"  # 默认文件,记录快捷键的内容

        self.operations = self.load_operations(self.default_file_path)

        # 图片截取目录
        self.image_path = None

        self.start_y = None  # 拖动框选的开始位置
        self.start_x = None
        self.end_y = None  # 拖动框选的结束位置
        self.end_x = None

        # 参数的初始化
        self.max_loops = None  # 扫描最大数量

        self.scanning = False  # 是否扫描
        self.is_executing = False  #是否执行

        self.selection_address = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]] # 四个不同的扫描地址
        self.max_loc = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]  # 四个不同的扫描成功地址

        self.result_check = ["是", "是", "是", "是"]  # 与或非的检查单,全为是则通过检查

        # 默认的扫描相似度阈值
        self.check_similar = 0.75
        self.similar_bind()
        # 线程池,最大20个同时进行的线程
        self.scan_pool = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        self.scan_futures = set()

        # 显示默认的操作列表
        self.populate_operation_list()
        # 添加默认图片信息
        self.add_default_photos()
        # 显示默认图片信息
        self.populate_photo_address(self.photo_path)


    def init_ui(self, ui):
        """
        得到UI实例,对组件进行初始化配置
        """
        self.ui = ui
        # TODO 组件初始化 赋值操作

    # 开始扫描,读取个个图片框的位置,匹配对应的地址,对应的与或非,然后传参图片匹配算法
    def start_scanning(self, evt, max_loops=None):
        self.start_time = time.time()
        self.time_count = 0
        self.scan_count = 0
        self.photo_if = self.tab.photo_if_var.get()
        if self.photo_if == "all":
            self.result_check = ["是", "是", "是", "是"]
        elif self.photo_if == "one":
            self.result_check = ["否", "否", "否", "否"]

        photo_address=[[],[],[],[]]
        photo_image_path=['','','','']

        for future in list(self.scan_futures):
            if future.done():
                self.scan_futures.remove(future)  # 移除已完成的任务
        if len(self.scan_futures) >= 20:
            return
        if self.scanning:
            self.stop_scanning()
            return

        self.scanning = True
        if self.max_loops is not None:
            max_loops = self.max_loops

        self.tab.tk_label_scanning_state_label.config(text="扫描中")

        for i in range(4):
            photo_address[i]=self.tab.photo_scan_box[i].get()
            photo_image_path[i]=self.tab.photo_input[i].get()
            if photo_image_path[i].strip():
                self.result_check[i] = "否"
                target_image = self.load_target_image(photo_image_path[i],0)
                future = self.scan_pool.submit(self.scan_loop, target_image, photo_address[i], i, max_loops)
                self.scan_futures.add(future)
        self.save_photos()

    #停止扫描
    def stop_scanning(self):
        # 停止扫描
        self.scanning = False  #扫描标签归零
        self.tab.tk_label_scanning_state_label.config(background="#6c757d") #变为灰色
        self.start_time = None
        self.time_count = 0  #运行时间清空
        self.time_limit = None
        self.scan_count = 0  #扫描次数清空
        self.scan_limit = None
        self.execution_count = 0 #执行次数清空
        self.execution_limit = None
        self.max_loc = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]] #识别成功地址清空
        for future in list(self.scan_futures):  #从线程池子移除所有的扫描线程
            if not future.done():
                future.cancel()
                self.scan_futures.remove(future)
        self.tab.tk_label_scanning_state_label.after(100, lambda: self.tab.tk_label_scanning_state_label.config(
            text="未开始扫描"))
        self.tab.tk_button_start_scanning_button.config(text="开始扫描")

    # 确认本次扫描的循环次数
    def confirm_selection(self, evt, selection):
        if selection == "无限循环":
            self.max_loops = None
        elif selection == "循环1次":
            self.max_loops = 1
        elif selection == "循环10次":
            self.max_loops = 10
        (self.max_loops)

    # 图片文件读取
    def scan_browser1_enter(self, evt):
        if self.image_path is not None:
            target_image_path_str = filedialog.askopenfilename(initialdir=os.path.dirname(self.image_path),
                                                                initialfile=os.path.basename(self.image_path),
                                                                title="图片文件",
                                                                filetypes=(
                                                                    ("Json files", "*.json"), ("all files", "*.*")))
        else:
            target_image_path_str = filedialog.askopenfilename(title="Select file",
                                                                filetypes=(
                                                                    ("Json files", "*.json"), ("all files", "*.*")))
        self.tab.tk_input_scan_photo_text.delete(0, tk.END)
        self.tab.tk_input_scan_photo_text.insert(0, target_image_path_str)

    # 操作文件读取
    def scan_browser2_enter(self, evt):
        if self.image_path is not None:
            target_image_path_str = filedialog.askopenfilename(initialdir=os.path.dirname(self.image_path),
                                                                initialfile=os.path.basename(self.image_path),
                                                                title="操作文件",
                                                                filetypes=(
                                                                    ("Json files", "*.json"), ("all files", "*.*")))
        else:
            target_image_path_str = filedialog.askopenfilename(title="Select file",
                                                                filetypes=(
                                                                    ("Json files", "*.json"), ("all files", "*.*")))
        self.tab.tk_input_scan_operation_text.delete(0, tk.END)
        self.tab.tk_input_scan_operation_text.insert(0, target_image_path_str)

    # 将图片文件+操作文件组合输出
    def scan_output_enter(self, evt):
        with open(self.tab.tk_input_scan_operation_text.get(), 'r') as operation_file:
            operation_data = json.load(operation_file)

        # 读取 setting_json/photo_cache.json 文件
        with open(self.tab.tk_input_scan_photo_text.get(), 'r') as photo_file:
            photo_data = json.load(photo_file)

        # 合并两个字典
        merged_data = {**operation_data, **photo_data}
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        # 写入新的 JSON 文件
        with open(file_path, 'w') as merged_file:
            json.dump(merged_data, merged_file, ensure_ascii=False, indent=4)


#工具/造轮子代码


    # 创建绘制曲线窗口
    def create_drag_window(self, selection_window, move_type, line_type,callback):
        self.ui.iconify()
        # 打开记录拖动窗口并且记录拖动起始位置与结束位置
        pstart = None
        pend = None
        points = []  # 用于记录鼠标路径的列表
        start_time = None
        drag_window = tk.Toplevel(self.ui)
        drag_window.attributes('-alpha', 0.2)  # 设置透明度
        drag_window.attributes('-fullscreen', True)  # 设置全屏
        drag_window.title("鼠标拖动/滑动")
        drag_window.wm_attributes('-topmost', 1)
        canvas = tk.Canvas(drag_window)
        canvas.pack(fill="both", expand=True)

        def record_start_position(event):
            nonlocal pstart, start_time
            pstart = (event.x, event.y)
            points.append(pstart)  # 记录起始点
            start_time = time.time()

        def draw_drag_line(event):
            nonlocal points
            canvas.delete("all")  # 每次更新时删除旧的画布内容
            points.append((event.x, event.y))# 记录当前鼠标位置
            if line_type == "curve":  # 如果是拖动则画曲线
                canvas.create_line(points, fill='red', width=5, smooth=True)
            else:  # 否则画直线
                if len(points) > 1:
                    canvas.create_line(points[0], (event.x, event.y), fill='red', width=5)
                    points.remove(points[-1])

        def record_end_position(event):
            nonlocal pend
            pend = (event.x, event.y)
            points.append(pend)  # 记录结束点
            if line_type == "curve":
                simplified_points = points[::2]  # 每隔一个点选择一次
            else:
                simplified_points = points
            end_time = time.time()
            duration = end_time - start_time
            duration = round(duration, 2)

            # 将拖动操作加入operations
            callback([duration,move_type,simplified_points])
            self.ui.deiconify()
            selection_window.deiconify()
            time.sleep(0.2)
            drag_window.destroy()

        drag_window.bind("<Button-1>", record_start_position)  # 记录起始位置
        drag_window.bind("<B1-Motion>", draw_drag_line)  # 绘制拖动曲线
        drag_window.bind("<ButtonRelease-1>", record_end_position)  # 记录结束位置

        drag_window.focus_set()

    # 添加寻路操作窗口
    def add_pathfinding_operation_window(self, callback):
        # 打开自动寻路窗口并且记录寻路位置偏差
        pathfinding_window = tk.Toplevel(self.ui)
        pathfinding_window.title("自动寻路")
        pathfinding_window.geometry("300x290")  # 增加一些高度以适应新控件
        pathfinding_window.lift()
        pathfinding_window.focus_set()

        def validate_input(entry):
            if entry.isdigit() or (entry.startswith('-') and entry[1:].isdigit()):
                return True
            else:
                return False

        def handle_confirm_click(x_entry, y_entry, combobox):
            if validate_input(x_entry.get()) and validate_input(y_entry.get()):
                x_value = int(x_entry.get())
                y_value = int(y_entry.get())
                selected_label = combobox.get()  # 获取选中的标签
                selected_index = int(selected_label[-1]) - 1
                result = f"({selected_index},{x_value},{y_value})"
                pathfinding_window.destroy()
                callback(result)

        # 添加 Combobox 控件
        label_options = ["图文1", "图文2", "图文3", "图文4"]
        combobox_label = tk.Label(pathfinding_window, text="选择起始点:")
        combobox_label.pack(pady=5)
        combobox = ttk.Combobox(pathfinding_window, values=label_options)
        combobox.pack(pady=5)
        combobox.set(label_options[0])  # 默认选中第一个标签

        x_label = tk.Label(pathfinding_window, text="填入变动值"+"\nx(正值为＋):")
        x_label.pack(pady=5)
        x_entry = tk.Entry(pathfinding_window)
        x_entry.insert(0, "0")  # 设置默认值为 0
        x_entry.pack(pady=5)

        y_label = tk.Label(pathfinding_window, text="y(正值为＋):")
        y_label.pack(pady=5)
        y_entry = tk.Entry(pathfinding_window)
        y_entry.insert(0, "0")
        y_entry.pack(pady=5)

        pathfinding_button = tk.Button(pathfinding_window, text="确认",
                                        command=lambda: handle_confirm_click(x_entry, y_entry, combobox))
        pathfinding_button.pack(pady=5)

    # 创建寻路拖动窗口
    def pathfinding_drag_window(self,move_type ,callback):
        pathfinding_window = tk.Toplevel(self.ui)
        pathfinding_window.title("匹配位置拖动")
        pathfinding_window.geometry("500x320")  # 调整窗口宽度
        pathfinding_window.lift()
        pathfinding_window.focus_set()

        def validate_input(entry):
            if entry.isdigit() or (entry.startswith('-') and entry[1:].isdigit()):
                return True
            else:
                return False

        def handle_confirm_click(start_x_entry, start_y_entry, end_x_entry, end_y_entry, start_combobox, end_combobox):
            if validate_input(start_x_entry.get()) and validate_input(start_y_entry.get()) and \
            validate_input(end_x_entry.get()) and validate_input(end_y_entry.get()):
                start_x_value = int(start_x_entry.get())
                start_y_value = int(start_y_entry.get())
                end_x_value = int(end_x_entry.get())
                end_y_value = int(end_y_entry.get())
                start_selected_label = start_combobox.get()  # 获取起始点选中的标签
                end_selected_label = end_combobox.get()  # 获取结束点选中的标签
                def get_selected_index(label):
                    if label[-1].isdigit():
                        return int(label[-1]) - 1
                    return None  # 返回 None 表示没有有效索引

                start_selected_index = get_selected_index(start_selected_label)
                end_selected_index = get_selected_index(end_selected_label)

                duration = 1
                if start_selected_index is None and end_selected_index is None:
                    result = [duration,move_type,[(start_x_value, start_y_value),(end_x_value,end_y_value)]]
                elif start_selected_index is not None and end_selected_index is not None:
                    result = [duration,move_type,[(start_selected_index,start_x_value, start_y_value),(end_selected_index, end_x_value,end_y_value)]]
                elif start_selected_index is None:
                    result = [duration,move_type,[(start_x_value, start_y_value),(end_selected_index, end_x_value,end_y_value)]]
                elif end_selected_index is None:
                    result = [duration,move_type,[(start_selected_index,start_x_value, start_y_value), (end_x_value, end_y_value)]]

                pathfinding_window.destroy()
                callback(result)

        point_frame = tk.Frame(pathfinding_window)
        point_frame.pack()

        # 左侧起始点区域
        start_frame = tk.Frame(point_frame)
        start_frame.pack(side=tk.LEFT, padx=10, pady=10)

        # 起始点
        start_combobox_label = tk.Label(start_frame, text="选择起始点:")
        start_combobox_label.pack(pady=5)
        start_combobox = ttk.Combobox(start_frame, values=["图文1", "图文2", "图文3", "图文4","固定"])
        start_combobox.pack(pady=5)
        start_combobox.set("固定")

        start_x_label = tk.Label(start_frame, text="x(右为正):")
        start_x_label.pack(pady=5)
        start_x_entry = tk.Entry(start_frame)
        start_x_entry.insert(0, "0")  # 默认值为 0
        start_x_entry.pack(pady=5)

        start_y_label = tk.Label(start_frame, text="y(上为正):")
        start_y_label.pack(pady=5)
        start_y_entry = tk.Entry(start_frame)
        start_y_entry.insert(0, "0")
        start_y_entry.pack(pady=5)

        # 中间的 "to" 标签
        to_label = tk.Label(point_frame, text="to", font=("Arial", 16))
        to_label.pack(side=tk.LEFT, padx=10, pady=100)  # 适当调整位置

        # 右侧结束点区域
        end_frame = tk.Frame(point_frame)
        end_frame.pack(side=tk.LEFT, padx=10, pady=10)

        # 结束点
        end_combobox_label = tk.Label(end_frame, text="选择结束点:")
        end_combobox_label.pack(pady=5)
        end_combobox = ttk.Combobox(end_frame, values=["图文1", "图文2", "图文3", "图文4","固定"])
        end_combobox.pack(pady=5)
        end_combobox.set("固定")

        end_x_label = tk.Label(end_frame, text="x(右为正):")
        end_x_label.pack(pady=5)
        end_x_entry = tk.Entry(end_frame)
        end_x_entry.insert(0, "0")  # 默认值为 0
        end_x_entry.pack(pady=5)

        end_y_label = tk.Label(end_frame, text="y(上为正):")
        end_y_label.pack(pady=5)
        end_y_entry = tk.Entry(end_frame)
        end_y_entry.insert(0, "0")
        end_y_entry.pack(pady=5)

        # 确认按钮
        button_frame = tk.Frame(pathfinding_window)
        button_frame.pack(side=tk.BOTTOM, pady=10)  # 你可以通过调整padding来调整按钮位置

        pathfinding_button = tk.Button(button_frame, text="确认", command=lambda: handle_confirm_click(start_x_entry, start_y_entry, end_x_entry, end_y_entry, start_combobox, end_combobox), width=20,font=("微软雅黑", -16, "bold"))
        pathfinding_button.pack()  # 放置确认按钮

    #保存各种其他/快捷键
    def save_else(self,key,value):
        json_file = self.key_setting_path
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                settings = json.load(file)
        except FileNotFoundError as e:
            self.error_print(f"未找到文件: {e}")
        except json.JSONDecodeError as e:
            self.error_print(f"JSON解码错误: {e}")
        # 更新相似度值
        if "else" in settings:
            settings["else"][key] = value
        else:
            self.error_print(f"未找到有关{key}设置")
        # 将更新后的数据写回 JSON 文件
        try:
            with open(json_file, "w", encoding="utf-8") as file:
                json.dump(settings, file, ensure_ascii=False, indent=4)
        except IOError as e:
            self.error_print(f"写入文件时发生错误: {e}")

    #打印错误信息到日志
    def error_print(self,error):
        now = datetime.now()
        timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
        log_filename = f"backtrace_logs/{timestamp}"
        with open(log_filename, "w") as file:
            file.write(f"Error occurred at {now}:\n")
            file.write(f"{error}\n")

    # 日志文件夹打开
    def check_out_log(self, evt):
        logs_dir = 'backtrace_logs'  # 日志文件夹名称
        # 获取当前工作目录
        current_dir = os.getcwd()
        # 拼接日志文件夹的完整路径
        logs_path = os.path.join(current_dir, logs_dir)
        # 检查日志文件夹是否存在
        if os.path.exists(logs_path):
            # 使用系统命令打开文件夹
            try:
                if os.name == 'nt':  # Windows系统
                    subprocess.Popen(['explorer', logs_path])
            except FileNotFoundError as e:
                self.error_print(e)
        else:
            try:
                os.makedirs(logs_path)
            except OSError as e:
                self.error_print(e)
                return
            subprocess.Popen(['explorer', logs_path])
        return

    # 初始化界面
    def scan_reopen_enter(self, evt, Tab, Parent, Ui):
        class_type = type(self)

    # 重新调用 __init__ 方法来重新构建对象
        new_instance = class_type.__new__(class_type)
        new_instance.__init__(tab=Tab)  # 调用初始化方法

        class_type2 = type(Tab)

    # 重新调用 __init__ 方法来重新构建对象
        new_instances = class_type2.__new__(class_type2)
        new_instances.__init__(parent=Parent,ui=Ui)  # 调用初始化方法

    #读取ocr模型
    def load_ocr(self):
        self.tab.tk_label_scanning_state_label.config(text="加载OCR模型中...")
        from PPOCR_api import GetOcrApi
        self.ocr = GetOcrApi("tool/PaddleOCR-json_v1.4.1/PaddleOCR-json.exe")
        self.tab.tk_label_scanning_state_label.config(text="OCR模型加载完成")

    def start_ocr_loading(self):
        """加载 OCR 模型"""
        if not hasattr(self, 'ocr') or not self.ocr:
            self.load_ocr()
        else:
            return

    # 确认地址选择后显示出来
    def confirm_address_selection(self, evt):
        self.select_photo_show()
        self.save_photos()

    # 浏览图片所在位置的文本框填入
    def browse_target_image(self, evt, text_box_number):
        if self.image_path is not None:
            target_image_path_str = filedialog.askopenfilename(initialdir=os.path.dirname(self.image_path),
                                                                initialfile=os.path.basename(self.image_path),
                                                                title="Select file",
                                                                filetypes=(
                                                                    ("jpeg files", "*.jpg"), ("all files", "*.*")))
        else:
            target_image_path_str = filedialog.askopenfilename(title="Select file",
                                                                filetypes=(
                                                                    ("jpeg files", "*.jpg"), ("all files", "*.*")))
        self.tab.photo_input[text_box_number].delete(0, tk.END)
        self.tab.photo_input[text_box_number].insert(0, target_image_path_str)
        self.save_photos()

    # 选择的图片地址显示出来
    def select_photo_show(self):
        address_select = self.tab.tk_select_box_photo_address.get()
        address_index = int(address_select[-1]) - 1
        if 0 <= address_index < len(self.selection_address) and self.selection_address[address_index] is not None:
            start_x, start_y, end_x, end_y = self.selection_address[address_index]
            self.tab.tk_label_photo_start_label.config(text=f"({start_x},{start_y})")
            self.tab.tk_label_photo_end_label.config(text=f"({end_x},{end_y})")

    # 更改地址参数的选项,让地址(x1,y1),(x2,y2)符合状态
    def address_change(self,evt, address_select=None,change_type="del"):
        if address_select is None :
            address_select = self.tab.tk_select_box_photo_address.get()
            address_index = int(address_select[-1]) - 1
            start_address = self.tab.tk_label_photo_start_label.cget("text")
            end_address = self.tab.tk_label_photo_end_label.cget("text")
            if change_type == "del": #不给选择地址,选择删除模式
                self.tab.tk_label_photo_start_label.config(text="(0,0)")
                self.tab.tk_label_photo_end_label.config(text="(0,0)")
                self.selection_address[address_index]=[0,0,0,0]
            elif change_type == "save": #不给选择地址,选择保存模式
                start_x, start_y = map(int, start_address.strip('()').split(','))
                end_x, end_y = map(int, end_address.strip('()').split(','))
                # 更新 selection_address 中对应位置的值
                self.selection_address[address_index] = [start_x, start_y, end_x, end_y]
                # 返回更新后的地址
                return self.selection_address[address_index]
        elif address_select is not None:
            address_index = int(address_select[-1]) - 1
            if change_type is None: #给选择地址,选择读取模式
                return self.selection_address[address_index]
        self.save_photos()

    # 根据位置来读取照片
    def load_target_image(self,path,place=None):
        try:
            target_image = Image.open(path)
        except:
            if not path or path.strip() == "":  # 检查字符串是否为空或None
                if place is not None:
                    self.result_check[place] = '是'  # 设置结果为 "是"
                return None  # 返回 None 表示没有有效的内容
            else:
                return path
        target_image = np.array(target_image)
        return target_image

    #比对图片相似度,确认是否是符合要求的
    def compare_images_with_template_matching(self, image1, image2, address_content,chosen_index=None):
        # 比较图片的算法
        # 将图像转换为灰度图
        try:
            gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
            gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        except cv2.error as e:
            self.error_print(e)
            return False

        # 使用模板匹配
        result = cv2.matchTemplate(gray_image1, gray_image2, cv2.TM_CCOEFF_NORMED)
        # 获取最大和最小匹配值及其位置
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # 设置相似度阈值
        similarity_threshold = self.check_similar     # 通过调整阈值来判断相似度,阈值默认0.75

        # 判断匹配值是否大于阈值
        if max_val >= similarity_threshold:
            h, w = image2.shape[:2]  # 获取模板图像的高度和宽度
            dx, dy = address_content[0], address_content[1]  # 计算相对偏移量
            top_left = (max_loc[0] + dx, max_loc[1] + dy)  # 最佳匹配位置的左上角坐标
            bottom_right = (top_left[0] + w, top_left[1] + h)  # 最佳匹配位置的右下角坐标
            if chosen_index is not None:
                self.max_loc[chosen_index] = (top_left, bottom_right)
            return True  # 图片相似
        else:
            return False  # 图片不相似

    #比对文字相似度,确认是否符合要求
    def compare_text_with_ocr(self,screenshot,text, address_content,chosen_index=None):
        byte_io = io.BytesIO()
        screenshot.save(byte_io, format='PNG')
        image_bytes = byte_io.getvalue()
        self.start_ocr_loading()  # 如果OCR模型还未加载,启动加载
        ocr_result = None
        # 设置相似度阈值
        similarity_threshold = self.check_similar-0.05     # 通过调整阈值来判断相似度,文字识别相似度判断可以放松一点
        dx, dy = address_content[0], address_content[1]  # 计算相对偏移量
        try:
            ocr_result = self.ocr.runBytes(image_bytes)
        except Exception as e:
            self.error_print(e)
            ocr_result = None

        if ocr_result and isinstance(ocr_result, dict) and 'data' in ocr_result and isinstance(ocr_result['data'], list):
            # 获取识别的文字
            for item in ocr_result['data']:
                score = item['score']
                box = item['box']
                recognized_text = item['text']
                adjusted_box = [[x + dx, y + dy] for x, y in box]
                if text.strip() in recognized_text.strip():
                    if score >=similarity_threshold:  # 判断识别文字是否包含目标文字并且可信度够高
                        pt1 = tuple(adjusted_box[0])  # 左上角坐标
                        pt2 = tuple(adjusted_box[2])  # 右下角坐标
                        if chosen_index is not None:
                            self.max_loc[chosen_index]=(pt1,pt2)  #将识别到的坐标保存至识别成功坐标组
                        return True
                    else:
                        return False
            return False
        else:
            return False

    #扫描循环(此处是进行扫描的核心代码)
    def scan_loop(self, target, photo_address, chosen_index, max_loops):
        # 检查地址内容
        address_content = self.address_change(evt=None, address_select=photo_address, change_type=None)
        screenshot = None
        if address_content == [0, 0, 0, 0]:
            self.ui.after(0, lambda: self.tab.tk_label_scanning_state_label.config(text="地址无效"))
            self.ui.after(2500, lambda: self.stop_scanning())
            return

        if self.scanning and (max_loops is None or max_loops > 0):
            self.ui.after(0, lambda: self.tab.tk_button_start_scanning_button.configure(text="关闭扫描"))
            active_window = gw.getActiveWindow()
            if active_window:
                if self.process_name and self.process_name not in active_window.title:
                    self.ui.after(0, lambda: self.tab.tk_label_scanning_state_label.config(text="选择窗口未置顶", background="#FFB84D"))
                    self.ui.after(self.scan_interval, lambda: self.scan_loop(target, photo_address, chosen_index, max_loops))
                    return  # 不执行操作
            x1, y1, x2, y2 = address_content
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            screen_region = np.array(screenshot)
            # 判断target_image类型,如果是图片(numpy.ndarray)则进行图像处理,否则进行OCR识别
            if isinstance(target, np.ndarray):
                result = self.compare_images_with_template_matching(screen_region, target, address_content, chosen_index)
                if result:
                    self.ui.after(0, lambda: self.tab.tk_label_scanning_state_label.config(text="扫描成功", background="#007bff"))
                    self.result_check[chosen_index] = "是"
                else:
                    self.result_check[chosen_index] = "否"
                    self.ui.after(0, lambda: self.tab.tk_label_scanning_state_label.config(text="未扫描到结果", background="#007bff"))
            else:
                ocr_result = self.compare_text_with_ocr(screenshot, target, address_content, chosen_index)
                if ocr_result:  # 判断识别文字是否包含目标文字
                    self.result_check[chosen_index] = "是"
                    self.ui.after(0, lambda: self.tab.tk_label_scanning_state_label.config(text="文字识别成功", background="#007bff"))
                else:
                    self.result_check[chosen_index] = "否"
                    self.ui.after(0, lambda: self.tab.tk_label_scanning_state_label.config(text="未扫描到结果", background="#007bff"))

            if self.photo_if == "all":
                current_scan_result = self.previous_scan_result
                # 如果是 "all"，要求 result_check 所有项都是 "是"
                if self.result_check == ["是", "是", "是", "是"]:
                    self.previous_scan_result = True
                    if not self.is_executing:
                        self.is_executing = True  # 设置为正在执行
                        thread = threading.Thread(target=self.execute_operations)
                        thread.daemon = True  # 设置为守护线程
                        thread.start()
                    if self.previous_scan_result != current_scan_result and self.execution_method == "scan_changed":
                        self.execution_count += 1
                else:
                    self.previous_scan_result = False
            elif self.photo_if == "one":
                current_scan_result = self.previous_scan_result
                # 如果是 "one"，只要有一个是 "是" 就满足
                if "是" in self.result_check:
                    self.previous_scan_result = True
                    if not self.is_executing:
                        self.is_executing = True  # 设置为正在执行
                        thread = threading.Thread(target=self.execute_operations)
                        thread.daemon = True  # 设置为守护线程
                        thread.start()
                    if self.previous_scan_result != current_scan_result and self.execution_method == "scan_changed":
                        self.execution_count += 1
                else:
                    self.previous_scan_result = False
            # 关闭截图资源
            screenshot.close()

            # 更新扫描时间和扫描次数
            self.time_count = (time.time() - self.start_time).__round__(2)
            if self.time_limit:
                self.ui.after(0, lambda: self.tab.tk_label_operation_timeout_limit.config(
                    text=f"定时{self.time_limit}秒结束" + f"\n还剩下{int(self.time_limit - self.time_count)} 秒"))
                if self.time_count >= self.time_limit:
                    self.ui.after(0, lambda: self.tab.tk_label_operation_timeout_limit.config(text="定时结束,已停止扫描"))
                    self.ui.deiconify()
                    self.ui.after(0, lambda: self.stop_scanning())  # 达到定时停止时间，停止扫描

            self.scan_count += 1
            if self.scan_limit:
                self.ui.after(0, lambda: self.tab.tk_label_operation_timeout_limit.config(
                    text=f"预计扫描{self.scan_limit}次" + f"\n还剩下{self.scan_limit - self.scan_count} 次"))
                if self.scan_count >= self.scan_limit:
                    self.ui.after(0, lambda: self.tab.tk_label_operation_timeout_limit.config(text="次数到达,已停止扫描"))
                    self.ui.deiconify()
                    self.ui.after(0, lambda: self.stop_scanning())  # 达到扫描次数限制，停止扫描

            # 调整循环次数
            if max_loops is not None:
                max_loops -= 1

            # 继续循环扫描
            if max_loops is None or max_loops > 0:
                self.ui.after(self.scan_interval, lambda: self.scan_loop(target, photo_address, chosen_index, max_loops))
            else:
                self.ui.after(0, lambda: self.stop_scanning())

    #单次检查扫描(用于检查是否成功执行)
    def check_scan(self, load_target, photo_address):
        # 检查地址内容check_
        screenshot=None
        if photo_address == [0, 0, 0, 0]:
            return False
        active_window = gw.getActiveWindow()
        if active_window:
            if self.process_name and self.process_name not in active_window.title:
                return False  # 不执行操作
        x1, y1, x2, y2 = photo_address
        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        screen_region = np.array(screenshot)
        # 判断target_image类型,如果是图片(numpy.ndarray)则进行图像处理,否则进行OCR识别
        result_found = False
        if isinstance(load_target, np.ndarray):
            result = self.compare_images_with_template_matching(screen_region,load_target, photo_address)
            if result:
                result_found = True
            else:
                result_found = False
        else:
            ocr_result = self.compare_text_with_ocr(screenshot,load_target,photo_address)
            if ocr_result:  # 判断识别文字是否包含目标文字
                result_found = True
            else:
                result_found = False
        # 关闭截图资源
        screenshot.close()
        return result_found

    # 框选/截图窗口代码
    def open_manual_selection_window(self, evt, grab_photo=False,localentry = None):
        self.ui.iconify()  # 将主窗口最小化
        self.manual_selection_window = tk.Toplevel(self.ui)  # 创建一个新的Toplevel窗口
        self.manual_selection_window.attributes('-alpha', 0.3)
        self.manual_selection_window.attributes('-fullscreen', True)
        self.manual_selection_window.title("截图窗口")
        canvas = tk.Canvas(self.manual_selection_window)
        canvas.pack(fill="both", expand=True)

        def on_press_select(event):
            self.start_x = event.x  # 记录鼠标按下时的横坐标
            self.start_y = event.y  # 记录鼠标按下时的纵坐标

        def on_release_select(event):
            self.end_x = event.x  # 记录鼠标释放时的横坐标
            self.end_y = event.y  # 记录鼠标释放时的纵坐标
            if localentry is None:
                self.tab.tk_label_photo_start_label.config(text=f"({self.start_x},{self.start_y})")
                self.tab.tk_label_photo_end_label.config(text=f"({self.end_x},{self.end_y})")
                # 检查并自动将图片地址保存到 selection_address
                for address_index in range(4):
                    if self.selection_address[address_index] == [0, 0, 0, 0]:
                        # 更新对应的地址
                        self.selection_address[address_index] = [self.start_x, self.start_y, self.end_x, self.end_y]
                        # 更新地址显示
                        self.tab.tk_select_box_photo_address.set(f"地址{address_index + 1}")
                        # 调用保存地址变化的方法
                        self.address_change(evt, change_type="save")
                        break  # 退出循环，因为只需要处理第一个符合条件的地址
            else:
                localentry[0].delete(0, tk.END)
                localentry[0].insert(0, f"[{self.start_x},{self.start_y},{self.end_x},{self.end_y}]")
            self.manual_selection_window.destroy()
            if grab_photo:  # 如果需要截图
                x1, y1 = min(self.start_x, self.end_x), min(self.start_y, self.end_y)
                x2, y2 = max(self.start_x, self.end_x), max(self.start_y, self.end_y)
                # 在对应位置产生截图
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                # 要求用户选择路径保存截图
                file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg")])
                if file_path:  # 如果用户选择了路径
                    screenshot.save(file_path)  # 保存截图
                    self.tab.photo_input[0].delete(0, tk.END)
                    self.tab.photo_input[0].insert(0, file_path)

            self.ui.deiconify()  # 恢复最小化的之前的界面
            if localentry is not None:
                localentry[1].deiconify()
            self.save_photos()

        def draw_drag_line(event):
            canvas.delete("all")
            if self.start_x is not None:
                canvas.create_line(self.start_x, self.start_y, self.start_x, event.y, fill='black',
                                    width=5)  # Draw line from (start_x,start_y) to (start_x,end_y)
                canvas.create_line(self.start_x, self.start_y, event.x, self.start_y, fill='black',
                                    width=5)  # Draw line from (start_x,start_y) to (end_x,start_y)
                canvas.create_line(self.start_x, event.y, event.x, event.y, fill='black',
                                    width=5)  # Draw line from (start_x,end_y) to (end_x,end_y)
                canvas.create_line(event.x, self.start_y, event.x, event.y, fill='black',
                                    width=5)  # Draw line from (end_x,start_y) to (end_x,end_y)

        canvas.bind("<Button-1>", on_press_select)  # Record start position
        canvas.bind("<B1-Motion>", draw_drag_line)  # Draw drag line
        canvas.bind("<ButtonRelease-1>", on_release_select)  # Record end position

        self.manual_selection_window.focus_set()

    def on_close(self,position,dele_op,window):
        if dele_op is not None:
            self.operations.insert(position, dele_op)
            self.save_operations()
            self.populate_operation_list()
        window.destroy()
        self.ui.deiconify()

#操作添加窗口代码,为操作添加代码提供可视化窗口,用户在窗口添加参数,代码将参数处理并传递给添加操作代码,将操作添加到operations中

    #添加开始操作窗口
    def add_start_operation_window(self, position,dele_op = None):
        # 打开打开操作窗口并且记录打开的扫描
        start_window = tk.Toplevel(self.ui)
        start_window.title("开始扫描")
        start_window.geometry("300x200")
        start_window.lift()
        start_window.focus_set()

        tab_names = [self.ui.tk_tabs_first_tab.tab(i, "text") for i in range(self.ui.tk_tabs_first_tab.index("end"))]

        start_label = tk.Label(start_window, text="请选择需要操作的标签：")
        start_label.pack(pady=5)

        selected_tab = tk.StringVar(value=tab_names[0])
        tab_combobox = ttk.Combobox(start_window, textvariable=selected_tab, values=tab_names, state="readonly")
        tab_combobox.pack()

        loop_options = ["无限循环", "循环1次", "循环10次"]
        selected_loop = tk.StringVar(value=loop_options[0])
        loop_combobox = ttk.Combobox(start_window, textvariable=selected_loop, values=loop_options, state="readonly")
        loop_combobox.pack()

        def confirm_selection():
            chosen_index = tab_combobox.current()
            loop_selection = selected_loop.get()  # Get the selected loop option
            loop_count = None
            if loop_selection == "循环1次":
                loop_count = 1
            elif loop_selection == "循环10次":
                loop_count = 10

            self.operations.insert(position, {
                "operation_name": "开启",
                "parameters": [chosen_index, loop_count],
                "operation_text": f"开启{chosen_index}号扫描{loop_count}次"
            })
            self.save_operations()
            self.populate_operation_list()
            start_window.destroy()

        confirm_button = tk.Button(start_window, text="确定", command=confirm_selection)
        confirm_button.pack(pady=5)
        start_window.protocol("WM_DELETE_WINDOW", lambda: self.on_close(position,dele_op,start_window))

    # 添加关闭扫描窗口
    def add_close_operation_window(self, position,dele_op = None):
        # 打开关闭扫描窗口并且记录关闭扫描位置
        close_window = tk.Toplevel(self.ui)
        close_window.title("关闭扫描")
        close_window.geometry("300x200")
        close_window.lift()
        close_window.focus_set()

        tab_names = [self.ui.tk_tabs_first_tab.tab(i, "text") for i in range(self.ui.tk_tabs_first_tab.index("end"))]

        close_label = tk.Label(close_window, text="请选择需要操作的标签：")
        close_label.pack(pady=5)

        selected_tab = tk.StringVar(value=tab_names[0])
        tab_combobox = ttk.Combobox(close_window, textvariable=selected_tab, values=tab_names, state="readonly")
        tab_combobox.pack()

        def confirm_selection():
            chosen_index = tab_combobox.current()
            # 将关闭操作加入operations
            self.operations.insert(position, {
                "operation_name": "关闭",
                "parameters": [chosen_index],
                "operation_text": f"关闭{chosen_index}号扫描"
            })
            self.save_operations()
            self.populate_operation_list()
            close_window.destroy()

        confirm_button = tk.Button(close_window, text="确定", command=confirm_selection)
        confirm_button.pack(pady=5)
        close_window.protocol("WM_DELETE_WINDOW", lambda: self.on_close(position,dele_op, close_window))

    # 添加拖动操作窗口
    def add_drag_operation_window(self, position,dele_op = None):
        # 创建选择操作类型的窗口
        selection_window = tk.Toplevel(self.ui)
        selection_window.title("选择操作类型")
        selection_window.geometry("400x270")

        # 选择拖动或移动
        move_type = tk.StringVar(value="drag")  # 默认选项为拖动

        # 选择曲线或直线
        line_type = tk.StringVar(value="curve")  # 默认选项为曲线

        # 创建容器来放置直线/曲线单选框
        line_container = tk.Frame(selection_window)
        line_container.pack(pady=10)

        curve_button = tk.Radiobutton(line_container, text="绘制曲线(速度慢)", variable=line_type, value="curve")
        curve_button.pack(side=tk.LEFT, padx=10)

        line_button = tk.Radiobutton(line_container, text="绘制直线(速度快)", variable=line_type, value="line")
        line_button.pack(side=tk.LEFT, padx=10)

        # 添加分割线
        separator = ttk.Separator(selection_window, orient='horizontal')
        separator.pack(fill='x', pady=10)

        # 创建容器来放置拖动/移动单选框
        move_container = tk.Frame(selection_window)
        move_container.pack(pady=10)

        drag_button = tk.Radiobutton(move_container, text="拖动(鼠标按下)", variable=move_type, value="drag")
        drag_button.pack(side=tk.LEFT, padx=10)

        move_button = tk.Radiobutton(move_container, text="移动(鼠标不按)", variable=move_type, value="move")
        move_button.pack(side=tk.LEFT, padx=10)

        # 添加分割线2
        separator2 = ttk.Separator(selection_window, orient='horizontal')
        separator2.pack(fill='x', pady=10)

        # 添加输入框，用户可以输入一些额外的值
        input_label = tk.Label(selection_window, text="绘制轨迹(起始点->终止点)：")
        input_label.pack(pady=5)

        input_entry = tk.Entry(selection_window, width=30)
        input_entry.pack(pady=5)

        # 创建录制曲线按钮
        def record_curve():
            self.create_drag_window(selection_window,move_type.get(), line_type.get(),set_result)
            selection_window.iconify()

        def pathfinding_operation():
            self.pathfinding_drag_window(move_type.get(),set_result)

        duration = 1
        points = []
        def set_result(pathfinding_result):
            nonlocal duration, points
            duration = pathfinding_result[0]
            points = pathfinding_result[2]
            input_entry.delete(0, tk.END)  # 清空输入框
            input_entry.insert(tk.END, f"{duration}-{move_type.get()}-{points}")  # 设置新值

        def confirm_input():
            if points:
                self.operations.insert(position, {
                    "operation_name": "拖动",
                    "parameters": [duration, move_type.get(), points],
                    "operation_text": f"鼠标拖动-{input_entry.get()}"
                })
            else:
                tk.messagebox.showwarning("警告", "内容缺失,请录制曲线/手动填入")
            self.save_operations()
            self.populate_operation_list()
            selection_window.destroy()
            self.ui.deiconify()

        button_frame = tk.Frame(selection_window)
        button_frame.pack(pady=10)

        confirm_button = tk.Button(button_frame, text="确认提交", command=confirm_input)
        confirm_button.pack(side=tk.LEFT, padx=20)

        record_button = tk.Button(button_frame, text="录制曲线", command=record_curve)
        record_button.pack(side=tk.LEFT,padx=20)

        path_button = tk.Button(button_frame, text="手动输入", command=pathfinding_operation)
        path_button.pack(side=tk.LEFT, padx=20)

        selection_window.focus_set()
        selection_window.protocol("WM_DELETE_WINDOW", lambda: self.on_close(position,dele_op,selection_window))

    # 添加等待操作窗口
    def add_wait_operation_window(self, position,dele_op = None):
        # 打开等待操作窗口
        wait_window = tk.Toplevel(self.ui)
        wait_window.title("等待操作")
        wait_window.geometry("350x300")
        wait_window.lift()
        wait_window.focus_set()

        # 等待时间选择
        wait_type = tk.StringVar(value="time")  # 默认选择等待时间

        wait_label = tk.Label(wait_window, text="请选择等待类型:")
        wait_label.pack(pady=5)

        # 选择等待方式（时间或扫描成功）
        time_radio = tk.Radiobutton(wait_window, text="固定等待时间", variable=wait_type, value="time")
        time_radio.pack(pady=5)

        scan_radio = tk.Radiobutton(wait_window, text="等待识别成功", variable=wait_type, value="scan")
        scan_radio.pack(pady=5)

        # 固定等待时间
        def show_time_wait():
            time_frame.pack(pady=5)
            scan_frame.pack_forget()

        # 等待扫描成功
        def show_scan_wait():
            scan_frame.pack(pady=5)
            time_frame.pack_forget()

        wait_type.trace("w", lambda *args: show_time_wait() if wait_type.get() == "time" else show_scan_wait())

        # 固定时间输入框
        time_frame = tk.Frame(wait_window)
        time_input_frame = tk.Frame(time_frame)
        time_label = tk.Label(time_input_frame, text="等待(毫秒):")
        time_label.pack(side="left", padx=5)
        times_entry = tk.Entry(time_input_frame)
        times_entry.pack(side="left", padx=5)
        time_input_frame.pack(pady=5)

        def confirm_time_wait():
            try:
                wait_time = int(times_entry.get())
                self.operations.insert(position, {
                "operation_name": "等待",
                "parameters": [wait_time],
                "operation_text": f"等待:{wait_time}ms"
                })
                self.save_operations()
                self.populate_operation_list()
                wait_window.destroy()
            except ValueError:
                tk.messagebox.showwarning("警告", "请输入有效的数字!")

        time_button = tk.Button(time_frame, text="确认", command=confirm_time_wait)
        time_button.pack(pady=5)

        # 扫描成功等待输入框与选择图片按钮
        scan_frame = tk.Frame(wait_window)
        scan_input_frame = tk.Frame(scan_frame)
        scan_label = tk.Label(scan_input_frame, text="图文:")
        scan_label.pack(side="left", padx=5)
        scan_entry = tk.Entry(scan_input_frame)
        scan_entry.pack(side="left", padx=5)

        def browse_file():
            file_path = filedialog.askopenfilename(title="选择扫描图片", filetypes=[("JPG", "*.jpg"),("PNG", "*.png")])
            if file_path:
                scan_entry.delete(0, tk.END)
                scan_entry.insert(0, file_path)

        browse_button = tk.Button(scan_input_frame, text="浏览", command=browse_file)
        browse_button.pack(side="left", padx=5)
        scan_input_frame.pack(pady=5)

        def select_scan_region():
            wait_window.iconify()
            self.open_manual_selection_window(evt=None,localentry=[location_entry,wait_window])
        # 扫描位置与等待时间
        location_frame = tk.Frame(scan_frame)
        location_label = tk.Label(location_frame, text="地址:")
        location_label.pack(side="left", padx=5)
        location_entry = tk.Entry(location_frame)
        location_entry.pack(side="left", padx=5)
        scan_button = tk.Button(location_frame, text="框选", command=select_scan_region)
        scan_button.pack(side="left", padx=5)
        location_frame.pack(pady=5)

        long_time_frame = tk.Frame(scan_frame)
        time_label = tk.Label(long_time_frame, text="最长等待(秒):")
        time_label.pack(side="left", padx=5)
        time_entry = tk.Entry(long_time_frame)
        time_entry.insert(0,10)
        time_entry.pack(side="left", padx=5)
        long_time_frame.pack(pady=5)


        # 框选扫描区域和确认按钮
        scan_button_frame = tk.Frame(scan_frame)
        def confirm_scan_wait():
            scan_image = scan_entry.get()
            location = eval(location_entry.get())
            max_wait_time = float(time_entry.get())
            # 检查是否有输入
            if not scan_image:
                tk.messagebox.showwarning("警告", "请输入扫描图片路径!")
                return
            if not location:
                tk.messagebox.showwarning("警告", "请输入扫描位置!")
                return
            if not max_wait_time:
                tk.messagebox.showwarning("警告", "请输入有效的最长等待时间!")
                return

            # 将结果插入操作列表并更新UI
            self.operations.insert(position, {
            "operation_name": "等待匹配",
            "parameters": [scan_image,location,float(max_wait_time)],
            "operation_text": f"等待匹配{scan_image}-{location}-{max_wait_time}秒"
            })
            self.save_operations()
            self.populate_operation_list()
            wait_window.destroy()

        scan_button_confirm = tk.Button(scan_button_frame, text="确认", command=confirm_scan_wait)
        scan_button_confirm.pack(side="left", padx=5)

        scan_button_frame.pack(pady=5)

        show_time_wait()

        wait_window.protocol("WM_DELETE_WINDOW", lambda: self.on_close(position,dele_op,wait_window))

    # 添加滚轮操作窗口
    def add_scroll_operation_window(self, position,dele_op = None):
        # 打开滚轮窗口并记录滚轮步数
        scroll_steps = 0
        scroll_window = tk.Toplevel(self.ui)
        scroll_window.title("滚轮操作")
        scroll_window.geometry("280x150")
        scroll_window.lift()
        scroll_window.focus_set()

        scroll_label = tk.Label(scroll_window, text="请输入滚轮步数(正数向上)：")
        scroll_label.pack(pady=5)

        scroll_entry = tk.Entry(scroll_window)
        scroll_entry.pack(pady=5)

        def confirm_scroll():
            scroll_time = int(scroll_entry.get())
            # 直接在这里处理滚轮操作,避免调用额外的函数
            self.operations.insert(position, {
            "operation_name": "滚轮",
            "parameters": [scroll_time],
            "operation_text": f"滚轮{scroll_time}步"
            })
            self.save_operations()
            self.populate_operation_list()
            scroll_window.destroy()

        scroll_button = tk.Button(scroll_window, text="确认", command=confirm_scroll)
        scroll_button.pack(pady=5)

        def on_mouse_wheel(event):
            nonlocal scroll_steps
            # 获取滚轮滚动的方向
            direction = event.delta // 120  # 正数表示向上滚动,负数表示向下滚动
            current_value = int(scroll_entry.get()) if scroll_entry.get() else 0
            scroll_steps = current_value + direction
            # 更新滚轮步数
            scroll_entry.delete(0, tk.END)  # 清空之前的内容
            scroll_entry.insert(0, str(scroll_steps))

        scroll_window.bind("<MouseWheel>", on_mouse_wheel)
            # 添加关闭窗口时的回调
        scroll_window.protocol("WM_DELETE_WINDOW", lambda: self.on_close(position,dele_op,scroll_window))

    #添加键盘操作窗口
    def add_keyboard_operation_window(self, position,dele_op = None):
        keyboard_window = tk.Toplevel(self.ui)
        keyboard_window.title("键盘操作")
        keyboard_window.geometry("340x300")
        keyboard_window.lift()
        keyboard_window.focus_set()

        input_frame = tk.Frame(keyboard_window)
        input_frame.pack(pady=5)

        input_label = tk.Label(input_frame, text="键：")
        input_label.pack(side=tk.LEFT, padx=3)

        input_entry = tk.Entry(input_frame, width=15,state="readonly")
        input_entry.pack(side=tk.LEFT, padx=5)

        mode_label = tk.Label(input_frame, text="选择按键模式：")
        mode_label.pack(side=tk.TOP, padx=5)

        mode_var = tk.StringVar(value="single")
        mode_frame = tk.Frame(input_frame)
        mode_frame.pack(side=tk.TOP, pady=5)

        mode_single = tk.Radiobutton(mode_frame, text="单点", variable=mode_var, value="single")
        mode_single.pack(side=tk.TOP, anchor="w")

        mode_multi = tk.Radiobutton(mode_frame, text="多按", variable=mode_var, value="multi")
        mode_multi.pack(side=tk.TOP, anchor="w")

        mode_long = tk.Radiobutton(mode_frame, text="长按", variable=mode_var, value="long")
        mode_long.pack(side=tk.TOP, anchor="w")

        mode_multi_long = tk.Radiobutton(mode_frame, text="多按长按", variable=mode_var, value="multi_long")
        mode_multi_long.pack(side=tk.TOP, anchor="w")

        mode_typing = tk.Radiobutton(mode_frame, text="打字", variable=mode_var, value="typing")
        mode_typing.pack(side=tk.TOP, anchor="w")

        press_frame = tk.Frame(keyboard_window)
        press_frame.pack(pady=5)
        long_press_label = tk.Label(press_frame, text="长按时间(秒):")
        long_press_label.pack(side=tk.LEFT, padx=5)

        long_press_entry = tk.Entry(press_frame, width=10)
        long_press_entry.pack(side=tk.LEFT, padx=5)

        self.key_bind = True
        def toggle_long_press_visibility(*args):
            input_entry.config(state="normal")
            input_entry.delete(0, tk.END)
            if mode_var.get() in ["long", "multi_long"]:
                press_frame.pack(pady=5)
                if self.key_bind:
                    input_entry.config(state="readonly")
            else:
                press_frame.pack_forget()
                if self.key_bind:
                    if mode_var.get() != "typing":
                        input_entry.config(state="readonly")

        mode_var.trace_add("write", toggle_long_press_visibility)
        toggle_long_press_visibility()

        def hand_input():
            if self.key_bind:
                keyboard_window.unbind("<KeyPress>")
                keyboard_window.unbind("<KeyRelease>")
                self.key_bind = False
                input_entry.config(state="normal")
                clear_button.config(text="切换自动输入")
            else:
                keyboard_window.bind("<KeyPress>", record_key_press)
                keyboard_window.bind("<KeyRelease>", record_key_press)
                self.key_bind = True
                input_entry.config(state="readonly")
                clear_button.config(text="切换手写输入")

        def confirm_input():
            key_sym = input_entry.get()
            long_press_time = long_press_entry.get()

            if mode_var.get() in ["long", "multi_long"] and not long_press_time:
                tk.messagebox.showwarning("警告", "请输入长按时间！")
                return

            if not key_sym:
                tk.messagebox.showwarning("警告", "请输入一个键后再确认！")
                return

            if mode_var.get() == "single":
                formatted_keys = ["单点",key_sym]
            elif mode_var.get() == "multi":
                formatted_keys = ["多按",key_sym.split('+')]
            elif mode_var.get() == "long":
                formatted_keys = ["长按",float(long_press_time),key_sym]
            elif mode_var.get() == "multi_long":
                formatted_keys = ["长按多按",float(long_press_time), key_sym.split('+')]
            elif mode_var.get() == "typing":
                formatted_keys = ["打字",''.join(lazy_pinyin(key_sym))]

            self.operations.insert(position, {
            "operation_name": "键盘",
            "parameters": formatted_keys,
            "operation_text": f"键盘操作:{formatted_keys}"
            })
            self.save_operations()
            self.populate_operation_list()
            keyboard_window.destroy()

        button_frame = tk.Frame(keyboard_window)
        button_frame.pack(pady=10)

        confirm_button = tk.Button(button_frame, text="确定", command=confirm_input)
        confirm_button.pack(side=tk.LEFT, padx=10)

        clear_button = tk.Button(button_frame, text="切换手动输入", command=hand_input)
        clear_button.pack(side=tk.LEFT, padx=10)

        pressed_keys = []

        def record_key_press(event):
            key_sym = event.keysym
            if mode_var.get() in ["single", "long"]:
                if event.type == tk.EventType.KeyPress:
                    input_entry.config(state="normal")
                    input_entry.delete(0, tk.END)
                    input_entry.insert(tk.END, key_sym)
                    if self.key_bind:
                        input_entry.config(state="readonly")
            elif mode_var.get() in ["multi", "multi_long"]:
                if event.type == tk.EventType.KeyPress and key_sym not in pressed_keys:
                    pressed_keys.append(key_sym)
                    input_entry.config(state="normal")
                    input_entry.delete(0, tk.END)
                    input_entry.insert(tk.END, "+".join(pressed_keys))
                    if self.key_bind:
                        input_entry.config(state="readonly")
                elif event.type == tk.EventType.KeyRelease and key_sym in pressed_keys:
                    pressed_keys.remove(key_sym)
            elif mode_var.get() == "typing":
                pass
        def on_focus_in(event):
            # 解绑按键事件
            keyboard_window.unbind("<KeyPress>")
            keyboard_window.unbind("<KeyRelease>")

        def on_focus_out(event):
            # 重新绑定按键事件
            if self.key_bind:
                keyboard_window.bind("<KeyPress>", record_key_press)
                keyboard_window.bind("<KeyRelease>", record_key_press)
        keyboard_window.bind("<KeyPress>", record_key_press)
        keyboard_window.bind("<KeyRelease>", record_key_press)
        long_press_entry.bind("<FocusIn>", on_focus_in)
        long_press_entry.bind("<FocusOut>", on_focus_out)
        keyboard_window.protocol("WM_DELETE_WINDOW", lambda: self.on_close(position,dele_op,keyboard_window))

    #添加鼠标操作窗口
    def add_mouse_operation_window(self, position, dele_op=None):
        # 打开鼠标操作窗口并记录点击位置
        self.ui.iconify()

        def open_mouse_operation_window(click_position, position):
            # 创建一个新窗口用于设置鼠标操作
            mouse_window = tk.Toplevel(self.ui)
            mouse_window.title("鼠标操作")
            mouse_window.geometry("300x350")

            input_frame = tk.Frame(mouse_window)
            input_frame.pack(pady=10)

            # 使用 Entry 组件代替 Label 显示点击位置,允许编辑
            click_position_var = tk.StringVar(value=click_position)
            click_position_entry = tk.Entry(input_frame, textvariable=click_position_var, width=30)
            click_position_entry.pack(pady=5)

            operation_label = tk.Label(input_frame, text="请选择操作类型：")
            operation_label.pack(pady=5)

            # 创建一个横向布局容器
            operation_frame = tk.Frame(input_frame)
            operation_frame.pack(side=tk.TOP)

            # 单击、双击、长按选项
            operation_var = tk.StringVar(value="单击")  # 默认选择单击
            click_options = [("单击", "单击"), ("双击", "双击"), ("长按", "长按")]
            for text, value in click_options:
                rb = tk.Radiobutton(operation_frame, text=text, variable=operation_var, value=value)
                rb.pack(side=tk.LEFT)  # 横向布局

            separator = ttk.Separator(input_frame, orient='horizontal')
            separator.pack(fill='x', pady=10)

            # 创建另一个横向布局容器来放置按键选择
            key_frame = tk.Frame(input_frame)
            key_frame.pack(side=tk.TOP, pady=10)

            # 左键、右键、中键选择
            mouse_button_var = tk.StringVar(value="左键")  # 默认选择左键
            button_options = [("左键", "左键"), ("中键", "中键"), ("右键", "右键")]
            for text, value in button_options:
                rb = tk.Radiobutton(key_frame, text=text, variable=mouse_button_var, value=value)
                rb.pack(side=tk.LEFT)  # 横向布局

            # 长按时输入长按时间
            press_time_label = tk.Label(input_frame, text="长按时间(秒):")
            press_time_label.pack(pady=5)
            press_time_entry = tk.Entry(input_frame)
            press_time_entry.insert(0, "1")  # 默认1秒
            press_time_entry.pack(pady=5)
            press_time_label.pack_forget()
            press_time_entry.pack_forget()

            # 只有选择 "长按" 时显示长按时间输入框
            def toggle_press_time_field():
                if operation_var.get() == "长按":
                    press_time_label.pack(pady=5)
                    press_time_entry.pack(pady=5)
                else:
                    press_time_label.pack_forget()
                    press_time_entry.pack_forget()

            # 绑定操作类型变化时显示/隐藏长按时间输入框
            operation_var.trace("w", lambda *args: toggle_press_time_field())

            def is_valid_operation_format(operation_text):
                """
                验证用户输入的操作格式是否符合规定的格式
                """
                # 定义正则表达式
                # 格式：(x,y) (x,y,z)
                valid_format = re.compile(r"^\(\d+,\d+\)$|^\(\d+,\d+,\d+\)$")
                return valid_format.match(operation_text)

            def confirm_input():
                operation = click_position_var.get()
                # 检查操作格式是否有效
                if not is_valid_operation_format(operation):
                    tk.messagebox.showwarning("警告", "输入的操作格式不正确,请按规则输入！")
                    return
                # 将鼠标操作加入operations
                self.operations.insert(position, {
                    "operation_name": "鼠标",
                    "parameters": [mouse_button_var.get(),operation_var.get(),operation,press_time_entry.get()],
                    "operation_text": f"鼠标操作:{mouse_button_var.get()}-{operation_var.get()}-{operation}"
                })
                self.save_operations()
                self.populate_operation_list()
                mouse_window.destroy()
                self.ui.deiconify()

            # 录制点击位置按钮
            def record_click():
                # 创建半透明蒙版窗口
                mouse_window.iconify()
                position_window = tk.Toplevel(self.ui)
                position_window.attributes('-alpha', 0.3)  # 设置透明度
                position_window.attributes('-fullscreen', True)  # 设置全屏
                position_window.title("鼠标操作")
                position_window.wm_attributes('-topmost', 1)

                mouse_label = tk.Label(position_window, text="请在此窗口点击一个位置：")
                mouse_label.pack(pady=5)

                def record_click_position(event):
                    click_position = f"({event.x},{event.y})"
                    # 更新已有窗口中的点击位置
                    click_position_var.set(click_position)
                    position_window.destroy()  # 关闭蒙版窗口
                    if event.num == 1:  # 左键点击
                        mouse_button_var.set("左键")
                    elif event.num == 2:  # 中键点击
                        mouse_button_var.set("中键")
                    elif event.num == 3:  # 右键点击
                        mouse_button_var.set("右键")
                    mouse_window.deiconify()

                # 绑定鼠标点击事件
                position_window.bind("<Button-1>", record_click_position)  # 左键
                position_window.bind("<Button-2>", record_click_position)  # 中键
                position_window.bind("<Button-3>", record_click_position)  # 右键

            # 按钮区域
            button_frame = tk.Frame(mouse_window)
            button_frame.pack(pady=10)

            confirm_button = tk.Button(button_frame, text="确认提交", command=confirm_input)
            confirm_button.pack(side=tk.LEFT, padx=5)

            # 改为录制点击位置
            record_button = tk.Button(button_frame, text="录制点击", command=record_click)
            record_button.pack(side=tk.LEFT, padx=5)

            # 添加不固定位置按钮
            def add_pathfinding_operation():
                # 启动 add_pathfinding_operation_window 函数
                self.add_pathfinding_operation_window(on_pathfinding_result)

            def on_pathfinding_result(pathfinding_result):
                click_position = f"{pathfinding_result}"
                click_position_var.set(click_position)  # 更新点击位置字段

            # 添加寻路按钮
            pathfinding_button = tk.Button(button_frame, text="匹配区域", command=add_pathfinding_operation)
            pathfinding_button.pack(side=tk.LEFT, padx=5)

            # 返回窗口和相关的组件
            return mouse_window, click_position_var, click_position_entry

        # 初始化鼠标操作窗口
        mouse_window, click_position_var, click_position_entry = open_mouse_operation_window("", position)  # 初始时点击位置为空
        mouse_window.protocol("WM_DELETE_WINDOW", lambda: self.on_close(position, dele_op, mouse_window))


#执行操作代码
    # 执行操作函数
    def execute_operations(self):
        try:
            for operation in self.operations:
                operation_name = operation["operation_name"]
                parameters = operation["parameters"]
                if not self.scanning: #不再扫描的时候,也不再继续执行
                    break
                if operation_name == "等待":
                    wait_time = parameters[0]  # 获取等待时间（单位：毫秒）
                    wstart_time = time.time()
                    sleep_time = wait_time / 1000  # 转换为秒
                    while time.time() - wstart_time < sleep_time:
                        if not self.scanning:  # 防止用户输入过大的数字，不再扫描时停止等待
                            break
                        time.sleep(0.1)
                elif operation_name == "等待匹配":
                    scan_image = parameters[0]  # 获取扫描图像路径
                    location = parameters[1]  # 获取扫描位置
                    max_wait_time = parameters[2]  # 获取最大等待时间（单位：秒）
                    start_time = time.time()
                    target_image = self.load_target_image(scan_image)
                    while time.time() - start_time < max_wait_time:
                        if self.check_scan(target_image, location):
                            break
                        if not self.scanning:  # 防止用户输入过大的数字，不再扫描时停止等待
                            break
                        time.sleep(0.1)
                elif operation_name == "滚轮":
                    scroll_time = parameters[0]  # 获取滚动步数
                    pyautogui.scroll(scroll_time)  # 执行滚轮操作
                elif operation_name == "键盘":
                    key_map = {
                    'Control_L': 'ctrl',
                    'Control_R': 'ctrl',
                    'Shift_L': 'shift',
                    'Shift_R': 'shift',
                    'Alt_L': 'alt',
                    'Alt_R': 'alt',
                    'Caps_Lock': 'capslock',
                    'Return': 'enter',
                    'BackSpace': 'backspace',
                    'Tab': 'tab',
                    'Escape': 'esc',
                    'space': 'space',
                    'period': '.',
                    'comma': ',',
                    'exclam': '!',
                    'at': '@',
                    'numbersign': '#',
                    'dollar': '$',
                    'percent': '%',
                    'ampersand': '&',
                    'quote': "'",
                    'doublequote': '"',
                    'colon': ':',
                    'semicolon': ';',
                    'less': '<',
                    'greater': '>',
                    'question': '?',
                    'bracketleft': '[',
                    'bracketright': ']',
                    'braceleft': '{',
                    'braceright': '}',
                    'parenleft': '(',
                    'parenright': ')',
                    'Return': 'enter',
                    'slash': '/',
                    'grave': '`',
                    'asciitilde': '~',
                    'minus': '-',
                    'underscore': '_',
                    'equal': '=',
                    'plus': '+',
                    'asterisk': '*',
                    'bar': '|',
                    'Up': 'up',
                    'Down': 'down',
                    'Left': 'left',
                    'Right': 'right',
                    'Win_L': 'win',
                    'Win_R': 'win',
                    # 添加更多需要的特殊键
                    }
                    # 解析键盘操作的参数
                    mode = parameters[0]  # 操作模式
                    if mode == "单点":
                        key_sym = parameters[1]  # 单个按键
                        pyautogui.press(key_map.get(key_sym, key_sym))  # 按下单个按键
                    elif mode == "多按":
                        keys = parameters[1]  # 多个按键
                        pyautogui.hotkey(*[key_map.get(key.strip("[]"), key.strip("[]")) for key in keys])  # 按下所有组合键
                    elif mode == "长按":
                        long_press_time = parameters[1]  # 长按时间
                        key_sym = parameters[2]  # 单个按键
                        key = key_map.get(key_sym, key_sym)
                        pyautogui.keyDown(key)
                        # 长按期间持续输出相同的按键
                        start_time = time.time()
                        while time.time() - start_time < long_press_time:
                            if not self.scanning:
                                break
                            time.sleep(0.1)
                        pyautogui.keyUp(key)
                    elif mode == "多按长按":
                        long_press_time = parameters[1]  # 长按时间
                        keys = parameters[2]  # 多个按键
                        # 按下所有组合键，长按
                        pyautogui.keyDown(key_map.get(keys[0], keys[0]))  # 按下第一个键
                        for key in keys[1:]:
                            pyautogui.press(key_map.get(key, key))  # 按下其他组合键
                        time.sleep(long_press_time)  # 按键长按的时间
                        pyautogui.keyUp(key_map.get(keys[0], keys[0]))  # 释放第一个键
                    elif mode == "打字":
                        text = parameters[1]  # 输入文本
                        pyautogui.write(text)  # 输入文本
                elif operation_name == "鼠标":
                    # 获取鼠标操作的参数
                    mouse_button = parameters[0]  # 左键、右键、中键
                    action = parameters[1]  # 单击、双击、长按
                    position_str = parameters[2]  # 位置字符串，如 "(150,200)" 或 "(0,150,200)"
                    press_time = parameters[3]  # 长按时间

                    # 将位置字符串转换为元组
                    position_values = tuple(map(int, position_str.strip("()").split(",")))

                    offset_x = 0
                    offset_y = 0
                    center_x = 0
                    center_y = 0
                    x = 0
                    y = 0
                    # 如果坐标是三个值，则为扫描操作，第一位为扫描区域标识
                    if len(position_values) == 3:
                        x, y = position_values[1], position_values[2]  # 扫描区域的坐标
                        max_loc = self.max_loc[position_values[0]]  # 获取扫描区域的坐标
                        if max_loc != [0, 0, 0, 0]:  # 如果扫描区域不为空
                            center_x = int((max_loc[0][0] + max_loc[1][0]) / 2)
                            center_y = int((max_loc[0][1] + max_loc[1][1]) / 2)
                        else:
                            continue  #如果目标没被识别到,此次循环跳过
                    else:
                        # 普通鼠标操作，坐标只有两个数字
                        x, y = position_values

                    # 执行鼠标操作
                    real_x = center_x + x + offset_x
                    real_y = center_y + y + offset_y
                    if mouse_button == "左键":
                        if action == "单击":
                            pyautogui.click(real_x, real_y)
                        elif action == "双击":
                            pyautogui.doubleClick(real_x, real_y, interval=0.1)
                        elif action == "长按" and press_time:
                            press_time = float(press_time)  # 获取按压时间
                            pyautogui.mouseDown(real_x, real_y)
                            pyautogui.sleep(press_time)  # 按压一段时间
                            pyautogui.mouseUp(real_x, real_y)
                    elif mouse_button == "右键":
                        if action == "单击":
                            pyautogui.rightClick(real_x, real_y)
                        elif action == "双击":
                            pyautogui.rightDoubleClick(real_x, real_y, interval=0.1)
                        elif action == "长按" and press_time:
                            press_time = float(press_time)  # 获取按压时间
                            pyautogui.mouseDown(real_x, real_y, button='right')
                            pyautogui.sleep(press_time)  # 按压一段时间
                            pyautogui.mouseUp(real_x, real_y, button='right')
                    elif mouse_button == "中键":
                        if action == "单击":
                            pyautogui.middleClick(real_x, real_y)
                        elif action == "双击":
                            pyautogui.middleDoubleClick(real_x, real_y, interval=0.1)
                        elif action == "长按" and press_time:
                            press_time = float(press_time)  # 获取按压时间
                            pyautogui.mouseDown(real_x, real_y, button='middle')
                            pyautogui.sleep(press_time)  # 按压一段时间
                            pyautogui.mouseUp(real_x, real_y, button='middle')
                elif operation_name == "开启":
                    chosen_index = parameters[0]
                    loop_count = parameters[1]
                    self.tab.tk_tabs_first_tab.select(chosen_index)  # 选择对应的标签页
                    selected_child_frame = self.tab.tk_tabs_first_tab.nametowidget(self.tab.tk_tabs_first_tab.select())
                    if loop_count == 1:
                        selected_child_frame.loop_var.set("循环1次")
                    elif loop_count == 10:
                        selected_child_frame.loop_var.set("循环10次")
                    elif loop_count is None:
                        selected_child_frame.loop_var.set("无限循环")
                    selected_child_frame.start_scanning()
                elif operation_name == "关闭":
                    chosen_index = parameters[0]
                    self.ui.tk_tabs_first_tab.select(chosen_index)
                    selected_child_frame = self.tab.tk_tabs_first_tab.nametowidget(self.tab.tk_tabs_first_tab.select())
                    selected_child_frame.stop_scanning()
                elif operation_name == "拖动":
                    # 获取拖动时长和坐标信息
                    duration = parameters[0]  # 将时长转换为浮动类型
                    move_type = parameters[1]
                    points = parameters[2]
                    # 计算每个点之间的持续时间
                    num_points = len(points)
                    time_per_move = round(duration / (num_points - 1),3)*2  # 每次移动的时间
                    # 如果 positions 里面有多个点,按顺序进行逐步移动
                    # 遍历所有坐标，如果是(0, 0, 0)的格式，将其特殊处理
                    processed_positions = []
                    if num_points == 2:
                        for pos in points:
                            # 如果坐标是三个值，检查是否为(0, 0, 0)
                            if len(pos) == 3:
                                scan_region_index = pos[0]  # 获取扫描区域标识
                                x, y = pos[1], pos[2]  # 获取坐标
                                # 通过扫描区域标识获取 max_loc
                                max_loc = self.max_loc[scan_region_index]  # 获取对应扫描区域的坐标范围
                                if max_loc != [0, 0, 0, 0]:  # 如果该区域存在有效坐标
                                    # 计算该区域的中心点坐标
                                    center_x = int((max_loc[0][0] + max_loc[1][0]) / 2)
                                    center_y = int((max_loc[0][1] + max_loc[1][1]) / 2)
                                    # 将计算出的中心点坐标替换原坐标
                                    processed_positions.append((center_x + x, center_y + y))
                                else:
                                    # 如果该区域无效,则直接结束这轮for循环
                                    continue
                            else:
                                # 如果坐标是 (x, y)，直接使用原坐标
                                processed_positions.append(pos)
                        start = processed_positions[0]
                        end = processed_positions[1]
                        intermediate_points = 28  # 可根据需求调整中间点的数量
                        for i in range(1, intermediate_points + 1):
                            # 插入中间点
                            x = int(start[0] + (end[0] - start[0]) * i / (intermediate_points + 1))
                            y = int(start[1] + (end[1] - start[1]) * i / (intermediate_points + 1))
                            processed_positions.insert(i, (x, y))
                        num_points = 30
                        time_per_move = round(duration / (num_points - 1),3)*2
                    else:
                        # 如果 positions 中有多个点，不进行坐标解析，直接使用原坐标
                        processed_positions = points
                    positions = processed_positions
                    if move_type == "drag":
                        # 如果是拖动,按下鼠标并进行拖动
                        pyautogui.moveTo(positions[0][0], positions[0][1], duration=0.001)
                        pyautogui.mouseDown()  # 模拟按下鼠标(开始拖动)
                        for i in range(0, num_points, 2):  # 每隔一个点选择一次
                            if i + 1 < num_points and self.scanning:
                                pyautogui.moveTo(positions[i + 1][0], positions[i + 1][1], duration=time_per_move)
                        # 最后释放鼠标(结束拖动)
                        pyautogui.mouseUp()
                    elif move_type == "move":
                        # 如果是移动,不按下鼠标也不抬起鼠标
                        pyautogui.moveTo(positions[0][0], positions[0][1], duration=0.001)
                        for i in range(0, num_points, 2):  # 每隔一个点选择一次
                            if i + 1 < num_points and self.scanning:
                                pyautogui.moveTo(positions[i + 1][0], positions[i + 1][1], duration=time_per_move)

            if self.execution_method == "script_done":
                self.execution_count += 1 # 记录执行成功次数

            self.ui.after(0, lambda: self.tab.tk_label_operation_times.config(text=f"运行完成{self.execution_count}次"))
            # 更新执行次数限制
            if self.execution_limit:
                self.ui.after(0, lambda: self.tab.tk_label_operation_timeout_limit.config(text=f"预计执行{self.execution_limit}次\n还剩下{self.execution_limit - self.execution_count} 次"))
                # 达到执行次数限制，停止扫描
                if self.execution_count >= self.execution_limit:
                    self.ui.after(0, lambda: self.tab.tk_label_operation_timeout_limit.config(text="次数到达,已停止扫描"))
                    self.ui.after(0, lambda: self.ui.deiconify())
                    self.ui.after(0, lambda: self.stop_scanning())
        finally:
            self.is_executing = False  # 操作完成，设置为 False



#操作添加修改代码
    # 修改操作
    def operation_change(self, evt=None,change_keep = False):
        selected_item = self.tab.tk_table_operation_box.selection()
        if selected_item:
            selected_index = self.tab.tk_table_operation_box.index(selected_item[0])
            dele_op = self.operations[selected_index]
            operation_name = dele_op['operation_name']
            del self.operations[selected_index]
            if change_keep:
                self.operation_add(evt, selected_index, dele_op,operation_content=operation_name)
            else:
                self.operation_add(evt, selected_index, dele_op)

    # 删除操作
    def operation_delete(self, evt=None):
        selected_items = self.tab.tk_table_operation_box.selection()
        if selected_items:
            selected_indices = [self.tab.tk_table_operation_box.index(item) for item in selected_items]
            selected_indices.sort(reverse=True)
            # 依次删除选中的项,从后面往前面删,不然会有问题
            for index in selected_indices:
                del self.operations[index]
            self.save_operations()
            self.populate_operation_list()

    # 添加操作
    def operation_add(self, evt=None, operation_position=None,dele_op = None,operation_content = None):
        if operation_content is None:
            operation_content = self.tab.tk_select_box_operation_list.get()
        num_rows = len(self.tab.tk_table_operation_box.get_children())
        if operation_position is None:
            operation_position = num_rows + 1
        if operation_content in ["等待时间","等待","等待匹配"]:
            self.add_wait_operation_window(operation_position,dele_op)
        elif operation_content in ["键盘操作", "键盘"]:
            self.add_keyboard_operation_window(operation_position,dele_op)
        elif operation_content in ["鼠标操作","鼠标"]:
            self.add_mouse_operation_window(operation_position,dele_op)
        elif operation_content in ["鼠标拖动","拖动"]:
            self.add_drag_operation_window(operation_position,dele_op)
        elif operation_content in ["滚轮操作","滚轮"]:
            self.add_scroll_operation_window(operation_position,dele_op)
        elif operation_content in ["开启扫描","开启"]:
            self.add_start_operation_window(operation_position,dele_op)
        elif operation_content in ["关闭扫描","关闭"]:
            self.add_close_operation_window(operation_position,dele_op)

    # 全选操作
    def operation_select_all(self,evt=None):
        # 获取表格中的所有项
        all_items = self.tab.tk_table_operation_box.get_children()
        # 选中所有项
        self.tab.tk_table_operation_box.selection_set(all_items)

    # 复制操作
    def operation_copy(self, evt=None):
        selected_item = self.tab.tk_table_operation_box.selection()
        if selected_item:
            selected_index = self.tab.tk_table_operation_box.index(selected_item[0])
            operation_to_copy = self.operations[selected_index]
            self.operations.append(operation_to_copy)
            self.save_operations()
            self.populate_operation_list()

    # 操作向上移动
    def operation_up(self, evt=None):
        selected_item = self.tab.tk_table_operation_box.selection()
        if selected_item:
            selected_index = self.tab.tk_table_operation_box.index(selected_item[0])
            op1 = self.operations[selected_index]
            self.operations[selected_index] = self.operations[selected_index-1]
            self.operations[selected_index-1]=op1
            self.save_operations()
            self.populate_operation_list()

    # 操作向下移动
    def operation_down(self, evt=None):
        selected_item = self.tab.tk_table_operation_box.selection()
        if selected_item:
            selected_index = self.tab.tk_table_operation_box.index(selected_item[0])
            op1 = self.operations[selected_index]
            self.operations[selected_index] = self.operations[selected_index+1]
            self.operations[selected_index+1]=op1
            self.save_operations()
            self.populate_operation_list()
        pass



#读取保存代码
    # 读取给定文件路径下的内容并且加入自己的self.operations中
    def load_operations(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = file.read()
                if not data:  # 检查数据是否为空
                    self.error_print("操作数据为空")
                    return []
                else:
                    data = json.loads(data)
                    operations = [
                        {
                            "operation_name": v.get("operation_name", ""),
                            "parameters": v.get("parameters", []),
                            "operation_text": v.get("operation_text", "")
                        }
                        for k, v in sorted(data.items(), key=lambda x: int(x[0])) if k.isdigit()
                    ]
                    return operations
        except FileNotFoundError as e:
            self.error_print(e)
            return []

    # 读取给定data中的内容并且加入自己的self.operations中
    def load_data_operations(self, data):
        operations = []
        for item in data:
            if isinstance(item, dict):
                for key, operation in item.items():
                    operation_name = operation.get("operation_name", "")
                    parameters = operation.get("parameters", [])
                    operation_text = operation.get("operation_text", "")
                    if operation_name and parameters is not None:  # 确保操作名和参数存在
                        operations.append({
                            "operation_name": operation_name,
                            "parameters": parameters,
                            "operation_text": operation_text
                        })
        self.operations = operations
        self.save_operations()  # 保存更新后的操作列表

    # 将默认的图片信息加入cache缓存
    def add_default_photos(self):
        with open(self.photo_path, "w") as json_file:
            with open(self.default_photo_path, "r", encoding='utf-8') as default_file:
                data = json.load(default_file)  # 读取位于setting_json/default_photo.json中的默认图片信息
            json.dump(data, json_file)  # 写入缓存

    # 保存操作列表到file_path(写入cache)的位置
    def save_operations(self):
        with open(self.file_path, "w") as json_file:
            data = [
                {"operation_name": op.get("operation_name", ""), "parameters": op.get("parameters", []),
                "operation_text": op.get("operation_text", "")}
                for op in self.operations
            ]
            json.dump(data, json_file, ensure_ascii=False, indent=4)  # 美化 JSON 格式

    # 保存图片信息到file_path(写入cache)的位置
    def save_photos(self, default_photo=None , getdata=None):
        data = {}
        for i in range(4):
            data[f"地址{i+1}"] = self.selection_address[i]
            data[f"图片{i+1}的位置"] = self.tab.photo_input[i].get()
            data[f"图片{i+1}的地址"] = self.tab.photo_scan_box[i].get()
        data["满足方式"] = self.tab.photo_if_var.get()
        data["窗口选择"] = self.process_name
        if default_photo is None:
            write_path = self.photo_path
        else:
            write_path = default_photo
        if getdata is not None:
            return data
        # 保存图片信息到图片缓存cache中
        with open(write_path, "w") as json_file:
            json.dump(data, json_file)

    # 单独保存图片文件内容
    def save_photo_context(self, evt):
        self.save_photos()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            # 复制文件到所选位置
            shutil.copyfile("setting_json/photo_cache.json", file_path)
        ("保存图片位置到文件")

    # 单独读取图片文件内容
    def load_photo_context(self, evt):
        file_path = filedialog.askopenfilename(initialdir=os.path.dirname(self.file_path),
                                                initialfile=os.path.basename(self.file_path),
                                                title="读取操作列表",
                                                filetypes=(("Json files", "*.json"), ("All files", "*.*")))
        if file_path:
            self.populate_photo_address(file_path)
        ("从文件中读取具体图片位置")

    # 单独保存操作文件内容
    def save_operation_context(self, evt):
        self.save_operations()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            # 复制文件到所选位置
            shutil.copyfile("setting_json/operation_cache.json", file_path)

    # 单独读取操作文件内容
    def load_operation_context(self, evt):

        file_path = filedialog.askopenfilename(initialdir=os.path.dirname(self.file_path),
                                                initialfile=os.path.basename(self.file_path),
                                                title="读取操作列表",
                                                filetypes=(("Json files", "*.json"), ("All files", "*.*")))
        if file_path:
            with open(file_path, 'rb') as file:
                self.operations = self.load_operations(file_path)
                self.save_operations()
                self.populate_operation_list()



#界面复现代码
    # 打印操作列表到面板
    def populate_operation_list(self):
        self.tab.tk_table_operation_box.delete(*self.tab.tk_table_operation_box.get_children())  # 清空表格
        # 遍历操作列表，逐行插入数据
        for i, operation in enumerate(self.operations, start=1):
            operation_name = operation["operation_name"]  # 获取操作名
            operation_text = operation["operation_text"]
            # 插入数据到表格
            self.tab.tk_table_operation_box.insert("", i, values=(i, operation_name, operation_text))

    # 打印图片信息到面板
    def populate_photo_address(self, photo_path, load_if=True):
        # 显示图片相关地址
        try:
            if load_if:
                with open(photo_path, "r") as json_file:
                    data = json.load(json_file)  # 如果是手动读取,那么photo_path作为json地址读取
            else:
                data = photo_path     # 如果是自动读取,那么photo_path作为data读取
            # 对读取内容缺失的调整
            for i in range(4):
                self.selection_address[i] = data.get(f"地址{i+1}", [0, 0, 0, 0])
                self.tab.photo_input[i].delete(0, "end")
                self.tab.photo_input[i].insert(0, data.get(f"图片{i+1}的位置", ""))
                self.tab.photo_scan_box[i].set(data.get(f"图片{i+1}的地址", "地址1"))
            self.tab.photo_if_var.set(data.get("满足方式", "all"))
            self.tab.tk_label_process_label.config(text=data.get("窗口选择", "窗口选择"+"\n暂无"))
            self.process_name = data.get("窗口选择", None)

            self.select_photo_show()

        except (IOError, json.JSONDecodeError, KeyError) as e:
            # 如果json内部键值错误
            for i in range(4):
                self.selection_address[i] = data.get([0, 0, 0, 0])
                self.tab.photo_input[i].delete(0, "end")
                self.tab.photo_input[i].insert(0, "")
                self.tab.photo_scan_box[i].set(data.get("地址1"))
            self.tab.photo_if_var.set("all")
            self.tab.tk_label_process_label.config(text="窗口选择"+"\n无")

            self.select_photo_show()


#默认设置代码
    # 打开默认图片设置窗口并且记录默认图片信息
    def set_default_photo(self, evt):
        default_photo_window = tk.Toplevel(self.ui)
        default_photo_window.title("设置默认图片")
        default_photo_window.geometry("355x500")
        default_photo_window.lift()
        default_photo_window.focus_set()

        with open('setting_json/default_photo.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        text_widget = tk.Text(default_photo_window, wrap=tk.WORD, width=35, height=20)
        text_widget.grid(row=0, column=0, padx=10, pady=10, columnspan=2)
        text_widget.insert(tk.END, json.dumps(data, indent=4, ensure_ascii=False))

        save_button = tk.Button(default_photo_window, text="保存", command=lambda: save_settings(text_widget.get("1.0", tk.END)))
        save_button.grid(row=1, column=0, pady=10)

        set_default_button = tk.Button(default_photo_window, text="导入本扫描图片信息", command=lambda:load_settings())
        set_default_button.grid(row=1, column=1, pady=10)

        def save_settings(settings_data_str):
            try:
            # Convert the JSON string back to a dictionary
                settings_data = json.loads(settings_data_str)
            # 保存在默认图片的文件中
                with open('setting_json/default_photo.json', 'w', encoding='utf-8') as f:
                    json.dump(settings_data, f, indent=4, ensure_ascii=False)
                default_photo_window.destroy()
            except Exception as e:
                self.error_print(e)

        def load_settings():
            data = self.save_photos(default_photo=None,getdata="1")
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, json.dumps(data, indent=4, ensure_ascii=False))

    # 打开默认操作设置窗口并且记录默认操作信息
    def set_default_operation(self, evt):

        default_operation_window = tk.Toplevel(self.ui)
        default_operation_window.title("设置默认操作")
        default_operation_window.geometry("440x400")
        default_operation_window.lift()
        default_operation_window.focus_set()

        with open('setting_json/default_operation.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        text_widget = tk.Text(default_operation_window, wrap=tk.WORD, width=44, height=15)
        text_widget.grid(row=0, column=0, padx=10, pady=10, columnspan=2)
        text_widget.insert(tk.END, json.dumps(data, indent=4, ensure_ascii=False))

        save_button = tk.Button(default_operation_window, text="保存", command=lambda: save_settings(text_widget.get("1.0", tk.END)))
        save_button.grid(row=1, column=0, pady=10)

        set_default_button = tk.Button(default_operation_window, text="导入本扫描操作信息", command=lambda:load_settings())
        set_default_button.grid(row=1, column=1, pady=10)

        def save_settings(settings_data_str):
            try:
                settings_data = json.loads(settings_data_str)
                with open('setting_json/default_operation.json', 'w', encoding='utf-8') as f:
                    json.dump(settings_data, f, indent=4, ensure_ascii=False)
                default_operation_window.destroy()
            except Exception as e:
                self.error_print(e)

        def load_settings():
            data = {}
            i = 0
            for i,op in enumerate(self.operations):
                data[i] = {"operation_name": op.get("operation_name", ""),
                        "parameters": op.get("parameters", []),
                        "operation_text": op.get("operation_text", "")}
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, json.dumps(data, indent=4, ensure_ascii=False))

    # 设置默认快捷键
    def set_default_key(self, evt):
        default_key_window = tk.Toplevel(self.ui)
        default_key_window.title("设置默认图片")
        default_key_window.geometry("355x500")
        default_key_window.lift()
        default_key_window.focus_set()

        with open('setting_json/key_setting.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        text_widget = tk.Text(default_key_window, wrap=tk.WORD, width=35, height=20)
        text_widget.grid(row=0, column=0, padx=10, pady=10)
        text_widget.insert(tk.END, json.dumps(data, indent=4, ensure_ascii=False))

        save_button = tk.Button(default_key_window, text="保存", command=lambda: save_settings(text_widget.get("1.0", tk.END)))
        save_button.grid(row=1, column=0, pady=10)

        def save_settings(settings_data_str):
            try:
                settings_data = json.loads(settings_data_str)
                with open('setting_json/key_setting.json', 'w', encoding='utf-8') as f:
                    json.dump(settings_data, f, indent=4, ensure_ascii=False)
                self.ui.ctl.bind_keys(path = "setting_json/key_setting.json")
                default_key_window.destroy()
            except Exception as e:
                self.error_print(f"保存默认快捷键时发生错误: {e}")

    # 设置默认相似度
    def set_default_similar(self, evt, similar):
        # 设置相似度
        numeric_value_str = similar.replace('%', '')
        numeric_value = float(numeric_value_str) / 100.0
        self.check_similar = numeric_value
        self.save_else("相似度", numeric_value)

    # 设置随机偏移
    def set_random_offset(self, evt):
        self.random_offset = int(self.tab.tk_scale_num_random_offset.get())
        self.save_else("随机偏移", self.random_offset)

    # 设置默认扫描方式(强相似/若相似)
    def set_default_check(self, evt):
        self.default_check = self.tab.tk_select_box_check_out_box.get()
        self.save_else("策略",self.default_check)
        return

    #设置默认扫描时间
    def set_scan_time(self, evt):
        # 创建设置窗口
        scan_time_window = tk.Toplevel(self.ui)
        scan_time_window.title("设置扫描间隔")
        scan_time_window.geometry("300x250")

        # 输入框和单选按钮
        input_frame = tk.Frame(scan_time_window)
        input_frame.pack(pady=10)

        # 输入框：扫描间隔（秒）
        input_label = tk.Label(input_frame, text="请输入扫描间隔(毫秒ms):")
        input_label.pack(pady=5)

        input_entry = tk.Entry(input_frame)
        input_entry.insert(0, self.scan_interval)  # 默认填充100ms
        input_entry.pack(pady=5)

        # 单选按钮：选择执行判断方式
        method_var = tk.StringVar(value=self.execution_method)

        method_label = tk.Label(input_frame, text="执行成功判断方式：")
        method_label.pack(pady=5)

        rb_script_done = tk.Radiobutton(input_frame, text="脚本执行完毕", variable=method_var, value="script_done")
        rb_script_done.pack()

        rb_scan_changed = tk.Radiobutton(input_frame, text="扫描结果发生变化", variable=method_var, value="scan_changed")
        rb_scan_changed.pack()

        # 确认按钮
        def confirm_scan_time():
            # 获取扫描间隔和选择的判断方式
            try:
                scan_interval = input_entry.get()  # 转换为毫秒
                self.scan_interval = int(scan_interval)
                self.save_else("扫描时间", self.scan_interval)
            except ValueError:
                tk.messagebox.showwarning("警告", "请输入有效的数字！")
                return

            self.execution_method = method_var.get()

            # 关闭设置窗口
            scan_time_window.destroy()

        confirm_button = tk.Button(scan_time_window, text="确认", command=confirm_scan_time)
        confirm_button.pack(pady=10)

    # 设置定时停止扫描
    def set_operaton_timeout(self, evt):
        self.time_limit = None
        self.scan_limit = None
        self.execution_limit = None
        # 创建设置面板
        timeout_window = tk.Toplevel(self.ui)
        timeout_window.title("设置操作超时")
        timeout_window.geometry("280x250")

        # 输入框和单选按钮
        input_frame = tk.Frame(timeout_window)
        input_frame.pack(pady=10)

        # 选项的单选按钮
        timeout_option = tk.StringVar(value="定时停止")

        timeout_choices = [("定时停止（秒）", "定时停止"), ("扫描成功次数（次）", "扫描次数"), ("脚本执行成功次数（次）", "脚本次数")]

        for text, value in timeout_choices:
            rb = tk.Radiobutton(input_frame, text=text, variable=timeout_option, value=value)
            rb.pack()

        # 输入框
        input_label = tk.Label(input_frame, text="请输入时间或次数：")
        input_label.pack(pady=5)

        input_entry = tk.Entry(input_frame)
        input_entry.pack(pady=5)

        # 确认按钮
        def confirm_timeout_input():
            # 获取选择的操作类型和输入的值
            selected_option = timeout_option.get()
            input_value = input_entry.get()

            if not input_value.isdigit():
                tk.messagebox.showwarning("警告", "请输入有效的数字！")
                return

            # 生成输出文本
            if selected_option == "定时停止":
                result_text = f"定时 {input_value} 秒 结束扫描"
                self.time_limit = float(input_value)
            elif selected_option == "扫描次数":
                result_text = f"扫描成功 {int(input_value)} 次后停止"
                self.scan_limit = int(input_value)
            elif selected_option == "脚本次数":
                result_text = f"脚本执行成功 {int(input_value)} 次后停止"
                self.execution_limit = int(input_value)
            self.tab.tk_label_operation_timeout_limit.config(text=result_text)
            timeout_window.destroy()  # 关闭窗口

        # 确认按钮
        confirm_button = tk.Button(timeout_window, text="确认", command=confirm_timeout_input)
        confirm_button.pack(pady=10)

    #打开窗口选择窗口,设置扫描窗口名
    def open_window_selection(self, evt):
        # 创建设置面板
        process_window = tk.Toplevel(self.ui)
        process_window.title("选择操作窗口")
        process_window.geometry("300x200")
        process_window.lift()
        process_window.focus_set()

        # 获取当前打开的窗口标题
        window_titles = [win.title for win in gw.getWindowsWithTitle('')
                        if win.title.strip()]  # 获取当前所有窗口的标题

        # 如果没有窗口，则给出提示
        if not window_titles:
            window_titles = ["没有可用窗口"]

        start_label = tk.Label(process_window, text="请选择需要扫描的窗口")
        start_label.pack(pady=5)

        selected_window = tk.StringVar(value=window_titles[0])  # 默认选择第一个窗口
        window_combobox = ttk.Combobox(process_window, textvariable=selected_window, values=window_titles, state="readonly")
        window_combobox.pack(pady=5)

        entry = tk.Entry(process_window)
        entry.pack(pady=5)

        def on_combobox_change(event):
            entry.delete(0, tk.END)
            if selected_window.get() == "选择操作窗口":
                entry.insert(0, "")
            else:
                entry.insert(0, selected_window.get())

        # 绑定 combobox 选择事件
        window_combobox.bind("<<ComboboxSelected>>", on_combobox_change)

        def confirm_selection():
            window_name = entry.get()  # 获取下拉框选中的窗口名称
            self.tab.tk_label_process_label.config(text=window_name)  # 更新标签的内容
            self.process_name = window_name  # 更新属性的值
            # 关闭设置窗口
            process_window.destroy()

        confirm_button = tk.Button(process_window, text="确认", command=confirm_selection)
        confirm_button.pack(pady=10)

    # 默认相似度/扫描策略/随机偏移/扫描间隔/···读取
    def similar_bind(self):
        json_file = self.key_setting_path
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                settings = json.load(file)
        except FileNotFoundError:
            self.error_print("未找到文件")
        # 获取相似度值
        if "else" in settings:
            if "相似度" in settings["else"]:
                self.check_similar = settings["else"]["相似度"]
            else:
                self.error_print("Key disappear:未找到相似度")

            if "随机偏移" in settings["else"]:
                self.random_offset = int(settings["else"]["随机偏移"])
                self.tab.tk_scale_num_random_offset.set(self.random_offset)
            else:
                self.error_print("Key disappear:未找到随机偏移")

            if "策略" in settings["else"]:
                self.check_method = settings["else"]["策略"]
                self.tab.tk_select_box_check_out_box.set(self.check_method)
            else:
                self.error_print("Key disappear:未找到扫描策略")

            if "扫描时间" in settings["else"]:
                self.scan_interval = settings["else"]["扫描时间"]
            else:
                self.error_print("Key disappear:未找到扫描时间")
        else:
            self.error_print("Key disappear:未找到else选项")



