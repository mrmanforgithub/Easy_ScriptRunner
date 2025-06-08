from PyQt5.QtCore import Qt, QUrl,QThread, pyqtSignal
from PyQt5.QtWidgets import QScrollArea,QApplication
from PyQt5.QtGui import QDesktopServices
from qfluentwidgets import MessageBox, BodyLabel, FluentStyleSheet,Dialog

from ..common.signal_bus import signalBus
from ..common.config import cfg,RELEASE_URL,VERSION
from ..common.photo_tool import photo_tool

from packaging.version import parse
from enum import Enum
import markdown
import requests
import re
import os
import time
import threading


class MessageBoxHtml(Dialog):
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(title, content, parent)
        self.setTitleBarVisible(False)
        self.textLayout.removeWidget(self.contentLabel)
        self.contentLabel.clear()

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;background-color: transparent;")
        scroll_area.setMinimumSize(400,400)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 设置 contentLabel
        self.contentLabel = BodyLabel(content, parent)
        scroll_area.setWidget(self.contentLabel)  # 将 contentLabel 放入滚动区域

        self.contentLabel.setWordWrap(True)
        self.contentLabel.setObjectName("contentLabel")
        self.contentLabel.setOpenExternalLinks(True)
        self.contentLabel.linkActivated.connect(self.open_url)
        self.contentLabel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        FluentStyleSheet.DIALOG.apply(self.contentLabel)
        self.contentLabel.setMinimumWidth(360)


        # 重新添加按钮
        self.textLayout.addWidget(scroll_area, 0, Qt.AlignTop)

    def open_url(self, url):
        QDesktopServices.openUrl(QUrl(url))



class MessageBoxUpdate(MessageBoxHtml):
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(title, content, parent)
        self.yesButton.setText(self.tr('立刻下载'))
        self.cancelButton.setText(self.tr('我知道了'))




class UpdateStatus(Enum):
    """更新状态枚举类，用于指示更新检查的结果状态。"""
    SUCCESS = 1
    UPDATE_AVAILABLE = 2
    FAILURE = 0


class UpdateThread(QThread):
    """负责后台检查更新的线程类。"""
    updateSignal = pyqtSignal(UpdateStatus)

    def __init__(self, timeout, flag):
        super().__init__()
        self.timeout = timeout  # 超时时间
        self.flag = flag  # 标志位，用于控制是否执行更新检查

    def remove_images_from_markdown(self, markdown_content):
        """从Markdown内容中移除图片标记。"""
        img_pattern = re.compile(r'!\[.*?\]\(.*?\)')
        return img_pattern.sub('', markdown_content)

    def fetch_latest_release_info(self):
        """获取最新的发布信息。"""
        response = requests.get(
            RELEASE_URL,
            timeout=10,
            headers= cfg.useragent
        )
        response.raise_for_status()
        return response.json()[0] if cfg.get(cfg.update_prerelease_enable) else response.json()

    def get_download_url_from_assets(self, assets):
        """从发布信息中获取下载URL(第一个文件)"""
        for asset in assets:
            if asset:
                return asset["browser_download_url"]
            return None
        return None

    def run(self):
        """执行更新检查逻辑。"""
        try:
            if not self.flag and not cfg.get(cfg.checkUpdateAtStartUp):
                return

            data = self.fetch_latest_release_info()
            version = data["tag_name"]
            content = self.remove_images_from_markdown(data["body"])
            assert_url = self.get_download_url_from_assets(data["assets"])

            if assert_url is None:
                self.updateSignal.emit(UpdateStatus.SUCCESS)
                return

            if parse(version.lstrip('v')) > parse(VERSION.lstrip('v')):
                self.title =self.tr("发现新版本：")+f"{VERSION} ——> {version}\n"+self.tr("更新日志|･ω･)")
                self.content = "<style>a {color: #f18cb9; font-weight: bold;}</style>" + markdown.markdown(content)
                self.assert_url = assert_url
                self.updateSignal.emit(UpdateStatus.UPDATE_AVAILABLE)
            else:
                self.updateSignal.emit(UpdateStatus.SUCCESS)
        except Exception as e:
            self.updateSignal.emit(UpdateStatus.FAILURE)




def checkUpdate(self, timeout=5, flag=False):
    """检查更新，并根据更新状态显示不同的信息或执行更新操作。"""
    def handle_update(status):
        try:
            if status == UpdateStatus.UPDATE_AVAILABLE:
                # 显示更新对话框

                message_box = MessageBoxUpdate(
                    self.update_thread.title,
                    self.update_thread.content,
                    self.window()
                )
                if message_box.exec():
                    assert_url = self.update_thread.assert_url
                    download_dir = cfg.get(cfg.downloadFolder)
                    if not os.path.exists(download_dir):
                        os.makedirs(download_dir)
                    # 启动下载线程
                    download_thread = threading.Thread(target=download_file, args=(assert_url, download_dir), daemon =True)
                    download_thread.start()
            elif status == UpdateStatus.SUCCESS:
                # 显示当前为最新版本的信息
                signalBus.main_infobar_signal.emit("","当前是最新版本(＾∀＾●)","TOP","success")
            else:
                signalBus.main_infobar_signal.emit("","检测更新失败(╥╯﹏╰╥)","TOP","warning")
        except Exception as e:
            photo_tool.error_print(e)


    def download_file(assert_url, download_dir, speed_threshold_kb=100):
        """后台下载文件的方法，支持速度监控和自动终止。"""
        try:
            signalBus.download_signal.emit(True, "")  # 发送开始下载信号

            file_name = os.path.basename(assert_url)
            file_path = os.path.join(download_dir, file_name)

            # 发起下载请求
            response = requests.get(assert_url, stream=True, timeout=30)
            response.raise_for_status()

            start_time = time.time()
            downloaded_bytes = 0

            # 将文件保存到本地
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded_bytes += len(chunk)

                    # 计算下载速度
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 0:
                        speed_kb = downloaded_bytes / elapsed_time / 1024
                        # 如果下载速度低于阈值，终止下载
                        if speed_kb < speed_threshold_kb:
                            signalBus.download_signal.emit(False, "下载速度过慢，已终止")
                            os.remove(file_path)  # 删除已下载的部分文件
                            return

            # 下载完成，发送成功信号
            signalBus.download_signal.emit(True, file_path)

        except requests.exceptions.RequestException as e:
            # 下载失败，发送失败信号
            signalBus.download_signal.emit(False, str(e))
        except (KeyboardInterrupt, SystemExit):
            # 捕获主程序退出信号，清理资源
            if os.path.exists(file_path):
                os.remove(file_path)
            signalBus.download_signal.emit(False, "下载已终止")


    self.update_thread = UpdateThread(timeout, flag)
    self.update_thread.updateSignal.connect(handle_update)
    self.update_thread.start()



