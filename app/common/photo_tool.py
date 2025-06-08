import win32gui
import win32con
import win32com.client
from datetime import datetime
import json
import os
import base64
from PIL import Image
from io import BytesIO
import re
import numpy as np

from PyQt5.QtCore import Qt,QRect,QObject
from PyQt5.QtGui import QGuiApplication,QIcon,QIcon, QPixmap, QPainter
from PyQt5.QtWidgets import QFileDialog
from qfluentwidgets import (qconfig,InfoBar,InfoBarPosition)

from ..common.screencap import capture_area,capture_point,capture_line,show_rec,capture_color
from ..common.signal_bus import signalBus
from ..common.config import cfg,RECENT_PATH,TAB_PATH,ADD_PATH




class Photo_Tools(QObject):
    def __init__(self):
        super().__init__()
        pass



    def image_to_base64(self,image_path):
        try:
            # 打开图像文件
            with Image.open(image_path) as img:
                # 将图像保存到内存中的字节流
                buffered = BytesIO()
                img.save(buffered, format="PNG")  # 保存为PNG格式
                img_data = buffered.getvalue()
                # 将字节数据转换为Base64编码
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                return f"data:image/png;base64,{img_base64}"  # 返回带前缀的Base64字符串
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("无法转化为Base64")+f"{e}","TOP","error")
            return image_path


    def browse_file(self,scan_entry):
        photo_folder = cfg.get(cfg.scriptFolders)
        Base64 = cfg.get(cfg.Base64Method)
        folder = ''
        if photo_folder:
            folder = photo_folder[0]
        filters = "Image Files (*.jpg *.jpeg *.png *.bmp *.gif *.tiff);;All Files (*)"
        file_path = QFileDialog.getOpenFileName(None, self.tr("选择扫描图片"), folder, filters)[0]
        if file_path:
            try:
                if Base64:
                    base64_image = self.image_to_base64(file_path)
                    if base64_image:
                        scan_entry.setText(base64_image)
                else:
                    scan_entry.setText(file_path)
            except Exception as e:
                signalBus.main_infobar_signal.emit(self.tr("错误"),f"{e}","TOP","error")


    def select_scan_region(self,location_entry,path_entry=None,grab=False,returnable=False):
        signalBus.minimizeSignal.emit()
        screenshot_rect,grab_photo_path = capture_area(capture=grab)
        if screenshot_rect:
            x, y, width, height = screenshot_rect
            location_entry.setText(f"[{x}, {y}, {x + width}, {y + height}]")

        signalBus.maximizeSignal.emit()
        if grab_photo_path and path_entry:
            path_entry.setText(f"{grab_photo_path}")
        elif returnable and grab_photo_path:
            return screenshot_rect,grab_photo_path
        elif returnable:
            return screenshot_rect


    def select_point(self,location_entry):
        signalBus.minimizeSignal.emit()
        start_point = capture_point()
        signalBus.maximizeSignal.emit()
        if start_point:
            location_entry.setText(f"{start_point}")


    def select_line(self,line_method):
        signalBus.minimizeSignal.emit()
        line_points,line_time = capture_line(line_method)
        signalBus.maximizeSignal.emit()
        if line_points and line_time:
            return line_points,line_time


    def select_color(self,location_entry):
        signalBus.hideSignal.emit()
        mouse_color = capture_color()
        signalBus.maximizeSignal.emit()
        if mouse_color:
            location_entry.setText(f"{mouse_color}")


    def show_address(self,rec):
        if rec:
            try:
                outerscreen = QGuiApplication.primaryScreen()
                device_pixel_ratio = outerscreen.devicePixelRatio()  # 获取屏幕的DPI比例
                coords = rec.strip('[]').split(',')
                if len(coords) == 4:
                    x1, y1, x2, y2 = map(int, coords)
                    rect = QRect(int(x1/device_pixel_ratio), int(y1/device_pixel_ratio), int((x2 - x1)/device_pixel_ratio), int((y2 - y1)/device_pixel_ratio))
                    signalBus.minimizeSignal.emit()
                    show_rec(rect)
                else:
                    signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("不合法的地址"),"TOP","error")
            except:
                signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("不合法的地址"),"TOP","error")
        signalBus.maximizeSignal.emit()


    # 获取所有窗口句柄
    def get_all_hwnd(self):
        def impl(hwnd, *args):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
                hwnd_map.update({hwnd: win32gui.GetWindowText(hwnd)})
        hwnd_map = {}
        win32gui.EnumWindows(impl, 0)
        return hwnd_map


    # 将窗口置顶
    def window_show_top(self,window_title:str):
        hwnd_map = self.get_all_hwnd()
        for handle, title in hwnd_map.items():
            if window_title.isdigit():
                if not handle or handle != int(window_title):
                    continue
            else:
                if not title or title != window_title:
                    continue
            win32gui.BringWindowToTop(handle)
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')
            # 被其他窗口遮挡，调用后放到最前面
            win32gui.SetForegroundWindow(handle)
            # 解决被最小化的情况
            win32gui.ShowWindow(handle, win32con.SW_RESTORE)


    def error_print(self,error):
        now = datetime.now()
        log_directory = "app/backtrace_logs"
        timestamp = now.strftime("backtrace_%Y_%m_%d_%H_%M_log.txt")
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        log_filename = os.path.join(log_directory, timestamp)
        with open(log_filename, "w") as file:
            file.write(f"Error occurred at {now}:\n")
            file.write(f"{error}\n")


    def saveDataToJson(self,data: dict):
        """ Save the provided data dictionary to a JSON file using a file dialog """
        photo_folder = cfg.get(cfg.scriptFolders)
        folder = ''
        if photo_folder:
            folder = photo_folder[0]
        file_path, _ = QFileDialog.getSaveFileName(None, self.tr("保存为"), folder , "JSON Files (*.json)")
        self.saveDataToPath(data,file_path)



    def saveDataToPath(self,data: dict, file_path: str):
        if file_path:
            try:
                directory = os.path.dirname(file_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)
                if not file_path.endswith('.json'):
                    file_path += '.json'
                with open(file_path, 'w', encoding='utf-8') as json_file:
                    json.dump(data, json_file, ensure_ascii=False, indent=4)
            except Exception as e:
                signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("保存文件时发生错误:")+f"{e}","TOP","error")
                self.error_print(f"保存文件时发生错误: {e}")



    def loadDataFromJson(self):
        # 弹出文件选择对话框，允许用户选择一个文件
        photo_folder = cfg.get(cfg.scriptFolders)
        folder = ''
        if photo_folder:
            folder = photo_folder[0]
        file_path, _ = QFileDialog.getOpenFileName(None, self.tr('选择文件'), folder , 'JSON Files (*.json);;All Files (*)')
        return self.loadDataFromPath(file_path)



    def loadDataFromPath(self, file_path: str):
        if file_path:
            try:
                if not os.path.exists(file_path):
                    if file_path.startswith(TAB_PATH) or file_path.startswith(ADD_PATH):
                        default_data = {}
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(default_data, f, ensure_ascii=False, indent=4)
                        self.write_recent(file_path)
                        return default_data
                    else:
                        raise FileNotFoundError(f"文件不存在: {file_path}")

                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                self.write_recent(file_path)
                return data
            except Exception as e:
                signalBus.main_infobar_signal.emit(
                    self.tr("错误"),
                    self.tr("读取文件失败:") + f"{e}",
                    "TOP",
                    "error"
                )
                self.error_print(f"读取文件失败: {e}")
                return None
        else:
            return None



    def write_recent(self, file_path:str):
        try:
            # 生成新的数据项
            new_item = {
                "name": os.path.basename(file_path),
                "path": str(file_path),
                "load_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 当前时间
            }

            if os.path.exists(RECENT_PATH):
                with open(RECENT_PATH, 'r', encoding='utf-8') as recent_file:
                    recent_data = json.load(recent_file)
            else:
                recent_data = []


            found = False
            for item in recent_data:
                if item['path'] == file_path:
                    item.update(new_item)  # 覆盖
                    found = True
                    break

            if not found:
                recent_data.append(new_item)  # 追加

            recent_data.sort(key=lambda x: datetime.strptime(x['load_time'], "%Y-%m-%d %H:%M:%S"), reverse=True)

            # 写回 RECENT_PATH
            with open(RECENT_PATH, 'w', encoding='utf-8') as recent_file:
                json.dump(recent_data, recent_file, indent=4, ensure_ascii=False)

            signalBus.load_finished.emit(recent_data)

        except Exception as e:
            print(e)
            with open(RECENT_PATH, 'w', encoding='utf-8') as recent_file:
                json.dump([], recent_file, indent=4, ensure_ascii=False)



    def remove_recent(self, file_path):
        try:
            if not os.path.exists(RECENT_PATH):
                return
            with open(RECENT_PATH, 'r', encoding='utf-8') as recent_file:
                recent_data = json.load(recent_file)

            recent_data = [item for item in recent_data if item['path'] != str(file_path)]

            with open(RECENT_PATH, 'w', encoding='utf-8') as recent_file:
                json.dump(recent_data, recent_file, indent=4, ensure_ascii=False)

            signalBus.load_finished.emit(recent_data)
        except Exception as e:
            self.error_print(e)



    #显示信息条
    def show_infobar(self, parent , title:str , content:str,  pos = InfoBarPosition.TOP_RIGHT, method:str = None):
        existing_infobar = parent.findChild(InfoBar)
        if existing_infobar:
            return
        else:
            bar_method = getattr(InfoBar, method, InfoBar.info)
            bar_method(
                self.tr(title),
                self.tr(content),
                duration=1500,
                position=pos,
                parent=parent if parent else self.window()
            )




    def update_config_value(self,config_file_path, key_path, value):
        """更新配置文件中的指定键值，如果键不存在，则会自动创建"""
        # 1. 读取现有配置文件
        if not os.path.exists(config_file_path):  # 如果文件不存在
            config_data = {}  # 初始化空的配置数据
        else:
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except FileNotFoundError:
                signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("不存在的配置文件"),"TOP","error")
                return
            except json.JSONDecodeError as e:
                signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("解码错误")+f"{e}","TOP","error")
                return

        # 2. 逐级找到指定的键并更新其值，若键不存在则创建新的键
        keys = key_path.split(".")  # 按 "." 分割获取多级路径
        data = config_data
        for key in keys[:-1]:  # 遍历到倒数第二级
            if key not in data:
                data[key] = {}  # 如果键不存在，则创建一个新的字典
            data = data[key]

        # 更新最后一个键的值
        final_key = keys[-1]
        data[final_key] = value

        # 3. 保存回配置文件
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)


    def read_config_value(self,config_file_path, key_path):
        """读取配置文件中的指定键值"""
        if not os.path.exists(config_file_path):  # 如果文件不存在
            return None
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("解码错误")+f"{e}","TOP","error")
            return None

        keys = key_path.split(".")  # 按 "." 分割获取多级路径
        data = config_data
        for key in keys:
            if key in data:
                data = data[key]
            else:
                return None
        return data



    def figure_out(self,text:str):
        result = None
        try:
            if re.match(r'^[\d+\-*/().\s]+$', text):
                result = eval(text)
        except Exception as e:
            pass
        return result



#读取目标图片
    def load_target_image(self,path):
        if isinstance(path, np.ndarray):
            return path
        try:
            if path.startswith("data:image"):
                base64_data = path.split(',')[1]
                img_data = base64.b64decode(base64_data)
                img = Image.open(BytesIO(img_data))
                target_image = np.array(img)
                return target_image
            target_image = Image.open(path)
        except:
            return None  # 返回 None 表示没有有效的内容
        target_image = np.array(target_image)
        return target_image


photo_tool = Photo_Tools()