import os
import subprocess
import logging
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

class PipInstallerWorker(QObject):
    """在工作线程中安装Python包"""
    installationStarted = pyqtSignal(str)  # tool_name
    installationProgress = pyqtSignal(str, str)  # tool_name, message
    installationFinished = pyqtSignal(str, bool, str, object)  # tool_name, success, error_msg, tool_object
    def __init__(self):
        super().__init__()
        self._running = True

    def stop(self):
        self._running = False
    @pyqtSlot(object, str)
    def install(self, tool, target):
        """
        安装依赖
        :param tool: 工具对象
        :param target: 'requirements' 或模块名
        """
        if not self._running:
            return
        self.installationStarted.emit(tool.name)
        tool_dir = os.path.dirname(tool.path)
        
        try:
            if target == 'requirements':
                req_file = os.path.join(tool_dir, 'requirements.txt')
                cmd = ["python", "-m", "pip", "install", "--upgrade", "pip"]
                
                # 首先升级pip
                self.installationProgress.emit(tool.name, "正在检查并升级pip...")
                upgrade_process = subprocess.run(cmd, cwd=tool_dir, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if upgrade_process.returncode == 0:
                    self.installationProgress.emit(tool.name, "pip已是最新版本或升级成功。")
                else:
                    self.installationProgress.emit(tool.name, f"pip升级失败，继续尝试安装依赖...")

                # 然后安装requirements
                cmd = ["python", "-m", "pip", "install", "-r", req_file]
                self.installationProgress.emit(tool.name, f"正在从 requirements.txt 安装依赖...")
            else:
                cmd = ["python", "-m", "pip", "install", target]
                self.installationProgress.emit(tool.name, f"正在安装模块: {target}...")

            process = subprocess.Popen(
                cmd,
                cwd=tool_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            for line in iter(process.stdout.readline, ''):
                self.installationProgress.emit(tool.name, line.strip())
            
            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                self.installationProgress.emit(tool.name, "依赖安装成功!")
                self.installationFinished.emit(tool.name, True, "", tool)
            else:
                error_msg = f"Pip 安装失败，返回码: {return_code}"
                self.installationProgress.emit(tool.name, error_msg)
                self.installationFinished.emit(tool.name, False, error_msg, tool)

        except Exception as e:
            error_msg = f"安装过程中发生错误: {e}"
            self.installationProgress.emit(tool.name, error_msg)
            self.installationFinished.emit(tool.name, False, error_msg, tool)

class Tool:
    """工具类"""
    def __init__(self, name, path, category, subcategory="", tool_type="exe",
                 description="", icon_path=None, color="#000000", launch_count=0, args=""):
        self.name = name
        self.path = path
        self.category = category
        self.subcategory = subcategory
        self.tool_type = tool_type
        self.description = description
        self.icon_path = icon_path
        self.color = color
        self.launch_count = launch_count
        self.last_launch = None
        self.args = args  # 新增启动参数字段
    
    def to_dict(self):
        """转换为字典"""
        return {
            "name": self.name,
            "path": self.path,
            "category": self.category,
            "subcategory": self.subcategory,
            "tool_type": self.tool_type,
            "description": self.description,
            "icon_path": self.icon_path,
            "color": self.color,
            "launch_count": self.launch_count,
            "last_launch": self.last_launch,
            "args": self.args  # 新增启动参数字段
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建Tool对象"""
        tool = cls(
            data.get("name", ""),
            data.get("path", ""),
            data.get("category", ""),
            data.get("subcategory", ""),
            data.get("tool_type", "exe"),
            data.get("description", ""),
            data.get("icon_path"),
            data.get("color", "#000000"),
            data.get("launch_count", 0),
            data.get("args", "")
        )
        tool.last_launch = data.get("last_launch")
        return tool
