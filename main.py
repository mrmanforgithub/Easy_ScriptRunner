# coding:utf-8
import os
import sys
import portalocker
from pathlib import Path

from PyQt5.QtCore import Qt, QTranslator
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.common.photo_tool import photo_tool
from app.view.main_window import MainWindow




def start():

    # 将主程序根目录加入Python路径
    sys.path.append(str(Path(__file__).parent.parent))

    def check_single_instance():
        lockfile_path = 'app/config/ScriptRunner.lock'
        os.makedirs(os.path.dirname(lockfile_path), exist_ok=True)
        try:
            lockfile = open(lockfile_path, 'w')
            portalocker.lock(lockfile, portalocker.LOCK_EX | portalocker.LOCK_NB)
            return lockfile
        except Exception:
            return None

    lockfile = check_single_instance()
    if lockfile is None:
        sys.stderr = open(os.devnull, 'w')
        photo_tool.window_show_top("ScriptRunner")
        sys.exit(0)

    # enable dpi scale
    if cfg.get(cfg.dpiScale) == "Auto":
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    else:
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # create application
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    locale = cfg.get(cfg.language).value
    translator = FluentTranslator(locale)
    app.installTranslator(translator)

    galleryTranslator = QTranslator()
    if locale.name() != "zh_CN":
        galleryTranslator.load(locale, "scriptrunner", ".", ":/i18n")
        app.installTranslator(galleryTranslator)
    # create main window
    w = MainWindow()
    w.show()
    app.exec_()


start()