import json
import threading
import time
from tkinter import filedialog, messagebox
from tkinter.simpledialog import askstring
import keyboard
import traceback
from datetime import datetime
import win32gui
import win32con
import win32com.client


class Controller:
    # 导入UI类后,替换以下的 object 类型,将获得 IDE 属性提示功能
    ui: object

    def __init__(self, list_name="NewOperation"):
        self.keep_scanning = None
        self.tabs = []
        self.key_setting_path = "setting_json/key_setting.json"   # 快捷键,默认扫描次数,默认扫描相似度阈值保存位置
        self.bind_keys(self.key_setting_path)

    def init(self, ui):
        """
        得到UI实例,对组件进行初始化配置
        """
        self.ui = ui
        self.tabs = self.ui.all_tabs
        # TODO 组件初始化 赋值操作

    def load_all_scripts(self):
        json_path = filedialog.askopenfilename(title="Select file",
                                                filetypes=(
                                                    ("Json files", "*.json"), ("all files", "*.*")))
        with open(json_path, 'r') as file:
            data = json.load(file)

        operations_data = []
        images_data = []
        for tab in self.ui.tk_tabs_first_tab.tabs():
            self.ui.tk_tabs_first_tab.forget(tab)
        self.ui.all_tabs = []
        for page in data['pages']:
            for i, (page_name, page_data) in enumerate(page.items()):
                # 添加页面名称到标签页中
                self.ui.new_tab = self.ui.create_tab(self.ui.tk_tabs_first_tab)
                self.ui.tk_tabs_first_tab.add(self.ui.new_tab, text=page_name)
                self.tabs = self.ui.all_tabs
                # 处理页面的操作数据
                if isinstance(page_data, list) and isinstance(page_data[0], dict) and 'operations' in page_data[
                    0] and 'images' in page_data[0]:
                    operations_data.append(page_data[0]['operations'])
                    images_data.append(page_data[0]['images'])
                    self.tabs[i].ctl.populate_photo_address(images_data[i], load_if=False)
                    self.tabs[i].ctl.load_data_operations(operations_data[i])
                    self.tabs[i].ctl.populate_operation_list()

    def save_all_scripts(self):
        data = {
            "pages": []
        }
        scan_page = {}  # 初始化为空字典
        for tab_index, tab in enumerate(self.ui.tk_tabs_first_tab.tabs()):
            scan_name = self.ui.tk_tabs_first_tab.tab(tab_index, "text")
            scan_page[scan_name] = []  # 初始化为空字典
            page_operations = []
            # 所有和operation有关的for
            for operation_index, operation_data in enumerate(self.tabs[tab_index].ctl.operations):
                page_operations.append({
                    str(operation_index): {
                        "operation_name": operation_data.get("operation_name", ""),
                        "parameters": operation_data.get("parameters", []),
                        "operation_text": operation_data.get("operation_text", "")
                    }
                })
            images = {}
            for i in range(self.tabs[tab_index].containers_count):
                images[f"地址{i+1}"] = self.tabs[tab_index].ctl.selection_address[i]
                images[f"图片{i+1}的位置"] = self.tabs[tab_index].photo_input[i].get()
                images[f"图片{i+1}的地址"] = self.tabs[tab_index].photo_scan_box[i].get()
            images["满足方式"] = self.tabs[tab_index].photo_if_var.get()
            images["窗口选择"] = self.tabs[tab_index].ctl.process_name
            images["图文数量"] = self.tabs[tab_index].containers_count
            page = {
                "page_index": tab_index,
                "operations": page_operations,
                "images": images
            }
            scan_page[scan_name].append(page)
        data["pages"].append(scan_page)

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])

        if file_path:
            with open(file_path, "w") as file:
                json.dump(data, file)

    def tab_delete_enter(self, evt):
        current_tab = self.ui.tk_tabs_first_tab.select()
        if current_tab:
            index = self.ui.tk_tabs_first_tab.index(current_tab)  # 获取选项卡的索引
            del self.ui.all_tabs[index]
            self.ui.tk_tabs_first_tab.forget(current_tab)

    def tab_change_enter(self, evt):
        current_tab = self.ui.tk_tabs_first_tab.select()
        if current_tab:
            tab_name = self.ui.tk_tabs_first_tab.tab(current_tab, "text")
            new_name = askstring("修改扫描名", "请输入新的扫描名", initialvalue=tab_name)
            if new_name:
                self.ui.tk_tabs_first_tab.tab(current_tab, text=new_name)

    def tab_add_enter(self, evt):
        tab_name = f"Tab {len(self.ui.tk_tabs_first_tab.tabs())}"
        new_name = askstring("添加扫描", "请输入扫描名", initialvalue=tab_name)
        if new_name:
            self.ui.new_tab = self.ui.create_tab(self.ui.tk_tabs_first_tab)
            self.ui.tk_tabs_first_tab.add(self.ui.new_tab, text=new_name)
            self.tabs = self.ui.all_tabs

    def tab_play_enter(self, evt):
        # 调用循环扫描，完成按扫描次序循环扫描
        if self.keep_scanning is not True:
            self.keep_scanning = True
            scanning_thread = threading.Thread(target=self.scanning_looper, args=(evt,))
            scanning_thread.start()

    def scanning_looper(self, evt):
        # 循环扫描
        while self.keep_scanning is True:
            for tab in self.tabs:
                if not self.keep_scanning:  # 检查标志位,判断是否需要继续扫描
                    break
                tab.tk_select_box_circle_time_checkbox.set("循环1次")
                tab.ctl.start_scanning(evt, max_loops=1)
                time.sleep(0.25)
            if not self.keep_scanning:  # 在每次循环结束后再次检查标志位
                break
            time.sleep(0.1)

    # 获取所有窗口句柄
    def get_all_hwnd(self):
        def impl(hwnd, *args):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
                hwnd_map.update({hwnd: win32gui.GetWindowText(hwnd)})
        hwnd_map = {}
        win32gui.EnumWindows(impl, 0)
        return hwnd_map
    # 将窗口置顶
    def window_show_top(self,window_title):
        hwnd_map = self.get_all_hwnd()
        for handle, title in hwnd_map.items():
            if not title or title != window_title:
                continue
            win32gui.BringWindowToTop(handle)
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')
            # 被其他窗口遮挡，调用后放到最前面
            win32gui.SetForegroundWindow(handle)
            # 解决被最小化的情况
            win32gui.ShowWindow(handle, win32con.SW_RESTORE)

    def tab_stop_enter(self, evt):
        self.window_show_top("脚本运行器")
        if self.keep_scanning is True:
            self.keep_scanning = False
        for tab in self.tabs:
            tab.ctl.stop_scanning()
        self.ui.show_window() #关闭一下系统托盘

    def tab_question_enter(self, evt):
        messagebox.showinfo("提示", "侧边栏内容（从上到下）"
                                    "\n1.删除选中扫描单"
                                    "\n2.修改选中扫描单名称"
                                    "\n3.创建新的扫描单"
                                    "\n4.开启所有扫描"
                                    "\n5.关闭所有扫描"
                                    "\n鼠标移动上去0.5s"
                                    "\n会告诉你按钮的作用"
                                    "\n填入图片位置的输入框"
                                    "\n也可以填入文字进行文字识别哦")

    def bind_keys(self, path):
        default_bindings ={
            "快捷键": {
                "循环开启扫描": "F12",
                "关闭所有扫描": "esc"
            },
            "else": {
                "相似度": 0.75,
                "随机偏移": 0,
                "策略": "强相似",
                "关闭方式": "直接退出",
                "扫描时间": 100
            }
        }
        try:
            with open(path, 'r', encoding='utf-8') as f:
                key_bindings = json.load(f)
        except FileNotFoundError:
            key_bindings = default_bindings
            # 如果文件不存在，则创建并写入默认配置
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(default_bindings, f, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            now = datetime.now()
            timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
            # 构造日志文件名
            log_filename = f"backtrace_logs/{timestamp}"
            # 将异常信息写入日志文件
            with open(log_filename, "w") as file:
                file.write(f"Error occurred at {now}:\n")
                traceback.print_exc(file=file)  # 将异常信息写入文件
            return
        if "快捷键" in key_bindings:
            bindings = key_bindings["快捷键"]
            for function_desc, key in bindings.items():
                if function_desc == "循环开启扫描":
                    keyboard.add_hotkey(key, lambda:self.tab_play_enter(evt=1))
                elif function_desc == "关闭所有扫描":
                    keyboard.add_hotkey(key, lambda: self.tab_stop_enter(evt=1))
                else:
                    return
        return
