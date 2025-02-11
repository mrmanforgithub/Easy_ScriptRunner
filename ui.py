from tkinter import *
from pytkUI.widgets import *
from ttkbootstrap import *
from tabui import TabGUI
from ToolTip import *
import pystray
from PIL import Image
import threading
from tkinter import messagebox
import json

class WinGUI(Window):

    def __init__(self):
        super().__init__(themename="cosmo", hdpi=False)
        self.all_tabs = []
        self.__win()
        self.tk_tabs_first_tab = self.__tk_tabs_first_tab(self, "扫描1")  # 第一层选项卡
        # 侧边栏
        self.tk_frame_sidebar_label = self.__tk_frame_sidebar_label(self)
        # 侧边栏扫描删除按钮
        self.ext_icon_tab_delete_icon = self.__ext_icon_tab_delete_icon(self.tk_frame_sidebar_label)
        # 侧边栏扫描修改按钮
        self.ext_icon_tab_change_icon = self.__ext_icon_tab_change_icon(self.tk_frame_sidebar_label)
        # 侧边栏扫描添加按钮
        self.ext_icon_tab_add_icon = self.__ext_icon_tab_add_icon(self.tk_frame_sidebar_label)
        # 侧边栏循环扫描按钮
        self.ext_icon_tab_play_icon = self.__ext_icon_tab_play_icon(self.tk_frame_sidebar_label)
        # 侧边栏停止所有扫描按钮
        self.ext_icon_tab_stop_icon = self.__ext_icon_tab_stop_icon(self.tk_frame_sidebar_label)
        # 侧边栏具体内容按钮
        self.ext_icon_tab_question_icon = self.__ext_icon_tab_question_icon(self.tk_frame_sidebar_label)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def __win(self):
        self.title("脚本运行器")
        # 设置窗口大小、居中
        width = 810
        height = 535
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        geometry = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.geometry(geometry)
        self.resizable(width=True, height=True)
        self.iconbitmap('images/icons/menu.ico')

    def on_close(self):
        # 清空 setting_json/operation_cache.json 文件内容
        file_path = "setting_json/operation_cache.json"
        with open(file_path, "w") as file:
            file.write("")  # 清空文件内容
        file_path = "setting_json/photo_cache.json"
        with open(file_path, "w") as file:
            file.write("")  # 清空文件内容
        # 关闭窗口
        self.destroy()

    def create_tab(self, parent):
        # 创建一个新的扫描页,往all_tabs里加入这个页面
        frame = Frame(parent)
        self.all_tabs.append(TabGUI(frame, self))
        return frame

    def __tk_tabs_first_tab(self, parent, name):
        # 创建选项卡界面
        frame = Notebook(parent)
        self.new_tab = self.create_tab(frame)
        frame.add(self.new_tab, text=name)
        frame.place(x=10, y=14, width=735, height=490)
        return frame

    def __tk_frame_sidebar_label(self, parent):
        # 创建侧边栏界面
        frame = Frame(parent, bootstyle="default")
        frame.place(x=760, y=0, width=40, height=505)
        return frame

    def __ext_icon_tab_delete_icon(self, parent):
        # 创建删除扫描列icon
        icon = Icon(parent, icon_name="trash-fill", size=27, color="#CD45FF")
        icon.place(x=5, y=11, width=30, height=30)
        return icon

    def __ext_icon_tab_change_icon(self, parent):
        # 创建修改扫描列名称icon
        icon = Icon(parent, icon_name="tools", size=27, color="#CD45FF")
        icon.place(x=5, y=50, width=30, height=30)
        return icon

    def __ext_icon_tab_add_icon(self, parent):
        # 创建添加扫描列icon
        icon = Icon(parent, icon_name="plus-square-fill", size=27, color="#CD45FF")
        icon.place(x=5, y=92, width=30, height=30)
        return icon

    def __ext_icon_tab_play_icon(self, parent):
        # 创建循环开启扫描列icon
        icon = Icon(parent, icon_name="caret-right-square-fill", size=27, color="#CD45FF")
        icon.place(x=5, y=131, width=30, height=30)
        return icon

    def __ext_icon_tab_stop_icon(self, parent):
        # 创建关闭所有扫描列icon
        icon = Icon(parent, icon_name="power", size=27, color="#CD45FF")
        icon.place(x=5, y=170, width=30, height=30)
        return icon

    def __ext_icon_tab_question_icon(self, parent):
        # 创建小贴士icon
        icon = Icon(parent, icon_name="question-circle-fill", size=27, color="#CD45FF")
        icon.place(x=5, y=465, width=30, height=30)
        return icon


