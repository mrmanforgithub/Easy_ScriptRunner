import json
import threading
import time
from tkinter import filedialog, messagebox
from tkinter.simpledialog import askstring


class Controller:
    # 导入UI类后，替换以下的 object 类型，将获得 IDE 属性提示功能
    ui: object

    def __init__(self, list_name="NewOperation"):
        self.keep_scanning = None
        self.tabs = []

    def init(self, ui):
        """
        得到UI实例，对组件进行初始化配置
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
                        "operation_index": operation_index,
                        "operation_name": operation_data
                    }
                })
            page = {
                "page_index": tab_index,
                "operations": page_operations,
                "images":
                    {"地址1": self.tabs[tab_index].ctl.selection1_address,
                     "地址2": self.tabs[tab_index].ctl.selection2_address,
                     "地址3": self.tabs[tab_index].ctl.selection3_address,
                     "地址4": self.tabs[tab_index].ctl.selection4_address,
                     "图片1的位置": self.tabs[tab_index].tk_input_photo1_text.get(),
                     "图片2的位置": self.tabs[tab_index].tk_input_photo2_text.get(),
                     "图片3的位置": self.tabs[tab_index].tk_input_photo3_text.get(),
                     "图片4的位置": self.tabs[tab_index].tk_input_photo4_text.get(),
                     "图片1的地址": self.tabs[tab_index].tk_select_box_photo1_scan_box.get(),
                     "图片2的地址": self.tabs[tab_index].tk_select_box_photo2_scan_box.get(),
                     "图片3的地址": self.tabs[tab_index].tk_select_box_photo3_scan_box.get(),
                     "图片4的地址": self.tabs[tab_index].tk_select_box_photo4_scan_box.get(),
                     "图片1的与或非": self.tabs[tab_index].tk_select_box_photo1_switch_box.get(),
                     "图片2的与或非": self.tabs[tab_index].tk_select_box_photo2_switch_box.get(),
                     "图片3的与或非": self.tabs[tab_index].tk_select_box_photo3_switch_box.get(),
                     "图片4的与或非": self.tabs[tab_index].tk_select_box_photo4_switch_box.get()}
            }
            scan_page[scan_name].append(page)
        data["pages"].append(scan_page)

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])

        if file_path:
            with open(file_path, "w") as file:
                json.dump(data, file)
            print("脚本已保存至:", file_path)
        else:
            print("保存取消")

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
        if self.keep_scanning is not True:
            self.keep_scanning = True
            scanning_thread = threading.Thread(target=self.scanning_looper, args=(evt,))
            scanning_thread.start()

    def scanning_looper(self, evt):
        while self.keep_scanning is True:
            for tab in self.tabs:
                if not self.keep_scanning:  # 检查标志位，判断是否需要继续扫描
                    break
                tab.tk_select_box_circle_time_checkbox.set("循环1次")
                tab.ctl.start_scanning(evt, max_loops=1)
                time.sleep(0.25)
            if not self.keep_scanning:  # 在每次循环结束后再次检查标志位
                break
            time.sleep(0.25)

    def tab_stop_enter(self, evt):
        if self.keep_scanning is True:
            self.keep_scanning = False
        for tab in self.tabs:
            tab.ctl.stop_scanning()

    def tab_question_enter(self, evt):
        messagebox.showinfo("提示", "侧边栏内容（从上到下）"
                                    "\n1.删除选中扫描单"
                                    "\n2.修改选中扫描单名称"
                                    "\n3.创建新的扫描单"
                                    "\n4.开启所有扫描"
                                    "\n5.关闭所有扫描"
                                    "\n鼠标移动上去0.5s"
                                    "\n会告诉你按钮的作用")
