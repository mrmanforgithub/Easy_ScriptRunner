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
import traceback
from datetime import datetime
import subprocess
import win32gui
import win32con
import re
import io

class TabController:
    # 导入UI类后,替换以下的 object 类型,将获得 IDE 属性提示功能
    ui: object
    tab: object

    def __init__(self, tab):
        self.tab = tab     # 本身的tab页面,用于给自己的tab控件进行操作
        self.operation_position = None
        self.operation_content = None
        self.keep_scanning = False   # 扫描的信标,保证正在扫描
        self.sub_windows = []   # 子窗口集合,用于调用其他tab
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

        self.photo_if = "all"  #图片策略

        self.file_path = "setting_json/operation_cache.json"  # 缓存文件,临时记录操作数据,关闭后清空
        self.photo_path = "setting_json/photo_cache.json"  # 缓存文件,临时记录图片数据,关闭后清空
        self.default_file_path = "setting_json/default_operation.json"   # 默认文件,记录开启时导入的操作内容
        self.default_photo_path = "setting_json/default_photo.json"    # 默认文件,记录开启时导入的图片内容
        self.key_setting_path = "setting_json/key_setting.json"
        self.window = None
        # self.windowsfocus()

        self.operations = self.load_operations(self.default_file_path)
        if not self.operations:
            self.add_default_operations()
        self.max_loc = None
        # 图片截取目录
        self.image_path = None

        self.start_y = None  # 拖动框选的开始位置
        self.start_x = None
        self.end_y = None  # 拖动框选的结束位置
        self.end_x = None

        # 参数的初始化
        self.max_loops = None  # 扫描数量

        self.scanning = False  # 是否扫描

        self.manual_selection_coordinates = None  # 框选的扫描

        self.selection1_address = [0, 0, 0, 0]  # 四个不同的扫描地址
        self.selection2_address = [0, 0, 0, 0]
        self.selection3_address = [0, 0, 0, 0]
        self.selection4_address = [0, 0, 0, 0]

        self.result_check = ["是", "是", "是", "是"]  # 与或非的检查单,全为是则通过检查
        self.blink = False
        self.result_found = False
        self.scroll_offset = 0

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


    def load_ocr(self):
        self.tab.tk_label_scanning_state_label.config(text="加载OCR模型中...")
        from PPOCR_api import GetOcrApi
        self.ocr = GetOcrApi("tool/PaddleOCR-json_v1.4.1/PaddleOCR-json.exe")
        self.tab.tk_label_scanning_state_label.config(text="OCR模型加载完成")

    def start_ocr_loading(self):
        """加载 OCR 模型"""
        if not hasattr(self, 'ocr') or not self.ocr:
            self.load_ocr()

    def init_ui(self, ui):
        """
        得到UI实例,对组件进行初始化配置
        """
        self.ui = ui
        # TODO 组件初始化 赋值操作

    def windowsfocus(self):
        self.window = win32gui.FindWindow(None, 'qq')
        if self.window == 0:
            raise Exception('无法找到指定的窗口')
        print(self.window)
        if win32gui.IsIconic(self.window):
            print("最小化了")
            win32gui.ShowWindow(self.window, win32con.SW_RESTORE)
        if not win32gui.IsWindowVisible(self.window):
            raise Exception('窗口不可见')
        win32gui.SetForegroundWindow(self.window)

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
        photo1_address = self.tab.tk_select_box_photo1_scan_box.get()
        photo2_address = self.tab.tk_select_box_photo2_scan_box.get()
        photo3_address = self.tab.tk_select_box_photo3_scan_box.get()
        photo4_address = self.tab.tk_select_box_photo4_scan_box.get()

        photo1_image_path = self.tab.tk_input_photo1_text.get()
        photo2_image_path = self.tab.tk_input_photo2_text.get()
        photo3_image_path = self.tab.tk_input_photo3_text.get()
        photo4_image_path = self.tab.tk_input_photo4_text.get()

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

        if photo1_image_path.strip():
            self.result_check[0] = "否"
            target_image1 = self.load_target_image(photo1_image_path,0)
            future = self.scan_pool.submit(self.scan_loop, target_image1, photo1_address, 0, max_loops)
            self.scan_futures.add(future)
        if photo2_image_path.strip():
            self.result_check[1] = "否"
            target_image2 = self.load_target_image(photo2_image_path,1)
            future = self.scan_pool.submit(self.scan_loop, target_image2, photo2_address, 1, max_loops)
            self.scan_futures.add(future)
        if photo3_image_path.strip():
            self.result_check[2] = "否"
            target_image3 = self.load_target_image(photo3_image_path,2)
            future = self.scan_pool.submit(self.scan_loop, target_image3, photo3_address, 2, max_loops)
            self.scan_futures.add(future)
        if photo4_image_path.strip():
            self.result_check[3] = "否"
            target_image4 = self.load_target_image(photo4_image_path,3)
            future = self.scan_pool.submit(self.scan_loop, target_image4, photo4_address, 3, max_loops)
            self.scan_futures.add(future)
        self.save_photos()

        #停止扫描

    def stop_scanning(self):
        # 停止扫描
        self.scanning = False
        self.blink = False
        self.result_found = False
        self.tab.tk_label_scanning_state_label.config(background="#6c757d")
        self.time_count = 0
        self.scan_count = 0
        self.execution_count = 0
        for future in list(self.scan_futures):
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
        if text_box_number == 1:
            self.tab.tk_input_photo1_text.delete(0, tk.END)
            self.tab.tk_input_photo1_text.insert(0, target_image_path_str)
        elif text_box_number == 2:
            self.tab.tk_input_photo2_text.delete(0, tk.END)
            self.tab.tk_input_photo2_text.insert(0, target_image_path_str)
        elif text_box_number == 3:
            self.tab.tk_input_photo3_text.delete(0, tk.END)
            self.tab.tk_input_photo3_text.insert(0, target_image_path_str)
        elif text_box_number == 4:
            self.tab.tk_input_photo4_text.delete(0, tk.END)
            self.tab.tk_input_photo4_text.insert(0, target_image_path_str)
        self.save_photos()

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

    # 修改操作
    def operation_change(self, evt):
        ("修改操作列表")
        selected_item = self.tab.tk_table_operation_box.selection()
        if selected_item:
            selected_index = self.tab.tk_table_operation_box.index(selected_item[0])
            del self.operations[selected_index]
            self.operation_add(evt, operation_position=selected_index)
            self.save_operations()
            self.populate_operation_list()

    # 删除操作
    def operation_delete(self, evt):
        ("删除操作内容")
        selected_item = self.tab.tk_table_operation_box.selection()
        if selected_item:
            selected_index = self.tab.tk_table_operation_box.index(selected_item[0])
            del self.operations[selected_index]
            self.save_operations()
            self.populate_operation_list()

    # 添加操作
    def operation_add(self, evt, operation_position=None):
        self.operation_content = self.tab.tk_select_box_operation_list.get()
        num_rows = len(self.tab.tk_table_operation_box.get_children())
        if operation_position is None:
            self.operation_position = num_rows + 1
        else:
            self.operation_position = operation_position
        if self.operation_content == "等待时间":
            self.add_wait_operation_window(self.operation_position)
        elif self.operation_content == "键盘操作":
            self.add_keyboard_operation_window(self.operation_position)
        elif self.operation_content == "鼠标操作":
            self.add_mouse_operation_window(self.operation_position)
        elif self.operation_content == "鼠标拖动":
            self.add_drag_operation_window(self.operation_position)
        elif self.operation_content == "滚轮操作":
            self.add_scroll_operation_window(self.operation_position)
        elif self.operation_content == "自动寻路":
            self.add_pathfinding_operation_window(self.operation_position)
        elif self.operation_content == "开启扫描":
            self.add_start_operation_window(self.operation_position)
        elif self.operation_content == "关闭扫描":
            self.add_close_operation_window(self.operation_position)

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
                now = datetime.now()
                timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
                log_filename = f"backtrace_logs/{timestamp}"

                with open(log_filename, "w") as file:
                    file.write(f"Error occurred at {now}:\n")
                    traceback.print_exc(file=file)  # 将异常信息写入文件

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
                now = datetime.now()
                timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
                log_filename = f"backtrace_logs/{timestamp}"

                with open(log_filename, "w") as file:
                    file.write(f"Error occurred at {now}:\n")
                    traceback.print_exc(file=file)  # 将异常信息写入文件

        def load_settings():
            data = {}
            i = 0
            for operation in self.operations:
                operation_index = i
                operation_name = operation
                data[i] = {"operation_index": operation_index, "operation_name": operation_name}
                i = i + 1
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
                now = datetime.now()
                timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
                log_filename = f"backtrace_logs/{timestamp}"

                with open(log_filename, "w") as file:
                    file.write(f"Error occurred at {now}:\n")
                    traceback.print_exc(file=file)  # 将异常信息写入文件

    # 设置默认相似度
    def set_default_similar(self, evt, similar):
        # 设置相似度
        numeric_value_str = similar.replace('%', '')
        numeric_value = float(numeric_value_str) / 100.0
        self.check_similar = numeric_value
        json_file = self.key_setting_path
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                settings = json.load(file)
        except FileNotFoundError:
            now = datetime.now()
            timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
            log_filename = f"backtrace_logs/{timestamp}"
            with open(log_filename, "w") as file:
                file.write(f"Error occurred at {now}:\n")
                traceback.print_exc(file=file)  # 将异常信息写入文件
        except json.JSONDecodeError:
            now = datetime.now()
            timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
            log_filename = f"backtrace_logs/{timestamp}"
            with open(log_filename, "w") as file:
                file.write(f"Error occurred at {now}:\n")
                traceback.print_exc(file=file)  # 将异常信息写入文件
        # 更新相似度值
        if "else" in settings:
            settings["else"]["相似度"] = self.check_similar
        else:
            now = datetime.now()
            timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
            log_filename = f"backtrace_logs/{timestamp}"
            with open(log_filename, "w") as file:
                file.write(f"Error occurred at {now}:\n")
                file.write(f"Key disappear:'相似度' is not founded\n")

        # 将更新后的数据写回 JSON 文件
        try:
            with open(json_file, "w", encoding="utf-8") as file:
                json.dump(settings, file, ensure_ascii=False, indent=4)
        except IOError as e:
            now = datetime.now()
            timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
            log_filename = f"backtrace_logs/{timestamp}"
            with open(log_filename, "w") as file:
                file.write(f"Error occurred at {now}:\n")
                traceback.print_exc(file=file)  # 将异常信息写入文件

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
            except FileNotFoundError:
                now = datetime.now()
                timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
                log_filename = f"backtrace_logs/{timestamp}"

                with open(log_filename, "w") as file:
                    file.write(f"Error occurred at {now}:\n")
                    traceback.print_exc(file=file)  # 将异常信息写入文件
        else:
            try:
                os.makedirs(logs_path)
            except OSError as e:
                return
            now = datetime.now()
            timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
            log_filename = f"backtrace_logs/{timestamp}"

            with open(log_filename, "w") as file:
                file.write(f"Error occurred at {now}:\n")
                file.write(f"{logs_path} does not exist\n")
            subprocess.Popen(['explorer', logs_path])
        return

    # 设置xxx
    def scan_reopen_enter(self, evt, Tab, Parent, Ui):
        class_type = type(self)

    # 重新调用 __init__ 方法来重新构建对象
        new_instance = class_type.__new__(class_type)
        new_instance.__init__(tab=Tab)  # 调用初始化方法

        class_type2 = type(Tab)

    # 重新调用 __init__ 方法来重新构建对象
        new_instances = class_type2.__new__(class_type2)
        new_instances.__init__(parent=Parent,ui=Ui)  # 调用初始化方法

    # 设置随机偏移
    def set_random_offset(self, evt):
        return

    # 设置默认扫描方式
    def set_default_check(self, evt):
        return

    #设置扫描时间
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
        timeout_window.geometry("300x300")

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

    # 选择的图片地址显示出来
    def select_photo_show(self):
        address_select = self.tab.tk_select_box_photo_address.get()
        if address_select == "地址1":
            if self.selection1_address is not None:
                start_x, start_y, end_x, end_y = self.selection1_address
                self.tab.tk_label_photo_start_label.config(text=f"({start_x},{start_y})")
                self.tab.tk_label_photo_end_label.config(text=f"({end_x},{end_y})")
        elif address_select == "地址2":
            if self.selection2_address is not None:
                start_x, start_y, end_x, end_y = self.selection2_address
                self.tab.tk_label_photo_start_label.config(text=f"({start_x},{start_y})")
                self.tab.tk_label_photo_end_label.config(text=f"({end_x},{end_y})")
        elif address_select == "地址3":
            if self.selection3_address is not None:
                start_x, start_y, end_x, end_y = self.selection3_address
                self.tab.tk_label_photo_start_label.config(text=f"({start_x},{start_y})")
                self.tab.tk_label_photo_end_label.config(text=f"({end_x},{end_y})")
        elif address_select == "地址4":
            if self.selection4_address is not None:
                start_x, start_y, end_x, end_y = self.selection4_address
                self.tab.tk_label_photo_start_label.config(text=f"({start_x},{start_y})")
                self.tab.tk_label_photo_end_label.config(text=f"({end_x},{end_y})")

    # 更改地址参数的选项,让地址(x1,y1),(x2,y2)符合状态
    def address_change(self, address_select=None):
        if address_select is None:
            address_select = self.tab.tk_select_box_photo_address.get()
            start_address = self.tab.tk_label_photo_start_label.cget("text")
            end_address = self.tab.tk_label_photo_end_label.cget("text")
            if address_select == "地址1":
                start_x, start_y = map(int, start_address.strip('()').split(','))
                end_x, end_y = map(int, end_address.strip('()').split(','))
                self.selection1_address = [start_x, start_y, end_x, end_y]
                return self.selection1_address
            elif address_select == "地址2":
                start_x, start_y = map(int, start_address.strip('()').split(','))
                end_x, end_y = map(int, end_address.strip('()').split(','))
                self.selection2_address = [start_x, start_y, end_x, end_y]
                return self.selection2_address
            elif address_select == "地址3":
                start_x, start_y = map(int, start_address.strip('()').split(','))
                end_x, end_y = map(int, end_address.strip('()').split(','))
                self.selection3_address = [start_x, start_y, end_x, end_y]
                return self.selection3_address
            elif address_select == "地址4":
                start_x, start_y = map(int, start_address.strip('()').split(','))
                end_x, end_y = map(int, end_address.strip('()').split(','))
                self.selection4_address = [start_x, start_y, end_x, end_y]
                return self.selection4_address
        else:
            if address_select == "地址1":
                return self.selection1_address
            elif address_select == "地址2":
                return self.selection2_address
            elif address_select == "地址3":
                return self.selection3_address
            elif address_select == "地址4":
                return self.selection4_address

    # 保存框选的地址
    def select_photo_save(self, evt):
        # 保存对应地址1~4的函数
        self.address_change()
        self.save_photos()

    # 根据位置来读取照片
    def load_target_image(self,path,place):
        try:
            target_image = Image.open(path)
        except:
            if not path or path.strip() == "":  # 检查字符串是否为空或None
                self.result_check[place] = '是'  # 设置结果为 "是"
                return None  # 返回 None 表示没有有效的内容
            else:
                return path
        target_image = np.array(target_image)
        return target_image

    #比对图片相似度,确认是否是符合要求的
    def compare_images_with_template_matching(self, image1, image2, address_content):
        # 比较图片的算法
        # 将图像转换为灰度图
        try:
            gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
            gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        except cv2.error as e:
            print(e)
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
            self.max_loc = (top_left, bottom_right)
            return True  # 图片相似
        else:
            return False  # 图片不相似

    # 文字移动
    def blink_text(self, label, text, delay=800):
        if self.scanning and not self.result_found:  # 确保闪烁只在扫描时进行
            label.config(background="#007bff")
            full_text = text + "\u3000"
            scroll_text = (full_text + full_text)[self.scroll_offset:self.scroll_offset + len(text)]
            label.config(text=scroll_text)  # 更新Label内容
            self.scroll_offset = (self.scroll_offset + 1) % len(full_text)  # 偏移量自增
            self.ui.after(delay, lambda: self.blink_text(label, text, delay))
            self.blink = True

    #扫描循环(此处是进行扫描的核心代码)
    def scan_loop(self, target_image, photo_address, chosen_index, max_loops):
        # 检查地址内容
        address_content = self.address_change(address_select=photo_address)
        screenshot=None
        if address_content == [0, 0, 0, 0]:
            self.tab.tk_label_scanning_state_label.config(text="地址无效")
            self.ui.after(2500, self.stop_scanning())
            return
        if self.scanning and (max_loops is None or max_loops > 0):
            self.tab.tk_button_start_scanning_button.configure(text="关闭扫描")
            x1, y1, x2, y2 = address_content
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            screen_region = np.array(screenshot)
            byte_io = io.BytesIO()
            screenshot.save(byte_io, format='PNG')
            image_bytes = byte_io.getvalue()
            # 判断target_image类型,如果是图片(numpy.ndarray)则进行图像处理,否则进行OCR识别
            if isinstance(target_image, np.ndarray):
                result = self.compare_images_with_template_matching(screen_region, target_image, address_content)
                if result:
                    self.result_found = True
                    self.tab.tk_label_scanning_state_label.config(text="扫描成功", background="#007bff")
                    self.scroll_offset = 0
                    self.blink = False
                    self.result_check[chosen_index] = "是"
                else:
                    self.result_found = False
                    self.result_check[chosen_index] = "否"
                    if not self.blink:
                        self.blink_text(self.tab.tk_label_scanning_state_label, "未扫描到结果")
            else:
                self.start_ocr_loading()  # 如果OCR模型还未加载,启动加载
                ocr_result = None
                try:
                    ocr_result = self.ocr.runBytes(image_bytes)
                except Exception as e:
                    ocr_result = None

                if ocr_result and isinstance(ocr_result, dict) and 'data' in ocr_result and isinstance(ocr_result['data'], list):
                    # 获取识别的文字
                    recognized_text = "".join([item['text'] for item in ocr_result['data']])
                    expected_text = target_image  # 你的目标文字(根据实际需求修改)
                    if expected_text.strip() in recognized_text.strip():  # 判断识别文字是否包含目标文字
                        self.result_found = True
                        self.scroll_offset = 0
                        self.blink = False
                        self.tab.tk_label_scanning_state_label.config(text="文字识别成功", background="#007bff")
                        self.result_check[chosen_index] = "是"
                    else:
                        self.result_found = False
                        self.result_check[chosen_index] = "否"
                        if not self.blink:
                            self.blink_text(self.tab.tk_label_scanning_state_label, "未识别到正确文字")
                else:
                    self.result_found = False
                    self.result_check[chosen_index] = "否"
                    if not self.blink:
                        self.blink_text(self.tab.tk_label_scanning_state_label, "未识别到文字")

            if self.photo_if == "all":
                current_scan_result = self.previous_scan_result
                # 如果是 "all"，要求 result_check 所有项都是 "是"
                if self.result_check == ["是", "是", "是", "是"]:
                    self.previous_scan_result=True
                    self.execute_operations()
                    if self.previous_scan_result != current_scan_result and self.execution_method == "scan_changed":
                        self.execution_count += 1
                else:
                    self.previous_scan_result=False
            elif self.photo_if == "one":
                # 如果是 "one"，只要有一个是 "是" 就满足
                if "是" in self.result_check:
                    self.previous_scan_result=True
                    self.execute_operations()
                    if self.previous_scan_result != current_scan_result and self.execution_method == "scan_changed":
                        self.execution_count += 1
                else:
                    self.previous_scan_result=False
            # 关闭截图资源
            screenshot.close()

            # 更新扫描时间和扫描次数
            self.time_count = (time.time() - self.start_time).__round__(2)
            if self.time_limit:
                self.tab.tk_label_operation_timeout_limit.config(text=f"定时{self.time_limit}秒结束"+
                                                                f"\n还剩下{int(self.time_limit-self.time_count)} 秒")
                if self.time_count >= self.time_limit:
                    self.tab.tk_label_operation_timeout_limit.config(text="定时结束,已停止扫描")
                    self.stop_scanning()  # 达到定时停止时间，停止扫描

            self.scan_count += 1
            if self.scan_limit:
                self.tab.tk_label_operation_timeout_limit.config(text=f"预计扫描{self.scan_limit}次"+
                                                                f"\n还剩下{self.scan_limit-self.scan_count} 次")
                if self.scan_count >= self.scan_limit:
                    self.tab.tk_label_operation_timeout_limit.config(text="次数到达,已停止扫描")
                    self.stop_scanning()  # 达到扫描次数限制，停止扫描

            # 调整循环次数
            if max_loops is not None:
                max_loops -= 1

            # 继续循环扫描
            if max_loops is None or max_loops > 0:
                self.ui.after(self.scan_interval, lambda: self.scan_loop(target_image, photo_address, chosen_index, max_loops))
            else:
                self.stop_scanning()

    # 框选/截图窗口代码
    def open_manual_selection_window(self, evt, grab_photo=False):
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
            self.manual_select_mode = False  # 退出手动框选模式
            self.tab.tk_label_photo_start_label.config(text=f"({self.start_x},{self.start_y})")
            self.tab.tk_label_photo_end_label.config(text=f"({self.end_x},{self.end_y})")
            self.manual_selection_coordinates = (
                self.start_x, self.start_y, self.end_x, self.end_y)  # Store the coordinates
                    # 检查并自动将图片地址移动到 selection1_address ~ selection4_address
            if self.selection1_address == [0, 0, 0, 0]:
                self.selection1_address = [self.start_x, self.start_y, self.end_x, self.end_y]
                self.tab.tk_select_box_photo_address.set("地址1")  # 更新地址显示
                self.select_photo_save(evt)
            elif self.selection2_address == [0, 0, 0, 0]:
                self.selection2_address = [self.start_x, self.start_y, self.end_x, self.end_y]
                self.tab.tk_select_box_photo_address.set("地址2")  # 更新地址显示
                self.select_photo_save(evt)
            elif self.selection3_address == [0, 0, 0, 0]:
                self.selection3_address = [self.start_x, self.start_y, self.end_x, self.end_y]
                self.tab.tk_select_box_photo_address.set("地址3")  # 更新地址显示
                self.select_photo_save(evt)
            elif self.selection4_address == [0, 0, 0, 0]:
                self.selection4_address = [self.start_x, self.start_y, self.end_x, self.end_y]
                self.tab.tk_select_box_photo_address.set("地址4")  # 更新地址显示
                self.select_photo_save(evt)
            self.manual_selection_window.destroy()
            if grab_photo:  # 如果需要截图
                x1, y1 = min(self.start_x, self.end_x), min(self.start_y, self.end_y)
                x2, y2 = max(self.start_x, self.end_x), max(self.start_y, self.end_y)
                self.manual_selection_coordinates = (
                    self.start_x - 5, self.start_y - 5, self.end_x + 5, self.end_y + 5)
                # 在对应位置产生截图
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                # 要求用户选择路径保存截图
                file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg")])
                if file_path:  # 如果用户选择了路径
                    screenshot.save(file_path)  # 保存截图
                    self.tab.tk_input_photo1_text.delete(0, tk.END)
                    self.tab.tk_input_photo1_text.insert(0, file_path)

            self.ui.deiconify()  # 恢复最小化的之前的界面
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


