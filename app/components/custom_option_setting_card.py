# coding:utf-8
from typing import Union
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QButtonGroup, QVBoxLayout, QPushButton, QHBoxLayout
from qfluentwidgets import (ExpandGroupSettingCard, RadioButton,
                            qconfig,FluentIconBase, PushButton,FluentIcon,
                            setTheme, setThemeColor, OptionsConfigItem, isDarkTheme,MessageBoxBase,SubtitleLabel)
from ..components.tabpage import TabPage
from ..common.photo_tool import photo_tool
from ..common.config import TAB_PATH,ADD_PATH



class CustomOptionSettingCard(ExpandGroupSettingCard):
    """ Custom Option setting card """

    tabContentChanged = pyqtSignal(dict)

    def __init__(self, configItem: OptionsConfigItem, icon: Union[str, QIcon, FluentIconBase], title: str,
                content=None, parent=None, enableAlpha=False , default = False):
        super().__init__(icon, title, content, parent=parent)
        self.setting = parent
        self.enableAlpha = enableAlpha
        self.configItem = configItem
        self.defaultPage = configItem.defaultValue
        self.customPage = qconfig.get(configItem)
        self.default = default  #判断是新建页面/默认页面
        self.single_content = {} #默认是空的字典

        self.tab_path = TAB_PATH
        self.add_path = ADD_PATH

        self.choiceLabel = QLabel(self)

        self.radioWidget = QWidget(self.view)
        self.radioLayout = QVBoxLayout(self.radioWidget)
        self.defaultRadioButton = RadioButton(
            self.tr('空白页'), self.radioWidget)
        self.customRadioButton = RadioButton(
            self.tr('自定义页面'), self.radioWidget)
        self.buttonGroup = QButtonGroup(self)

        self.customPageWidget = QWidget(self.view)
        self.customPageLayout = QHBoxLayout(self.customPageWidget)
        self.customLabel = QLabel(
            self.tr('自定义页面'), self.customPageWidget)
        self.choosePageButton = QPushButton(
            self.tr('编辑页面'), self.customPageWidget)
        self.tabContentChanged.connect(self.save_content)
        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()

        if self.customPage != self.defaultPage:
            self.customRadioButton.setChecked(True)
            self.choosePageButton.setEnabled(True)
        else:
            self.defaultRadioButton.setChecked(True)
            self.choosePageButton.setEnabled(False)

        self.choiceLabel.setText(self.buttonGroup.checkedButton().text())
        self.choiceLabel.adjustSize()

        self.choiceLabel.setObjectName("titleLabel")
        self.customLabel.setObjectName("titleLabel")
        self.choosePageButton.setObjectName('choosePageButton')

        self.buttonGroup.buttonClicked.connect(self.__onRadioButtonClicked)
        self.choosePageButton.clicked.connect(self.__showPageDialog)

    def __initLayout(self):
        self.addWidget(self.choiceLabel)

        self.radioLayout.setSpacing(19)
        self.radioLayout.setAlignment(Qt.AlignTop)
        self.radioLayout.setContentsMargins(48, 18, 0, 18)
        self.buttonGroup.addButton(self.customRadioButton)
        self.buttonGroup.addButton(self.defaultRadioButton)
        self.radioLayout.addWidget(self.customRadioButton)
        self.radioLayout.addWidget(self.defaultRadioButton)
        self.radioLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        self.customPageLayout.setContentsMargins(48, 18, 44, 18)
        self.customPageLayout.addWidget(self.customLabel, 0, Qt.AlignLeft)
        self.customPageLayout.addWidget(self.choosePageButton, 0, Qt.AlignRight)
        self.customPageLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.addGroupWidget(self.radioWidget)
        self.addGroupWidget(self.customPageWidget)

    def __onRadioButtonClicked(self, button: RadioButton):
        """ radio button clicked slot """
        if button.text() == self.choiceLabel.text():
            return

        self.choiceLabel.setText(button.text())
        self.choiceLabel.adjustSize()

        if button is self.defaultRadioButton:
            self.choosePageButton.setDisabled(True)
            qconfig.set(self.configItem, "Empty")
        else:
            self.choosePageButton.setDisabled(False)
            qconfig.set(self.configItem, "Custom")
            if self.single_content:
                self.tabContentChanged.emit(self.single_content)

    def __showPageDialog(self):
        """ show Page dialog """
        if self.default:
            w = DefaultSetBox(self.window())
        else:
            w = DefaultSetBox(self.window(),False)
        if w.exec_():
            detail = w.tabpage.pivotInterface.scanInterface.getdetail()
            graph_text = w.tabpage.pivotInterface.scanInterface.get_graph()
            operations = w.tabpage.pivotInterface.scriptInterface.operations
            self.single_content = {
                'detail': detail,
                'graph_text': graph_text,
                'operations': operations
            }
            if self.single_content:
                self.tabContentChanged.emit(self.single_content)

    def save_content(self,data:dict):
        if self.default:
            photo_tool.saveDataToPath(data=data,file_path=self.tab_path)
        else:
            photo_tool.saveDataToPath(data=data,file_path=self.add_path)


class DefaultSetBox(MessageBoxBase):
    """ DefaultSetBox"""

    def __init__(self, parent=None,default = True):
        super().__init__(parent)
        self.custoption = parent
        self.timeLabel = SubtitleLabel(self.tr('自定义页面设置'), self)
        self.default = default
        try:
            if default:
                tabData = photo_tool.loadDataFromPath(TAB_PATH)
            else:
                tabData = photo_tool.loadDataFromPath(ADD_PATH)

            if tabData:
                self.tabpage = TabPage(self,graph_text=tabData['graph_text'], operations=tabData['operations'],detail= tabData['detail'])
            else:
                self.tabpage = TabPage(self,title="default", graph_text=[],operations=[],detail=None)
        except:
            self.tabpage = TabPage(self,title= "default", graph_text=[],operations=[],detail=None)
        self.scanpage = self.tabpage.pivotInterface.scanInterface
        self.scriptpage = self.tabpage.pivotInterface.scriptInterface

        # 从布局中隐藏控件
        self.scanpage.timer_panel.hide()
        self.scanpage.scan_status_label.hide()
        self.scanpage.start_scan_button.hide()

        self.load_first_button = PushButton(self.tr('读取第一个扫描到此处'), self, FluentIcon.DOWNLOAD)
        self.load_first_button.setMinimumHeight(80)
        self.scanpage.right_layout.addWidget(self.load_first_button)
        self.load_first_button.clicked.connect(self.load_first)

        self.viewLayout.addWidget(self.timeLabel)
        self.viewLayout.addWidget(self.tabpage)

        self.yesButton.setText(self.tr('确定'))
        self.cancelButton.setText(self.tr('取消'))

        self.widget.setMinimumWidth(890)
        self.widget.setMinimumHeight(650)

    def load_first(self):
        try:
            data = self.custoption.homeInterface.tabs.getAllDataTab()
            first_route_key, first_tab_data = next(iter(data.items()))
            self.scanpage.detail = first_tab_data["detail"]
            self.scanpage.initdetail(self.scanpage.detail)
            self.scanpage.graph_text = first_tab_data["graph_text"]
            self.scanpage.generate_recognition_interface(self.scanpage.graph_text)
            self.scriptpage.operations = first_tab_data["operations"]
            self.scriptpage.operation_table.showoperation(self.scriptpage.operations)
        except:
            pass