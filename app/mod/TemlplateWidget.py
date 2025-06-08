# MOD_TYPE: recognizer
# 这是图像识别 Mod


import os, base64
import cv2
import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget,QLabel,QHBoxLayout,QTextEdit
from qfluentwidgets import  (Action, qrouter, PrimaryDropDownToolButton, LineEdit,TransparentPushButton,RoundMenu,qconfig,TeachingTipTailPosition,TeachingTipView,TeachingTip,PrimaryToolButton,ToolTipFilter,FluentIcon,TextEdit)


from app.common.photo_tool import photo_tool
from app.common.signal_bus import signalBus
from app.common.config import cfg
from app.common.style_sheet import StyleSheet
from app.components.hover_tooltip import HoverTrigger
from app.common.recognizer_registry import register_recognizer
from app.components.recognizer_widget import RecognizeResult
from app.mod.param_text_edit import DynamicParamTextEdit


def compare_with_False(**kwargs):
    return False


def compare_images_with_template_matching(parent, target, address_content, chosen_index=None, returnloc=False, **kwargs):
    # 将图像转换为灰度图
    target = photo_tool.load_target_image(target)
    screenshot = kwargs.get("screenshot")
    image1 = np.array(screenshot)
    try:
        gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        gray_image2 = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
    except cv2.error as e:
        photo_tool.error_print(e)
        return False

    # 获取模板的宽高
    h, w = gray_image2.shape[:2]

    # 设置多尺度匹配的范围
    min_scale = 0.5
    max_scale = 2.0
    similarity_threshold = getattr(parent, 'check_similar', 0.75)  # 设定相似度阈值
    h1, w1 = gray_image1.shape  # 获取背景图尺寸

    scales = [1.0] + [s for s in np.arange(min_scale, max_scale + 0.1, 0.1) if s != 1.0]

    for scale in scales:
        resized_template = cv2.resize(gray_image2, (int(w * scale), int(h * scale)))
        if resized_template.shape[0] > h1 or resized_template.shape[1] > w1:
            continue
        result = cv2.matchTemplate(gray_image1, resized_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= similarity_threshold:
            dx, dy = address_content[0],address_content[1]
            top_left = (max_loc[0] + dx, max_loc[1] + dy)
            bottom_right = (top_left[0] + int(w * scale), top_left[1] + int(h * scale))

            result_obj = RecognizeResult(
                loc=(top_left, bottom_right)
            )

            return result_obj.save_and_return(parent, chosen_index, returnloc)
    return False



@register_recognizer("模板匹配", FluentIcon.PHOTO,  compare_images_with_template_matching,["loc","command"])
class TemlplateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建控件
        self.scanpage = parent
        self.t = None

        self.image_show = TransparentPushButton(self.tr('图片'), self)
        HoverTrigger(self.image_show, hover_callback=self.showLeftBottomTeachingTip, leave_callback=self.closeView, hover_delay=300)
        self.photo_base = ''
        self.line_edit = DynamicParamTextEdit()
        # self.line_edit = LineEdit(self)
        # self.line_edit.setClearButtonEnabled(True)
        self.line_edit.setMinimumWidth(160)
        self.line_edit.setPlaceholderText(self.tr("图片路径/Base64编码"))

        self.browse_button = PrimaryToolButton(FluentIcon.FOLDER, self)
        self.browse_button.clicked.connect(lambda: photo_tool.browse_file(self.line_edit))

        self.address_edit = LineEdit(self)
        self.address_edit.setText(self.tr('[0,0,0,0]'))
        self.address_edit.setPlaceholderText("[x1,y1,x2,y2]")

        menu = RoundMenu(parent=self)
        cut_action = Action(FluentIcon.CLIPPING_TOOL, self.tr('框选区域'))
        grab_action = Action(FluentIcon.CAMERA, self.tr('一键截图'))
        show_action = Action(FluentIcon.HIGHTLIGHT,self.tr('显示区域'))
        insert_action = Action(FluentIcon.EDIT,self.tr('插入文本'))
        cut_action.triggered.connect(lambda: photo_tool.select_scan_region(self.address_edit))  # 绑定框选
        grab_action.triggered.connect(self.handle_scan_result)
        show_action.triggered.connect(lambda: photo_tool.show_address(self.address_edit.text()))
        insert_action.triggered.connect(lambda: self.line_edit.insert_dynamic_param())
        menu.addAction(cut_action)
        menu.addAction(grab_action)
        menu.addAction(show_action)
        menu.addAction(insert_action)
        self.select_button = PrimaryDropDownToolButton(FluentIcon.CLIPPING_TOOL, self)
        self.select_button.setMenu(menu)

        # 创建布局，使用水平布局
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.image_show)
        self.layout.addWidget(self.line_edit)
        self.layout.addWidget(self.browse_button)
        self.layout.addWidget(self.address_edit)
        self.layout.addWidget(self.select_button)
        # 设置布局
        self.setLayout(self.layout)
        self.line_edit.textChanged.connect(self.check_picture)
        self.address_edit.textChanged.connect(self.scanpage.save_graph)



    def check_picture(self):
        text = self.line_edit.toPlainText()
        if not text:
            self.photo_base = ""
            self.scanpage.save_graph()
        try:
            if text.startswith("data:image"):
                    img_data = base64.b64decode(text.split(',')[1])  # 去除前缀 "data:image/png;base64,"
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)
                    if not pixmap.isNull():
                        self.photo_base = text
                        self.scanpage.save_graph()
            elif os.path.isfile(text) and text.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif')):
                pixmap = QPixmap(text)
                if not pixmap.isNull():
                    self.photo_base = text
                    self.scanpage.save_graph()
        except Exception:
            if self.photo_base.startswith(text):
                pass
            else:
                self.photo_base = text
                self.scanpage.save_graph()



    def handle_scan_result(self):
        try:
            _,photo_value = photo_tool.select_scan_region(self.address_edit, grab=True, returnable=True)
            if photo_value:
                self.photo_base = photo_value  # 清空 photo_base
                self.line_edit.setText(photo_value)  # 直接存入 line_edit
        except:
            pass


    def check_and_display_image(self):
        text = self.photo_base
        if not text:
            return None
        try:
            if text.startswith("data:image"):
                    img_data = base64.b64decode(text.split(',')[1])  # 去除前缀 "data:image/png;base64,"
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)
                    if not pixmap.isNull():
                        return pixmap
            elif os.path.isfile(text) and text.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif')):
                pixmap = QPixmap(text)
                if not pixmap.isNull():
                    return pixmap
        except Exception as e:
            signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("Base64解码错误:")+f"{e}","TOP","error")
            return None


    def showLeftBottomTeachingTip(self):
        pimage = self.check_and_display_image()
        if not pimage:
            signalBus.main_infobar_signal.emit(self.tr("错误"),self.tr("图片格式错误"),"TOP","error")
            return
        pos = TeachingTipTailPosition.LEFT_BOTTOM
        view = TeachingTipView(
            icon=None,
            title='',
            content=self.tr(""),
            image= pimage ,
            isClosable=False,
            tailPosition=pos,
        )
        view.imageLabel.setFixedSize(200,200)
        self.t = TeachingTip.make(view, self.image_show, -1, pos, self)


    def closeView(self):
        try:
            self.t.close()
        except:
            pass



@register_recognizer("必定失败", FluentIcon.BASKETBALL, compare_with_False)
class AlwaysFalseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanpage = parent
        # 创建控件
        self.text_label = QLabel(self.tr('此识别必定判断失败'), self)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setObjectName("text_label")

        self.line_edit = LineEdit(self)
        self.line_edit.setText("True")
        self.line_edit.setVisible(False)  # 隐藏文本框
        self.address_edit = LineEdit(self)
        self.address_edit.setText("[10,10,10,10]")
        self.address_edit.setVisible(False)
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.text_label)  # 文本标签
        self.layout.addWidget(self.line_edit)  # 文本框
        self.layout.addWidget(self.address_edit)  # 地址文本框
        # 设置布局
        self.setLayout(self.layout)
        StyleSheet.SCAN_PAGE.apply(self.text_label)