#操作添加窗口代码,为操作添加代码提供可视化窗口,用户在窗口添加参数,代码将参数处理并传递给添加操作代码,将操作添加到operations中

    #添加开始操作窗口
    def add_start_operation_window(self, position):
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

            self.operations.insert(position, f"开启:{chosen_index}号扫描{loop_count}次")
            self.save_operations()
            self.populate_operation_list()
            start_window.destroy()

        confirm_button = tk.Button(start_window, text="确定", command=confirm_selection)
        confirm_button.pack(pady=5)

    # 添加等待操作窗口
    def add_close_operation_window(self, position):
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
            self.operations.insert(position, f"关闭:{chosen_index}号扫描")
            self.save_operations()
            self.populate_operation_list()
            close_window.destroy()

        confirm_button = tk.Button(close_window, text="确定", command=confirm_selection)
        confirm_button.pack(pady=5)

    # 添加拖动操作窗口
    def add_drag_operation_window(self, position):
        # 弹出选择操作类型的面板
        self.ui.iconify()

        # 创建选择操作类型的窗口
        selection_window = tk.Toplevel(self.ui)
        selection_window.title("选择操作类型")
        selection_window.geometry("300x150")

        # 选择拖动或移动
        move_type = tk.StringVar(value="drag")  # 默认选项为拖动

        # 选择曲线或直线
        line_type = tk.StringVar(value="curve")  # 默认选项为曲线

        # 创建 Radiobutton 来选择曲线/直线
        curve_button = tk.Radiobutton(selection_window, text="绘制曲线(速度慢)", variable=line_type, value="curve")
        curve_button.pack(pady=5)

        line_button = tk.Radiobutton(selection_window, text="绘制直线(速度快)", variable=line_type, value="line")
        line_button.pack(pady=5)

        # 创建按钮来选择拖动/移动
        def on_drag_select():
            move_type.set("drag")
            self.create_drag_window(position, move_type.get(), line_type.get())
            selection_window.destroy()

        def on_move_select():
            move_type.set("move")
            self.create_drag_window(position, move_type.get(), line_type.get())
            selection_window.destroy()

        button_frame = tk.Frame(selection_window)
        button_frame.pack(pady=10)

        drag_button = tk.Button(button_frame, text="拖动(鼠标按下)", command=on_drag_select)
        drag_button.pack(side=tk.LEFT,padx=20)

        move_button = tk.Button(button_frame, text="移动(鼠标不按)", command=on_move_select)
        move_button.pack(side=tk.LEFT,padx=20)
        selection_window.focus_set()

    def create_drag_window(self, position, move_type, line_type):
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
            self.operations.insert(position, f"拖动:{duration}-{move_type}-{simplified_points}")
            self.save_operations()
            self.populate_operation_list()

            self.ui.deiconify()
            time.sleep(0.2)
            drag_window.destroy()

        drag_window.bind("<Button-1>", record_start_position)  # 记录起始位置
        drag_window.bind("<B1-Motion>", draw_drag_line)  # 绘制拖动曲线
        drag_window.bind("<ButtonRelease-1>", record_end_position)  # 记录结束位置

        drag_window.focus_set()

    # 添加寻路操作窗口
    def add_pathfinding_operation_window(self, position):
        # 打开自动寻路窗口并且记录寻路位置偏差
        pathfinding_window = tk.Toplevel(self.ui)
        pathfinding_window.title("自动寻路")
        pathfinding_window.geometry("300x200")
        pathfinding_window.lift()
        pathfinding_window.focus_set()

        def validate_input(entry):
            if entry.isdigit() or (entry.startswith('-') and entry[1:].isdigit()):
                return True
            else:
                return False

        def handle_confirm_click(x_entry, y_entry):
            if validate_input(x_entry.get()) and validate_input(y_entry.get()):
                x_value = int(x_entry.get())
                y_value = int(y_entry.get())
                # 将寻路操作加入operations
                self.operations.insert(position, f"寻路:{(x_value, y_value)}")
                self.save_operations()
                self.populate_operation_list()
                pathfinding_window.destroy()

        x_label = tk.Label(pathfinding_window, text="x(正值为＋):")
        x_label.pack(pady=5)
        x_entry = tk.Entry(pathfinding_window)
        x_entry.pack(pady=5)

        y_label = tk.Label(pathfinding_window, text="y(正值为＋):")
        y_label.pack(pady=5)
        y_entry = tk.Entry(pathfinding_window)
        y_entry.pack(pady=5)

        pathfinding_button = tk.Button(pathfinding_window, text="确认",
                                        command=lambda: handle_confirm_click(x_entry, y_entry))
        pathfinding_button.pack(pady=5)

    # 添加等待操作窗口
    def add_wait_operation_window(self, position):
        # 打开等待时间窗口并记录等待时间
        wait_window = tk.Toplevel(self.ui)
        wait_window.title("等待时间")
        wait_window.geometry("300x150")
        wait_window.lift()
        wait_window.focus_set()

        wait_label = tk.Label(wait_window, text="请输入等待时间(毫秒)：")
        wait_label.pack(pady=5)

        wait_entry = tk.Entry(wait_window)
        wait_entry.pack(pady=5)

        def confirm_wait():
            wait_time = int(wait_entry.get())
            # 直接在这里处理等待操作,避免调用额外的函数
            self.operations.insert(position, f"等待:{wait_time}ms")
            self.save_operations()
            self.populate_operation_list()
            wait_window.destroy()

        wait_button = tk.Button(wait_window, text="确认", command=confirm_wait)
        wait_button.pack(pady=5)

    # 添加滚轮操作窗口
    def add_scroll_operation_window(self, position):
        # 打开滚轮窗口并记录滚轮步数
        scroll_steps = 0
        scroll_window = tk.Toplevel(self.ui)
        scroll_window.title("滚轮操作")
        scroll_window.geometry("300x200")
        scroll_window.lift()
        scroll_window.focus_set()

        scroll_label = tk.Label(scroll_window, text="请输入滚轮步数(正数向上)：")
        scroll_label.pack(pady=5)

        scroll_entry = tk.Entry(scroll_window)
        scroll_entry.pack(pady=5)

        def confirm_scroll():
            scroll_time = int(scroll_entry.get())
            # 直接在这里处理滚轮操作,避免调用额外的函数
            self.operations.insert(position, f"滚轮:{scroll_time}步")
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

    #添加键盘操作窗口
    def add_keyboard_operation_window(self, position):
        # 打开键盘窗口并记录下一个按下的按键
        keyboard_window = tk.Toplevel(self.ui)
        keyboard_window.title("键盘操作")
        keyboard_window.geometry("340x260")  # 增加窗口高度以容纳所有内容
        keyboard_window.lift()
        keyboard_window.focus_set()

        input_frame = tk.Frame(keyboard_window)
        input_frame.pack(pady=5)

        input_label = tk.Label(input_frame, text="键：")
        input_label.pack(side=tk.LEFT, padx=3)

        input_entry = tk.Entry(input_frame, width=15)
        input_entry.pack(side=tk.LEFT, padx=5)

        # 添加选择模式
        mode_label = tk.Label(input_frame, text="选择按键模式：")
        mode_label.pack(side=tk.TOP, padx=5)

        mode_var = tk.StringVar(value="single")  # 默认为单点模式

        mode_frame = tk.Frame(input_frame)
        mode_frame.pack(side=tk.TOP, pady=5)

        # 使用pack以垂直方向排列
        mode_single = tk.Radiobutton(mode_frame, text="单点", variable=mode_var, value="single")
        mode_single.pack(side=tk.TOP, anchor="w")

        mode_multi = tk.Radiobutton(mode_frame, text="多按", variable=mode_var, value="multi")
        mode_multi.pack(side=tk.TOP, anchor="w")

        mode_long = tk.Radiobutton(mode_frame, text="长按", variable=mode_var, value="long")
        mode_long.pack(side=tk.TOP, anchor="w")

        mode_multi_long = tk.Radiobutton(mode_frame, text="多按长按", variable=mode_var, value="multi_long")
        mode_multi_long.pack(side=tk.TOP, anchor="w")

        # 将长按时间输入框移到mode_frame之外,放到input_frame的下方
        press_frame = tk.Frame(keyboard_window)
        press_frame.pack(pady=5)
        long_press_label = tk.Label(press_frame, text="长按时间(秒)：")
        long_press_label.pack(side=tk.LEFT, padx=5)

        long_press_entry = tk.Entry(press_frame, width=10)
        long_press_entry.pack(side=tk.LEFT, padx=5)
        self.key_bind = True

        def hand_input():
            if self.key_bind:
                # 如果已经绑定了事件,则解绑
                keyboard_window.unbind("<KeyPress>")
                keyboard_window.unbind("<KeyRelease>")
                self.key_bind = False  # 更新状态为未绑定
                clear_button.config(text="切换自动输入")
            else:
                # 如果没有绑定事件,则绑定
                keyboard_window.bind("<KeyPress>", record_key_press)
                keyboard_window.bind("<KeyRelease>", record_key_press)
                self.key_bind = True  # 更新状态为已绑定
                clear_button.config(text="切换手动输入")

        def confirm_input():
            key_sym = input_entry.get()
            long_press_time = long_press_entry.get()

            # 验证长按时间输入
            if mode_var.get() in ["long", "multi_long"] and not long_press_time:
                tk.messagebox.showwarning("警告", "请输入长按时间！")
                return

            if not key_sym:
                tk.messagebox.showwarning("警告", "请输入一个键后再确认！")
                return

            # 根据选择的模式构造传递的字符串
            if mode_var.get() == "single":
                # 单点模式
                formatted_keys = f"[{key_sym}]"
            elif mode_var.get() == "multi":
                # 多按模式
                pressed_keys = key_sym.split("+")  # 假设用户输入用 "+" 分隔的多个按键
                formatted_keys = "+".join([f"[{key}]" for key in pressed_keys])
            elif mode_var.get() == "long":
                # 长按模式
                formatted_keys = f"{long_press_time}秒-[{key_sym}]"
            elif mode_var.get() == "multi_long":
                # 多按长按模式
                pressed_keys = key_sym.split("+")  # 假设用户输入用 "+" 分隔的多个按键
                formatted_keys = f"{long_press_time}秒-{' + '.join([f'[{key}]' for key in pressed_keys])}"

            # 直接在这里处理键盘操作,避免调用额外的函数
            self.operations.insert(position, f"键盘操作:{formatted_keys}")
            self.save_operations()
            self.populate_operation_list()

            keyboard_window.destroy()

        button_frame = tk.Frame(keyboard_window)
        button_frame.pack(pady=10)

        confirm_button = tk.Button(button_frame, text="确定", command=confirm_input)
        confirm_button.pack(side=tk.LEFT, padx=10)

        clear_button = tk.Button(button_frame, text="切换手动输入", command=hand_input)
        clear_button.pack(side=tk.LEFT, padx=10)

        pressed_keys = []  # 用于存储当前按下的多个按键

        def record_key_press(event):
            key_sym = event.keysym

            # 根据选择的模式来决定如何记录
            if mode_var.get() in ["single", "long"]:
                if event.type == tk.EventType.KeyPress:
                    input_entry.delete(0, tk.END)
                    input_entry.insert(tk.END, key_sym)
                elif event.type == tk.EventType.KeyRelease:
                    pass

            elif mode_var.get() in ["multi", "multi_long"]:
                if event.type == tk.EventType.KeyPress:
                    if key_sym not in pressed_keys:
                        pressed_keys.append(key_sym)  # 记录按下的按键
                    input_entry.delete(0, tk.END)
                    input_entry.insert(tk.END, "+".join([f"{key}" for key in pressed_keys]))
                elif event.type == tk.EventType.KeyRelease:
                    if key_sym in pressed_keys:
                        pressed_keys.remove(key_sym)  # 释放时从记录中移除

        keyboard_window.bind("<KeyPress>", record_key_press)
        keyboard_window.bind("<KeyRelease>", record_key_press)

    # 添加鼠标操作窗口
    def add_mouse_operation_window(self, position):
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

            # 单击、双击、长按选项
            operation_var = tk.StringVar(value="single")  # 默认选择单击
            click_options = [("单击", "single"), ("双击", "double"), ("长按", "long_press")]
            for text, value in click_options:
                rb = tk.Radiobutton(input_frame, text=text, variable=operation_var, value=value)
                rb.pack()

            # 长按时输入长按时间
            press_time_label = tk.Label(input_frame, text="长按时间(秒)：")
            press_time_label.pack(pady=5)
            press_time_entry = tk.Entry(input_frame)
            press_time_entry.insert(0, "1")  # 默认1秒
            press_time_entry.pack(pady=5)

            # 清空和确认按钮
            def clear_input():
                click_position_var.set("")  # 清空点击位置
                press_time_entry.delete(0, tk.END)
                press_time_entry.insert(0, "1")
                operation_var.set("single")

            def is_valid_operation_format(operation_text):
                """
                验证用户输入的操作格式是否符合规定的格式
                """
                # 定义正则表达式
                # 格式：左键-单击-(x,y) 或 左键-长按【时间】秒-(x,y)
                valid_format = re.compile(r"(左键|右键|中键)-(单击|双击|长按【\d+】秒)-\(\d+, \d+\)")
                return valid_format.match(operation_text)

            def confirm_input():
                operation = click_position_var.get()

                # 检查操作格式是否有效
                if not is_valid_operation_format(operation):
                    tk.messagebox.showwarning("警告", "输入的操作格式不正确,请按规则输入！")
                    return
                # 将鼠标操作加入operations
                self.operations.insert(position, f"鼠标操作:{operation}")
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
                    operation = operation_var.get()

                    if event.num == 1:  # 左键
                        click_position = f"左键"
                    elif event.num == 2:  # 中键
                        click_position = f"中键"
                    elif event.num == 3:  # 右键
                        click_position = f"右键"

                    # 根据操作类型修改点击描述
                    if operation == "single":
                        click_position += f"-单击"
                    elif operation == "double":
                        click_position += f"-双击"
                    elif operation == "long_press":
                        press_time = press_time_entry.get()  # 获取长按时间
                        click_position += f"-长按【{press_time}】秒"
                    click_position += f"-({event.x}, {event.y})"

                    # 更新已有窗口中的点击位置
                    click_position_var.set(click_position)
                    position_window.destroy()  # 关闭蒙版窗口
                    mouse_window.deiconify()

                # 绑定鼠标点击事件
                position_window.bind("<Button-1>", record_click_position)  # 左键
                position_window.bind("<Button-2>", record_click_position)  # 中键
                position_window.bind("<Button-3>", record_click_position)  # 右键

            # 按钮区域
            button_frame = tk.Frame(mouse_window)
            button_frame.pack(pady=10)

            confirm_button = tk.Button(button_frame, text="确认", command=confirm_input)
            confirm_button.pack(side=tk.LEFT, padx=5)

            clear_button = tk.Button(button_frame, text="清空", command=clear_input)
            clear_button.pack(side=tk.LEFT, padx=5)

            # 改为录制点击位置
            record_button = tk.Button(button_frame, text="录制点击位置", command=record_click)
            record_button.pack(side=tk.LEFT, padx=5)

            # 返回窗口和相关的组件
            return mouse_window, click_position_var, click_position_entry

        # 初始化鼠标操作窗口
        mouse_window, click_position_var, click_position_entry = open_mouse_operation_window("", position)  # 初始时点击位置为空

    # 执行操作函数
    def execute_operations(self):
        for operation in self.operations:
            if operation.startswith("等待"):
                wait_time = int(operation.split(":")[1].strip("ms"))
                time.sleep(wait_time / 1000)  # Convert milliseconds to seconds and wait
            elif operation.startswith("寻路"):
                pathfinding_loc = (operation.split(":")[1])
                path = eval(pathfinding_loc)
                max_loc = self.max_loc
                center_x = int((max_loc[0][0] + max_loc[1][0]) / 2)
                center_y = int((max_loc[0][1] + max_loc[1][1]) / 2)
                # offset_x = random.randint(-1, 1)
                # offset_y = random.randint(-1, 1)
                offset_x = 0
                offset_y = 0
                pyautogui.click(center_x + int(path[0]) + offset_x, center_y + int(path[1]) + offset_y)
            elif operation.startswith("滚轮"):
                scroll_time = int(operation.split(":")[1].strip("步"))
                pyautogui.scroll(scroll_time)  # 执行滚轮
            elif operation.startswith("键盘操作"):
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
                # 分割操作类型和按键信息
                operation_details = operation.split(":")
                if len(operation_details) == 2:
                    key_info = operation_details[1]  # 获取按键信息部分,例如 10秒-[Shift]+[Ctrl]

                    # 如果包含 "秒" 则是长按模式
                    if "秒" in key_info:
                        # 解析长按时间和按键
                        long_press_time, keys = key_info.split("-")
                        long_press_time = int(long_press_time.replace("秒", "").strip())  # 提取长按时间

                        # 处理按键,如果是多按,则按下每个按键
                        if "+" in keys:
                            pressed_keys = keys.split("+")
                            # 使用映射后的键名同时按下每个按键
                            pyautogui.hotkey(*[key_map.get(key.strip("[]"), key.strip("[]")) for key in pressed_keys])  # 按下所有组合键
                            time.sleep(long_press_time)  # 持续按键的时间
                        else:
                            # 单个按键的长按
                            pyautogui.keyDown(key_map.get(keys.strip("[]"), keys.strip("[]")))  # 长按键
                            time.sleep(long_press_time)  # 按键长按的时间
                            pyautogui.keyUp(key_map.get(keys.strip("[]"), keys.strip("[]")))  # 释放键
                    else:
                        # 多按模式
                        if "+" in key_info:
                            pressed_keys = key_info.split("+")
                            # 使用映射后的键名同时按下每个按键
                            pyautogui.hotkey(*[key_map.get(key.strip("[]"), key.strip("[]")) for key in pressed_keys])  # 按下所有组合键
                        else:
                            pyautogui.press(key_map.get(key_info.strip("[]"), key_info.strip("[]")))  # 单个按键
            elif operation.startswith("鼠标操作"):
                operation_desc = operation.split(":")[1]  # 获取 "左键-长按【10】秒-(1517,269)"
                # 提取按钮类型和操作部分
                click_type, action = operation_desc.split("-")[:2]  # 分割得到 "左键" 和 "长按【10】秒"
                # 判断是否为长按,提取时间信息
                if "长按" in action:
                    press_time = action.split("【")[1].split("】")[0]  # 获取按压时间(例如 10)
                    action_type = "long_press"
                elif "双击" in action:
                    press_time = None  # 双击不需要按压时间
                    action_type = "double"
                else:
                    press_time = None  # 单击也不需要按压时间
                    action_type = "single"
                # 提取坐标部分
                position = operation_desc.split("-")[-1].strip("()")
                x, y = map(int, position.split(","))  # 获取坐标
                # 偏移量(如果需要)
                offset_x = 0
                offset_y = 0
                # offset_x = random.randint(-1, 1)
                # offset_y = random.randint(-1, 1)
                # 执行相应的鼠标操作
                if click_type == "左键":
                    if action_type == "single":
                        pyautogui.click(x + offset_x, y + offset_y)
                    elif action_type == "double":
                        pyautogui.doubleClick(x + offset_x, y + offset_y, interval=0.1)
                    elif action_type == "long_press":
                        pyautogui.mouseDown(x + offset_x, y + offset_y)
                        pyautogui.sleep(float(press_time))  # 按压一段时间
                        pyautogui.mouseUp(x + offset_x, y + offset_y)
                elif click_type == "右键":
                    if action_type == "single":
                        pyautogui.rightClick(x + offset_x, y + offset_y)
                    elif action_type == "double":
                        pyautogui.rightDoubleClick(x + offset_x, y + offset_y, interval=0.1)
                    elif action_type == "long_press":
                        pyautogui.mouseDown(x + offset_x, y + offset_y, button='right')
                        pyautogui.sleep(float(press_time))  # 按压一段时间
                        pyautogui.mouseUp(x + offset_x, y + offset_y, button='right')
                elif click_type == "中键":
                    if action_type == "single":
                        pyautogui.middleClick(x + offset_x, y + offset_y)
                    elif action_type == "double":
                        pyautogui.middleDoubleClick(x + offset_x, y + offset_y, interval=0.1)
                    elif action_type == "long_press":
                        pyautogui.mouseDown(x + offset_x, y + offset_y, button='middle')
                        pyautogui.sleep(float(press_time))  # 按压一段时间
                        pyautogui.mouseUp(x + offset_x, y + offset_y, button='middle')
            elif operation.startswith("开启"):
                chosen_index = int(operation.split("号扫描")[0].strip("开启："))
                loop_count_string = operation.split("号扫描")[1].split("次")[0].strip()
                loop_count = int(loop_count_string) if loop_count_string and loop_count_string != 'None' else None
                self.tab.tk_tabs_first_tab.select(chosen_index)  # 选择对应的标签页
                selected_child_frame = self.tab.tk_tabs_first_tab.nametowidget(self.tab.tk_tabs_first_tab.select())
                if loop_count == 1:
                    selected_child_frame.loop_var.set("循环1次")
                elif loop_count == 10:
                    selected_child_frame.loop_var.set("循环10次")
                elif loop_count is None:
                    selected_child_frame.loop_var.set("无限循环")
                selected_child_frame.start_scanning()
            elif operation.startswith("关闭"):
                chosen_index = int(operation.split(":")[1].strip("号扫描"))
                self.ui.tk_tabs_first_tab.select(chosen_index)
                selected_child_frame = self.tab.tk_tabs_first_tab.nametowidget(self.tab.tk_tabs_first_tab.select())
                selected_child_frame.stop_scanning()
                selected_child_frame.scanning_status_label.config(text="未开始扫描")
            elif operation.startswith("拖动"):
                # 获取拖动时长和坐标信息
                operation_data = operation.split(":")[1]  # 获取"拖动:{duration}-{move_type}-{points}"
                duration_str, move_type, points_str = operation_data.split("-")  # 分离时长和坐标
                duration = float(duration_str)  # 将时长转换为浮动类型
                positions = eval(points_str)  # 获取拖动的坐标信息并转换为元组
                # 计算每个点之间的持续时间
                num_points = len(positions)
                time_per_move = round(duration / (num_points - 1),3)*2  # 每次移动的时间
                # 如果 positions 里面有多个点,按顺序进行逐步移动
                if move_type == "drag":
                    # 如果是拖动,按下鼠标并进行拖动
                    pyautogui.moveTo(positions[0][0], positions[0][1], duration=0.001)
                    pyautogui.mouseDown()  # 模拟按下鼠标(开始拖动)
                    for i in range(0, num_points, 2):  # 每隔一个点选择一次
                        if i + 1 < num_points:
                            pyautogui.moveTo(positions[i + 1][0], positions[i + 1][1], duration=time_per_move)  # 每次移动时间
                    # 最后释放鼠标(结束拖动)
                    pyautogui.mouseUp()
                elif move_type == "move":
                    # 如果是移动,不按下鼠标也不抬起鼠标
                    pyautogui.moveTo(positions[0][0], positions[0][1], duration=0.001)
                    for i in range(0, num_points, 2):  # 每隔一个点选择一次
                        if i + 1 < num_points:
                            pyautogui.moveTo(positions[i + 1][0], positions[i + 1][1], duration=time_per_move)


        if self.execution_method == "script_done":
            self.execution_count += 1 # 记录执行成功次数

        self.tab.tk_label_operation_times.config(text=f"运行完成{self.execution_count}次")

        if self.execution_limit:
            self.tab.tk_label_operation_timeout_limit.config(text=f"预计执行{self.execution_limit}次"+
                                                            f"\n还剩下{self.execution_limit-self.execution_count} 次")
            if self.execution_count >= self.execution_limit:
                self.tab.tk_label_operation_timeout_limit.config(text="次数到达,已停止扫描")
                self.stop_scanning()  # 达到扫描次数限制，停止扫描
        pass

    # 读取给定文件路径下的内容并且加入自己的self.operations中
    def load_operations(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = file.read()
                if not data:  # 检查数据是否为空
                    return []
                else:
                    data = json.loads(data)
                    operation_names = [data.get(str(key), {}).get("operation_name", "") for key in data if
                                        key.isdigit()]
                    return operation_names
        except FileNotFoundError:
            return []

    # 读取给定data中的内容并且加入自己的self.operations中
    def load_data_operations(self, data):
        operation_names = []
        for item in data:
            for key, value in item.items():
                if isinstance(value, dict) and "operation_name" in value:
                    operation_names.append(value["operation_name"])
        self.operations = operation_names
        self.save_operations()

    # 将默认的操作信息加入cache缓存
    def add_default_operations(self):
        try:
            with open(self.default_file_path, "r",encoding = "utf-8") as file:
                data = file.read()
                if not data:  # 检查数据是否为空
                    self.operations = []
                else:
                    data = json.loads(data)
                    operation_names = [data.get(str(key), {}).get("operation_name", "") for key in data if
                                        key.isdigit()]
                    self.operations = operation_names
        except FileNotFoundError:
            self.operations = []
        self.save_operations()

    # 将默认的图片信息加入cache缓存
    def add_default_photos(self):
        with open(self.photo_path, "w") as json_file:
            with open(self.default_photo_path, "r", encoding='utf-8') as default_file:
                data = json.load(default_file)  # 读取位于setting_json/default_photo.json中的默认图片信息
            json.dump(data, json_file)  # 写入缓存

    # 保存操作列表到file_path(写入cache)的位置
    def save_operations(self):
        with open(self.file_path, "w") as json_file:
            data = {}
            i = 0
            for operation in self.operations:
                operation_index = i
                operation_name = operation
                data[i] = {"operation_index": operation_index, "operation_name": operation_name}
                i = i + 1
            json.dump(data, json_file)

    # 保存图片信息到file_path(写入cache)的位置
    def save_photos(self, default_photo=None , getdata=None):
        data = {
                "地址1": self.selection1_address,
                "地址2": self.selection2_address,
                "地址3": self.selection3_address,
                "地址4": self.selection4_address,
                "图片1的位置": self.tab.tk_input_photo1_text.get(),
                "图片2的位置": self.tab.tk_input_photo2_text.get(),
                "图片3的位置": self.tab.tk_input_photo3_text.get(),
                "图片4的位置": self.tab.tk_input_photo4_text.get(),
                "图片1的地址": self.tab.tk_select_box_photo1_scan_box.get(),
                "图片2的地址": self.tab.tk_select_box_photo2_scan_box.get(),
                "图片3的地址": self.tab.tk_select_box_photo3_scan_box.get(),
                "图片4的地址": self.tab.tk_select_box_photo4_scan_box.get(),
                "满足方式": self.tab.photo_if_var.get()
                }
        if default_photo is None:
            write_path = self.photo_path
        else:
            write_path = default_photo
        if getdata is not None:
            return data
        # 保存图片信息到图片缓存cache中
        with open(write_path, "w") as json_file:
            json.dump(data, json_file)

    # 打印操作列表到面板
    def populate_operation_list(self):
        self.tab.tk_table_operation_box.delete(*self.tab.tk_table_operation_box.get_children())  # Clear the table
        # 遍历操作列表,逐行插入数据
        for i, operation in enumerate(self.operations, start=1):
            operation_name = operation[:2]  # 获取操作名,取前两个字
            self.tab.tk_table_operation_box.insert("", i, values=(i, operation_name, operation))

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
            self.selection1_address = data.get("地址1", [0, 0, 0, 0])
            self.selection2_address = data.get("地址2", [0, 0, 0, 0])
            self.selection3_address = data.get("地址3", [0, 0, 0, 0])
            self.selection4_address = data.get("地址4", [0, 0, 0, 0])

            self.tab.tk_input_photo1_text.delete(0, "end")
            self.tab.tk_input_photo1_text.insert(0, data.get("图片1的位置", ""))
            self.tab.tk_input_photo2_text.delete(0, "end")
            self.tab.tk_input_photo2_text.insert(0, data.get("图片2的位置", ""))
            self.tab.tk_input_photo3_text.delete(0, "end")
            self.tab.tk_input_photo3_text.insert(0, data.get("图片3的位置", ""))
            self.tab.tk_input_photo4_text.delete(0, "end")
            self.tab.tk_input_photo4_text.insert(0, data.get("图片4的位置", ""))

            self.tab.tk_select_box_photo1_scan_box.set(data.get("图片1的地址", "地址1"))
            self.tab.tk_select_box_photo2_scan_box.set(data.get("图片2的地址", "地址1"))
            self.tab.tk_select_box_photo3_scan_box.set(data.get("图片3的地址", "地址1"))
            self.tab.tk_select_box_photo4_scan_box.set(data.get("图片4的地址", "地址1"))
            self.tab.photo_if_var.set(data.get("满足方式", "all"))

            self.select_photo_show()

        except (IOError, json.JSONDecodeError, KeyError) as e:
            # 如果json内部键值错误
            self.selection1_address = [0, 0, 0, 0]
            self.selection2_address = [0, 0, 0, 0]
            self.selection3_address = [0, 0, 0, 0]
            self.selection4_address = [0, 0, 0, 0]
            self.tab.tk_input_photo1_text.delete(0, "end")
            self.tab.tk_input_photo1_text.insert(0, "")
            self.tab.tk_input_photo2_text.delete(0, "end")
            self.tab.tk_input_photo2_text.insert(0, "")
            self.tab.tk_input_photo3_text.delete(0, "end")
            self.tab.tk_input_photo3_text.insert(0, "")
            self.tab.tk_input_photo4_text.delete(0, "end")
            self.tab.tk_input_photo4_text.insert(0, "")

            self.tab.tk_select_box_photo1_scan_box.set("地址1")
            self.tab.tk_select_box_photo2_scan_box.set("地址1")
            self.tab.tk_select_box_photo3_scan_box.set("地址1")
            self.tab.tk_select_box_photo4_scan_box.set("地址1")
            self.tab.photo_if_var.set("all")

            self.select_photo_show()

    # 相似度读取与写入
    def similar_bind(self):
        json_file = self.key_setting_path
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                settings = json.load(file)
        except FileNotFoundError:
            now = datetime.now()
            timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
            log_filename = f"backtrace_logs/{timestamp}"
            with open(log_filename, "w") as file:
                file.write(f"Error occurred at {now}:\n")
                traceback.print_exc(file=file)  # 将异常信息写入文件
        # 获取相似度值
        if "else" in settings and "相似度" in settings["else"]:
            self.check_similar = settings["else"]["相似度"]
        else:
            now = datetime.now()
            timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
            log_filename = f"backtrace_logs/{timestamp}"
            with open(log_filename, "w") as file:
                file.write(f"Error occurred at {now}:\n")
                file.write(f"Key disappear:'相似度' is not founded\n")



