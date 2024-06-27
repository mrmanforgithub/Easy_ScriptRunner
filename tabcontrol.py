import concurrent.futures
import json
import os
import random
import shutil
import time
import tkinter as tk
from tkinter import filedialog, ttk
import cv2
import keyboard
import numpy as np
import pyautogui
from PIL import Image, ImageGrab


class TabController:
    # 导入UI类后，替换以下的 object 类型，将获得 IDE 属性提示功能
    ui: object
    tab: object

    def __init__(self, tab):
        self.tab = tab
        self.operation_position = None
        self.operation_content = None
        self.keep_scanning = False
        self.sub_windows = []
        self.file_path = "operation_cache.json"  # 缓存文件，临时记录操作数据，关闭后清空
        self.photo_path = "photo_cache.json"  # 缓存文件，临时记录图片数据，关闭后清空
        self.operations = self.load_operations(self.file_path)
        if not self.operations:
            print("新建cache缓存文件")
            self.add_default_operations()
        self.max_loc = None

        self.image_path = None

        self.start_y = None  # 拖动框选的开始位置
        self.start_x = None
        self.end_y = None  # 拖动框选的开始位置
        self.end_x = None

        # 参数的初始化
        self.max_loops = None  # 扫描数量

        self.scanning = False  # 是否扫描

        self.manual_selection_coordinates = None  # 框选的扫描

        self.selection1_address = [0, 0, 0, 0]  # 四个不同的扫描地址
        self.selection2_address = [0, 0, 0, 0]
        self.selection3_address = [0, 0, 0, 0]
        self.selection4_address = [0, 0, 0, 0]

        self.result_check = ["是", "是", "是", "是"]  # 与或非的检查单

        self.grab_photo = False

        self.scan_pool = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        self.scan_futures = set()
        self.populate_operation_list()
        self.add_default_photos()
        self.populate_photo_address(self.photo_path)
        keyboard.on_press_key("esc", self.handle_escape)  # 监听全局的 "Escape" 键按下事件

    def init_ui(self, ui):
        """
        得到UI实例，对组件进行初始化配置
        """
        self.ui = ui
        # TODO 组件初始化 赋值操作

    def start_scanning(self, evt, max_loops=None):
        photo1_if = self.tab.tk_select_box_photo1_switch_box.get()
        photo2_if = self.tab.tk_select_box_photo2_switch_box.get()
        photo3_if = self.tab.tk_select_box_photo3_switch_box.get()
        photo4_if = self.tab.tk_select_box_photo4_switch_box.get()

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
            print("太多扫描正在同时运行了！")
            return
        if self.scanning:
            self.stop_scanning()
            return

        self.scanning = True
        if self.max_loops is not None:
            max_loops = self.max_loops

        self.tab.tk_label_scanning_state_label.config(text="扫描中")

        if photo1_image_path:
            self.result_check[0] = "否"
            target_image1 = self.load_target_image(photo1_image_path)
            future = self.scan_pool.submit(self.scan_loop, target_image1, photo1_if, photo1_address, 0, max_loops)
            self.scan_futures.add(future)
        if photo2_image_path:
            self.result_check[1] = "否"
            target_image2 = self.load_target_image(photo2_image_path)
            future = self.scan_pool.submit(self.scan_loop, target_image2, photo2_if, photo2_address, 1, max_loops)
            self.scan_futures.add(future)
        if photo3_image_path:
            self.result_check[2] = "否"
            target_image3 = self.load_target_image(photo3_image_path)
            future = self.scan_pool.submit(self.scan_loop, target_image3, photo3_if, photo3_address, 2, max_loops)
            self.scan_futures.add(future)
        if photo4_image_path:
            self.result_check[3] = "否"
            target_image4 = self.load_target_image(photo4_image_path)
            future = self.scan_pool.submit(self.scan_loop, target_image4, photo4_if, photo4_address, 3, max_loops)
            self.scan_futures.add(future)
        self.save_photos()

    def confirm_selection(self, evt, selection):
        if selection == "无限循环":
            self.max_loops = None
        elif selection == "循环1次":
            self.max_loops = 1
        elif selection == "循环10次":
            self.max_loops = 10
        print(self.max_loops)

    def confirm_address_selection(self, evt):
        self.select_photo_show()
        self.save_photos()

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

    def save_photo_context(self, evt):
        self.save_photos()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            # 复制文件到所选位置
            shutil.copyfile("photo_cache.json", file_path)
        print("保存图片位置到文件")

    def load_photo_context(self, evt):
        file_path = filedialog.askopenfilename(initialdir=os.path.dirname(self.file_path),
                                               initialfile=os.path.basename(self.file_path),
                                               title="读取操作列表",
                                               filetypes=(("Json files", "*.json"), ("All files", "*.*")))
        if file_path:
            self.populate_photo_address(file_path)
        print("从文件中读取具体图片位置")

    def operation_change(self, evt):
        print("修改操作列表")
        selected_item = self.tab.tk_table_operation_box.selection()
        if selected_item:
            selected_index = self.tab.tk_table_operation_box.index(selected_item[0])
            del self.operations[selected_index]
            self.operation_add(evt, operation_position=selected_index)
            self.save_operations()
            self.populate_operation_list()

    def operation_delete(self, evt):
        print("删除操作内容")
        selected_item = self.tab.tk_table_operation_box.selection()
        if selected_item:
            selected_index = self.tab.tk_table_operation_box.index(selected_item[0])
            del self.operations[selected_index]
            self.save_operations()
            self.populate_operation_list()

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

    def save_operation_context(self, evt):
        self.save_operations()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            # 复制文件到所选位置
            shutil.copyfile("operation_cache.json", file_path)
        print("保存操作信息到文件")

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
        print("从文件中读取具体操作信息")

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
        print("打开图片保存文件浏览窗口")

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
        print("打开操作保存文件浏览窗口")

    def scan_output_enter(self, evt):
        with open(self.tab.tk_input_scan_operation_text.get(), 'r') as operation_file:
            operation_data = json.load(operation_file)

        # 读取 photo_cache.json 文件
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
        print("输出组合内容")

    def set_default_photo(self, evt):
        print("设置默认图片")

    def set_default_operation(self, evt):
        print("设置默认操作")

    def scan_reopen_enter(self, evt):
        print("重启本次扫描")

    def start_grab_window(self, evt):
        print("打开框选窗口")
        self.open_manual_selection_window()

    def start_grab_photo_window(self, evt):
        self.grab_photo = True
        print("打开截图窗口")
        self.open_manual_selection_window()

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

    def select_photo_save(self, evt):
        selected_address = self.address_change()
        print(f"保存成功-{selected_address}")
        self.tab.tk_button_select_photo_show.config(text="成功")
        self.ui.after(1000, lambda: self.tab.tk_button_select_photo_show.config(text="显示"))
        self.save_photos()

    @staticmethod
    def take_screenshot():
        screenshot = ImageGrab.grab()
        return screenshot

    @staticmethod
    def load_target_image(path):  # 根据位置来读取照片
        target_image = Image.open(path)
        target_image = np.array(target_image)
        return target_image

    def compare_images_with_template_matching(self, image1, image2, address_content):
        # 将图像转换为灰度图
        gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        # 使用模板匹配
        result = cv2.matchTemplate(gray_image1, gray_image2, cv2.TM_CCOEFF_NORMED)

        # 获取最大和最小匹配值及其位置
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # 设置相似度阈值
        similarity_threshold = 0.75  # 通过调整阈值来判断相似度

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

    def stop_scanning(self):
        self.scanning = False
        for future in list(self.scan_futures):
            if not future.done():
                future.cancel()
                self.scan_futures.remove(future)
        self.tab.tk_label_scanning_state_label.after(100, lambda: self.tab.tk_label_scanning_state_label.config(
            text="未开始扫描"))
        self.tab.tk_button_start_scanning_button.configure(text="开始扫描")

    def scan_loop(self, target_image, photo_if, photo_address, chosen_index, max_loops):
        address_content = self.address_change(address_select=photo_address)
        if address_content == [0, 0, 0, 0]:
            self.tab.tk_label_scanning_state_label.config(text="地址无效")
            self.ui.after(2500, self.stop_scanning())
        if self.scanning and (max_loops is None or max_loops > 0):
            self.tab.tk_button_start_scanning_button.configure(text="关闭扫描")
            x1, y1, x2, y2 = address_content
            screenshot = self.take_screenshot()
            region = (x1, y1, x2, y2)
            screen_region = np.array(screenshot.crop(region))
            result = self.compare_images_with_template_matching(screen_region, target_image, address_content)
            if result:
                if photo_if == "与":
                    self.result_check[chosen_index] = "是"
                elif photo_if == "或":
                    self.result_check[chosen_index] = "是"
                elif photo_if == "非":
                    self.result_check[chosen_index] = "否"
                if self.result_check == ["是", "是", "是", "是"]:
                    self.execute_operations()
                self.tab.tk_label_scanning_state_label.config(text="扫描中")
            else:
                if photo_if == "与":
                    self.result_check[chosen_index] = "否"
                elif photo_if == "或":
                    if "是" in [item for index, item in enumerate(self.result_check) if index != chosen_index]:
                        self.result_check[chosen_index] = "是"
                    else:
                        self.result_check[chosen_index] = "否"
                elif photo_if == "非":
                    self.result_check[chosen_index] = "是"
            screenshot.close()

            if max_loops is not None:
                max_loops -= 1
            if max_loops is None or max_loops > 0:
                self.ui.after(100,
                              lambda: self.scan_loop(target_image, photo_if, photo_address, chosen_index, max_loops))
            else:
                print("结束扫描")
                self.stop_scanning()

    def open_manual_selection_window(self):
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
            self.manual_selection_window.destroy()
            if self.grab_photo:  # 如果需要截图
                x1, y1 = min(self.start_x, self.end_x), min(self.start_y, self.end_y)
                x2, y2 = max(self.start_x, self.end_x), max(self.start_y, self.end_y)
                self.manual_selection_coordinates = (
                    self.start_x - 5, self.start_y - 5, self.end_x + 5, self.end_y + 5)
                # 在对应位置产生截图
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                self.grab_photo = False
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

    def add_start_operation(self, chosen_index, position, loop_count):
        self.operations.insert(position, f"开启：{chosen_index}号扫描{loop_count}次")
        self.save_operations()
        self.populate_operation_list()

    def add_close_operation(self, chosen_index, position):
        self.operations.insert(position, f"关闭：{chosen_index}号扫描")
        self.save_operations()
        self.populate_operation_list()

    def add_drag_operation(self, pstart, pend, position):
        self.operations.insert(position, f"拖动：({pstart},{pend})")
        self.save_operations()
        self.populate_operation_list()

    def add_pathfinding_operation(self, pathfinding_loc, position):
        self.operations.insert(position, f"寻路：{pathfinding_loc}")
        self.save_operations()
        self.populate_operation_list()

    def add_wait_operation(self, wait_time, position):
        self.operations.insert(position, f"等待：{wait_time}ms")
        self.save_operations()
        self.populate_operation_list()

    def add_scroll_operation(self, scroll_time, position):
        self.operations.insert(position, f"滚轮：{scroll_time}步")
        self.save_operations()
        self.populate_operation_list()

    def add_keyboard_operation(self, key_position, position):
        self.operations.insert(position, f"键盘操作：按键位置 - {key_position}")
        self.save_operations()
        self.populate_operation_list()

    def add_mouse_operation(self, click_position, position):
        self.operations.insert(position, f"鼠标操作：点击位置 - {click_position}")
        self.save_operations()
        self.populate_operation_list()

    def add_close_operation_window(self, position):
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
            self.add_close_operation(chosen_index, position=position)
            close_window.destroy()

        confirm_button = tk.Button(close_window, text="确定", command=confirm_selection)
        confirm_button.pack(pady=5)

    def add_drag_operation_window(self, position):
        self.ui.iconify()
        pstart = None
        pend = None
        drag_window = tk.Toplevel(self.ui)
        drag_window.attributes('-alpha', 0.2)  # Set transparency
        drag_window.attributes('-fullscreen', True)  # Set fullscreen
        drag_window.title("继续扫描")
        drag_window.wm_attributes('-topmost', 1)
        canvas = tk.Canvas(drag_window)
        canvas.pack(fill="both", expand=True)

        def record_start_position(event):
            nonlocal pstart  # Use nonlocal to modify the pstart variable in the outer scope
            pstart = (event.x, event.y)

        def draw_drag_line(event):
            canvas.delete("all")
            if pstart is not None:
                canvas.create_line(pstart[0], pstart[1], event.x, event.y, fill='red', width=5)

        def record_end_position(event):
            nonlocal pend
            pend = (event.x, event.y)
            self.add_drag_operation(pstart, pend, position=position)
            self.ui.deiconify()
            time.sleep(0.2)
            drag_window.destroy()

        drag_window.bind("<Button-1>", record_start_position)  # Record start position
        drag_window.bind("<B1-Motion>", draw_drag_line)  # Draw drag line
        drag_window.bind("<ButtonRelease-1>", record_end_position)  # Record end position

        drag_window.focus_set()

    def add_start_operation_window(self, position):
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
            self.add_start_operation(chosen_index, position=position, loop_count=loop_count)
            start_window.destroy()

        confirm_button = tk.Button(start_window, text="确定", command=confirm_selection)
        confirm_button.pack(pady=5)

    def add_pathfinding_operation_window(self, position):
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
                self.add_pathfinding_operation((x_value, y_value), position=position)
                pathfinding_window.destroy()

        x_label = tk.Label(pathfinding_window, text="x（正值为＋）：")
        x_label.pack(pady=5)
        x_entry = tk.Entry(pathfinding_window)
        x_entry.pack(pady=5)

        y_label = tk.Label(pathfinding_window, text="y（正值为＋）：")
        y_label.pack(pady=5)
        y_entry = tk.Entry(pathfinding_window)
        y_entry.pack(pady=5)

        pathfinding_button = tk.Button(pathfinding_window, text="确认",
                                       command=lambda: handle_confirm_click(x_entry, y_entry))
        pathfinding_button.pack(pady=5)

    def add_wait_operation_window(self, position):
        wait_window = tk.Toplevel(self.ui)
        wait_window.title("等待时间")
        wait_window.geometry("300x150")
        wait_window.lift()
        wait_window.focus_set()
        wait_label = tk.Label(wait_window, text="请输入等待时间（毫秒）：")
        wait_label.pack(pady=5)
        wait_entry = tk.Entry(wait_window)
        wait_entry.pack(pady=5)
        wait_button = tk.Button(wait_window, text="确认",
                                command=lambda: [self.add_wait_operation(int(wait_entry.get()), position=position),
                                                 wait_window.destroy()])
        wait_button.pack(pady=5)

    def add_scroll_operation_window(self, position):
        scroll_steps = 0
        scroll_window = tk.Toplevel(self.ui)
        scroll_window.title("滚轮操作")
        scroll_window.geometry("300x200")
        scroll_window.lift()
        scroll_window.focus_set()
        scroll_label = tk.Label(scroll_window, text="请输入滚轮步数（正数向上）：")
        scroll_label.pack(pady=5)
        scroll_entry = tk.Entry(scroll_window)
        scroll_entry.pack(pady=5)
        scroll_button = tk.Button(scroll_window, text="确认",
                                  command=lambda: [
                                      self.add_scroll_operation(int(scroll_entry.get()), position=position),
                                      scroll_window.destroy()])
        scroll_button.pack(pady=5)

        def on_mouse_wheel(event):
            nonlocal scroll_steps
            # 获取滚轮滚动的方向
            direction = event.delta // 120  # 正数表示向上滚动，负数表示向下滚动
            current_value = int(scroll_entry.get()) if scroll_entry.get() else 0
            scroll_steps = current_value + direction
            # 在这里执行记录滚轮步数的方法
            scroll_entry.delete(0, tk.END)  # 清空之前的内容
            scroll_entry.insert(0, str(scroll_steps))

        scroll_window.bind("<MouseWheel>", on_mouse_wheel)

    def add_keyboard_operation_window(self, position):
        keyboard_window = tk.Toplevel(self.ui)
        keyboard_window.title("键盘操作")
        keyboard_window.geometry("300x200")
        keyboard_window.lift()
        keyboard_window.focus_set()

        input_frame = tk.Frame(keyboard_window)
        input_frame.pack(pady=10)

        input_label = tk.Label(input_frame, text="请输入一个键：")
        input_label.pack(side=tk.LEFT, padx=5)

        input_entry = tk.Entry(input_frame, width=10)
        input_entry.pack(side=tk.LEFT, padx=5)

        def clear_input():
            input_entry.delete(0, tk.END)

        def confirm_input():
            key_sym = input_entry.get()
            if not key_sym:
                tk.messagebox.showwarning("警告", "请输入一个键后再确认！")
                return
            self.add_keyboard_operation(key_sym, position=position)
            keyboard_window.destroy()

        button_frame = tk.Frame(keyboard_window)
        button_frame.pack(pady=10)

        confirm_button = tk.Button(button_frame, text="确定", command=confirm_input)
        confirm_button.pack(side=tk.LEFT, padx=5)

        clear_button = tk.Button(button_frame, text="清空", command=clear_input)
        clear_button.pack(side=tk.LEFT, padx=5)

        def record_key_press(event):
            if event.keysym == "Return":
                input_entry.delete(0, tk.END)
                key_sym = "enter"
                input_entry.insert(tk.END, key_sym)
            else:
                input_entry.delete(0, tk.END)
                key_sym = event.keysym
                input_entry.insert(tk.END, key_sym)

        keyboard_window.bind("<Key>", record_key_press)

    def add_mouse_operation_window(self, position):
        self.ui.iconify()
        mouse_window = tk.Toplevel(self.ui)
        mouse_window.attributes('-alpha', 0.3)  # Set transparency
        mouse_window.attributes('-fullscreen', True)  # Set fullscreen
        mouse_window.title("鼠标操作")
        mouse_label = tk.Label(mouse_window, text="请在此窗口点击一个位置：")
        mouse_label.pack(pady=5)
        mouse_window.wm_attributes('-topmost', 1)

        def record_click_position(event):
            click_position = f"({event.x}, {event.y})"
            self.add_mouse_operation(click_position, position=position)
            self.ui.deiconify()
            time.sleep(0.2)
            mouse_window.destroy()

        mouse_window.bind("<Button-1>", record_click_position)

    def execute_operations(self):
        for operation in self.operations:
            if operation.startswith("等待"):
                wait_time = int(operation.split("：")[1].strip("ms"))
                time.sleep(wait_time / 1000)  # Convert milliseconds to seconds and wait
            elif operation.startswith("寻路"):
                pathfinding_loc = (operation.split("：")[1])
                path = eval(pathfinding_loc)
                max_loc = self.max_loc
                center_x = int((max_loc[0][0] + max_loc[1][0]) / 2)
                center_y = int((max_loc[0][1] + max_loc[1][1]) / 2)
                offset_x = random.randint(-1, 1)
                offset_y = random.randint(-1, 1)
                pyautogui.click(center_x + int(path[0]) + offset_x, center_y + int(path[1]) + offset_y)
            elif operation.startswith("滚轮"):
                scroll_time = int(operation.split("：")[1].strip("步"))
                pyautogui.scroll(scroll_time)  # 执行滚轮
            elif operation.startswith("键盘操作"):
                key_position = operation.split(" - ")[1]
                pyautogui.press(key_position)  # Simulate keyboard press
            elif operation.startswith("鼠标操作"):
                click_position = operation.split(" - ")[1]
                x, y = map(int, click_position.strip("()").split(","))
                offset_x = random.randint(-1, 1)
                offset_y = random.randint(-1, 1)
                pyautogui.click(x + offset_x, y + offset_y)
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
                chosen_index = int(operation.split("：")[1].strip("号扫描"))
                self.ui.tk_tabs_first_tab.select(chosen_index)
                selected_child_frame = self.tab.tk_tabs_first_tab.nametowidget(self.tab.tk_tabs_first_tab.select())
                selected_child_frame.stop_scanning()
                selected_child_frame.scanning_status_label.config(text="未开始扫描")
            elif operation.startswith("拖动"):
                positions = eval(operation.split("：")[1])  # 获取拖动的坐标信息并转换为元组
                start_pos, end_pos = positions  # 解析起始位置和结束位置的坐标
                pyautogui.moveTo(start_pos[0], start_pos[1])  # 将鼠标移动到起始位置
                pyautogui.dragTo(end_pos[0], end_pos[1], duration=0.4)

    pass

    def load_operations(self, file_path):
        try:
            with open(file_path, "r") as file:
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

    def load_data_operations(self, data):
        operation_names = []
        for item in data:
            for key, value in item.items():
                if isinstance(value, dict) and "operation_name" in value:
                    operation_names.append(value["operation_name"])
        self.operations = operation_names
        self.save_operations()

    def add_default_operations(self):
        with open("default_operation.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
            self.operations = data["default_operations"]
            self.save_operations()

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

    def populate_operation_list(self):
        self.tab.tk_table_operation_box.delete(*self.tab.tk_table_operation_box.get_children())  # Clear the table
        # 遍历操作列表，逐行插入数据
        for i, operation in enumerate(self.operations, start=1):
            operation_name = operation[:2]  # 获取操作名，取前两个字
            self.tab.tk_table_operation_box.insert("", i, values=(i, operation_name, operation))

    def add_default_photos(self):
        with open(self.photo_path, "w") as json_file:
            with open("default_photo.json", "r", encoding='utf-8') as default_file:
                data = json.load(default_file)  # 读取位于default_photo.json中的默认图片信息
            json.dump(data, json_file)  # 写入缓存

    def save_photos(self):
        with open(self.photo_path, "w") as json_file:
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
                "图片1的与或非": self.tab.tk_select_box_photo1_switch_box.get(),
                "图片2的与或非": self.tab.tk_select_box_photo2_switch_box.get(),
                "图片3的与或非": self.tab.tk_select_box_photo3_switch_box.get(),
                "图片4的与或非": self.tab.tk_select_box_photo4_switch_box.get()}
            json.dump(data, json_file)

    def populate_photo_address(self, photo_path, load_if=True):
        if load_if is True:
            with open(photo_path, "r") as json_file:
                data = json.load(json_file)
        else:
            data = photo_path
        self.selection1_address = data["地址1"]
        self.selection2_address = data["地址2"]
        self.selection3_address = data["地址3"]
        self.selection4_address = data["地址4"]
        self.tab.tk_input_photo1_text.delete(0, "end")
        self.tab.tk_input_photo1_text.insert(0, data["图片1的位置"])
        self.tab.tk_input_photo2_text.delete(0, "end")
        self.tab.tk_input_photo2_text.insert(0, data["图片2的位置"])
        self.tab.tk_input_photo3_text.delete(0, "end")
        self.tab.tk_input_photo3_text.insert(0, data["图片3的位置"])
        self.tab.tk_input_photo4_text.delete(0, "end")
        self.tab.tk_input_photo4_text.insert(0, data["图片4的位置"])
        self.tab.tk_select_box_photo1_scan_box.set(data["图片1的地址"])
        self.tab.tk_select_box_photo2_scan_box.set(data["图片2的地址"])
        self.tab.tk_select_box_photo3_scan_box.set(data["图片3的地址"])
        self.tab.tk_select_box_photo4_scan_box.set(data["图片4的地址"])
        self.tab.tk_select_box_photo1_switch_box.set(data["图片1的与或非"])
        self.tab.tk_select_box_photo2_switch_box.set(data["图片2的与或非"])
        self.tab.tk_select_box_photo3_switch_box.set(data["图片3的与或非"])
        self.tab.tk_select_box_photo4_switch_box.set(data["图片4的与或非"])
        self.select_photo_show()

    def handle_escape(self, event):
        self.keep_scanning = False
        for sub_window in self.sub_windows:
            sub_window.stop_scanning()
        self.ui.focus_force()  # 窗口置顶
        self.ui.state('normal')  # 恢复正常状态
        self.ui.lift()  # 将主窗口放置在其他窗口之上