class Win(WinGUI):
    def __init__(self, controller):
        self.ctl = controller
        super().__init__()
        self.key_setting_path = "setting_json/key_setting.json"
        self.tray_thread = None
        self.is_tray_running = False
        self.tray_icon =None
        self.checkfirst()
        self.__event_bind()
        self.config(menu=self.create_menu())
        self.add_tooltips()
        self.ctl.init(self)

    def checkfirst(self):
        try:
            with open(self.key_setting_path, 'r',encoding='utf-8') as file:
                data = json.load(file)
                if data["else"]["关闭方式"] == "未设置":
                    self.protocol("WM_DELETE_WINDOW", self.confirm_close)
                elif data["else"]["关闭方式"] == "最小化":
                    self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        except:
            pass

    def confirm_close(self):
        with open(self.key_setting_path, 'r',encoding='utf-8') as file:
            data = json.load(file)
        result = messagebox.askquestion("关闭确认", "您确定要关闭吗？\n选择“是”将直接关闭,选择“否”将最小化到托盘。\n此弹窗只会跳出一次,如需要修改,\n请在默认快捷键中修改,选择'最小化'或者'直接关闭'")
        if result == "yes":
            data["else"]["关闭方式"] = "直接关闭"
            with open(self.key_setting_path, 'w',encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            self.quit()
        else:
            data["else"]["关闭方式"] = "最小化"
            with open(self.key_setting_path, 'w',encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            self.minimize_to_tray()

    def run_tray_thread(self):
        self.withdraw()  # 隐藏窗口
        self.tray_icon = pystray.Icon("ScriptRunner")
        self.tray_icon.menu = self.create_icon_menu()
        self.tray_icon.icon = Image.open("images/icons/menu.ico")  # 替换为实际图标图片的路径
        self.is_tray_running = True
        self.tray_icon.run()  # 启动系统托盘循环
        self.is_tray_running = False

    def minimize_to_tray(self):
        if self.is_tray_running:
            return  # 如果系统托盘线程正在运行，则直接返回
        self.is_tray_running = True
        self.tray_thread = threading.Thread(target=self.run_tray_thread)
        self.tray_thread.start()

    def show_window(self):
        self.deiconify()  # 显示窗口
        if(self.is_tray_running):
            self.tray_icon.stop()

    def create_icon_menu(self):
        menu = pystray.Menu(
            pystray.MenuItem("恢复窗口", self.show_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("开始扫描", self.ctl.tab_play_enter),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("停止扫描", self.ctl.tab_stop_enter),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("直接退出", self.exit_program)
        )
        return menu

    def exit_program(self):
        if self.tray_icon is not None:
            self.tray_icon.stop()  # 停止系统托盘循环
            self.tray_icon = None
        self.tray_thread = None
        self.quit()

    def create_menu(self):
        menu = Menu(self, tearoff=False)
        menu.add_cascade(label="菜单", menu=self.menu_main_menu(menu))
        return menu

    def menu_main_menu(self, parent):
        menu = Menu(parent, tearoff=False)
        menu.add_command(label="加载全局脚本", command=self.ctl.load_all_scripts)
        menu.add_command(label="保存全局脚本", command=self.ctl.save_all_scripts)
        return menu

    def __event_bind(self):
        self.ext_icon_tab_delete_icon.bind('<Button-1>', self.ctl.tab_delete_enter)
        self.ext_icon_tab_change_icon.bind('<Button-1>', self.ctl.tab_change_enter)
        self.ext_icon_tab_add_icon.bind('<Button-1>', self.ctl.tab_add_enter)
        self.ext_icon_tab_play_icon.bind('<Button-1>', self.ctl.tab_play_enter)
        self.ext_icon_tab_stop_icon.bind('<Button-1>', self.ctl.tab_stop_enter)
        self.ext_icon_tab_question_icon.bind('<Button-1>', self.ctl.tab_question_enter)
        pass
    def add_tooltips(self):
        # 为按钮创建浮动标签，可以查看按钮的作用
        create_tooltip(self.ext_icon_tab_delete_icon, "删除此页扫描")
        create_tooltip(self.ext_icon_tab_change_icon, "修改这页扫描的名称")
        create_tooltip(self.ext_icon_tab_add_icon, "创建一个新的扫描")
        create_tooltip(self.ext_icon_tab_play_icon, "循环开始所有的扫描")
        create_tooltip(self.ext_icon_tab_stop_icon, "停止当前所有的扫描")
        create_tooltip(self.ext_icon_tab_question_icon, "查看小贴士")


if __name__ == "__main__":
    win = WinGUI()
    win.mainloop()
