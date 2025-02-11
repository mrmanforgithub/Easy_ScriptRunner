import random
import json
from tkinter import *
from tkinter.ttk import *
from ttkbootstrap import *
from pytkUI.widgets import *
from tabcontrol import TabController as tab_controller
from ToolTip import *
import os

class TabGUI(Frame):
    ui: object
    def __init__(self, parent, ui):
        self.parent = parent #父窗口,即主窗口中的tabview notebook控件
        self.key_setting_path = "setting_json/key_setting.json"

        self.ext_tabs_second_tab = self.__ext_tabs_second_tab(parent)
        self.tk_frame_enter_container = self.__tk_frame_enter_container(self.ext_tabs_second_tab_0)
        # 开始循环按钮
        self.tk_button_start_scanning_button = self.__tk_button_start_scanning_button(self.tk_frame_enter_container)
        # 循环状态标签
        self.tk_label_scanning_state_label = self.__tk_label_scanning_state_label(self.tk_frame_enter_container)
        # 循环次数下拉框
        self.tk_select_box_circle_time_checkbox = self.__tk_select_box_circle_time_checkbox(
            self.tk_frame_enter_container)

        self.tk_frame_photo_all_container = self.__tk_frame_photo_all_container(self.ext_tabs_second_tab_0)

        self.tk_frame_photo_text_container = self.__tk_frame_photo_text_container(self.tk_frame_photo_all_container)[1]
        # 图片相关选项卡,默认是下列几个框,可以修改
        self.photo_containers= {}
        self.photo_frame= {}
        self.photo_label= {}
        self.photo_input= {}
        self.photo_browser_button= {}
        self.photo_scan_box= {}
        self.containers_count = self.get_container_count()
        self.bind_container(self.containers_count)

        self.photo_if_var = tk.StringVar(value="all")  # 默认选中 "全部满足"
        # 扫描策略的容器
        self.tk_frame_photo_other = self.__tk_frame_photo_other( self.tk_frame_photo_all_container)
        # 扫描策略 全部满足
        self.tk_radio_button_photo_if_all = self.__tk_radio_button_photo_if_all( self.tk_frame_photo_other)
        # 扫描策略 一个满足
        self.tk_radio_button_photo_if_one = self.__tk_radio_button_photo_if_one( self.tk_frame_photo_other)
        # 扫描策略标签
        self.tk_label_photo_if_label = self.__tk_label_photo_if_label( self.tk_frame_photo_other)
        # 窗口选择按钮
        self.tk_button_process_button = self.__tk_button_process_button(self.tk_frame_photo_other)
        # 窗口选择标签
        self.tk_label_process_label = self.__tk_label_process_label( self.tk_frame_photo_other)

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

        self.tk_button_select_all_button = self.__tk_button_select_all_button(self.tk_frame_operation_container)
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
        #当前操作
        self.tk_label_current_operation = self.__tk_label_current_operation( self.tk_frame_operation_container)
        #运行完成次数
        self.tk_label_operation_times = self.__tk_label_operation_times( self.tk_frame_operation_container)


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
        self.tk_input_scan_operation_text = self.__tk_input_scan_operation_text( self.tk_frame_scan_detail_container)

        # 重启此次扫描
        self.tk_button_scan_reopen_button = self.__tk_button_scan_reopen_button( self.tk_frame_scan_detail_container)

        # 设置默认图片
        self.tk_button_set_default_photo = self.__tk_button_set_default_photo( self.tk_frame_scan_detail_container)
        # 设置默认操作
        self.tk_button_set_default_operation = self.__tk_button_set_default_operation( self.tk_frame_scan_detail_container)
        # 设置默认快捷键/其他
        self.tk_button_set_default_key = self.__tk_button_set_default_key( self.tk_frame_scan_detail_container)
        # 设置相似度
        self.tk_button_set_default_similar = self.__tk_button_set_default_similar( self.tk_frame_scan_detail_container)


        # 设置扫描时间
        self.tk_button_set_scan_time = self.__tk_button_set_scan_time( self.tk_frame_scan_detail_container)
        # 设置自动结束定时时间
        self.tk_button_set_operation_timeout = self.__tk_button_set_operation_timeout( self.tk_frame_scan_detail_container)
        # 当前定时时间
        self.tk_label_operation_timeout_limit = self.__tk_label_operation_timeout_limit( self.tk_frame_scan_detail_container)

        self.label_value = tk.StringVar()
        self.label_value.set("75%")
        # 相似度拉条
        self.tk_scale_num_similar = self.__tk_scale_num_similar( self.tk_frame_scan_detail_container)
        # 相似度标签
        self.tk_label_label_similar = self.__tk_label_label_similar( self.tk_frame_scan_detail_container)
        # 查看错误日志
        self.tk_button_checkout_backlog = self.__tk_button_checkout_backlog( self.tk_frame_scan_detail_container)

        self.offset_value = tk.StringVar()
        self.offset_value.set("小")
        self.label_texts = ["小", "中", "大"]
        # 偏移值拉条
        self.tk_scale_num_random_offset = self.__tk_scale_num_random_offset(self.tk_frame_scan_detail_container, self.label_texts)
        # 偏移值标签
        self.tk_label_label_random_offset = self.__tk_label_label_random_offset(self.tk_frame_scan_detail_container)
        # 设计偏移值按钮
        self.tk_button_random_offset = self.__tk_button_random_offset(self.tk_frame_scan_detail_container)
        # 强相似/弱相似
        self.tk_select_box_check_out_box = self.__tk_select_box_check_out_box(self.tk_frame_scan_detail_container)

        # tab_controller实例化,在ui里可以绑定对应按钮事件函数
        self.ctl = tab_controller(self)
        # 创建ui对象,这个ui主要用于传递给tab_controller,让tab_controller可以调用侧边栏之类的位置的函数,相反也可以让ui调用这里的
        self.ui = ui
        self.similar_default_set()
        # 在ctl中创建这个ui
        self.ctl.init_ui(self.ui)
        # 添加鼠标移上去显示小贴士
        self.add_tooltips()
        # 个性化字体设置
        self.__style_config()
        # 绑定按钮事件
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
        label = Label(parent, text="未开始扫描", anchor="center", bootstyle="info inverse",background="#6c757d")
        label.place(x=8, y=2, width=176, height=40)
        return label

    def __tk_select_box_circle_time_checkbox(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="info")
        cb['values'] = ("无限循环", "循环1次", "循环10次")
        cb.current(0)
        cb.place(x=199, y=6, width=176)
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

    def __tk_frame_photo_text_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        # 创建Canvas,滚动条和显示内容的Frame
        canvas = Canvas(frame)
        scrollbar = Scrollbar(frame, orient="vertical", command=canvas.yview)
        content_frame = Frame(canvas)

        # 配置Canvas的滚动条
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # 将content_frame放入canvas中
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        # 自动更新scrollregion
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        content_frame.bind("<Configure>", on_frame_configure)
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")  # 滚动的速度可以调整
        canvas.bind_all("<MouseWheel>", on_mouse_wheel)  # Windows系统用 <MouseWheel>

        def show_context_menu(event):
            # 创建菜单
            menu = Menu(canvas, tearoff=0)
            menu.add_command(label="添加新图文行", command=lambda:self.bind_container(self.containers_count , True))
            # 显示菜单
            menu.post(event.x_root, event.y_root)
        canvas.bind("<Button-3>", show_context_menu)
        # 设置容器的固定大小
        frame.place(x=0, y=0, width=489, height=274)
        return [frame,content_frame]

    def update_photo_row(self):
        address_values = [f"地址{i+1}" for i in range(self.containers_count)]
        for i in range(self.containers_count):
            self.photo_scan_box[i]['values'] = address_values
        self.tk_select_box_photo_address['values'] = address_values
        for i in range(self.containers_count):
            self.photo_label[i].config(text=f"图文{i + 1}:")  # 重新设置label的文本
            self.photo_browser_button[i].bind('<Button-1>', lambda event,index=i: self.ctl.browse_target_image(event, index))

    def delete_selected_row(self, photo_index):
        text = photo_index.cget("text")
        photo_index =int(text[-2])-1  # 获取最后一位字符
        self.photo_containers[photo_index]['frame'].destroy()
        # 从各个列表中移除对应的元素
        self.photo_containers.pop(photo_index) # 移除photo_containers中的对应条目
        self.photo_frame.pop(photo_index)  # 从photo_frame中移除对应的frame
        self.photo_label.pop(photo_index)  # 从photo_label中移除对应的label
        self.photo_input.pop(photo_index)  # 从photo_input中移除对应的input_text
        self.photo_browser_button.pop(photo_index)  # 从photo_browser_button中移除对应的btn
        self.photo_scan_box.pop(photo_index)  # 从photo_scan_box中移除对应的cb
        # 更新容器计数
        self.containers_count -= 1
        containers = {}
        for i, (key, container) in enumerate(self.photo_containers.items()):  # .items()返回键值对
            containers[i] = container  # 将值(container)放入新字典，新的键是连续的数字
        self.photo_containers = containers  # 更新self.photo_containers为重新索引后的字典
        self.update_photo_row()
        pass

    #将container绑定
    def bind_container(self, containers_count,new_row = False):
        if new_row:
            current_index = self.containers_count
            # 调用 __create_photo_container 创建新的控件
            self.containers_count += 1
            self.photo_containers[current_index] = self.__create_photo_container(self.tk_frame_photo_text_container, current_index, self.containers_count)
            # 将新的控件添加到相应的列表中
            self.photo_frame.append(self.photo_containers[current_index]['frame'])
            self.photo_label.append(self.photo_containers[current_index]['label'])
            self.photo_input.append(self.photo_containers[current_index]['input_text'])
            self.photo_browser_button.append(self.photo_containers[current_index]['btn'])
            self.photo_scan_box.append(self.photo_containers[current_index]['cb'])
            self.update_photo_row()
        else:
            # 清除旧的控件
            if hasattr(self, 'photo_containers'):
                for container in self.photo_containers.values():
                    container['frame'].destroy()
            # 创建新的控件
            self.photo_containers = {}
            for i in range(containers_count):
                self.photo_containers[i] = self.__create_photo_container(self.tk_frame_photo_text_container, i,containers_count)
            self.containers_count = containers_count
            self.photo_frame = [self.photo_containers[i]['frame'] for i in range(self.containers_count)]
            self.photo_label = [self.photo_containers[i]['label'] for i in range(self.containers_count)]
            self.photo_input = [self.photo_containers[i]['input_text'] for i in range(self.containers_count)]
            self.photo_browser_button = [self.photo_containers[i]['btn'] for i in range(self.containers_count)]
            self.photo_scan_box = [self.photo_containers[i]['cb'] for i in range(self.containers_count)]
            for i in range(self.containers_count):
                self.photo_browser_button[i].bind('<Button-1>', lambda event,index=i: self.ctl.browse_target_image(event, index))

    #图片选项卡的重复化内容
    def __create_photo_container(self, parent,photo_index,containers_count):
        # 创建一个容器frame
        frame = Frame(parent, bootstyle="default", relief="solid", width=480, height=61)
        frame.pack(fill="x", pady=5, padx=5)

        # 创建标签
        label = Label(frame, text=f"图文{photo_index + 1}:", anchor="center", bootstyle="secondary")
        label.pack(side="left", padx=5, pady=5)

        # 创建文本输入框
        input_text = Entry(frame, bootstyle="info", width=25)
        input_text.pack(side="left", padx=5, pady=5)

        # 创建浏览按钮, width=70, height=30
        btn = Button(frame, text="浏览", takefocus=False, bootstyle="info")
        btn.pack(side="left", padx=5, pady=5)

        address_values = [f"地址{i+1}" for i in range(containers_count)]
        # 创建选择框
        cb = Combobox(frame, state="readonly", bootstyle="default", width=5, height=30)
        cb['values'] = address_values
        cb.current(0)
        cb.pack(side="left" ,padx=5, pady=5)

                # 创建右键菜单
        def show_context_menu(event):
            # 创建菜单
            menu = Menu(label, tearoff=0)
            menu.add_command(label="删除此图文行", command=lambda:self.delete_selected_row(label))
            menu.add_command(label="添加新图文行", command=lambda:self.bind_container(self.containers_count , True))
            # 显示菜单
            menu.post(event.x_root, event.y_root)

        # 绑定右键点击事件，弹出菜单
        label.bind("<Button-3>", show_context_menu)
        input_text.bind("<Button-3>", show_context_menu)
        btn.bind("<Button-3>", show_context_menu)

        # 返回所有部件，方便存放在一个字典里
        return {
            'frame': frame,
            'label': label,
            'input_text': input_text,
            'btn': btn,
            'cb': cb
        }


    def __tk_frame_photo_save_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=10, y=276, width=560, height=39)
        return frame

    def __tk_button_save_photo_button(self, parent):
        btn = Button(parent, text="单 独 保 存", takefocus=False, bootstyle="info")
        btn.place(x=8, y=4, width=272, height=30)
        return btn

    def __tk_button_load_photo_button(self, parent):
        btn = Button(parent, text="单 独 读 取", takefocus=False, bootstyle="default")
        btn.place(x=288, y=4, width=272, height=30)
        return btn

    def __tk_frame_photo_other(self,parent):
        frame = Frame(parent,bootstyle="default")
        frame.place(x=490, y=10, width=79, height=261)
        return frame
    def __tk_radio_button_photo_if_all(self,parent):
        rb = Radiobutton(parent,text="全部"+"\n满足",bootstyle="default",variable=self.photo_if_var, value="all")
        rb.place(x=8, y=51, width=69, height=40)
        return rb
    def __tk_radio_button_photo_if_one(self,parent):
        rb = Radiobutton(parent,text="满足"+"\n一个",bootstyle="default", variable=self.photo_if_var, value="one")
        rb.place(x=8, y=100, width=69, height=40)
        return rb
    def __tk_label_photo_if_label(self,parent):
        label = Label(parent,text="满足策略",anchor="center", bootstyle="default")
        label.place(x=4, y=2, width=73, height=48)
        return label

    def __tk_button_process_button(self,parent):
        btn = Button(parent, text="选择"+"\n窗口", takefocus=False, bootstyle="default")
        btn.place(x=0, y=205, width=78, height=56)
        return btn
    def __tk_label_process_label(self,parent):
        label = Label(parent,text="窗口选择"+"\n无",anchor="center", bootstyle="default")
        label.place(x=2, y=150, width=75, height=55)
        return label


    def __tk_frame_select_box(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=9, y=320, width=560, height=70)
        return frame

    def __tk_button_select_button(self, parent):
        btn = Button(parent, text="手动框选", takefocus=False, bootstyle="default")
        btn.place(x=288, y=4, width=130, height=60)
        return btn

    def __tk_button_select_photo_button(self, parent):
        btn = Button(parent, text="一键截图", takefocus=False, bootstyle="default")
        btn.place(x=432, y=4, width=130, height=60)
        return btn

    def __tk_select_box_photo_address(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        address_values = [f"地址{i+1}" for i in range(self.containers_count)]
        if not address_values:
            address_values = ["地址1"]
        cb['values'] = address_values
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

    def __tk_button_select_photo_save(self, parent):
        btn = Button(parent, text="删除地址", takefocus=False, bootstyle="info")
        btn.place(x=7, y=4, width=120, height=60)
        return btn

    def __tk_frame_operation_container(self, parent):
        frame = Frame(parent, bootstyle="default")
        frame.place(x=0, y=0, width=577, height=455)
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
        btn.place(x=144, y=320, width=427, height=63)
        return btn

    def __tk_button_select_all_button(self, parent):
        btn = Button(parent, text="全选", takefocus=False, bootstyle="info")
        btn.place(x=5, y=320, width=130, height=63)
        return btn

    def __tk_button_operation_add_button(self, parent):
        btn = Button(parent, text="添加", takefocus=False, bootstyle="info")
        btn.place(x=300, y=220, width=130, height=50)
        return btn

    def __tk_select_box_operation_list(self, parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("等待时间", "检查匹配", "鼠标操作", "键盘操作","鼠标拖动", "滚轮操作", "开启扫描", "关闭扫描")
        cb.current(0)
        cb.place(x=140, y=220, width=140)
        return cb

    def __tk_table_operation_box(self, parent):
        # 表头字段 表头宽度
        columns = {"id": 114, "操作名称": 114, "操作参数": 401}
        tk_table = Treeview(parent, show="headings", columns=list(columns), bootstyle="primary")
        for text, width in columns.items():  # 批量设置列属性
            tk_table.heading(text, text=text, anchor='center')
            tk_table.column(text, anchor='center', width=width, stretch=False)  # stretch 不自动拉伸

        tk_table.place(x=1, y=1, width=575, height=192)
        self.create_bar(parent, tk_table, True, False, 1, 1, 575, 180, 577, 398)
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

    def __tk_label_current_operation(self,parent):
        label = Label(parent,text="目前执行的操作：",anchor="center", bootstyle="secondary")
        label.place(x=0, y=390, width=337, height=42)
        return label

    def __tk_label_operation_times(self,parent):
        label = Label(parent,text="运行完成：",anchor="center", bootstyle="secondary")
        label.place(x=343, y=390, width=233, height=44)
        return label



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

    def __tk_input_scan_operation_text(self,parent):
        ipt = Entry(parent, bootstyle="primary")
        ipt.place(x=317, y=45, width=150, height=30)
        return ipt


    def __tk_button_scan_reopen_button(self,parent):
        btn = Button(parent, text="初始化此扫描", takefocus=False,bootstyle="primary")
        btn.place(x=6, y=335, width=565, height=55)
        return btn

    def __tk_button_set_default_photo(self,parent):
        btn = Button(parent, text="设置默认图片", takefocus=False,bootstyle="info")
        btn.place(x=6, y=275, width=150, height=50)
        return btn

    def __tk_button_set_default_operation(self,parent):
        btn = Button(parent, text="设置默认事件", takefocus=False,bootstyle="info")
        btn.place(x=163, y=275, width=134, height=50)
        return btn

    def __tk_button_set_default_key(self,parent):
        btn = Button(parent, text="设置其他", takefocus=False,bootstyle="default")
        btn.place(x=302, y=275, width=137, height=49)
        return btn

    def __tk_button_set_scan_time(self,parent):
        btn = Button(parent, text="设置间隔", takefocus=False,bootstyle="default")
        btn.place(x=444, y=275, width=125, height=49)
        return btn

    def __tk_button_set_default_similar(self,parent):
        btn = Button(parent, text="设置相似度", takefocus=False,bootstyle="info")
        btn.place(x=6, y=233, width=150, height=30)
        return btn

    def __tk_scale_num_similar(self,parent):
        def update_label(scale_value):
            integer_value = int(float(scale_value))  # 转换为整数
            self.label_value.set(f"{integer_value}%")
        scale = Scale(parent, from_=0, to=100, orient=HORIZONTAL, bootstyle="info", command=update_label)
        scale.set(75)
        scale.place(x=170, y=233, width=266, height=30)
        return scale

    def __tk_label_label_similar(self,parent):
        label = Label(parent,textvariable=self.label_value,anchor="center", bootstyle="info")
        label.place(x=444, y=233, width=113, height=30)
        return label

    def __tk_button_checkout_backlog(self,parent):
        btn = Button(parent, text="错误日志", takefocus=False,bootstyle="default")
        btn.place(x=442, y=97, width=121, height=79)
        return btn

    def __tk_button_random_offset(self,parent):
        btn = Button(parent, text="设置随机偏移", takefocus=False,bootstyle="default")
        btn.place(x=6, y=188, width=150, height=30)
        return btn

    def __tk_scale_num_random_offset(self,parent, label_texts):
        # 设置偏移量大小的scale控件
        updating_position = False
        def update_label(scale_value):
            nonlocal updating_position
            scale_int_value = int(float(scale_value))
            if scale_int_value < 25:
                scale_int_value = 0
            elif scale_int_value < 75:
                scale_int_value = 50
            else:
                scale_int_value = 100
            self.offset_value.set(label_texts[scale_int_value // 50])

            if not updating_position:
                updating_position = True
                scale.set(scale_int_value)
                updating_position = False

        scale = Scale(parent, from_=0, to=100, orient=HORIZONTAL, bootstyle="primary", command=update_label)
        scale.set(0)
        scale.place(x=170, y=190, width=266, height=30)
        update_label(scale.get())
        return scale

    def __tk_label_label_random_offset(self,parent):
        label = Label(parent,textvariable=self.offset_value, anchor="center", bootstyle="primary")
        label.place(x=444, y=190, width=113, height=30)
        return label

    def __tk_select_box_check_out_box(self,parent):
        cb = Combobox(parent, state="readonly", bootstyle="default")
        cb['values'] = ("强相似","弱相似")
        cb.current(0)
        cb.place(x=6, y=98, width=150, height=30)
        return cb

    def __tk_button_set_operation_timeout(self,parent):
        btn = Button(parent, text="设置定时结束", takefocus=False,bootstyle="default")
        btn.place(x=6, y=144, width=150, height=30)
        return btn

    def __tk_label_operation_timeout_limit(self,parent):
        label = Label(parent,text="距离停止扫描还剩下( )秒",anchor="center", bootstyle="secondary inverse")
        label.place(x=165, y=98, width=271, height=80)
        return label


#工具/轮子代码
    def similar_default_set(self):
        json_file = self.key_setting_path
        try:
            with open(json_file, "r", encoding="utf-8") as file:
                settings = json.load(file)
        except FileNotFoundError as e:
            tab_controller.error_print(e)

        # 获取相似度值
        if "else" in settings and "相似度" in settings["else"]:
            similarity_value = settings["else"]["相似度"]
            similarity_percent = str(int(float(similarity_value) * 100)) + "%"
            similarity_num = int(float(similarity_value) * 100)
            self.label_value.set(similarity_percent)
            self.tk_scale_num_similar.set(similarity_num)
        else:
            tab_controller.error_print(None,"缺少键值")

    #右键显示菜单
    def show_context_menu(self, event):
        selected_item = self.tk_table_operation_box.identify_row(event.y)
        if selected_item:  # 如果点到了某一行
            self.tk_table_operation_box.selection_set(selected_item)  # 选中该行
        else:  # 如果没点到任何行
            self.tk_table_operation_box.selection_remove(self.tk_table_operation_box.selection())  # 取消所有选中项
            return  # 不显示菜单
            # 获取当前选中行的索引
        selected_index = self.tk_table_operation_box.index(selected_item)
        total_rows = len(self.tk_table_operation_box.get_children())  # 获取总行数
        context_menu = Menu(self.tk_table_operation_box, tearoff=0)
        # 向上移动：如果是第一行，禁用
        if selected_index == 0:
            context_menu.add_command(label="向上移动", state="disabled")
        else:
            context_menu.add_command(label="向上移动", command=self.ctl.operation_up)
        # 向下移动：如果是最后一行，禁用
        if selected_index == total_rows - 1:
            context_menu.add_command(label="向下移动", state="disabled")
        else:
            context_menu.add_command(label="向下移动", command=self.ctl.operation_down)
        context_menu.add_command(label="复制此操作", command=self.ctl.operation_copy)
        context_menu.add_command(label="修改此操作", command=lambda: self.ctl.operation_change(change_keep=True))
        context_menu.add_command(label="删除此操作", command=self.ctl.operation_delete)
        context_menu.post(event.x_root, event.y_root)

    # 当左键选择了空白区域的时候,取消当前选中
    def clear_select(self, event):
        selected_item = self.tk_table_operation_box.identify_row(event.y)
        if not selected_item:  # 如果点到了某一行
            self.tk_table_operation_box.selection_remove(self.tk_table_operation_box.selection())  # 取消所有选中项

    #读取这页包含多少个图文
    def get_container_count(self):
        # 显示图片相关地址
        try:
            with open("setting_json/default_photo.json", "r", encoding='utf-8') as json_file:
                data = json.load(json_file)
        except:
            return 4  # 如果没找到,默认四个
        return data.get("图文数量", 4)

#事件绑定代码
    def __event_bind(self):
        #开始扫描
        self.tk_button_start_scanning_button.bind('<Button-1>', self.ctl.start_scanning)
        #循环次数
        self.tk_select_box_circle_time_checkbox.bind('<<ComboboxSelected>>',
                                                        lambda event: self.ctl.confirm_selection(event,
                                                                                                self.tk_select_box_circle_time_checkbox.get()))
        # 确认地址
        self.tk_select_box_photo_address.bind('<<ComboboxSelected>>',self.ctl.confirm_address_selection)

        # 单独图片保存
        self.tk_button_save_photo_button.bind('<Button-1>', self.ctl.save_photo_context)
        # 单独图片读取
        self.tk_button_load_photo_button.bind('<Button-1>', self.ctl.load_photo_context)

        self.tk_button_process_button.bind('<Button-1>', self.ctl.open_window_selection)

        #绑定右键显示菜单
        self.tk_table_operation_box.bind('<Button-3>', self.show_context_menu)

        self.tk_table_operation_box.bind('<Button-1>', self.clear_select)
        # 修改操作按钮
        self.tk_button_operation_change_button.bind('<Button-1>', self.ctl.operation_change)
        # 删除操作按钮
        self.tk_button_operation_delete_button.bind('<Button-1>', self.ctl.operation_delete)
        # 添加操作按钮
        self.tk_button_operation_add_button.bind('<Button-1>', self.ctl.operation_add)
        # 全选操作按钮
        self.tk_button_select_all_button.bind('<Button-1>', self.ctl.operation_select_all)
        # 单独操作保存
        self.tk_button_save_operation_button.bind('<Button-1>', self.ctl.save_operation_context)
        # 单独操作读取
        self.tk_button_load_operation_button.bind('<Button-1>', self.ctl.load_operation_context)

        # 图片位置读取
        self.tk_button_scan_browser1_button.bind('<Button-1>', self.ctl.scan_browser1_enter)
        # 操作位置读取
        self.tk_button_scan_browser2_button.bind('<Button-1>', self.ctl.scan_browser2_enter)
        # 操作图片合成输出
        self.tk_button_scan_output.bind('<Button-1>', self.ctl.scan_output_enter)

        # 重新初始化
        self.tk_button_scan_reopen_button.bind('<Button-1>', lambda event: self.ctl.scan_reopen_enter(event, self, self.parent, self.ui))

        # 设置默认图片
        self.tk_button_set_default_photo.bind('<Button-1>',self.ctl.set_default_photo)
        # 设置默认操作
        self.tk_button_set_default_operation.bind('<Button-1>',self.ctl.set_default_operation)
        # 设置默认快捷键
        self.tk_button_set_default_key.bind('<Button-1>',self.ctl.set_default_key)
        # 设置默认相似度
        self.tk_button_set_default_similar.bind('<Button-1>',lambda event: self.ctl.set_default_similar(event, self.label_value.get()))

        #设置定时停止时间
        self.tk_button_set_operation_timeout.bind('<Button-1>',self.ctl.set_operaton_timeout)
        #设置扫描间隔
        self.tk_button_set_scan_time.bind('<Button-1>',self.ctl.set_scan_time)


        # 读取日志
        self.tk_button_checkout_backlog.bind('<Button-1>',self.ctl.check_out_log)

        # 设置偏差值
        self.tk_button_random_offset.bind('<Button-1>',self.ctl.set_random_offset)
        # 设置强相似/弱相似
        self.tk_select_box_check_out_box.bind('<<ComboboxSelected>>',self.ctl.set_default_check)

        # 手动框选
        self.tk_button_select_button.bind('<Button-1>',self.ctl.open_manual_selection_window)
        # 手动截图
        self.tk_button_select_photo_button.bind('<Button-1>',lambda event:  self.ctl.open_manual_selection_window(event,grab_photo=True))

        # 保存选择图片的地址
        self.tk_button_select_photo_save.bind('<Button-1>', self.ctl.address_change)
        pass

    def __style_config(self):
        # 更改字体大小
        sty = Style()
        #开始扫描按钮
        sty.configure(self.new_style(self.tk_button_start_scanning_button), font=("微软雅黑", -20, "bold"))
        #扫描状态标签
        sty.configure(self.new_style(self.tk_label_scanning_state_label), font=("微软雅黑", -20, "bold"))

        sty.configure(self.new_style(self.tk_button_save_photo_button), font=("微软雅黑", -15, "bold"))
        sty.configure(self.new_style(self.tk_button_load_photo_button), font=("微软雅黑", -15, "bold"))
        #图片扫描策略容器
        sty.configure(self.new_style(self.tk_frame_photo_other), borderwidth=1, relief="solid")
        #一键截图按钮
        sty.configure(self.new_style(self.tk_button_select_photo_button), font=("微软雅黑", -16, "bold"))
        #手动框选按钮
        sty.configure(self.new_style(self.tk_button_select_button), font=("微软雅黑", -16, "bold"))
        #选择窗口
        sty.configure(self.new_style(self.tk_button_process_button), font=("微软雅黑", -12, "bold"))
        #窗口选择标签
        sty.configure(self.new_style(self.tk_label_process_label), font=("微软雅黑", -12, "bold"))
        #图片地址记录
        sty.configure(self.new_style(self.tk_button_select_photo_save), font=("微软雅黑", -16, "bold"))

        sty.configure(self.new_style(self.tk_label_operation_list_label), font=("微软雅黑", -19, "bold"))
        sty.configure(self.new_style(self.tk_button_operation_change_button), font=("微软雅黑", -20, "bold"))
        sty.configure(self.new_style(self.tk_button_operation_delete_button), font=("微软雅黑", -27, "bold"))
        sty.configure(self.new_style(self.tk_button_operation_add_button), font=("微软雅黑", -20, "bold"))
        sty.configure(self.new_style(self.tk_button_save_operation_button), font=("微软雅黑", -15, "bold"))
        sty.configure(self.new_style(self.tk_button_load_operation_button), font=("微软雅黑", -15, "bold"))
        sty.configure(self.new_style(self.tk_button_select_all_button),font=("微软雅黑", -20, "bold"))

        sty.configure(self.new_style(self.tk_label_scan_photo_label), font=("微软雅黑", -20, "bold"))
        sty.configure(self.new_style(self.tk_label_scan_operation_label), font=("微软雅黑", -20, "bold"))
        sty.configure(self.new_style(self.tk_button_scan_browser1_button), font=("微软雅黑", -16, "bold"))
        sty.configure(self.new_style(self.tk_button_scan_browser2_button), font=("微软雅黑", -16, "bold"))
        sty.configure(self.new_style(self.tk_button_scan_output), font=("微软雅黑", -18, "bold"))

        sty.configure(self.new_style(self.tk_button_scan_reopen_button),font=("微软雅黑",-25,"bold"))
        sty.configure(self.new_style(self.tk_button_set_default_photo),font=("微软雅黑",-18,"bold"))
        sty.configure(self.new_style(self.tk_button_set_default_operation),font=("微软雅黑",-18,"bold"))
        sty.configure(self.new_style(self.tk_button_set_default_key),font=("微软雅黑",-18,"bold"))

        sty.configure(self.new_style(self.tk_label_label_similar),font=("微软雅黑",-20,"bold"))
        sty.configure(self.new_style(self.tk_button_checkout_backlog),font=("微软雅黑",-20,"bold"))

        sty.configure(self.new_style(self.tk_label_label_random_offset),font=("微软雅黑",-20,"bold"))

        sty.configure(self.new_style(self.tk_label_photo_start_label), font=("微软雅黑", -12))
        sty.configure(self.new_style(self.tk_label_photo_end_label), font=("微软雅黑", -12))


        sty.configure(self.new_style(self.tk_label_operation_timeout_limit),font=("微软雅黑",-17,"bold"))
        sty.configure(self.new_style(self.tk_button_set_scan_time),font=("微软雅黑",-18,"bold"))
        sty.configure(self.new_style(self.tk_label_current_operation),font=("微软雅黑",-18))
        sty.configure(self.new_style(self.tk_label_operation_times),font=("微软雅黑",-18))
        pass

    def add_tooltips(self):
        # 为按钮创建浮动标签，可以查看按钮的作用
        create_tooltip(self.tk_button_start_scanning_button, "按下开始扫描")
        create_tooltip(self.tk_label_scanning_state_label, "扫描的当前状态")
        create_tooltip(self.tk_select_box_circle_time_checkbox, "选择扫描的次数")
        try:
            create_tooltip(self.photo_label[0], "右键可以新建/删除此图文")
            create_tooltip(self.photo_browser_button[0], "浏览对应图片的文件(也可以直接填入文字,进行文字识别)")
        except:
            pass

        create_tooltip(self.tk_button_load_photo_button, "单独读取图片记录到本页")
        create_tooltip(self.tk_button_save_photo_button, "单独保存本页图片记录")
        create_tooltip(self.tk_button_select_button, "手动框选一个扫描地址")
        create_tooltip(self.tk_button_select_photo_button, "截图并且将框选地址填入")
        create_tooltip(self.tk_select_box_photo_address, "当前地址信息")
        create_tooltip(self.tk_button_select_photo_save, "记录下当前地址信息")
        create_tooltip(self.tk_label_photo_if_label, "设置执行策略,满足一个或者全部则执行操作")
        create_tooltip(self.tk_label_process_label, "只有该窗口被选中时才会扫描")
        create_tooltip(self.tk_button_process_button,"选择一个窗口名称,只有这个窗口在最前方时才会执行操作")

        create_tooltip(self.tk_button_operation_change_button, "修改对应行的操作内容")
        create_tooltip(self.tk_button_operation_delete_button, "删除对应行的操作内容")
        create_tooltip(self.tk_button_operation_add_button, "添加一行新的操作进入")
        create_tooltip(self.tk_select_box_operation_list, "选择一项操作，按下添加即可")
        create_tooltip(self.tk_button_save_operation_button, "单独保存本页操作记录")
        create_tooltip(self.tk_button_load_operation_button, "单独读取操作记录到本页")

        create_tooltip(self.tk_button_scan_browser1_button, "在文件夹中浏览图片记录")
        create_tooltip(self.tk_button_scan_browser2_button, "在文件夹中浏览操作记录")
        create_tooltip(self.tk_button_scan_output, "将图片与操作融合输出一个全局文件")
        create_tooltip(self.tk_button_scan_reopen_button, "按照默认图片与操作初始化这页的扫描")
        create_tooltip(self.tk_button_set_default_operation, "设置默认的操作")
        create_tooltip(self.tk_button_set_default_key, "设置默认的快捷键")
        create_tooltip(self.tk_button_set_default_similar, "设置扫描相似度的阈值")
        create_tooltip(self.tk_scale_num_similar, "扫描相似度的滑条")
        create_tooltip(self.tk_button_set_default_photo, "设置默认的图片记录")
        create_tooltip(self.tk_button_checkout_backlog, "查看错误日志")
        create_tooltip(self.tk_select_box_check_out_box, "弱相似有滤镜变化或者旋转缩放的图片也算做扫描成功  强相似必须完全相似")
        create_tooltip(self.tk_button_random_offset, "设置操作位置偏移值，防止被视为机器人")
