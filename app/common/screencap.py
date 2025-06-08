from PyQt5.QtCore import Qt, QRect, QPoint,QBuffer, QIODevice
from PyQt5.QtGui import QPen, QPainter, QColor, QGuiApplication,QFont, QRegion
from PyQt5.QtWidgets import QDialog, QFileDialog,QLabel
import base64
import time
from ..common.signal_bus import signalBus
from ..common.config import cfg

class ScreenshotWindow(QDialog):
    def __init__(self, capture=False, select_point=False, drag_method = None, show_rec = None,color = False):
        super().__init__()
        self.capture = capture  # 判断是否截图
        self.select_point = select_point  # 是否选择单点
        self.drag_method = drag_method  # 是否选择画线
        self.show_rec = show_rec  # 是否选择显示区域
        self.color = color   # 是否选择获取颜色
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setWindowFlag(Qt.FramelessWindowHint)  # 无边框
        self.setWindowState(Qt.WindowFullScreen)   # 全屏
        self.opacity = 0.4
        if self.drag_method is None:
            self.setCursor(Qt.CrossCursor)          # 设置十字光标,画线的时候除外
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)


        self.start_pos = QPoint()  # 鼠标起始位置
        self.end_pos = QPoint()  # 鼠标结束位置
        self.selected_rect = QRect()  # 选框区域
        self.linepoints = []  # 画线的点
        self.start_time = None  # 开始画线时间
        self.end_time = None
        self.screenshot_image = None
        self.photo_path = None
        self.img_base64 = None
        self.outerscreen = QGuiApplication.primaryScreen()
        self.resize(self.outerscreen.size())
        self.device_pixel_ratio = self.outerscreen.devicePixelRatio()  # 获取屏幕的DPI比例

        #当前鼠标位置和鼠标下方颜色
        self.mouse_position = QPoint()
        self.real_position = QPoint()
        self.mouse_color = QColor(0, 0, 0)  # 初始颜色为空



    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPos()
            if self.drag_method is not None:
                self.start_time = time.time()
                self.linepoints.append(self.start_pos)
            if self.select_point or self.show_rec or self.color:  # 如果是单点选择或者显示框选区域或者获得颜色,则直接结束
                self.close()  # 关闭窗口
            else:  # 否则执行框选操作
                self.selected_rect = QRect(self.start_pos, self.start_pos)


    def mouseMoveEvent(self, event):
        """鼠标拖动事件，实时绘制选框"""
        self.mouse_position = QPoint(int(event.globalPos().x() * self.device_pixel_ratio),
                                int(event.globalPos().y() * self.device_pixel_ratio))
        self.real_position = event.globalPos()
        screen = QGuiApplication.primaryScreen()
        screenshot = screen.grabWindow(0) # 获取全屏截图
        pixel_color = screenshot.toImage().pixel(self.mouse_position)
        if (self.show_rec and self.show_rec.contains(event.globalPos())) or self.color:
            color = self.adjust_color(pixel_color)
        else:
            color = self.reverse_blend(QColor(pixel_color), self.opacity)
        self.mouse_color = QColor(color)
        if event.buttons() == Qt.LeftButton and not self.select_point:
            self.end_pos = event.globalPos()
            if self.drag_method :  # 画线模式
                self.linepoints.append(self.end_pos)  # 添加新的点
            else:
                self.selected_rect = QRect(self.start_pos, self.end_pos).normalized()  # 获取矩形选框区域
        self.update()  # 更新绘制


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self.select_point:
            self.end_pos = event.globalPos()
            if self.drag_method:
                self.linepoints.append(self.end_pos)
                self.end_time = time.time()
            else:
                self.selected_rect = QRect(self.start_pos, self.end_pos).normalized()
            if self.capture:
                self.captureSelectedRegion()
            self.close()  # 关闭窗口


    def paintEvent(self, event):
        """绘制选框"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        clip_region = QRegion(self.rect())  # 获取整个窗口区域
        if self.show_rec:
            clip_region -= QRegion(self.show_rec)  # 从区域中去除show_rec
        if self.selected_rect:
            clip_region -= QRegion(self.selected_rect)  # 从区域中去除selected_rect
        painter.setClipRegion(clip_region)  # 设置剪切区域，
        painter.setPen(Qt.transparent)
        if self.color:
            painter.setBrush(QColor(0, 0, 0, 1))
        else:
            painter.setBrush(QColor(0, 0, 0, int(self.opacity*255)))
        painter.drawRect(self.rect())  # 填充除去选区部分的全部窗口

        painter.setPen(QPen(QColor(30, 150, 255), 3))  # 设置蓝色画笔
        painter.setBrush(QColor(255, 255, 255, 1))
        if self.show_rec is not None:
            painter.setClipRegion(QRegion(self.rect()))
            painter.drawRect(self.show_rec)
        if self.drag_method == "line":
            if len(self.linepoints) > 1:
                painter.drawLine(self.start_pos, self.end_pos)  # 连接每两个点
        elif self.drag_method == "curve":
            if len(self.linepoints) > 1:
                for i in range(1, len(self.linepoints)):
                    painter.drawLine(self.linepoints[i-1], self.linepoints[i])  # 连接每两个点
        else:
            painter.drawRect(self.selected_rect)  # 绘制选框
        if self.mouse_position:
            if self.selected_rect or self.show_rec:
                rect = self.getdpiRect() if self.selected_rect else self.getdpiRect(self.show_rec)
                text1 = f"  ({rect.left()}, {rect.top()})  ({rect.right()}, {rect.bottom()})  "
            else:
                text1 = f"  ({self.mouse_position.x()}, {self.mouse_position.y()})  "
            text2 = f"{self.mouse_color.name()}"

            if self.color:
                magnifier_size = 125  # 放大镜窗口大小
                zoom_factor = 5  # 放大倍数
                off_set = 20
                snapshot_size = magnifier_size // zoom_factor  # 截取区域大小
                screen = self.outerscreen
                snapshot = screen.grabWindow(0,
                                            self.real_position.x() - snapshot_size // 2,
                                            self.real_position.y() - snapshot_size // 2,
                                            snapshot_size, snapshot_size)
                # 放大
                magnified_pixmap = snapshot.scaled(magnifier_size, magnifier_size,
                                                Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
                # 计算放大镜位置
                magnifier_x = self.real_position.x() + off_set
                magnifier_y = self.real_position.y() + off_set
                dpi_size = int(magnifier_size / self.device_pixel_ratio)
                # 获取屏幕的宽高
                screen_width = self.outerscreen.size().width()
                screen_height = self.outerscreen.size().height()
                # 如果放大镜超出屏幕右边界，移动到鼠标左侧
                if magnifier_x + dpi_size > screen_width:
                    magnifier_x = self.real_position.x() - dpi_size - off_set  # 移动到左侧
                # 如果放大镜超出屏幕底部，移动到鼠标上方
                if magnifier_y + dpi_size + 40 > screen_height:
                    magnifier_y = self.real_position.y() - dpi_size - off_set-40  # 移动到上方
                # 绘制放大镜背景
                painter.setPen(QPen(QColor(255, 255, 255),  2))  # 边框
                painter.setBrush(QColor(255, 255, 255))
                painter.drawRect(magnifier_x-1, magnifier_y-1, dpi_size+2, dpi_size+40)
                font = QFont("Arial", 8)
                painter.setFont(font)
                text2_width = painter.fontMetrics().width(self.tr("色值:")+text2)
                painter.setPen(QPen(Qt.black))
                text1_rect = QRect(magnifier_x, magnifier_y + dpi_size, dpi_size, 20)  # 文字区域
                painter.drawText(text1_rect, Qt.AlignLeft| Qt.AlignVCenter, self.tr("坐标:")+text1)
                text2_rect = QRect(magnifier_x, magnifier_y + dpi_size+20, text2_width, 20)  # 文字区域
                painter.drawText(text2_rect, Qt.AlignLeft| Qt.AlignVCenter, self.tr("色值:")+text2)
                color_block_rect = QRect(magnifier_x+ dpi_size-20, magnifier_y + dpi_size + 20, 18, 18)  # 小色块区域
                painter.setPen(QPen(Qt.black,1))  # 设置边框颜色为黑色
                painter.setBrush(self.mouse_color)  # 设置填充颜色为鼠标颜色
                painter.drawRect(color_block_rect)  # 绘制小色块

                # 绘制放大的截图
                painter.drawPixmap(magnifier_x, magnifier_y, magnified_pixmap)
                # 绘制十字准心
                center_x = magnifier_x + dpi_size // 2
                center_y = magnifier_y + dpi_size // 2
                painter.setPen(QPen(QColor(30, 150, 255), 1))
                line_size = int(dpi_size/2) -1
                painter.drawLine(center_x - line_size, center_y, center_x + line_size, center_y)  # 水平线
                painter.drawLine(center_x, center_y - line_size, center_x, center_y + line_size)  # 垂直线
            else:
                bar_height = 24
                font = QFont("Arial", 12)
                painter.setFont(font)  # 应用字体
                painter.setOpacity(1)
                text1_width = painter.fontMetrics().width(text1)
                text2_width = painter.fontMetrics().width(text2)
                # 动态调整 bar_rect 的宽度
                total_width = text1_width + text2_width+5
                bar_rect = QRect(10, 10, total_width, bar_height)  # 调整 bar_rect 的宽度以适应文本
                painter.setBrush(QColor(255, 255, 255))
                painter.drawRect(bar_rect)
                # 绘制坐标部分文本
                painter.setPen(QPen(Qt.black))
                painter.drawText(bar_rect, Qt.AlignLeft | Qt.AlignVCenter, text1)
                # 绘制后半部分文本
                painter.setPen(QPen(self.mouse_color))  # 使用鼠标颜色作为文字颜色
                text2_rect = bar_rect.adjusted(text1_width, 0, 0, 0)
                painter.drawText(text2_rect, Qt.AlignLeft | Qt.AlignVCenter, text2)


    def adjust_color(self,pixel_color):
        # 提取 RGB 分量
        r = (pixel_color >> 16) & 0xFF
        g = (pixel_color >> 8) & 0xFF
        b = pixel_color & 0xFF
        # 手动调整颜色值，确保当大于 80 时增加 1
        def adjust_value(value):
            if value > 0x80:
                return min(value + 1, 255)  # 如果值大于 80，增加 1，但不超过 255
            return value
        r = adjust_value(r)
        g = adjust_value(g)
        b = adjust_value(b)
        # 创建 QColor 对象
        color = QColor(r, g, b)
        return color


    def reverse_blend(self,pixel_color, alpha):
        r = (pixel_color.red()) / (1 - alpha)
        g = (pixel_color.green()) / (1 - alpha)
        b = (pixel_color.blue()) / (1 - alpha)
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return QColor(int(r), int(g), int(b))

    def captureSelectedRegion(self):
        """截取选定区域"""
        self.hide()
        screen = QGuiApplication.primaryScreen()
        screenshot = screen.grabWindow(0)  # 获取全屏截图
        scaled_rect = self.getdpiRect()
        self.screenshot_image = screenshot.copy(scaled_rect)  # 截取选框区域
        self.saveImage()  # 保存截图

    def image_to_base64(self,image):
        try:
            buffer = QBuffer()
            buffer.open(QIODevice.ReadWrite)
            image.save(buffer, "PNG")
            img_data = buffer.data()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("无法转化为Base64")+f"{e}","TOP","error")
            return None

    def saveImage(self):
        """保存截图"""
        if cfg.get(cfg.Base64Method):
            self.img_base64 = self.image_to_base64(self.screenshot_image)
        else:
            file_path, _ = QFileDialog.getSaveFileName(self, self.tr("保存截图"), "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            if file_path:
                self.screenshot_image.save(file_path)
                self.photo_path = file_path

    def getSelectedRect(self):
        """获取框选区域坐标，返回(x, y, width, height)"""
        if self.selected_rect:
            scaled_rect = self.getdpiRect()
            return (scaled_rect.x(), scaled_rect.y(), scaled_rect.width(), scaled_rect.height())
        return None

    def getdpiRect(self,change_rect = None):   #当屏幕缩放率不同的时候 能返回正确的选区位置
        rect = self.selected_rect
        if change_rect is not None:
            rect = change_rect
        scaled_rect = QRect(
        int(rect.x() * self.device_pixel_ratio),
        int(rect.y() * self.device_pixel_ratio),
        int(rect.width() * self.device_pixel_ratio),
        int(rect.height() * self.device_pixel_ratio))
        return scaled_rect

    def getdpiPoint(self,QPoint):
        return (int(QPoint.x() * self.device_pixel_ratio), int(QPoint.y() * self.device_pixel_ratio))

    def getdragTime(self):
        return self.end_time - self.start_time

    def getScreenshot(self):
        if cfg.get(cfg.Base64Method):
            return self.img_base64
        else:
            return self.photo_path

    def getSelectedPoint(self):
        """返回单点坐标"""
        startpos = self.getdpiPoint(self.start_pos)
        return startpos

    def getDragPoint(self):
        if self.drag_method == "line":
            startpos = self.getdpiPoint(self.start_pos)
            endpos =  self.getdpiPoint(self.end_pos)
            return [startpos,endpos]
        elif self.drag_method == "curve":
            dpipoints = []
            for point in self.linepoints:
                dpipoints.append(self.getdpiPoint(point))
            return dpipoints

    def getMouseColor(self):
        """获取当前鼠标指针下面的颜色"""
        screen = QGuiApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        pixel_color = screenshot.toImage().pixel(self.mouse_position)
        self.mouse_color = QColor(pixel_color)
        return self.mouse_color.name()

def capture_area(capture=False):
    """启动框选区域功能，返回框选区域坐标与框选内部的图片"""
    screenshot_window = ScreenshotWindow(capture=capture)
    screenshot_window.exec_()
    return screenshot_window.getSelectedRect(), screenshot_window.getScreenshot() if capture else None

def capture_point():
    """启动单点坐标"""
    screenshot_window = ScreenshotWindow(select_point=True)
    screenshot_window.exec_()
    return screenshot_window.getSelectedPoint()

def capture_line(drag_method):
    """启动画线"""
    screenshot_window = ScreenshotWindow(drag_method=drag_method)
    screenshot_window.exec_()
    return screenshot_window.getDragPoint(),screenshot_window.getdragTime()

def show_rec(rec):
    """根据Qrect显示区域"""
    screenshot_window = ScreenshotWindow(show_rec=rec)
    screenshot_window.exec_()

def capture_color():
    """抓色工具"""
    screenshot_window = ScreenshotWindow(color=True)
    screenshot_window.exec_()
    return screenshot_window.getMouseColor()