# coding:utf-8
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QStandardPaths
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog

from ..common.config import cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..common.check_update import checkUpdate
from ..components.custom_option_setting_card import CustomOptionSettingCard
from ..components.custom_keyset_card import CustomKeyBindCard
import os
import subprocess


class SettingInterface(ScrollArea):
    """ 设置页面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.mainwindow = parent
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("设置"), self)

        # scriptInThisPCGroup
        self.scriptInThisPCGroup = SettingCardGroup(
            self.tr("本地文件夹"), self.scrollWidget)
        self.scriptFolderCard = FolderListSettingCard(
            cfg.scriptFolders,
            self.tr("脚本文件夹"),
            parent=self.scriptInThisPCGroup
        )
        self.downloadFolderCard = PushSettingCard(
            self.tr('选择文件夹'),
            FIF.DOWNLOAD,
            self.tr("下载文件夹"),
            cfg.get(cfg.downloadFolder),
            self.scriptInThisPCGroup
        )


        self.defaultGroup = SettingCardGroup(
            self.tr('默认设置'), self.scrollWidget)
        self.defaultTabCard = CustomOptionSettingCard(
            cfg.defaultTab,
            FIF.DOCUMENT,
            self.tr('默认扫描页'),
            self.tr('默认打开软件生成的扫描页'),
            parent=self.defaultGroup,
            default = True
        )
        self.defaultAddCard = CustomOptionSettingCard(
            cfg.defaultAdd,
            FIF.ADD_TO,
            self.tr('默认新建页'),
            self.tr('点击加号创建的新扫描页'),
            parent=self.defaultGroup
        )
        self.keybindCard = CustomKeyBindCard(
            cfg.keybind,
            FIF.CAFE,
            self.tr('默认快捷键'),
            self.tr('快捷开启扫描/关闭扫描的快捷键'),
            parent=self.defaultGroup
        )
        self.offsetCard = OptionsSettingCard(
            cfg.offset,
            FIF.MOVE,
            self.tr("随机偏移"),
            self.tr("鼠标点击产生偏移的范围"),
            texts=[
                self.tr("无偏移"), "5px", "10px", "15px", "20px"
            ],
            parent=self.defaultGroup
        )
        self.photoMethodCard = OptionsSettingCard(
            cfg.photoMethod,
            FIF.LEAF,
            self.tr("图像识别"),
            self.tr("模板匹配快,相似度要求高/特征识别慢,但能识别带有变化的图片"),
            texts=[
                self.tr("模板匹配"), self.tr("特征识别")
            ],
            parent=self.defaultGroup
        )
        self.Base64Card = SwitchSettingCard(
            FIF.CLOUD,
            self.tr("启用Base64"),
            self.tr("启用后读取/保存图片均使用Base64格式,将图片本身保存在json文件中"),
            cfg.Base64Method,
            self.defaultGroup
        )
        self.logCard = OptionsSettingCard(
            cfg.logMethod,
            FIF.DICTIONARY,
            self.tr("运行日志"),
            self.tr("设置运行日志的记录方式"),
            texts=[
                self.tr("关闭日志记录"),self.tr("记录全部日志"), self.tr("记录非重复日志")
            ],
            parent=self.defaultGroup
        )
        self.closeCard = SwitchSettingCard(
            FIF.MINIMIZE,
            self.tr('最小化到托盘'),
            self.tr('选择直接关闭/最小化到托盘'),
            cfg.closeEnabled,
            self.defaultGroup
        )


        # personalization
        self.personalGroup = SettingCardGroup(
            self.tr('个性化'), self.scrollWidget)
        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('云母效果'),
            self.tr('窗口和界面显示半透明'),
            cfg.micaEnabled,
            self.personalGroup
        )
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('应用主题'),
            self.tr("调整你的应用的外观"),
            texts=[
                self.tr('浅色'), self.tr('深色'),
                self.tr('跟随系统设置')
            ],
            parent=self.personalGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr('主题色'),
            self.tr('调整你的应用的主题色'),
            self.personalGroup
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("界面缩放"),
            self.tr("调整小部件和字体的大小"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("跟随系统设置")
            ],
            parent=self.personalGroup
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr('语言'),
            self.tr('选择界面所使用的语言'),
            texts=['简体中文', 'English', self.tr('跟随系统设置')],
            parent=self.personalGroup
        )


        # update software
        self.updateSoftwareGroup = SettingCardGroup(
            self.tr("软件更新"), self.scrollWidget)
        self.updateOnStartUpCard = SwitchSettingCard(
            FIF.UPDATE,
            self.tr('在应用程序启动时检查更新'),
            self.tr('如果更新失败,请启用能连接github的加速器,或者手动下载'),
            configItem=cfg.checkUpdateAtStartUp,
            parent=self.updateSoftwareGroup
        )
        self.updatePrereleaseCard = SwitchSettingCard(
            FIF.BOOK_SHELF,
            self.tr('下载预发布版本'),
            self.tr('预发布版本功能更多,但可能会有未知的bug'),
            configItem=cfg.update_prerelease_enable,
            parent=self.updateSoftwareGroup
        )


        # application
        self.aboutGroup = SettingCardGroup(self.tr('关于'), self.scrollWidget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            self.tr('打开帮助页面'),
            FIF.HELP,
            self.tr('帮助'),
            self.tr(
                '学习如何使用ScriptRunner'),
            self.aboutGroup
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('提供反馈'),
            FIF.FEEDBACK,
            self.tr('提供反馈'),
            self.tr('帮助我修复ScriptRunner,为我提供使用反馈'),
            self.aboutGroup
        )
        self.errorCard = PrimaryPushSettingCard(
            self.tr('错误日志'),
            FIF.PRINT,
            self.tr('查看错误日志'),
            self.tr('查看本地错误日志文件夹'),
            self.aboutGroup
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('检查更新'),
            FIF.INFO,
            self.tr('关于'),
            '© ' + self.tr('Copyright') + f" {YEAR}, {AUTHOR}. " +
            self.tr('Version') + " " + VERSION,
            self.aboutGroup
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.micaCard.setEnabled(isWin11())

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # add cards to group
        self.scriptInThisPCGroup.addSettingCard(self.scriptFolderCard)
        self.scriptInThisPCGroup.addSettingCard(self.downloadFolderCard)

        self.defaultGroup.addSettingCard(self.defaultTabCard)
        self.defaultGroup.addSettingCard(self.defaultAddCard)
        self.defaultGroup.addSettingCard(self.keybindCard)
        self.defaultGroup.addSettingCard(self.offsetCard)
        self.defaultGroup.addSettingCard(self.photoMethodCard)
        self.defaultGroup.addSettingCard(self.Base64Card)
        self.defaultGroup.addSettingCard(self.logCard)
        self.defaultGroup.addSettingCard(self.closeCard)


        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)


        self.updateSoftwareGroup.addSettingCard(self.updateOnStartUpCard)
        self.updateSoftwareGroup.addSettingCard(self.updatePrereleaseCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.errorCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.scriptInThisPCGroup)
        self.expandLayout.addWidget(self.defaultGroup)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.updateSoftwareGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('成功更新'),
            self.tr('配置将在重启后生效'),
            duration=1500,
            parent=self
        )

    def __onDownloadFolderCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("选择文件夹"), "./")
        if not folder or cfg.get(cfg.downloadFolder) == folder:
            return
        cfg.set(cfg.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)

    def error_open(self):
        folder_path = os.path.join("app", "backtrace_logs")
        # 判断文件夹是否存在
        if os.path.exists(folder_path):
            if os.name == 'nt':  # Windows
                subprocess.run(['explorer', folder_path])
            # elif os.name == 'posix':  # macOS 或 Linux
            #     subprocess.run(['open', folder_path])  # macOS
            #     # subprocess.run(['xdg-open', folder_path])  # Linux
        else:
            print(f"文件夹 {folder_path} 不存在")
        pass

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # music in the pc
        self.downloadFolderCard.clicked.connect(
            self.__onDownloadFolderCardClicked)

        # personalization
        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)
        self.aboutCard.clicked.connect(lambda : checkUpdate(self, timeout=5, flag=True))
        self.errorCard.clicked.connect(self.error_open)

        # about
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
