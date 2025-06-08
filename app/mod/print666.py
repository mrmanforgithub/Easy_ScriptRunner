# MOD_TYPE: operation
# 这是操作mod


import pyautogui
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from qfluentwidgets import LineEdit
from qfluentwidgets import FluentIcon as FIF

from app.common.signal_bus import signalBus
from app.common.operation_registry import register_operation



def print666(scriptpage, parameters:list,args:list):
    print(666)
    return args[0]+"-done","exe"




@register_operation("打出666", icon=FIF.BASKETBALL, execute_func=print666,fields=["loc","text"])
class print666Widget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.scriptpage = parent
        self.layout = QVBoxLayout(self)
        self.scroll_label = QLabel(self.tr("打出666！"))
        self.layout.addWidget(self.scroll_label)
        self.setLayout(self.layout)


    def get_operation(self):
        operation = {
            "operation_name": self.__class__.key,
            "parameters": [666],
            "operation_text": ["六百六十六"]
        }
        return operation

    def insert_parameters(self,parameters):
        pass


