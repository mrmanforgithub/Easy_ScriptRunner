# coding:utf-8
from typing import Union
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QButtonGroup, QVBoxLayout, QPushButton, QHBoxLayout,QCompleter
from qfluentwidgets import (ColorDialog, ExpandGroupSettingCard, RadioButton,
                            qconfig, ColorConfigItem,
                            FluentIconBase,LineEdit,
                            setTheme, setThemeColor, OptionsConfigItem, isDarkTheme,MessageBoxBase,SubtitleLabel)
from ..common.signal_bus import signalBus
from ..common.photo_tool import photo_tool
from ..common.config import cfg,KEY_PATH
import re


class CustomKeyBindCard(ExpandGroupSettingCard):
    """ Custom KeyBind card """

    def __init__(self, configItem: OptionsConfigItem, icon: Union[str, QIcon, FluentIconBase], title: str,
                content=None, parent=None, enableAlpha=False):
        super().__init__(icon, title, content, parent=parent)
        self.enableAlpha = enableAlpha
        self.configItem = configItem

        self.defaultkey = configItem.defaultValue
        self.customkey = qconfig.get(configItem)
        self.short_cut_key = []

        self.choiceLabel = QLabel(self)

        self.radioWidget = QWidget(self.view)
        self.radioLayout = QVBoxLayout(self.radioWidget)
        self.defaultRadioButton = RadioButton(
            self.tr('默认快捷键'), self.radioWidget)
        self.customRadioButton = RadioButton(
            self.tr('自定义快捷键'), self.radioWidget)
        self.buttonGroup = QButtonGroup(self)

        self.customPageWidget = QWidget(self.view)
        self.customPageLayout = QHBoxLayout(self.customPageWidget)
        self.customLabel = QLabel(
            self.tr('自定义快捷键'), self.customPageWidget)
        self.choosePageButton = QPushButton(
            self.tr('设置快捷键'), self.customPageWidget)
        self.__initWidget()

    def __initWidget(self):
        self.__initLayout()

        if self.customkey != self.defaultkey:
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
            qconfig.set(self.configItem, "default")
        else:
            self.choosePageButton.setDisabled(False)
            qconfig.set(self.configItem, "Custom")
            if self.short_cut_key:
                photo_tool.update_config_value(KEY_PATH, "hotkeys", self.short_cut_key)

    def __showPageDialog(self):
        """ show Page dialog """
        w = KeySetBox(self.window())
        if w.exec_():
            modifierText1 = w.modifierEdit.text().strip().lower()  # 第一个修饰符
            modifierText2 = w.modifierEdit2.text().strip().lower()  # 第二个修饰符
            keyText1 = w.keyEdit.text().strip().lower()  # 第一个按键
            keyText2 = w.keyEdit2.text().strip().lower()  # 第二个按键
            start_hotkey = []
            stop_hotkey = []
            if modifierText1 and modifierText1 in w.modifiers:
                start_hotkey.append(modifierText1)
            if modifierText2 and modifierText2 in w.modifiers:
                stop_hotkey.append(modifierText2)
            if keyText1:
                start_hotkey.append(keyText1)
            if keyText2:
                stop_hotkey.append(keyText2)
            self.short_cut_key.append(start_hotkey)
            self.short_cut_key.append(stop_hotkey)
            if self.short_cut_key:
                qconfig.set(self.configItem, "Custom")
                photo_tool.update_config_value(KEY_PATH,"hotkeys", self.short_cut_key)


