from tkinter import *
from pytkUI.widgets import *
from ttkbootstrap import *
from tabui import TabGUI
from ToolTip import *

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class WinGUI(Window):
    _instance = None

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
        self.focus_force()  # 窗口置顶
        self.resizable(width=False, height=False)
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
        self.__event_bind()
        self.config(menu=self.create_menu())
        self.add_tooltips()
        self.ctl.init(self)

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
