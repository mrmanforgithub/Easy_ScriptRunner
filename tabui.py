import random
from tkinter import *
from tkinter.ttk import *
from ttkbootstrap import *
from pytkUI.widgets import *
from tabcontrol import TabController as tab_controller

class TabGUI(Frame):
    ui: object
    def __init__(self, parent, ui):
        self.parent = parent
        self.ext_tabs_second_tab = self.__ext_tabs_second_tab(parent)
        self.tk_frame_enter_container = self.__tk_frame_enter_container(self.ext_tabs_second_tab_0)
        # 开始循环按钮
        self.tk_button_start_scanning_button = self.__tk_button_start_scanning_button(self.tk_frame_enter_container)
        # 循环状态标签
        self.tk_label_scanning_state_label = self.__tk_label_scanning_state_label(self.tk_frame_enter_container)
        # 循环次数下拉框
        self.tk_select_box_circle_time_checkbox = self.__tk_select_box_circle_time_checkbox(
            self.tk_frame_enter_container)

        # 图片相关选项卡
        self.tk_frame_photo_all_container = self.__tk_frame_photo_all_container(self.ext_tabs_second_tab_0)
        # 图片4的容器
        self.tk_frame_photo4_container = self.__tk_frame_photo4_container(self.tk_frame_photo_all_container)
        # 图片4的标签
        self.tk_label_photo4_label = self.__tk_label_photo4_label(self.tk_frame_photo4_container)
        # 图片4的地址
        self.tk_input_photo4_text = self.__tk_input_photo4_text(self.tk_frame_photo4_container)
        # 浏览图片4的按钮
        self.tk_button_photo4_browser_button = self.__tk_button_photo4_browser_button(self.tk_frame_photo4_container)
        # 图片4 与或非
        self.tk_select_box_photo4_switch_box = self.__tk_select_box_photo4_switch_box(self.tk_frame_photo4_container)
        # 图片4 扫描地址
        self.tk_select_box_photo4_scan_box = self.__tk_select_box_photo4_scan_box(self.tk_frame_photo4_container)

        # 图片3的容器
        self.tk_frame_photo3_container = self.__tk_frame_photo3_container(self.tk_frame_photo_all_container)
        # 图片3的标签
        self.tk_label_photo3_label = self.__tk_label_photo3_label(self.tk_frame_photo3_container)
        # 图片3的地址
        self.tk_input_photo3_text = self.__tk_input_photo3_text(self.tk_frame_photo3_container)
        # 浏览图片3的按钮
        self.tk_button_photo3_browser_button = self.__tk_button_photo3_browser_button(self.tk_frame_photo3_container)
        # 图片3 与或非
        self.tk_select_box_photo3_switch_box = self.__tk_select_box_photo3_switch_box(self.tk_frame_photo3_container)
        # 图片3 扫描地址
        self.tk_select_box_photo3_scan_box = self.__tk_select_box_photo3_scan_box(self.tk_frame_photo3_container)

        # 图片2的容器
        self.tk_frame_photo2_container = self.__tk_frame_photo2_container(self.tk_frame_photo_all_container)
        # 图片2的标签
        self.tk_label_photo2_label = self.__tk_label_photo2_label(self.tk_frame_photo2_container)
        # 图片2的地址
        self.tk_input_photo2_text = self.__tk_input_photo2_text(self.tk_frame_photo2_container)
        # 浏览图片2的按钮
        self.tk_button_photo2_browser_button = self.__tk_button_photo2_browser_button(self.tk_frame_photo2_container)
        # 图片2 与或非
        self.tk_select_box_photo2_switch_box = self.__tk_select_box_photo2_switch_box(self.tk_frame_photo2_container)
        # 图片2 扫描地址
        self.tk_select_box_photo2_scan_box = self.__tk_select_box_photo2_scan_box(self.tk_frame_photo2_container)

        # 图片1的容器
        self.tk_frame_photo1_container = self.__tk_frame_photo1_container(self.tk_frame_photo_all_container)
        # 图片1的标签
        self.tk_label_photo1_label = self.__tk_label_photo1_label(self.tk_frame_photo1_container)
        # 图片1的地址
        self.tk_input_photo1_text = self.__tk_input_photo1_text(self.tk_frame_photo1_container)
        # 浏览图片2的按钮
        self.tk_button_photo1_browser_button = self.__tk_button_photo1_browser_button(self.tk_frame_photo1_container)
        # 图片1 与或非
        self.tk_select_box_photo1_switch_box = self.__tk_select_box_photo1_switch_box(self.tk_frame_photo1_container)
        # 图片1 扫描地址
        self.tk_select_box_photo1_scan_box = self.__tk_select_box_photo1_scan_box(self.tk_frame_photo1_container)

        # 图片保存容器
        self.tk_frame_photo_save_container = self.__tk_frame_photo_save_container(self.tk_frame_photo_all_container)
        # 图片地址保存按钮
        self.tk_button_save_photo_button = self.__tk_button_save_photo_button(self.tk_frame_photo_save_container)
        # 图片地址加载按钮
        self.tk_button_load_photo_button = self.__tk_button_load_photo_button(self.tk_frame_photo_save_container)

        # 图片扫描相关选项卡
        self.tk_frame_select_box = self.__tk_frame_select_box(self.tk_frame_photo_all_container)
        # 手动框选按钮
        self.tk_button_select_button = self.__tk_button_select_button(self.tk_frame_select_box)
        # 一键截图按钮
        self.tk_button_select_photo_button = self.__tk_button_select_photo_button(self.tk_frame_select_box)
        # 地址下拉框
        self.tk_select_box_photo_address = self.__tk_select_box_photo_address(self.tk_frame_select_box)
        # 地址开始坐标
        self.tk_label_photo_start_label = self.__tk_label_photo_start_label(self.tk_frame_select_box)
        # 地址结束坐标
        self.tk_label_photo_end_label = self.__tk_label_photo_end_label(self.tk_frame_select_box)
        # 显示地址坐标按钮
        self.tk_button_select_photo_show = self.__tk_button_select_photo_show(self.tk_frame_select_box)
        # 记录地址坐标按钮
        self.tk_button_select_photo_save = self.__tk_button_select_photo_save(self.tk_frame_select_box)

        # 操作相关选项卡
        self.tk_frame_operation_container = self.__tk_frame_operation_container(self.ext_tabs_second_tab_1)
        # 操作标签
        self.tk_label_operation_list_label = self.__tk_label_operation_list_label(self.tk_frame_operation_container)
        # 操作修改按钮
        self.tk_button_operation_change_button = self.__tk_button_operation_change_button(
            self.tk_frame_operation_container)
        # 操作删除按钮
        self.tk_button_operation_delete_button = self.__tk_button_operation_delete_button(
            self.tk_frame_operation_container)
        # 操作添加按钮
        self.tk_button_operation_add_button = self.__tk_button_operation_add_button(self.tk_frame_operation_container)
        # 操作选择下拉框
        self.tk_select_box_operation_list = self.__tk_select_box_operation_list(self.tk_frame_operation_container)
        # 操作列表表格
        self.tk_table_operation_box = self.__tk_table_operation_box(self.tk_frame_operation_container)
        # 操作文件保存按钮
        self.tk_button_save_operation_button = self.__tk_button_save_operation_button(self.tk_frame_operation_container)
        # 操作文件加载按钮
        self.tk_button_load_operation_button = self.__tk_button_load_operation_button(self.tk_frame_operation_container)
        # 操作保存图标
        self.ext_icon_save_operation_icon = self.__ext_icon_save_operation_icon(self.tk_frame_operation_container)
        # 操作读取图标
        self.ext_icon_load_operation_icon = self.__ext_icon_load_operation_icon(self.tk_frame_operation_container)

        # 扫描相关选项卡
        self.tk_frame_scan_detail_container = self.__tk_frame_scan_detail_container(self.ext_tabs_second_tab_2)
        # 图片标签
        self.tk_label_scan_photo_label = self.__tk_label_scan_photo_label(self.tk_frame_scan_detail_container)
        # 操作标签
        self.tk_label_scan_operation_label = self.__tk_label_scan_operation_label(self.tk_frame_scan_detail_container)
        # 图片文件浏览按钮
        self.tk_button_scan_browser1_button = self.__tk_button_scan_browser1_button(self.tk_frame_scan_detail_container)
        # 操作文件浏览按钮
        self.tk_button_scan_browser2_button = self.__tk_button_scan_browser2_button(self.tk_frame_scan_detail_container)
        # 文件组合输出按钮
        self.tk_button_scan_output = self.__tk_button_scan_output(self.tk_frame_scan_detail_container)
        # 图片文件地址文本框
        self.tk_input_scan_photo_text = self.__tk_input_scan_photo_text(self.tk_frame_scan_detail_container)
        # 操作文件地址文本框
        self.tk_input_scan_operation_text = self.__tk_input_scan_operation_text(self.tk_frame_scan_detail_container)
        self.tk_label_recent_scan_recall = self.__tk_label_recent_scan_recall(self.tk_frame_scan_detail_container)
        self.tk_button_recent_scan_button = self.__tk_button_recent_scan_button(self.tk_frame_scan_detail_container)
        # 最近扫描内容
        self.tk_list_box_recent_scan_box = self.__tk_list_box_recent_scan_box(self.tk_frame_scan_detail_container)
        # 最近扫描开启按钮
        self.tk_button_scan_reopen_button = self.__tk_button_scan_reopen_button(self.tk_frame_scan_detail_container)
        self.ctl = tab_controller(self)
        self.ui = ui
        self.ctl.init_ui(self.ui)
        self.__style_config()
        self.__event_bind()

    def scrollbar_autohide(self, vbar, hbar, widget):
        """自动隐藏滚动条"""

        def show():
            if vbar: vbar.lift(widget)
            if hbar: hbar.lift(widget)

        def hide():
            if vbar: vbar.lower(widget)
            if hbar: hbar.lower(widget)

        hide()
        widget.bind("<Enter>", lambda e: show())
        if vbar: vbar.bind("<Enter>", lambda e: show())
        if vbar: vbar.bind("<Leave>", lambda e: hide())
        if hbar: hbar.bind("<Enter>", lambda e: show())
        if hbar: hbar.bind("<Leave>", lambda e: hide())
        widget.bind("<Leave>", lambda e: hide())

    def v_scrollbar(self, vbar, widget, x, y, w, h, pw, ph):
        widget.configure(yscrollcommand=vbar.set)
        vbar.config(command=widget.yview)
        vbar.place(relx=(w + x) / pw, rely=y / ph, relheight=h / ph, anchor='ne')

    def h_scrollbar(self, hbar, widget, x, y, w, h, pw, ph):
        widget.configure(xscrollcommand=hbar.set)
        hbar.config(command=widget.xview)
        hbar.place(relx=x / pw, rely=(y + h) / ph, relwidth=w / pw, anchor='sw')

    def create_bar(self, master, widget, is_vbar, is_hbar, x, y, w, h, pw, ph):
        vbar, hbar = None, None
        if is_vbar:
            vbar = Scrollbar(master)
            self.v_scrollbar(vbar, widget, x, y, w, h, pw, ph)
        if is_hbar:
            hbar = Scrollbar(master, orient="horizontal")
            self.h_scrollbar(hbar, widget, x, y, w, h, pw, ph)
        self.scrollbar_autohide(vbar, hbar, widget)

    def new_style(self, widget):
        ctl = widget.cget('style')
        ctl = "".join(random.sample('0123456789', 5)) + "." + ctl
        widget.configure(style=ctl)
        return ctl

    def __tk_frame_enter_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=0, y=402, width=578, height=54)
        return frame

    def __tk_button_start_scanning_button(self, parent):
        btn = Button(parent, text="开始扫描", takefocus=False, bootstyle="default")
        btn.place(x=393, y=2, width=175, height=39)
        return btn

    def __tk_label_scanning_state_label(self, parent):
        label = Label(parent, text="扫描状态", anchor="center", bootstyle="info inverse")
        label.place(x=8, y=2, width=176, height=40)
        return label

    def __tk_select_box_circle_time_checkbox(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="info")
        cb['values'] = ("无限循环", "循环1次", "循环10次")
        cb.current(0)
        cb.place(x=199, y=6, width=176, height=40)
        return cb
    def __tk_frame_second_tab_0(self, parent):
        frame = Frame(parent)
        return frame

    def __tk_frame_second_tab_1(self, parent):
        frame = Frame(parent)
        return frame

    def __tk_frame_second_tab_2(self, parent):
        frame = Frame(parent)
        return frame

    def __ext_tabs_second_tab(self, parent):
        frame = ExtTabs(parent)
        self.ext_tabs_second_tab_0 = self.__tk_frame_second_tab_0(frame)
        self.ext_tabs_second_tab_1 = self.__tk_frame_second_tab_1(frame)
        self.ext_tabs_second_tab_2 = self.__tk_frame_second_tab_2(frame)
        tabs = [
            TabItem("image", "图片", self.ext_tabs_second_tab_0),
            TabItem("hammer", "事件", self.ext_tabs_second_tab_1),
            TabItem("list", "扫描", self.ext_tabs_second_tab_2),
        ]
        frame.init(tabs=tabs)
        frame.place(x=0, y=3, width=735, height=461)
        return frame

    def __tk_frame_photo_all_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=0, y=0, width=577, height=398)
        return frame

    def __tk_frame_photo4_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=10, y=210, width=560, height=61)
        return frame

    def __tk_label_photo4_label(self, parent):
        label = Label(parent, text="图片4：", anchor="center", bootstyle="secondary")
        label.place(x=15, y=15, width=50, height=30)
        return label

    def __tk_input_photo4_text(self, parent):
        ipt = Entry(parent, bootstyle="info")
        ipt.place(x=80, y=15, width=220, height=30)
        return ipt

    def __tk_button_photo4_browser_button(self, parent):
        btn = Button(parent, text="浏览", takefocus=False, bootstyle="info")
        btn.place(x=315, y=15, width=70, height=30)
        return btn

    def __tk_select_box_photo4_switch_box(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("与", "或", "非")
        cb.current(0)
        cb.place(x=398, y=15, width=70, height=30)
        return cb

    def __tk_select_box_photo4_scan_box(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("地址1", "地址2", "地址3", "地址4")
        cb.current(0)
        cb.place(x=478, y=15, width=76, height=30)
        return cb

    def __tk_frame_photo3_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=10, y=144, width=560, height=61)
        return frame

    def __tk_label_photo3_label(self, parent):
        label = Label(parent, text="图片3：", anchor="center", bootstyle="secondary")
        label.place(x=15, y=15, width=50, height=30)
        return label

    def __tk_input_photo3_text(self, parent):
        ipt = Entry(parent, bootstyle="info")
        ipt.place(x=80, y=15, width=220, height=30)
        return ipt

    def __tk_button_photo3_browser_button(self, parent):
        btn = Button(parent, text="浏览", takefocus=False, bootstyle="info")
        btn.place(x=315, y=15, width=70, height=30)
        return btn

    def __tk_select_box_photo3_switch_box(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("与", "或", "非")
        cb.current(0)
        cb.place(x=398, y=15, width=70, height=30)
        return cb

    def __tk_select_box_photo3_scan_box(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("地址1", "地址2", "地址3", "地址4")
        cb.current(0)
        cb.place(x=478, y=15, width=76, height=30)
        return cb

    def __tk_frame_photo2_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=10, y=76, width=560, height=61)
        return frame

    def __tk_label_photo2_label(self, parent):
        label = Label(parent, text="图片2：", anchor="center", bootstyle="secondary")
        label.place(x=15, y=15, width=50, height=30)
        return label

    def __tk_input_photo2_text(self, parent):
        ipt = Entry(parent, bootstyle="info")
        ipt.place(x=80, y=15, width=220, height=30)
        return ipt

    def __tk_button_photo2_browser_button(self, parent):
        btn = Button(parent, text="浏览", takefocus=False, bootstyle="info")
        btn.place(x=315, y=15, width=70, height=30)
        return btn

    def __tk_select_box_photo2_switch_box(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("与", "或", "非")
        cb.current(0)
        cb.place(x=398, y=15, width=70, height=30)
        return cb

    def __tk_select_box_photo2_scan_box(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("地址1", "地址2", "地址3", "地址4")
        cb.current(0)
        cb.place(x=478, y=15, width=76, height=30)
        return cb

    def __tk_frame_photo1_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=9, y=9, width=560, height=61)
        return frame

    def __tk_label_photo1_label(self, parent):
        label = Label(parent, text="图片1：", anchor="center", bootstyle="secondary")
        label.place(x=15, y=15, width=50, height=30)
        return label

    def __tk_input_photo1_text(self, parent):
        ipt = Entry(parent, bootstyle="info")
        ipt.place(x=80, y=15, width=220, height=30)
        return ipt

    def __tk_button_photo1_browser_button(self, parent):
        btn = Button(parent, text="浏览", takefocus=False, bootstyle="info")
        btn.place(x=315, y=15, width=70, height=30)
        return btn

    def __tk_select_box_photo1_switch_box(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("与", "或", "非")
        cb.current(0)
        cb.place(x=398, y=15, width=70, height=30)
        return cb

    def __tk_select_box_photo1_scan_box(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("地址1", "地址2", "地址3", "地址4")
        cb.current(0)
        cb.place(x=478, y=15, width=76, height=30)
        return cb

    def __tk_frame_photo_save_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=10, y=276, width=560, height=39)
        return frame

    def __tk_button_save_photo_button(self, parent):
        btn = Button(parent, text="单 独 保 存", takefocus=False, bootstyle="info")
        btn.place(x=8, y=4, width=267, height=30)
        return btn

    def __tk_button_load_photo_button(self, parent):
        btn = Button(parent, text="单 独 读 取", takefocus=False, bootstyle="default")
        btn.place(x=283, y=4, width=267, height=30)
        return btn

    def __tk_frame_select_box(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=9, y=320, width=560, height=70)
        return frame

    def __tk_button_select_button(self, parent):
        btn = Button(parent, text="手动框选", takefocus=False, bootstyle="info")
        btn.place(x=7, y=4, width=120, height=60)
        return btn

    def __tk_button_select_photo_button(self, parent):
        btn = Button(parent, text="一键截图", takefocus=False, bootstyle="default")
        btn.place(x=432, y=4, width=120, height=60)
        return btn

    def __tk_select_box_photo_address(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("地址1", "地址2", "地址3", "地址4")
        cb.current(0)
        cb.place(x=135, y=20, width=70, height=45)
        return cb

    def __tk_label_photo_start_label(self, parent):
        label = Label(parent, text="(0,0)", anchor="center", bootstyle="info")
        label.place(x=213, y=3, width=63, height=30)
        return label

    def __tk_label_photo_end_label(self, parent):
        label = Label(parent, text="(0,0)", anchor="center", bootstyle="info")
        label.place(x=213, y=38, width=63, height=30)
        return label

    def __tk_button_select_photo_show(self, parent):
        btn = Button(parent, text="显示", takefocus=False, bootstyle="default")
        btn.place(x=284, y=4, width=65, height=60)
        return btn

    def __tk_button_select_photo_save(self, parent):
        btn = Button(parent, text="记录", takefocus=False, bootstyle="default")
        btn.place(x=358, y=4, width=65, height=60)
        return btn

    def __tk_frame_operation_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=0, y=0, width=577, height=398)
        return frame

    def __tk_label_operation_list_label(self, parent):
        label = Label(parent, text="操作列表", anchor="center", bootstyle="primary")
        label.place(x=0, y=220, width=130, height=50)
        return label

    def __tk_button_operation_change_button(self, parent):
        btn = Button(parent, text="修改", takefocus=False, bootstyle="default")
        btn.place(x=445, y=220, width=130, height=50)
        return btn

    def __tk_button_operation_delete_button(self, parent):
        btn = Button(parent, text="删 除", takefocus=False, bootstyle="default")
        btn.place(x=1, y=320, width=575, height=63)
        return btn

    def __tk_button_operation_add_button(self, parent):
        btn = Button(parent, text="添加", takefocus=False, bootstyle="info")
        btn.place(x=300, y=220, width=130, height=50)
        return btn

    def __tk_select_box_operation_list(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("等待时间", "键盘操作", "鼠标操作", "鼠标拖动", "滚轮操作", "自动寻路", "开启扫描", "关闭扫描")
        cb.current(0)
        cb.place(x=140, y=220, width=140, height=50)
        return cb

    def __tk_table_operation_box(self, parent):
        # 表头字段 表头宽度
        columns = {"id": 114, "操作名称": 114, "操作数据": 401}
        tk_table = Treeview(parent, show="headings", columns=list(columns), bootstyle="primary")
        for text, width in columns.items():  # 批量设置列属性
            tk_table.heading(text, text=text, anchor='center')
            tk_table.column(text, anchor='center', width=width, stretch=False)  # stretch 不自动拉伸

        tk_table.place(x=1, y=1, width=575, height=192)
        self.create_bar(parent, tk_table, True, False, 1, 1, 575, 192, 577, 398)
        return tk_table

    def __tk_button_save_operation_button(self, parent):
        btn = Button(parent, text="单 独 保 存", takefocus=False, bootstyle="primary")
        btn.place(x=40, y=280, width=240, height=30)
        return btn

    def __tk_button_load_operation_button(self, parent):
        btn = Button(parent, text="单 独 读 取", takefocus=False, bootstyle="warning")
        btn.place(x=339, y=282, width=237, height=30)
        return btn

    def __ext_icon_save_operation_icon(self, parent):
        icon = Icon(parent, icon_name="layer-forward", size=32, color="#0F9BFF")
        icon.place(x=2, y=279, width=35, height=35)
        return icon

    def __ext_icon_load_operation_icon(self, parent):
        icon = Icon(parent, icon_name="layer-backward", size=32, color="#FF4E02")
        icon.place(x=300, y=280, width=35, height=35)
        return icon

    def __tk_frame_scan_detail_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=0, y=0, width=577, height=398)
        return frame

    def __tk_label_scan_photo_label(self, parent):
        label = Label(parent, text="图片文件", anchor="center", bootstyle="info")
        label.place(x=89, y=7, width=144, height=30)
        return label

    def __tk_label_scan_operation_label(self, parent):
        label = Label(parent, text="事件文件", anchor="center", bootstyle="info")
        label.place(x=320, y=7, width=145, height=30)
        return label

    def __tk_button_scan_browser1_button(self, parent):
        btn = Button(parent, text="浏览", takefocus=False, bootstyle="success")
        btn.place(x=17, y=45, width=60, height=30)
        return btn

    def __tk_button_scan_browser2_button(self, parent):
        btn = Button(parent, text="浏览", takefocus=False, bootstyle="success")
        btn.place(x=248, y=45, width=60, height=30)
        return btn

    def __tk_button_scan_output(self, parent):
        btn = Button(parent, text="输出", takefocus=False, bootstyle="default")
        btn.place(x=480, y=45, width=86, height=30)
        return btn

    def __tk_input_scan_photo_text(self, parent):
        ipt = Entry(parent, bootstyle="primary")
        ipt.place(x=86, y=45, width=150, height=30)
        return ipt

    def __tk_input_scan_operation_text(self, parent):
        ipt = Entry(parent, bootstyle="primary")
        ipt.place(x=317, y=45, width=150, height=30)
        return ipt

    def __tk_label_recent_scan_recall(self, parent):
        label = Label(parent, text="最 近 的 扫 描", anchor="center", bootstyle="info inverse")
        label.place(x=17, y=103, width=140, height=30)
        return label

    def __tk_button_recent_scan_button(self, parent):
        btn = Button(parent, text="打 开", takefocus=False, bootstyle="default")
        btn.place(x=425, y=103, width=140, height=30)
        return btn

    def __tk_list_box_recent_scan_box(self, parent):
        lb = Listbox(parent)

        lb.place(x=17, y=135, width=550, height=187)
        self.create_bar(parent, lb, True, False, 17, 135, 550, 187, 577, 398)
        return lb

    def __tk_button_scan_reopen_button(self, parent):
        btn = Button(parent, text="初始化图片事件", takefocus=False, bootstyle="primary")
        btn.place(x=0, y=338, width=577, height=55)
        return btn

    def __event_bind(self):
        self.tk_button_start_scanning_button.bind('<Button-1>', self.ctl.start_scanning)
        self.tk_select_box_circle_time_checkbox.bind('<<ComboboxSelected>>',
                                                         lambda event: self.ctl.confirm_selection(event,
                                                                                                  self.tk_select_box_circle_time_checkbox.get()))
        self.tk_select_box_photo_address.bind('<<ComboboxSelected>>',self.ctl.confirm_address_selection)
        self.tk_button_photo4_browser_button.bind('<Button-1>', lambda event: self.ctl.browse_target_image(event, 4))
        self.tk_button_photo3_browser_button.bind('<Button-1>', lambda event: self.ctl.browse_target_image(event, 3))
        self.tk_button_photo2_browser_button.bind('<Button-1>', lambda event: self.ctl.browse_target_image(event, 2))
        self.tk_button_photo1_browser_button.bind('<Button-1>', lambda event: self.ctl.browse_target_image(event, 1))
        self.tk_button_save_photo_button.bind('<Button-1>', self.ctl.save_photo_context)
        self.tk_button_load_photo_button.bind('<Button-1>', self.ctl.load_photo_context)
        self.tk_button_operation_change_button.bind('<Button-1>', self.ctl.operation_change)
        self.tk_button_operation_delete_button.bind('<Button-1>', self.ctl.operation_delete)
        self.tk_button_operation_add_button.bind('<Button-1>', self.ctl.operation_add)
        self.tk_button_save_operation_button.bind('<Button-1>', self.ctl.save_operation_context)
        self.tk_button_load_operation_button.bind('<Button-1>', self.ctl.load_operation_context)
        self.tk_button_scan_browser1_button.bind('<Button-1>', self.ctl.scan_browser1_enter)
        self.tk_button_scan_browser2_button.bind('<Button-1>', self.ctl.scan_browser2_enter)
        self.tk_button_scan_output.bind('<Button-1>', self.ctl.scan_output_enter)
        self.tk_button_recent_scan_button.bind('<Button-1>', self.ctl.recent_scan_recall)
        self.tk_button_scan_reopen_button.bind('<Button-1>', self.ctl.scan_reopen_enter)
        self.tk_button_select_button.bind('<Button-1>', self.ctl.start_grab_window)
        self.tk_button_select_photo_button.bind('<Button-1>', self.ctl.start_grab_photo_window)
        self.tk_button_select_photo_show.bind('<Button-1>', self.ctl.select_photo_show())
        self.tk_button_select_photo_save.bind('<Button-1>', self.ctl.select_photo_save)
        pass

    def __style_config(self):
        sty = Style()
        sty.configure(self.new_style(self.tk_button_start_scanning_button), font=("微软雅黑", -20, "bold"))
        sty.configure(self.new_style(self.tk_label_scanning_state_label), font=("微软雅黑", -20, "bold underline"))
        sty.configure(self.new_style(self.tk_label_photo4_label), font=("微软雅黑", -12))
        sty.configure(self.new_style(self.tk_button_photo4_browser_button), font=("微软雅黑 Light", -13, "bold"))
        sty.configure(self.new_style(self.tk_label_photo3_label), font=("微软雅黑", -12))
        sty.configure(self.new_style(self.tk_button_photo3_browser_button), font=("微软雅黑 Light", -13, "bold"))
        sty.configure(self.new_style(self.tk_label_photo2_label), font=("微软雅黑", -12))
        sty.configure(self.new_style(self.tk_button_photo2_browser_button), font=("微软雅黑 Light", -13, "bold"))
        sty.configure(self.new_style(self.tk_label_photo1_label), font=("微软雅黑", -12))
        sty.configure(self.new_style(self.tk_button_photo1_browser_button), font=("微软雅黑 Light", -13, "bold"))
        sty.configure(self.new_style(self.tk_button_save_photo_button), font=("微软雅黑", -15, "bold"))
        sty.configure(self.new_style(self.tk_button_load_photo_button), font=("微软雅黑", -15, "bold"))
        sty.configure(self.new_style(self.tk_label_operation_list_label), font=("微软雅黑", -19, "bold"))
        sty.configure(self.new_style(self.tk_button_operation_change_button), font=("微软雅黑", -20, "bold"))
        sty.configure(self.new_style(self.tk_button_operation_delete_button), font=("微软雅黑", -27, "bold"))
        sty.configure(self.new_style(self.tk_button_operation_add_button), font=("微软雅黑", -20, "bold"))
        sty.configure(self.new_style(self.tk_button_save_operation_button), font=("微软雅黑", -15, "bold"))
        sty.configure(self.new_style(self.tk_button_load_operation_button), font=("微软雅黑", -15, "bold"))
        sty.configure(self.new_style(self.tk_label_scan_photo_label), font=("微软雅黑", -20, "bold"))
        sty.configure(self.new_style(self.tk_label_scan_operation_label), font=("微软雅黑", -20, "bold"))
        sty.configure(self.new_style(self.tk_button_scan_browser1_button), font=("微软雅黑", -16, "bold"))
        sty.configure(self.new_style(self.tk_button_scan_browser2_button), font=("微软雅黑", -16, "bold"))
        sty.configure(self.new_style(self.tk_button_scan_output), font=("微软雅黑", -18, "bold"))
        sty.configure(self.new_style(self.tk_label_recent_scan_recall), font=("微软雅黑", -15, "bold italic underline"))
        sty.configure(self.new_style(self.tk_button_recent_scan_button), font=("微软雅黑", -16, "bold"))
        sty.configure(self.new_style(self.tk_button_scan_reopen_button), font=("微软雅黑", -25, "bold"))
        sty.configure(self.new_style(self.tk_button_select_button), font=("微软雅黑", -21, "bold"))
        sty.configure(self.new_style(self.tk_button_select_photo_button), font=("微软雅黑", -21, "bold"))
        sty.configure(self.new_style(self.tk_label_photo_start_label), font=("微软雅黑", -12))
        sty.configure(self.new_style(self.tk_label_photo_end_label), font=("微软雅黑", -12))
        sty.configure(self.new_style(self.tk_button_select_photo_show), font=("微软雅黑", -16, "bold"))
        sty.configure(self.new_style(self.tk_button_select_photo_save), font=("微软雅黑", -16, "bold"))
        pass