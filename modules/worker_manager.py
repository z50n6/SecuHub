import os
import subprocess
import logging
import sys
import time
import json # CacheManager需要
from PyQt6.QtWidgets import QApplication # ToolLauncherWorker需要
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl,QSettings
from PyQt6.QtGui import QIcon, QDesktopServices # IconLoaderWorker和ToolLauncherWorker需要
# for ProcessMonitorWorker
try:
    import psutil
except ImportError:
    psutil = None
    logging.warning("psutil模块未安装，进程监控功能将受限。请运行 'pip install psutil' 安装。")

from modules.config_manager import Config # ConfigSaverWorker和ToolLauncherWorker需要


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
class SearchWorker(QObject):
    """在工作线程中执行搜索"""
    resultsReady = pyqtSignal(list)

    @pyqtSlot(list, str)
    def search(self, tools, text):
        """搜索工具"""
        if not text:
            self.resultsReady.emit(tools)
            return

        text = text.lower().strip()
        results = []
        
        for tool_data in tools:
            # 获取搜索字段
            name = tool_data.get('name', '').lower()
            description = tool_data.get('description', '').lower()
            category = tool_data.get('category', '').lower()
            subcategory = tool_data.get('subcategory', '').lower()
            tool_type = tool_data.get('tool_type', '').lower()
            
            # 计算匹配分数
            score = 0
            
            # 名称匹配（最高权重）
            if text in name:
                score += 100
                if name.startswith(text):
                    score += 50  # 开头匹配额外加分
                if name == text:
                    score += 100  # 完全匹配额外加分
            
            # 描述匹配
            if text in description:
                score += 30
            
            # 分类匹配
            if text in category:
                score += 20
            
            # 子分类匹配
            if text in subcategory:
                score += 15
            
            # 工具类型匹配
            if text in tool_type:
                score += 10
            
            # 如果任何字段匹配，添加到结果
            if score > 0:
                # 添加分数到工具数据中用于排序
                tool_data_with_score = tool_data.copy()
                tool_data_with_score['_search_score'] = score
                results.append(tool_data_with_score)
        
        # 按分数排序，分数高的在前
        results.sort(key=lambda x: x.get('_search_score', 0), reverse=True)
        
        # 移除临时分数字段
        for result in results:
            if '_search_score' in result:
                del result['_search_score']
        
        self.resultsReady.emit(results)

