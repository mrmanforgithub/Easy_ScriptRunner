# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import  QVBoxLayout, QLabel,QTextBrowser
from .gallery_interface import GalleryInterface


class SupportInterface(GalleryInterface):
    """ support interface """

    def __init__(self, parent=None):
        super().__init__(
            title="关于",
            subtitle="软件/作者/鸣谢/其他",
            parent=parent
        )
        self.setObjectName('supportInterface')
        # 创建作者部分
        creater_label = QLabel(self.tr("作者"))
        creater_label.setStyleSheet("font-size: 18px;")
        creater_content = QLabel("mrmanforgithub")
        creater_content.setStyleSheet("font-size: 18px; color: #009faa;")


        # 创建鸣谢部分
        thank_label = QLabel(self.tr("鸣谢"))
        thank_label.setStyleSheet("font-size: 18px;")
        thanks_label = QTextBrowser()
        thanks_label.setHtml("""
            <a href="https://github.com/mrmanforgithub/Easy_ScriptRunner" style="color: #009faa; text-decoration: none;">"""+self.tr("软件仓库")+""":ScriptRunner</a><br>
            <a href="https://opencv.org/" style="color: #009faa; text-decoration: none;">"""+self.tr("图像识别")+""":opencv</a><br>
            <a href="https://github.com/hiroi-sora/PaddleOCR-json" style="color: #009faa; text-decoration: none;">"""+self.tr("文字识别")+""":PaddleOCR</a><br>
            <a href="https://github.com/zhiyiYo/PyQt-Fluent-Widgets" style="color: #009faa; text-decoration: none;">"""+self.tr("GUI组件库")+""":PyQt-Fluent-Widgets</a><br>
            <a href="https://github.com/moesnow/March7thAssistant" style="color: #009faa; text-decoration: none;">"""+self.tr("软件参考")+""":March7thAssistant</a><br>
        """)
        thanks_label.setOpenExternalLinks(True)  # 允许点击跳转
        thanks_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        thanks_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        thanks_label.setMinimumHeight(150)

        # 创建软件声明部分
        declara_label = QLabel(self.tr("软件声明"))
        declara_label.setStyleSheet("font-size: 18px;")
        declaration_text = self.tr("本软件永久开源、免费，仅供学习交流。")+"\n"+self.tr("请勿使用此软件代练或者是滥用软件。")+"\n"+self.tr("因此产生问题及后果, 与本软件和作者无关。")+"\n"+self.tr("用户在使用过程中需自行遵守相关平台的使用规则与服务条款。")+"\n"+self.tr("因使用本软件可能导致的游戏账号封禁、违规行为等一切后果作者概不负责。")+"\n"+self.tr("用户需对自身行为负责,并承担使用本软件可能带来的所有风险。")
        declaration_label = QLabel(declaration_text)
        declaration_label.setStyleSheet("font-size: 15px; color: #009faa;")

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(creater_label)
        self.vlayout.addWidget(creater_content)
        self.vlayout.addWidget(thank_label)
        self.vlayout.addWidget(thanks_label)
        self.vlayout.addWidget(declara_label)
        self.vlayout.addWidget(declaration_label)

        self.vlayout.setContentsMargins(10, 10, 10, 10)
        self.vlayout.setSpacing(20)


        self.addNolinkLayout(
            self.vlayout
        )
