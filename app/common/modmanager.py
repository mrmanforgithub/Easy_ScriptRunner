import importlib.util
from pathlib import Path
import re

from .recognizer_registry import RECOGNIZER_REGISTRY
from .operation_registry import OPERATION_REGISTRY
from .photo_tool import photo_tool
from .signal_bus import signalBus


class ModManager:
    def __init__(self, mod_folder: str = "app/mod"):
        self.mod_folder = Path(mod_folder)
        self.mod_folder.mkdir(exist_ok=True)
        self.mod_types = {
            "recognizer": self._handle_recognizer,
            "operation": self._handle_operation
        }



    def load_mods(self):
        """加载所有 Mod 文件"""
        for py_file in self.mod_folder.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                mod_type = self._detect_mod_type(py_file)
                if mod_type in self.mod_types:
                    self._load_module(py_file, mod_type)
            except Exception as e:
                photo_tool.error_print(f"Failed to process mod {py_file.name}: {str(e)}")


    def _detect_mod_type(self, filepath: Path) -> str:
        """检测文件头部的类型标注"""
        with open(filepath, 'r', encoding='utf-8') as f:
            first_lines = [f.readline() for _ in range(3)]  # 读取前3行

        for line in first_lines:
            if match := re.search(r"#\s*MOD_TYPE:\s*(\w+)", line):
                return match.group(1).lower()
        return ""



    def _load_module(self, filepath: Path, mod_type: str):
        mod_name = filepath.stem
        spec = importlib.util.spec_from_file_location(mod_name, filepath)
        module = importlib.util.module_from_spec(spec)

        # 保存原始注册表状态以便回滚
        original_registry = RECOGNIZER_REGISTRY.copy()
        original_operation = OPERATION_REGISTRY.copy()

        try:
            handler = self.mod_types.get(mod_type)
            if handler:
                handler(module, mod_name)
                spec.loader.exec_module(module)

        except Exception as e:
            # 回滚注册表
            RECOGNIZER_REGISTRY.clear()
            RECOGNIZER_REGISTRY.update(original_registry)

            OPERATION_REGISTRY.clear()
            OPERATION_REGISTRY.update(original_operation)

            photo_tool.error_print(f"Failed to load mod {mod_name}: {str(e)}")


    def _handle_recognizer(self, module, mod_name):
        """处理识别器类型的Mod"""
        pass

    def _handle_operation(self, module, mod_name):
        """处理操作类型的Mod"""
        pass