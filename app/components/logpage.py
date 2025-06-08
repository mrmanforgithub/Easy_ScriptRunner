import time
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout,QHBoxLayout,QSizePolicy,QTableWidgetItem, QHeaderView
from PyQt5.QtCore import pyqtSignal
from qfluentwidgets import TableWidget,qconfig,PrimaryPushButton
from ..common.config import cfg


#操作界面内容
class LogPage(QWidget):
    """自定义操作页面"""
    update_log_signal = pyqtSignal(str,str)
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.pivot = parent
        self.scan_log = []
        self.upif = False
        self.stoplog = False
        self.main_layout = QVBoxLayout(self)
        self.logtable =LogTable(self)
        self.logtable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        self.button_layout = QHBoxLayout()
        self.clear_button = PrimaryPushButton(self.tr("清空记录"))

        self.button_layout.addWidget(self.clear_button)

        self.main_layout.addWidget(self.logtable)
        self.main_layout.addLayout(self.button_layout)

        self.update_log_signal.connect(self.write_log)
        self.clear_button.clicked.connect(self.clear_log)



    def clear_log(self):
        self.scan_log =[]
        self.logtable.showlogs(self.scan_log)



    def write_log(self, content, method):
        if cfg.get(cfg.logMethod)=="stop":
            return
        try:
            current_time = time.time()
            formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))
            past = 0
            if not hasattr(self, 'scan_log'):
                self.scan_log = []

            if self.scan_log:
                last_log = self.scan_log[-1]
                last_time = last_log["time"]
                past = round(current_time - last_time, 2)

                if cfg.get(cfg.logMethod)=="no_repeat" and last_log["content"] == content:
                    last_log["time"] = current_time
                    last_log["formatted_time"] = formatted_time
                    last_log["past"] += past
                    if self.upif:
                        self.logtable.showlogs(self.scan_log)
                    return

                if len(self.scan_log) >= 500:
                    self.scan_log.pop(0)  # 删除最前面的条目

            new_log = {
                "time": current_time,
                "formatted_time": formatted_time,
                "past": past,
                "content": content,
                "method": method
            }

            self.scan_log.append(new_log)

            if self.upif:
                self.logtable.showlogs(self.scan_log)
        except Exception as e:
            pass


class LogTable(TableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logpage = parent
        self.verticalHeader().hide()
        self.setBorderRadius(8)
        self.setBorderVisible(True)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels([
            self.tr('开始时间'), self.tr('执行时间'),
            self.tr('执行行为')
        ])
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)


    def showlogs(self, scan_log:list):
        if scan_log is None:
            return
        self.setRowCount(0)
        for i, log in enumerate(scan_log):
            time = log.get('formatted_time', '')
            past = log.get('past', 0)
            content = log.get('content', '')
            time = str(time)
            past = str(round(past,2))
            content = str(content)
            self.insertRow(i)
            new_row = [
            time ,
            past,
            content
            ]
            method = log.get('method', None)
            for column, value in enumerate(new_row):
                text = str(value)
                if len(text) > 50:
                    text = text[:47] + "..."
                item = QTableWidgetItem(text)
                if method is not None:
                    if method == "error":
                        item.setForeground(QColor(255, 0, 0))
                    elif method == "success":
                        item.setForeground(QColor(25, 204, 55))
                    elif method == "end":
                        item.setForeground(QColor(255, 46, 147))
                    elif method == "exe":
                        item.setForeground(QColor(22, 142, 254))
                    elif method == "warnning":
                        item.setForeground(QColor(255, 140, 0))
                self.setItem(i, column, item)