class IconLoaderWorker(QObject):
    """在工作线程中懒加载图标"""
    # 信号发出: 行号, 工具路径 (用于验证), QIcon对象
    iconReady = pyqtSignal(int, str, QIcon)

    @pyqtSlot(int, str, str)
    def load_icon(self, row, tool_path, icon_path):
        """加载图标文件"""
        if icon_path and os.path.exists(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.iconReady.emit(row, tool_path, icon)


class ToolLauncherWorker(QObject):
    """在工作线程中启动工具"""
    toolLaunched = pyqtSignal(str, bool, str)  # 工具名, 成功状态, 错误信息
    installationRequired = pyqtSignal(object, str) # tool, target ('requirements' or module_name)
    
    @pyqtSlot(object, bool)
    def launch_tool(self, tool, dependency_check=True):
        """
        启动工具
        :param tool: 工具对象
        :param dependency_check: 是否进行依赖检查
        """
        try:
            from shutil import which
            import os, sys, subprocess
            # 获取主窗口config
            mainwin = QApplication.activeWindow()
            config = getattr(mainwin, 'config', None)
            # 选择python/java路径
            def get_valid_path(cfg_path, default):
                if cfg_path:
                    if os.path.isabs(cfg_path) and os.path.isfile(cfg_path):
                        return cfg_path
                    elif which(cfg_path):
                        return cfg_path
                return default
            # Windows下隐藏控制台窗口
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW
            # Python依赖检查
            if tool.tool_type == "python" and dependency_check:
                tool_dir = os.path.dirname(tool.path)
                req_file = os.path.join(tool_dir, 'requirements.txt')
                python_path = get_valid_path(config.python_path if config else None, "python")
                if os.path.exists(req_file):
                    self.installationRequired.emit(tool, 'requirements')
                    return
                cmd = [python_path, tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                process = subprocess.run(cmd, cwd=tool_dir, capture_output=True, text=True, encoding='utf-8', errors='replace', creationflags=creationflags)
                if process.returncode != 0:
                    stderr = process.stderr
                    if "ModuleNotFoundError" in stderr:
                        match = re.search(r"ModuleNotFoundError: No module named '([\w\.]+)'", stderr)
                        if match:
                            module_name = match.group(1)
                            self.installationRequired.emit(tool, module_name)
                            return
                    self.toolLaunched.emit(tool.name, False, stderr or process.stdout)
                    return
            # 启动
            if tool.tool_type == "url":
                QDesktopServices.openUrl(QUrl(tool.path))
                self.toolLaunched.emit(tool.name, True, "")
            elif tool.tool_type == "folder":
                QDesktopServices.openUrl(QUrl.fromLocalFile(tool.path))
                self.toolLaunched.emit(tool.name, True, "")
            elif tool.tool_type == "cmd":
                # 用cmd.exe /k 启动命令行工具
                cmd = ["cmd.exe", "/k", tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                tool_dir = os.path.dirname(os.path.abspath(tool.path)) or None
                process = subprocess.Popen(
                    cmd,
                    cwd=tool_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.toolLaunched.emit(tool.name, True, str(process.pid))
                return
            else:
                tool_dir = os.path.dirname(tool.path)
                cmd = []
                if tool.tool_type in ["java8_gui", "java8"]:
                    java8_path = get_valid_path(config.java8_path if config else None, "java")
                    if not java8_path or not self._is_exe_valid(java8_path):
                        self.toolLaunched.emit(tool.name, False, "Java8路径未配置或无效")
                        return
                    if tool.tool_type == "java8_gui":
                        cmd = [java8_path, "-jar", tool.path]
                    else:
                        cmd = [java8_path]
                elif tool.tool_type in ["java11_gui", "java11"]:
                    java11_path = get_valid_path(config.java11_path if config else None, "java")
                    if not java11_path or not self._is_exe_valid(java11_path):
                        self.toolLaunched.emit(tool.name, False, "Java11路径未配置或无效")
                        return
                    if tool.tool_type == "java11_gui":
                        cmd = [java11_path, "-jar", tool.path]
                    else:
                        cmd = [java11_path]
                elif tool.tool_type == "python":
                    python_path = get_valid_path(config.python_path if config else None, "python")
                    if not python_path or not self._is_exe_valid(python_path):
                        self.toolLaunched.emit(tool.name, False, "Python路径未配置或无效")
                        return
                    cmd = [python_path, tool.path]
                elif tool.tool_type == "powershell":
                    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", tool.path]
                elif tool.tool_type == "batch":
                    bat_path = os.path.abspath(tool.path)
                    cmd = ["cmd.exe", "/k", bat_path]
                    if tool.args:
                        cmd.extend(tool.args.split())
                    tool_dir = os.path.dirname(bat_path) or None
                    # 强制新开一个控制台窗口
                    process = subprocess.Popen(
                        cmd,
                        cwd=tool_dir,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                    self.toolLaunched.emit(tool.name, True, str(process.pid))
                    return
                elif tool.tool_type == "vbs":
                    vbs_path = os.path.abspath(tool.path)
                    cmd = ["wscript.exe", vbs_path]
                    if tool.args:
                        cmd.extend(tool.args.split())
                    tool_dir = os.path.dirname(vbs_path) or None
                    process = subprocess.Popen(cmd, cwd=tool_dir)
                    self.toolLaunched.emit(tool.name, True, str(process.pid))
                    return
                else:  # 默认为 exe
                    cmd = [tool.path]
                if tool.tool_type != "batch" and tool.args:
                    cmd.extend(tool.args.split())
                tool_dir = os.path.dirname(os.path.abspath(tool.path)) or None
                process = subprocess.Popen(cmd, cwd=tool_dir, creationflags=creationflags)
                self.toolLaunched.emit(tool.name, True, str(process.pid))
        except Exception as e:
            self.toolLaunched.emit(tool.name, False, str(e))
    def _is_exe_valid(self, path):
        import os
        if not path:
            return False
        if os.path.isabs(path):
            return os.path.isfile(path)
        from shutil import which
        return which(path) is not None
class ProcessMonitorWorker(QObject):
    """监控已启动的进程"""
    processStatusChanged = pyqtSignal(str, str, bool)  # 工具名, 进程ID, 是否运行
    
    def __init__(self):
        super().__init__()
        self.monitored_processes = {}  # {tool_name: pid}
        self.running = True
    
    @pyqtSlot()
    def start_monitoring(self):
        """开始监控进程"""
        while self.running:
            try:
                for tool_name, pid in list(self.monitored_processes.items()):
                    try:
                        # 检查进程是否还在运行
                        process = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                               capture_output=True, text=True)
                        is_running = str(pid) in process.stdout
                        self.processStatusChanged.emit(tool_name, str(pid), is_running)
                        
                        if not is_running:
                            # 进程已结束，从监控列表中移除
                            del self.monitored_processes[tool_name]
                    except:
                        # 进程可能已经结束
                        del self.monitored_processes[tool_name]
                
                time.sleep(2)  # 每2秒检查一次
            except:
                break
    
    def add_process(self, tool_name, pid):
        """添加进程到监控列表"""
        self.monitored_processes[tool_name] = pid
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False

class ConfigSaverWorker(QObject):
    """在工作线程中保存配置"""
    configSaved = pyqtSignal(bool, str)  # 成功状态, 错误信息
    
    @pyqtSlot(dict)
    def save_config(self, config_data):
        """保存配置"""
        try:
            # 保存到QSettings
            settings = QSettings("SecuHub", "SecuHub")
            for key, value in config_data.items():
                settings.setValue(key, value)
            settings.sync()
            
            # 保存到JSON文件
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.configSaved.emit(True, "")
        except Exception as e:
            self.configSaved.emit(False, str(e))


class CacheManager:
    """缓存管理器"""
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get(self, key):
        """获取缓存项"""
        if key in self.cache:
            # 更新访问顺序
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key, value):
        """设置缓存项"""
        if key in self.cache:
            # 更新现有项
            self.cache[key] = value
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # 添加新项
            if len(self.cache) >= self.max_size:
                # 移除最久未访问的项
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
            
            self.cache[key] = value
            self.access_order.append(key)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()

class ClipboardBridge(QObject):
    """提供给JS调用的剪贴板桥接"""
    @pyqtSlot(str)
    def copy(self, text):
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            logging.info(f"通过桥接复制到剪贴板: {text[:50]}...")
