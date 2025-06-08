import os, base64, io
from PIL import ImageGrab
import cv2
import numpy as np
import io
import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QWidget,QLabel,QHBoxLayout
from qfluentwidgets import (Action, qrouter, PrimaryDropDownToolButton, LineEdit,TransparentPushButton,RoundMenu,qconfig,TeachingTipTailPosition,TeachingTipView,TeachingTip,PrimaryToolButton,ToolTipFilter,FluentIcon)


from ..common.photo_tool import photo_tool
from ..common.signal_bus import signalBus
from ..common.config import cfg
from .hover_tooltip import HoverTrigger
from ..common.style_sheet import StyleSheet
from ..common.recognizer_registry import register_recognizer



# 返回值类 用于确信返回值并将其保存到manager中去
class RecognizeResult(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置默认结构
        self.setdefault("loc", [0, 0, 0, 0])      # 匹配区域坐标
        self.setdefault("text", "")                # 识别文本
        self.setdefault("command", "")             # 命令执行结果

    def save(self, parent, chosen_index):
        """将结果保存到 ParametersManager 的统一字典中"""
        if hasattr(parent, 'manager') and hasattr(parent.manager, 'results'):
            # 只保存我们关心的字段
            for key in ['loc', 'text', 'command']:
                if key in self:
                    parent.manager.results[chosen_index][key] = self[key]
        else:
            photo_tool.error_print(f"[警告] 未找到有效的 results 存储位置")

    def save_and_return(self, parent, chosen_index=None, returnloc=False):
        """保存结果并可选择返回位置信息"""
        if chosen_index is not None:
            self.save(parent, chosen_index)
        if returnloc:
            return self.get('loc', [0, 0, 0, 0])
        return True



def compare_images_with_config(parent, target, address_content, chosen_index=None, returnloc=False, **kwargs):
    method = cfg.get(cfg.photoMethod)
    if method == "template":
        return compare_images_with_template_matching(
            parent, target, address_content, chosen_index, returnloc, **kwargs
        )
    else:
        return compare_images_with_feature_matching(
            parent, target, address_content, chosen_index, returnloc, **kwargs
        )



#模板匹配图片识别
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



#特征匹配图片识别
def compare_images_with_feature_matching(parent, target, address_content, chosen_index=None, returnloc=False, **kwargs):
    target = photo_tool.load_target_image(target)
    screenshot = kwargs.get("screenshot")
    image1 = np.array(screenshot)
    try:
        # 转换为灰度图
        gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        gray_image2 = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
    except cv2.error as e:
        photo_tool.error_print(e)
        return False

    # 初始化SIFT特征检测器
    sift = cv2.SIFT_create()

    # 检测特征点和描述符
    keypoints1, descriptors1 = sift.detectAndCompute(gray_image1, None)
    keypoints2, descriptors2 = sift.detectAndCompute(gray_image2, None)

    if len(keypoints1) == 0 or len(keypoints2) == 0:
        return False  # 没有找到足够的特征点

    # 使用FLANN (Fast Library for Approximate Nearest Neighbors) 进行匹配
    index_params = dict(algorithm=1, trees=10)  # 这里设置了FLANN的参数
    search_params = dict(checks=50)  # 设置搜索的次数

    flann = cv2.FlannBasedMatcher(index_params, search_params)

    # 进行特征点匹配
    matches = flann.knnMatch(descriptors1, descriptors2, k=2)

    # 过滤匹配点 使用低e值比值检验 David Lowe方法
    good_matches = []
    similarity_threshold = getattr(parent, 'check_similar', 0.75)
    for m, n in matches:
        if m.distance < similarity_threshold * n.distance:
            good_matches.append(m)

    # 如果匹配点数目少于某个阈值，认为匹配失败
    if len(good_matches) > 0:
        # 获取匹配点的坐标
        src_pts = np.float32([keypoints1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        # 计算变换矩阵（透视变换）
        try:
            matrix, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        except cv2.error as e:
            return False
        if matrix is not None:
            # 获取模板图像的大小
            h, w = target.shape[:2]
            corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
            transformed_corners = cv2.perspectiveTransform(corners, matrix)

            top_left = transformed_corners[0][0]  # 左上角
            bottom_right = transformed_corners[2][0]  # 右下角
            dx, dy = address_content[0], address_content[1]

            global_top_left = (int(top_left[0]) + int(dx), int(top_left[1]) + int(dy))
            global_bottom_right = (int(bottom_right[0]) + int(dx), int(bottom_right[1]) + int(dy))

            result_obj = RecognizeResult(
                loc=(global_top_left, global_bottom_right)
            )
            return result_obj.save_and_return(parent, chosen_index, returnloc)
        else:
            return False
    else:
        return False



#比对文字相似度,确认是否符合要求
def compare_text_with_ocr(parent, target, address_content, chosen_index=None, returnloc=False, **kwargs):
    """对比OCR识别结果与目标文本"""
    screenshot = kwargs.get("screenshot")
    # 将截图转换为字节流
    byte_io = io.BytesIO()
    screenshot.save(byte_io, format='PNG')
    # 获取OCR实例
    ocr = getattr(parent.pivot.tabpage.tabinterface.homeInterface, "ocr", None)
    if ocr is None:
        return False

    try:
        ocr_result = ocr.runBytes(byte_io.getvalue())
    except Exception as e:
        photo_tool.error_print(e)
        return False  # 发生异常时，直接返回 False

    if not (ocr_result and isinstance(ocr_result, dict) and 'data' in ocr_result and isinstance(ocr_result['data'], list)):
        return False  # OCR 结果无效，直接返回 False

    similarity_threshold = getattr(parent, 'check_similar', 0.75)
    dx, dy = address_content[0],address_content[1]
    all_texts = []
    all_boxes = []

    for item in ocr_result['data']:
        recognized_text = item.get('text', '').strip()
        score = item.get('score', 0)
        box = item.get('box', [])
        if not recognized_text or score < similarity_threshold:
            continue
        adjusted_box = [[x + dx, y + dy] for x, y in box]
        pt1, pt2 = tuple(adjusted_box[0]), tuple(adjusted_box[2])
        all_texts.append(recognized_text)
        all_boxes.append((pt1, pt2))

        if target.startswith("re(") and target.endswith(")"):
            continue
        elif target.strip() in recognized_text:
            result_obj = RecognizeResult(
                loc=(pt1, pt2),
                text=recognized_text
            )
            return result_obj.save_and_return(parent, chosen_index, returnloc)

    combined_text = " ".join(all_texts)

    if target.startswith("re(") and target.endswith(")") and all_texts:
        pattern = target[3:-1]
        match = re.search(pattern, combined_text)
        if match:
            matched_text = match.group()
            matched_words = matched_text.split()  # 拆分匹配到的文本（按空格）
            matched_boxes = []
            matched_text_found = ""
            for idx, recognized_text in enumerate(all_texts):
                if any(word in recognized_text for word in matched_words):
                    matched_boxes.append(all_boxes[idx])
                    matched_text_found += recognized_text + " "
                # 如果已经匹配到完整的 `matched_text`，就停止搜索
                if matched_text_found.strip() == matched_text.strip():
                    break
            if matched_boxes:
                pt1 = min(matched_boxes, key=lambda x: x[0])[0]  # 取最左上角
                pt2 = max(matched_boxes, key=lambda x: x[1])[1]  # 取最右下角
                result_obj = RecognizeResult(
                    loc=(pt1, pt2),
                    text=matched_text
                )
                return result_obj.save_and_return(parent, chosen_index, returnloc)

    return False  # 未找到匹配文本



# 识别图像中的颜色位置
def compare_images_with_color(parent, target, address_content, chosen_index=None, returnloc=False, **kwargs):
    screenshot = kwargs.get("screenshot")
    image = np.array(screenshot)
    try:
        target_color_rgb = np.array([int(target[i:i+2], 16) for i in (1, 3, 5)], dtype=np.uint8)
    except Exception:
        return False

    # 计算颜色差异
    diff = np.abs(image.astype(np.int16) - target_color_rgb)  # 用 int16 防止溢出
    mask = np.all(diff <= 10, axis=-1)  # 找到所有颜色匹配的像素点

    if np.any(mask):  # 如果找到了匹配的颜色
        # 获取所有匹配像素的坐标
        matching_pixels = np.column_stack(np.where(mask))

        # 获取最小 & 最大 x、y 坐标
        min_y, min_x = np.min(matching_pixels, axis=0)
        max_y, max_x = np.max(matching_pixels, axis=0)
        # 计算偏移后的坐标
        dx, dy = address_content[0], address_content[1]

        result_obj = RecognizeResult(
            loc=(
                (int(min_x + dx), int(min_y + dy)),
                (int(max_x + dx), int(max_y + dy))
            )
        )
        return result_obj.save_and_return(parent, chosen_index, returnloc)
    else:
        return False  # 没有找到匹配的颜色



def compare_with_true(**kwargs):
    return True



#图像识别栏
@register_recognizer("图像识别", FluentIcon.PHOTO, compare_images_with_config , ["loc"])
class ImageRecognitionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建控件
        self.scanpage = parent
        self.t = None

        self.image_show = TransparentPushButton(self.tr('图片'), self)
        HoverTrigger(self.image_show, hover_callback=self.showLeftBottomTeachingTip, leave_callback=self.closeView, hover_delay=300)
        self.photo_base = ''
        self.line_edit = LineEdit(self)
        self.line_edit.setClearButtonEnabled(True)
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
        cut_action.triggered.connect(lambda: photo_tool.select_scan_region(self.address_edit))  # 绑定框选
        grab_action.triggered.connect(self.handle_scan_result)
        show_action.triggered.connect(lambda: photo_tool.show_address(self.address_edit.text()))
        menu.addAction(cut_action)
        menu.addAction(grab_action)
        menu.addAction(show_action)
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


    def check_picture(self,text):
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



#文字识别栏
@register_recognizer("文字识别", FluentIcon.DICTIONARY,compare_text_with_ocr , ["loc","text"])
class TextRecognitionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanpage = parent

        # 创建控件
        self.text_label = TransparentPushButton(self.tr('文本'), self)
        self.text_label.installEventFilter(ToolTipFilter(self.text_label))
        self.text_label.setToolTip(self.tr('re()内被视为正则,如"re(.*)"代表任何内容'))
        self.line_edit = LineEdit(self)
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.setMinimumWidth(160)
        self.line_edit.setPlaceholderText(self.tr("文字识别内容"))

        self.address_edit = LineEdit(self)
        self.address_edit.setText(self.tr('[0,0,0,0]'))
        self.address_edit.setPlaceholderText("[x1,y1,x2,y2]")
        menu = RoundMenu(parent=self)
        cut_action = Action(FluentIcon.CLIPPING_TOOL, self.tr('框选区域'))
        grab_action = Action(FluentIcon.FONT, self.tr('文字识别'))
        show_action = Action(FluentIcon.HIGHTLIGHT,self.tr('显示区域'))
        cut_action.triggered.connect(lambda: photo_tool.select_scan_region(self.address_edit))  # 绑定框选
        grab_action.triggered.connect(self.getOCRresult)
        show_action.triggered.connect(lambda: photo_tool.show_address(self.address_edit.text()))
        menu.addAction(cut_action)
        menu.addAction(grab_action)
        menu.addAction(show_action)
        self.select_button = PrimaryDropDownToolButton(FluentIcon.CLIPPING_TOOL, self)
        self.select_button.setMenu(menu)

        # 创建布局，使用水平布局
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.text_label)  # 文本标签
        self.layout.addWidget(self.line_edit)  # 文本框
        self.layout.addWidget(self.address_edit)  # 地址文本框
        self.layout.addWidget(self.select_button)  # 框选按钮

        # 设置布局
        self.setLayout(self.layout)
        self.line_edit.textChanged.connect(self.scanpage.save_graph)
        self.address_edit.textChanged.connect(self.scanpage.save_graph)



    def OCRimg(self,image):
        byte_io = io.BytesIO()
        image.save(byte_io, format='PNG')
        image_bytes = byte_io.getvalue()
        ocr_result = None
        ocr = self.scanpage.pivot.tabpage.tabinterface.homeInterface.ocr
        try:
            ocr_result = ocr.runBytes(image_bytes)
        except Exception as e:
            photo_tool.error_print(e)
            ocr_result = None
        recognized_result =""
        if ocr_result and isinstance(ocr_result, dict) and 'data' in ocr_result and isinstance(ocr_result['data'], list):
            for item in ocr_result['data']:
                recognized_text = item['text']
                if recognized_text:
                    recognized_result += recognized_text + " "
            recognized_result = recognized_result.strip()
        return recognized_result


    def getOCRresult(self):
        return_address =  photo_tool.select_scan_region(self.address_edit,returnable=True)
        x1, y1, w, h = return_address
        image = ImageGrab.grab(bbox=(x1, y1, x1+w, y1+h))
        if image is None:
            self.line_edit.clear()
        else:
            result = self.OCRimg(image)
            self.line_edit.setText(result)



#颜色识别栏
@register_recognizer("颜色识别", FluentIcon.PALETTE, compare_images_with_color , ["loc"])
class ColorRecognitionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanpage = parent

        # 创建控件
        self.color_show = QLabel(self.tr("颜色"))
        self.color_show.setObjectName("show_color")
        self.color_show.setMinimumWidth(53)

        self.line_edit = LineEdit(self)
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.setMinimumWidth(160)
        self.line_edit.setPlaceholderText("#000000")

        self.get_color_button = PrimaryToolButton(FluentIcon.BRUSH, self)
        self.get_color_button.clicked.connect(lambda: photo_tool.select_color(self.line_edit))

        self.address_edit = LineEdit(self)
        self.address_edit.setText(self.tr('[0,0,0,0]'))
        self.address_edit.setPlaceholderText("[x1,y1,x2,y2]")
        menu = RoundMenu(parent=self)
        cut_action = Action(FluentIcon.CLIPPING_TOOL, self.tr('框选区域'))
        show_action = Action(FluentIcon.HIGHTLIGHT,self.tr('显示区域'))
        cut_action.triggered.connect(lambda: photo_tool.select_scan_region(self.address_edit))  # 绑定框选
        show_action.triggered.connect(lambda: photo_tool.show_address(self.address_edit.text()))
        menu.addAction(cut_action)
        menu.addAction(show_action)
        self.select_button = PrimaryDropDownToolButton(FluentIcon.CLIPPING_TOOL, self)
        self.select_button.setMenu(menu)

        # 创建布局，使用水平布局
        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.color_show)  # 显示颜色
        self.layout.addWidget(self.line_edit)  # 颜色文本框
        self.layout.addWidget(self.get_color_button) # 取色按钮
        self.layout.addWidget(self.address_edit)  # 地址文本框
        self.layout.addWidget(self.select_button)  # 框选按钮

        # 设置布局
        self.setLayout(self.layout)
        self.line_edit.textChanged.connect(self.scanpage.save_graph)
        self.line_edit.textChanged.connect(self.showCurrentColor)
        self.address_edit.textChanged.connect(self.scanpage.save_graph)

    def showCurrentColor(self):
        color_text = self.line_edit.text().strip()
        color = QColor(color_text)
        if color.isValid():
            self.color_show.setStyleSheet(f"background-color: {color.name()};color:white;")
        else:
            self.color_show.setStyleSheet("background-color: transparent;")



#必定成功
@register_recognizer("必定成功", FluentIcon.CHECKBOX, compare_with_true)
class AlwaysSuccessWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanpage = parent
        # 创建控件
        self.text_label = QLabel(self.tr('此识别必定判断成功'), self)
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






