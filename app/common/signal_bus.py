# coding: utf-8
from PyQt5.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    """ Signal bus """

    switchToInterface = pyqtSignal(str)
    micaEnableChanged = pyqtSignal(bool)

    supportSignal = pyqtSignal()

    messagebox_signal = pyqtSignal(object, object, object)



    minimizeSignal = pyqtSignal()
    maximizeSignal = pyqtSignal()
    hideSignal = pyqtSignal()
    showSignal = pyqtSignal()

    is_minimize = pyqtSignal()
    is_normal = pyqtSignal()

    stop_scan_signal = pyqtSignal()
    start_scan_signal = pyqtSignal()
    stop_index_signal = pyqtSignal(str)
    start_index_signal = pyqtSignal(str)
    cycle_start_signal = pyqtSignal()

    save_scan_signal = pyqtSignal()
    load_scan_signal = pyqtSignal(bool)

    load_finished = pyqtSignal(list)
    load_path = pyqtSignal(str)

    download_signal = pyqtSignal(bool,str)
    main_infobar_signal = pyqtSignal(str,str,str,str)

signalBus = SignalBus()