from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QTextFormat
from PyQt5.QtCore import Qt, QEvent
from qfluentwidgets import  TextEdit


class DynamicParamTextEdit(TextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)


    def insert_dynamic_param(self, text="【识别1号+10,20】"):
        cursor = self.textCursor()

        # 1. 设置灰色块格式
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#eeeeee"))
        fmt.setForeground(QColor("gray"))
        fmt.setProperty(QTextFormat.UserProperty, "dynamic_param")

        # 2. 插入动态参数
        cursor.insertText(text, fmt)

        # 3. 恢复默认格式（防止“传染”）
        cursor.setCharFormat(QTextCharFormat())  # 清除格式
        self.setTextCursor(cursor)


    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            cursor = self.textCursor()
            full_cursor = self._get_dynamic_param_block_cursor(cursor)
            if full_cursor:
                full_cursor.removeSelectedText()
                return True
        return super().eventFilter(obj, event)


    def mousePressEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.WordUnderCursor)
        if self._cursor_on_dynamic_param(cursor):
            print("点击了一个动态参数块")
            # 你可以在这里弹出参数编辑窗口
        super().mousePressEvent(event)

    def _cursor_on_dynamic_param(self, cursor):
        char_format = cursor.charFormat()
        return char_format.hasProperty(QTextFormat.UserProperty) and \
               char_format.property(QTextFormat.UserProperty) == "dynamic_param"

    def _get_dynamic_param_block_cursor(self, cursor):
        """获取光标所在的完整动态参数块（若有），否则返回 None"""
        doc = self.document()
        start = cursor.position()
        end = cursor.position()

        # 向前找起点
        while start > 0:
            test_cursor = QTextCursor(doc)
            test_cursor.setPosition(start - 1, QTextCursor.MoveAnchor)
            test_cursor.setPosition(start, QTextCursor.KeepAnchor)
            if not self._cursor_on_dynamic_param(test_cursor):
                break
            start -= 1

        # 向后找终点
        while end < doc.characterCount() - 1:
            test_cursor = QTextCursor(doc)
            test_cursor.setPosition(end, QTextCursor.MoveAnchor)
            test_cursor.setPosition(end + 1, QTextCursor.KeepAnchor)
            if not self._cursor_on_dynamic_param(test_cursor):
                break
            end += 1

        if end > start:
            full_cursor = QTextCursor(doc)
            full_cursor.setPosition(start)
            full_cursor.setPosition(end, QTextCursor.KeepAnchor)
            return full_cursor
        return None