class KeySetBox(MessageBoxBase):
    """ KeySetBox """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.customkey = cfg.get(cfg.keybind)
        self.keybind = photo_tool.read_config_value(KEY_PATH , "hotkeys")
        self.shortcutLabel = SubtitleLabel(self.tr('设置快捷键'), self)
        self.shortcutLabel.setContentsMargins(0,0,0,10)

        self.startLabel = QLabel(self.tr('开始扫描快捷键:'), self)
        # 第一个输入框：修饰符输入框
        self.modifierEdit = LineEdit(self)
        self.modifierEdit.setPlaceholderText(self.tr('输入修饰符'))
        self.modifierEdit.setClearButtonEnabled(True)
        self.modifierEdit.setFixedWidth(150)
        # 第二个输入框：字符输入框
        self.keyEdit = LineEdit(self)
        self.keyEdit.setPlaceholderText(self.tr('输入字符'))
        self.keyEdit.setClearButtonEnabled(True)
        self.keyEdit.setFixedWidth(150)
        # 加号标签
        self.plusLabel = QLabel('+', self)
        self.modifiers = [
            "ctrl", "shift", "alt",  # 常见修饰键
            "space", "tab", "enter", "esc",  # 常见控制键
            "backspace", "delete", "home", "end",  # 常见导航键
            "up", "down", "left", "right",  # 方向键
            "pageup", "pagedown", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"  # 功能键
        ]
        completer = QCompleter(self.modifiers, self.modifierEdit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setMaxVisibleItems(10)
        self.modifierEdit.setCompleter(completer)

        self.hLayout = QHBoxLayout()
        self.hLayout.addWidget(self.modifierEdit)
        self.hLayout.addWidget(self.plusLabel)
        self.hLayout.addWidget(self.keyEdit)

        self.stopLabel = QLabel(self.tr('停止扫描快捷键:'), self)

        self.modifierEdit2 = LineEdit(self)
        self.modifierEdit2.setPlaceholderText(self.tr('输入修饰符'))
        self.modifierEdit2.setClearButtonEnabled(True)
        self.modifierEdit2.setFixedWidth(150)
        self.plusLabel2 = QLabel('+', self)
        self.keyEdit2 = LineEdit(self)
        self.keyEdit2.setPlaceholderText(self.tr('输入字符'))
        self.keyEdit2.setClearButtonEnabled(True)
        self.keyEdit2.setFixedWidth(150)
        completer2 = QCompleter(self.modifiers, self.modifierEdit)
        completer2.setCaseSensitivity(Qt.CaseInsensitive)
        completer2.setMaxVisibleItems(10)
        self.modifierEdit2.setCompleter(completer2)

        self.hLayout2 = QHBoxLayout()
        self.hLayout2.addWidget(self.modifierEdit2)
        self.hLayout2.addWidget(self.plusLabel2)
        self.hLayout2.addWidget(self.keyEdit2)

        self.viewLayout.addWidget(self.shortcutLabel)
        self.viewLayout.addWidget(self.startLabel)
        self.viewLayout.addLayout(self.hLayout)
        self.viewLayout.addWidget(self.stopLabel)
        self.viewLayout.addLayout(self.hLayout2)

        self.yesButton.setText(self.tr('确定'))
        self.cancelButton.setText(self.tr('取消'))

        self.widget.setMinimumWidth(380)
        self.yesButton.setDisabled(True)

        self.modifierEdit.textChanged.connect(self.validateAll)
        self.modifierEdit2.textChanged.connect(self.validateAll)
        self.keyEdit.textChanged.connect(self.validateAll)
        self.keyEdit2.textChanged.connect(self.validateAll)
        self.addlocal()


    def addlocal(self):
        if not isinstance(self.keybind, list) or not self.keybind or self.customkey == "default":
            self.modifierEdit.setText("alt")
            self.modifierEdit2.setText("alt")
            self.keyEdit.setText("o")
            self.keyEdit2.setText("p")
        else:
            self.modifierEdit.setText(self.keybind[0][0])
            self.modifierEdit2.setText(self.keybind[1][0])
            self.keyEdit.setText(self.keybind[0][1])
            self.keyEdit2.setText(self.keybind[1][1])


    def  validateAll(self):
        modifierText = self.modifierEdit.text()
        modifierText2 = self.modifierEdit2.text()
        keyText = self.keyEdit.text()
        keyText2 = self.keyEdit2.text()
        # 验证修饰符
        is_modifier_valid = self.__validateModifiers(modifierText) and self.__validateModifiers(modifierText2)

        # 验证按键内容
        is_key_valid = self.__validateKey(keyText) and self.__validateKey(keyText2)

        if len(keyText) > 1 and not self.__validateModifiers(keyText):
            is_key_valid = False  # 长度大于1时不是修饰符 不是合法按键
        if len(keyText2) > 1 and not self.__validateModifiers(keyText2):
            is_key_valid = False

        # 如果修饰符和按键都有效，启用按钮
        if is_modifier_valid and is_key_valid:
            self.yesButton.setDisabled(False)
        else:
            self.yesButton.setDisabled(True)


    def __validateModifiers(self,text):
        if text.lower() in self.modifiers:
            return True
        else:
            return False

    def __validateKey(self, text):
        """ 验证是否为有效按键 """
        valid_chars = re.match(r'^[a-zA-Z0-9`~!@#$%^&*()_+\-=\[\]{};:\'",<>\./?\\|]$', text)
        if valid_chars:
            return True
        return False