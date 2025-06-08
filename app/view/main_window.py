# coding: utf-8
import keyboard
import time
import psutil

from PyQt5.QtCore import QUrl, QSize, QTimer,QEvent,Qt
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QApplication,QSystemTrayIcon,QHBoxLayout,QButtonGroup


from qfluentwidgets import (Action, NavigationItemPosition, FluentWindow,ToggleButton,
                            SplashScreen, isDarkTheme,SystemThemeListener,InfoBarPosition,StateToolTip,RoundMenu,MessageBoxBase)
from qfluentwidgets import FluentIcon as FIF


from .home_interface import HomeInterface
from .recently_open_interface import RecentlyOpenInterface
from .support_interface import SupportInterface
from .setting_interface import SettingInterface
from ..common.config import  cfg,TAB_PATH,KEY_PATH,REPO_URL
from ..common.signal_bus import signalBus
from ..common.photo_tool import photo_tool
from ..common import resource
from ..common.check_update import checkUpdate




class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()  # 调用父类 FluentWindow 的构造函数
        self.initWindow()  # 初始化窗口
        self.themeListener = SystemThemeListener(self)
        self.stateTooltip = None

        # 创建不同的子界面
        self.homeInterface = HomeInterface(self)
        self.recentlyOpenInterface = RecentlyOpenInterface(self)
        self.supportInterface = SupportInterface(self)
        self.settingInterface = SettingInterface(self)
        # 启用窗体的毛玻璃效果
        self.navigationInterface.setAcrylicEnabled(True)


        self.routeKeyToInterface = {
            'home': self.homeInterface,
            'history': self.recentlyOpenInterface,
            'support': self.supportInterface,
            'setting': self.settingInterface,
        }


        # 连接信号和槽
        self.connectSignalToSlot()

        # 初始化导航栏
        self.initNavigation()

        #初始化快捷键绑定
        self.bind_global_shortcut()

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(":/images/logo.png"))
        self.tray_icon.setVisible(True)

        # 系统托盘图标
        self.initTray()

        #初始化默认扫描页
        self.initHome()

        #检查是否需要更新
        checkUpdate(self, timeout=5, flag=cfg.get(cfg.checkUpdateAtStartUp))

        # 完成启动画面
        self.splashScreen.finish()
        self.themeListener.start()


    #初始化扫描页面内容
    def initHome(self):
        defaultTab =  cfg.get(cfg.defaultTab)
        try:
            if defaultTab == "Empty":
                self.homeInterface.tabs.addNewTab(self.tr("默认扫描"))
            elif defaultTab == "Custom":
                data = photo_tool.loadDataFromPath(TAB_PATH)
                self.homeInterface.tabs.addDataTab(data,default=True)
            else:
                photo_tool.show_infobar(self,self.tr("错误"),self.tr("不存在的设置！"),pos=InfoBarPosition.TOP)
        except Exception as e:
            photo_tool.show_infobar(self,self.tr("错误"),self.tr("初始化扫描页面失败！"),pos=InfoBarPosition.TOP)


    #创建托盘图标
    def initTray(self):
        # 创建右键菜单
        self.tray_menu = RoundMenu()

        # 创建菜单项
        restore_action = Action(FIF.FULL_SCREEN,self.tr("恢复窗口"), self)
        restore_action.triggered.connect(self.restore_window)

        start_scan_action = Action(FIF.PLAY,self.tr("开始扫描"), self)
        start_scan_action.triggered.connect(self.start_scan)

        stop_scan_action = Action(FIF.PAUSE,self.tr("停止扫描"))
        stop_scan_action.triggered.connect(self.stop_scan)

        quit_action = Action(FIF.POWER_BUTTON,self.tr("退出软件"))
        quit_action.triggered.connect(self.quit_app)

        # 将菜单项添加到右键菜单
        self.tray_menu.addAction(restore_action)
        self.tray_menu.addAction(start_scan_action)
        self.tray_menu.addAction(stop_scan_action)
        self.tray_menu.addAction(quit_action)

        # 设置托盘图标的右键菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        # 显示托盘图标
        self.tray_icon.show()


    #恢复窗口
    def restore_window(self):
        self.show()
        self.activateWindow()


    #重写关闭界面事件
    def quit_app(self):
        self.stop_quit()
        QApplication.quit()


    #绑定快捷键
    def bind_global_shortcut(self):
        try:
            if cfg.get(cfg.keybind) == "default":
                keyboard.add_hotkey("alt+o", self.start_scan)
                keyboard.add_hotkey("alt+p", self.stop_scan)
            else:
                keybind = photo_tool.read_config_value(KEY_PATH,"hotkeys")
                if keybind:
                    start_hotkey = keybind[0]  # 第一个组合键绑定 start_scan
                    stop_hotkey = keybind[1]   # 第二个组合键绑定 stop_scan
                    start_modifiers = start_hotkey[0]
                    start_key = start_hotkey[1]
                    start_combined_hotkey = f"{start_modifiers}+{start_key}"
                    stop_modifiers = stop_hotkey[0]
                    stop_key = stop_hotkey[1]
                    stop_combined_hotkey = f"{stop_modifiers}+{stop_key}"
                    keyboard.add_hotkey(start_combined_hotkey, self.start_scan)
                    keyboard.add_hotkey(stop_combined_hotkey, self.stop_scan)
        except Exception as e:
            message = self.tr("绑定快捷键出错") + f"{e}"
            photo_tool.show_infobar(self,self.tr("错误"),message,pos=InfoBarPosition.TOP)


    #关闭/开始扫描,提供信号,每个页面单独接受信号并且实现功能--》全部页面均关闭/开始扫描
    def stop_scan(self):
        signalBus.stop_scan_signal.emit()
        signalBus.maximizeSignal.emit()
        try:
            time.sleep(0.1)
            signalBus.maximizeSignal.emit()
            photo_tool.window_show_top("ScriptRunner")
        except:
            pass


    def start_scan(self):
        signalBus.start_scan_signal.emit()


    def start_cycle_scan(self):
        signalBus.cycle_start_signal.emit()


    def save_scan_json(self):
        signalBus.save_scan_signal.emit()



    def load_scan_json(self):
        try:
            loadmethod =  LoadMethodBox(self.window())
            if loadmethod.exec_():
                method = loadmethod.load_clear.isChecked()
                signalBus.load_scan_signal.emit(method)
        except Exception as e:
            photo_tool.error_print(e)



    def showNormal(self):
        super().showNormal()  # 调用父类的 showNormal 方法，恢复窗口到正常状态
        self.activateWindow()  # 激活窗口，使其成为前台窗口
        self.raise_()  # 确保窗口位于其他窗口之上



    #展示下载状态
    def show_download_status(self,bool,result):
        """处理下载完成后的操作。"""
        if bool and not result:
            if not self.stateTooltip:
                self.stateTooltip = StateToolTip(
                        self.tr('更新程序运行中'), self.tr('可以随时关闭此标签'), self.window())
                self.stateTooltip.move(self.stateTooltip.getSuitablePos())
                self.stateTooltip.show()
        elif not bool and result:
            if self.stateTooltip:
                self.stateTooltip.setTitle(self.tr("下载失败"))
                self.stateTooltip.setContent(
                self.tr("更新失败(╥╯﹏╰╥)")+f"{result}")
                self.stateTooltip.setState(True)
                self.stateTooltip = None
        elif bool and result:
            if self.stateTooltip:
                self.stateTooltip.setState(True)
                self.stateTooltip = None
                photo_tool.show_infobar(self,"",self.tr("文件已下载到:")+f"{result}",pos=InfoBarPosition.TOP,method="success")



    # 连接信号到槽函数
    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.switchToInterface.connect(self.switchToInterfaceByRoute)
        signalBus.minimizeSignal.connect(self.showMinimized)
        signalBus.maximizeSignal.connect(self.showNormal)
        signalBus.hideSignal.connect(self.hide)
        signalBus.showSignal.connect(self.show)
        signalBus.download_signal.connect(self.show_download_status)
        signalBus.main_infobar_signal.connect(self.show_mainbar)
        signalBus.supportSignal.connect(self.onSupport)


    # 初始化导航栏项
    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('扫描主页'))
        self.addSubInterface(self.recentlyOpenInterface, FIF.HISTORY, self.tr('最近打开'), NavigationItemPosition.TOP)

        self.navigationInterface.addSeparator()  # 添加分隔符

        self.navigationInterface.addItem(
            routeKey='save',
            icon=FIF.SAVE,
            text=self.tr('保存扫描'),
            onClick=self.save_scan_json,
            selectable=False,
            tooltip=self.tr('保存当前主页的所有数据到文件'),
            position=NavigationItemPosition.SCROLL
        )
        self.navigationInterface.addItem(
            routeKey='load',
            icon=FIF.DOWNLOAD,
            text=self.tr('读取扫描'),
            onClick=self.load_scan_json,
            selectable=False,
            tooltip=self.tr('读取扫描文件并且生成对应页面'),
            position=NavigationItemPosition.SCROLL
        )


        self.navigationInterface.addItem(
            routeKey='start',
            icon=FIF.PLAY,
            text=self.tr('开始扫描'),
            selectable=False,
            tooltip=self.tr('开始扫描'),
            position=NavigationItemPosition.SCROLL
        )
        self.navigationInterface.addItem(
            routeKey='start_all',
            icon=FIF.PLAY,
            text=self.tr('开始全部扫描'),
            onClick=self.start_scan,
            selectable=False,
            tooltip=self.tr('打开全部扫描'),
            position=NavigationItemPosition.SCROLL,
            parentRouteKey= 'start'
        )
        self.navigationInterface.addItem(
            routeKey='start_by',
            icon=FIF.PLAY,
            text=self.tr('循环扫描'),
            onClick=self.start_cycle_scan,
            selectable=False,
            tooltip=self.tr('循环开始扫描'),
            position=NavigationItemPosition.SCROLL,
            parentRouteKey= 'start'
        )
        self.navigationInterface.addItem(
            routeKey='stop_all',
            icon=FIF.PAUSE,
            text=self.tr('停止扫描'),
            onClick=self.stop_scan,
            selectable=False,
            tooltip=self.tr('停止扫描'),
            position=NavigationItemPosition.SCROLL
        )

        # self.navigationInterface.addItem(
        #     routeKey='test',
        #     icon=ScriptIcon.LOCK,
        #     text=self.tr('测试按钮'),
        #     onClick=self.test,
        #     selectable=False,
        #     tooltip=self.tr('测试扫描'),
        #     position=pos
        # )

        # 向底部添加自定义项
        self.addSubInterface(self.supportInterface, FIF.INFO, self.tr('软件信息'), NavigationItemPosition.BOTTOM)
        # 设置“设置”界面项
        self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('设置'), NavigationItemPosition.BOTTOM)


    def test(self):
        pass
        # try:
        #     loadmethod =  TestBox(self.window())
        #     if loadmethod.exec_():
        #         pass
        # except Exception as e:
        #     pass


    #点击后打开网站
    def onSupport(self):
        QDesktopServices.openUrl(QUrl(REPO_URL))



    def initWindow(self):
        # 初始化窗口尺寸和标题
        self.resize(900, 640)
        self.setMinimumWidth(760)
        self.setWindowIcon(QIcon(':/images/logo.png'))  # 设置窗口图标
        self.setWindowTitle('ScriptRunner')  # 设置窗口标题

        # 设置 Mica 效果（透明毛玻璃效果）
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # 创建启动画面(Splash Screen)
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        # 获取屏幕尺寸，居中显示窗口
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show()
        QApplication.processEvents()  # 处理应用事件



    #修改界面大小事件
    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())  # 启动画面随窗口尺寸调整



    def changeEvent(self, event):
        """ 窗口状态变化事件 """
        if event.type() == QEvent.WindowStateChange:
            main_window = self.window()  # 获取主窗口
            if main_window.isMinimized():  # 如果主窗口最小化
                signalBus.is_minimize.emit()
            else:
                signalBus.is_normal.emit()
        super().changeEvent(event)



    def closeEvent(self, e):
        if cfg.get(cfg.closeEnabled):
            e.ignore()
            self.hide()
        else:
            self.stop_quit()
            super().closeEvent(e)



    def stop_quit(self):
        signalBus.stop_scan_signal.emit()
        keyboard.unhook_all()
        self.themeListener.terminate()
        self.themeListener.deleteLater()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == 'PaddleOCR-json.exe':
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass



    #主题切换
    def _onThemeChangedFinished(self):
        super()._onThemeChangedFinished()

        # retry
        if self.isMicaEffectEnabled():
            QTimer.singleShot(100, lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()))



    #主界面展示info_bar
    def show_mainbar(self,title,text,pos,method):
        """主界面提示工具, 四个参数 title / text / pos / method"""
        if self.isMinimized():
            return
        title = self.tr(title)
        text = self.tr(text)
        photo_tool.show_infobar(self, title, text, pos=getattr(InfoBarPosition, pos, InfoBarPosition.TOP),method=method)



    def switchToInterfaceByRoute(self, routeKey):
        widget = self.routeKeyToInterface.get(routeKey)
        if widget:
            self.stackedWidget.setCurrentWidget(widget)
            widget.update()


