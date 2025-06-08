# coding:utf-8
import sys
from enum import Enum
from PyQt5.QtCore import QLocale
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, Theme, FolderValidator, ConfigSerializer, ConfigValidator)

class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO

def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    """ 应用设置config """

    # folders
    scriptFolders = ConfigItem(
        "Folders", "LocalScript", [], FolderListValidator())
    downloadFolder = ConfigItem(
        "Folders", "Download", "app/download", FolderValidator())


    #script
    defaultTab =  OptionsConfigItem(
        "Scripts", "defaultTab", "Empty" , OptionsValidator(["Custom", "Empty"]), restart=True)

    defaultAdd =  OptionsConfigItem(
        "Scripts", "defaultAdd", "Empty" , OptionsValidator(["Custom", "Empty"]))

    keybind =  OptionsConfigItem(
        "Scripts", "keybind", "default" , OptionsValidator(["Custom", "default"]), restart=True)

    closeEnabled = ConfigItem("Scripts", "CloseEnabled", False, BoolValidator())

    offset = OptionsConfigItem(
        "Scripts", "Offset", "None" , OptionsValidator(["None", 5, 10, 15, 20]))

    photoMethod =  OptionsConfigItem(
        "Scripts", "photomethod", "template" , OptionsValidator(["template", "feature"]))

    Base64Method =  ConfigItem("Scripts", "Base64Method", False, BoolValidator())


    logMethod = OptionsConfigItem("Scripts", "logMethod","no_repeat", OptionsValidator(["stop","all", "no_repeat"]))





    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.CHINESE_SIMPLIFIED , OptionsValidator(Language), LanguageSerializer(), restart=True)



    # software update
    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())

    update_prerelease_enable = ConfigItem("Update", "updatePrereleaseEnable", False , BoolValidator())

    useragent = {"User-Agent": "MyApp/1.0 (Windows; x86_64; Python)"}



YEAR = 2025
AUTHOR = "Mrman"
VERSION = "v1.0.1"
HELP_URL = "https://github.com/mrmanforgithub/Easy_ScriptRunner/blob/master/README.md"
REPO_URL = "https://github.com/mrmanforgithub/Easy_ScriptRunner"
FEEDBACK_URL = "https://github.com/mrmanforgithub/Easy_ScriptRunner/issues"
RELEASE_URL = "https://api.github.com/repos/mrmanforgithub/Easy_ScriptRunner/releases/latest"
TAB_PATH = "app/config/default_tab.json"
ADD_PATH = "app/config/default_add.json"
KEY_PATH = "app/config/hotkey.json"
RECENT_PATH = "app/config/recently_open.json"


cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load('app/config/config.json', cfg)