class LoadMethodBox(MessageBoxBase):
    """ 读取脚本到软件的方法 """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttonpanel = QHBoxLayout()
        self.load_clear = ToggleButton(FIF.DOWNLOAD,self.tr("覆盖读取"))
        self.load_full =  ToggleButton(FIF.DOWN,self.tr("添置读取"))
        self.load_clear.setMinimumHeight(120)
        self.load_full.setMinimumHeight(120)
        self.load_clear.setChecked(True)
        self.buttonpanel.addWidget(self.load_clear)
        self.buttonpanel.addWidget(self.load_full)
        self.viewLayout.addLayout(self.buttonpanel)


        self.button_group = QButtonGroup(self)

        # 将两个按钮添加到同一个按钮组中
        self.button_group.addButton(self.load_clear)
        self.button_group.addButton(self.load_full)

        # 设置按钮组为互斥模式
        self.button_group.setExclusive(True)


        self.yesButton.setText(self.tr('确定'))
        self.cancelButton.setText(self.tr('取消'))

        self.widget.setMinimumWidth(300)



class TestBox(MessageBoxBase):
    """ 测试用的Box """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.yesButton.setText(self.tr('确定'))
        self.cancelButton.setText(self.tr('取消'))

        self.widget.setMinimumWidth(300)

