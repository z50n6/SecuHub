import sys
import os
import json
import subprocess
import time
import logging
from datetime import datetime
from functools import partial
import re
from PyQt6.QtWidgets import ( 
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QPushButton, QLineEdit,
    QComboBox, QTextEdit, QFileDialog, QMessageBox, QDialog,
    QFormLayout, QMenu, QMenuBar, QSplitter, QStackedWidget,
    QInputDialog, QScrollArea, QGroupBox, QProgressBar,
    QStatusBar, QSizePolicy, QStyle, QTableWidget, QTableWidgetItem, QHeaderView,
    QListWidget, QListWidgetItem, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal, QSize, QPoint, QSettings, QObject, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap, QAction, QKeySequence, QDesktopServices
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebChannel import QWebChannel


# Add new imports for icon extraction
try:
    import win32gui
    import win32api
    import win32con
    from PIL import Image
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False
    logging.warning("pywin32或Pillow库未安装，无法使用EXE图标提取功能。")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# 日志初始化
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"run_{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# ========== 主题管理器 ==========
class ThemeManager:
    """主题管理器，自动发现和管理主题"""
    
    def __init__(self):
        self.themes_dir = os.path.join(os.path.dirname(__file__), 'themes')
        self.available_themes = self._discover_themes()
    
    def _discover_themes(self):
        """自动发现可用主题"""
        themes = {}
        if os.path.exists(self.themes_dir):
            for file in os.listdir(self.themes_dir):
                if file.endswith('.qss') and not file.startswith('scrollbar_'):
                    theme_name = file[:-4]  # 移除 .qss 扩展名
                    themes[theme_name] = os.path.join(self.themes_dir, file)
        return themes
    
    def get_theme_names(self):
        """获取所有可用主题名称"""
        return list(self.available_themes.keys())
    
    def load_theme(self, theme_name):
        """加载指定主题的QSS内容"""
        theme_file = self.available_themes.get(theme_name)
        if theme_file and os.path.exists(theme_file):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logging.error(f"加载主题 {theme_name} 失败: {e}")
                return ""
        return ""
    
    def load_scrollbar(self, theme_name):
        """加载指定主题的滚动条样式"""
        if theme_name == 'cyberpunk':
            scrollbar_file = os.path.join(self.themes_dir, 'scrollbar_cyberpunk.qss')
        else:
            scrollbar_file = os.path.join(self.themes_dir, 'scrollbar_default.qss')
        
        if os.path.exists(scrollbar_file):
            try:
                with open(scrollbar_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logging.error(f"加载滚动条样式失败: {e}")
                return ""
        return ""
    
    def get_theme_display_name(self, theme_name):
        """获取主题的显示名称"""
        display_names = {
            'modern_light': '🌞 现代浅色',
            'modern_dark': '🌙 现代深色',
            'tranquil_green': '🌿 静谧绿',
            'deep_ocean': '🌊 深海蓝',
            'cyberpunk': '🤖 科技风',
            'sunset_orange': '🌅 日落橙',
            'midnight_purple': '🌌 午夜紫',
            'forest_green': '🌲 森林绿',
            'ice_blue': '❄️ 冰蓝'
        }
        return display_names.get(theme_name, theme_name)

# ========== 全局唯一美化弹窗 ConfirmDialog ==========
class ConfirmDialog(QDialog):
    def __init__(self, parent=None, title="提示", content="操作成功", icon="ℹ️", yes_text="确定", no_text=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumWidth(400)
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: transparent;")
        # 极简卡片容器
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("""
            QWidget {
                background: #fff;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        main_layout.addWidget(container)
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(32, 32, 32, 32)
        vbox.setSpacing(18)
        # 图标
        icon_label = QLabel(icon)
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 26px;")
        vbox.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        # 主标题（直接用title参数，无横条）
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c48f; margin-top: 2px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title_label)
        # 内容（极简分行高亮）
        content_label = QLabel()
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_label.setStyleSheet("font-size: 15px; color: #222; margin-top: 10px; margin-bottom: 10px;")
        if "未配置:" in content:
            parts = content.split("未配置:")
            main_tip = f'<div style="font-size:15px;font-weight:bold;margin-bottom:8px;">{parts[0].strip()}</div>'
            if len(parts) > 1:
                items = [x.strip() for x in parts[1].replace("，", ",").split(",") if x.strip()]
                item_html = "<br>".join([f'<span style="color:#00c48f;font-weight:bold;">{item}</span>' for item in items])
                content_label.setText(main_tip + '<div style="margin-top:8px;">未配置：<br>' + item_html + '</div>')
            else:
                content_label.setText(main_tip)
        else:
            content_label.setText(content)
        vbox.addWidget(content_label)
        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        yes_btn = QPushButton(yes_text)
        yes_btn.setFixedHeight(38)
        yes_btn.setMinimumWidth(100)
        yes_btn.setStyleSheet("""
            QPushButton {
                background: #00c48f;
                color: white; font-size: 15px; font-weight: bold;
                border-radius: 19px; border: none;
            }
            QPushButton:hover {
                background: #00b07d;
            }
        """)
        yes_btn.clicked.connect(self.accept)
        btn_layout.addWidget(yes_btn)
        if no_text:
            no_btn = QPushButton(no_text)
            no_btn.setFixedHeight(38)
            no_btn.setMinimumWidth(100)
            no_btn.setStyleSheet("""
                QPushButton {
                    background: #f5f5f5; color: #888; font-size: 15px;
                    border-radius: 19px; border: none;
                }
                QPushButton:hover {
                    background: #e0e0e0; color: #222;
                }
            """)
            no_btn.clicked.connect(self.reject)
            btn_layout.addSpacing(14)
            btn_layout.addWidget(no_btn)
        btn_layout.addStretch(1)
        vbox.addSpacing(8)
        vbox.addLayout(btn_layout)

class Config:
    """配置管理类"""
    def __init__(self):
        logging.info("初始化配置...")
        self.settings = QSettings("SecuHub", "SecuHub")
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        self.theme_list = ["modern_light", "modern_dark"]
        # 新增环境变量字段
        self.python_path = ""
        self.java8_path = ""
        self.java11_path = ""
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        logging.info("加载配置...")
        # 定义默认导航项
        default_nav_items = [
            {"id": "safe", "name": "安全工具", "icon": "🛡️"},
            {"id": "code", "name": "编码与解码", "icon": "🔧"},
            {"id": "assist", "name": "辅助工具", "icon": "🛠️"}
        ]
        # 首先尝试从JSON文件加载
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tools = data.get("tools", [])
                    self.theme = data.get("theme", "modern_light")
                    self.view_mode = data.get("view_mode", "list")
                    self.recent_tools = data.get("recent_tools", [])
                    self.show_status_bar = data.get("show_status_bar", True)
                    self.auto_refresh = data.get("auto_refresh", True)
                    self.search_history = data.get("search_history", [])
                    self.navigation_items = data.get("navigation_items", default_nav_items)
                    # 新增环境变量字段
                    self.python_path = data.get("python_path", "")
                    self.java8_path = data.get("java8_path", "")
                    self.java11_path = data.get("java11_path", "")
            except Exception as e:
                logging.error(f"从JSON文件加载配置失败: {e}")
                # 如果JSON加载失败，从QSettings加载
                self._load_from_settings()
        else:
            # 如果JSON文件不存在，从QSettings加载
            self._load_from_settings()
        
        logging.info(f"配置加载完成: {len(self.navigation_items)}个导航项, {len(self.tools)}个工具")
    
    def _load_from_settings(self):
        """从QSettings加载配置"""
        default_nav_items = [
            {"id": "safe", "name": "安全工具", "icon": "🛡️"},
            {"id": "code", "name": "编码与解码", "icon": "🔧"},
            {"id": "assist", "name": "辅助工具", "icon": "🛠️"}
        ]
        self.tools = self.settings.value("tools", [])
        self.theme = self.settings.value("theme", "modern_light")
        self.view_mode = self.settings.value("view_mode", "list")
        self.recent_tools = self.settings.value("recent_tools", [])
        self.show_status_bar = self.settings.value("show_status_bar", True)
        self.auto_refresh = self.settings.value("auto_refresh", True)
        self.search_history = self.settings.value("search_history", [])
        self.navigation_items = self.settings.value("navigation_items", default_nav_items)
        # 新增环境变量字段
        self.python_path = self.settings.value("python_path", "")
        self.java8_path = self.settings.value("java8_path", "")
        self.java11_path = self.settings.value("java11_path", "")
    
    def save_config(self):
        """保存配置"""
        logging.info("保存配置...")
        # 保存到QSettings
        self.settings.setValue("tools", self.tools)
        self.settings.setValue("theme", self.theme)
        self.settings.setValue("view_mode", self.view_mode)
        self.settings.setValue("recent_tools", self.recent_tools)
        self.settings.setValue("show_status_bar", self.show_status_bar)
        self.settings.setValue("auto_refresh", self.auto_refresh)
        self.settings.setValue("search_history", self.search_history)
        self.settings.setValue("navigation_items", self.navigation_items)
        self.settings.setValue("python_path", self.python_path)
        self.settings.setValue("java8_path", self.java8_path)
        self.settings.setValue("java11_path", self.java11_path)
        self.settings.sync()

        # 自动备份
        if os.path.exists(self.config_file):
            import shutil
            shutil.copyfile(self.config_file, self.config_file + ".bak")

        # 合并写入，防止丢字段
        try:
            data = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            # 更新字段
            data.update({
                "tools": self.tools,
                "theme": self.theme,
                "view_mode": self.view_mode,
                "recent_tools": self.recent_tools,
                "show_status_bar": self.show_status_bar,
                "auto_refresh": self.auto_refresh,
                "search_history": self.search_history,
                "navigation_items": self.navigation_items,
                "python_path": self.python_path,
                "java8_path": self.java8_path,
                "java11_path": self.java11_path
            })
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存到JSON文件失败: {e}")
    
    def add_to_recent(self, tool_name):
        """添加到最近使用"""
        if tool_name in self.recent_tools:
            self.recent_tools.remove(tool_name)
        self.recent_tools.insert(0, tool_name)
        # 只保留最近20个
        self.recent_tools = self.recent_tools[:20]
        self.save_config()
    
    def add_to_favorites(self, tool_name):
        """添加到收藏"""
        if tool_name not in self.favorites:
            self.favorites.append(tool_name)
            self.save_config()
    
    def remove_from_favorites(self, tool_name):
        """从收藏中移除"""
        if tool_name in self.favorites:
            self.favorites.remove(tool_name)
        self.save_config()
    
    def add_search_history(self, search_text):
        """添加搜索历史"""
        if search_text in self.search_history:
            self.search_history.remove(search_text)
        self.search_history.insert(0, search_text)
        # 只保留最近10个
        self.search_history = self.search_history[:10]
        self.save_config()

logging.info("定义配置类完成...")

class PipInstallerWorker(QObject):
    """在工作线程中安装Python包"""
    installationStarted = pyqtSignal(str)  # tool_name
    installationProgress = pyqtSignal(str, str)  # tool_name, message
    installationFinished = pyqtSignal(str, bool, str, object)  # tool_name, success, error_msg, tool_object

    @pyqtSlot(object, str)
    def install(self, tool, target):
        """
        安装依赖
        :param tool: 工具对象
        :param target: 'requirements' 或模块名
        """
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
        """从字典创建工具"""
        # 兼容旧版本的sub_category字段
        subcategory = data.get("subcategory", data.get("sub_category", ""))
        
        return cls(
            data["name"],
            data["path"],
            data["category"],
            subcategory,
            data.get("tool_type", "exe"),
            data.get("description", ""),
            data.get("icon_path"),
            data.get("color", "#000000"),
            data.get("launch_count", 0),
            data.get("args", "")  # 新增启动参数字段
        )

logging.info("定义工具类完成...")

def extract_icon_from_exe(exe_path, save_dir):
    """
    从 .exe 或 .dll 文件中提取最佳质量的图标并保存为.png文件 (更健壮的版本)
    :param exe_path: 文件路径
    :param save_dir: 图标保存目录
    :return: 保存的png文件路径, 或在失败时返回None
    """
    if not IS_WINDOWS or not os.path.exists(exe_path):
        return None

    os.makedirs(save_dir, exist_ok=True)
    
    # 1. 提取所有图标句柄
    large_icons, small_icons = [], []
    try:
        icon_count = win32gui.ExtractIconEx(exe_path, -1)
        if icon_count > 0:
            large_icons, small_icons = win32gui.ExtractIconEx(exe_path, 0, icon_count)
    except Exception as e:
        logging.warning(f"ExtractIconEx 提取 '{os.path.basename(exe_path)}' 图标计数失败: {e}。尝试提取第一个图标。")
    
    # 如果标准方法失败或没有图标，尝试仅提取第一个作为备用方案
    if not large_icons and not small_icons:
        try:
            large_icons, small_icons = win32gui.ExtractIconEx(exe_path, 0, 1)
        except Exception as e:
            logging.error(f"无法从 '{os.path.basename(exe_path)}' 提取任何图标: {e}")
            return None
    
    all_hicons = large_icons + small_icons
    if not all_hicons:
        logging.warning(f"无法从 {exe_path} 中找到任何图标。")
        return None

    # 将所有句柄放入一个我们将保证清理的列表中
    hicons_to_destroy = list(all_hicons)
    saved_path = None

    try:
        # 2. 遍历所有句柄，收集有效图标信息
        icons_info = []
        for hicon in all_hicons:
            info = hbmMask = hbmColor = None
            try:
                info = win32gui.GetIconInfo(hicon)
                fIcon, _, _, hbmMask, hbmColor = info
                # 我们只处理彩色的图标以简化保存逻辑
                if fIcon and hbmColor:
                    bmp = win32api.GetObject(hbmColor)
                    icons_info.append({
                        'hicon': hicon, 'width': bmp.bmWidth, 'bpp': bmp.bmBitsPixel
                    })
            except Exception as e:
                logging.debug(f"处理来自 {exe_path} 的一个图标句柄时出错: {e}")
            finally:
                # 无论成功与否，都释放GetIconInfo创建的位图资源
                if hbmMask: win32gui.DeleteObject(hbmMask)
                if hbmColor: win32gui.DeleteObject(hbmColor)
        
        if not icons_info:
            logging.warning(f"未能从 {exe_path} 成功提取任何可用的彩色图标信息。")
            return None

        # 3. 选择最佳图标（尺寸最大，其次色深最高）
        icons_info.sort(key=lambda x: (x['width'], x['bpp']), reverse=True)
        best_hicon = icons_info[0]['hicon']

        # 4. 保存最佳图标
        info = hbmMask = hbmColor = None
        try:
            info = win32gui.GetIconInfo(best_hicon)
            _, _, _, hbmMask, hbmColor = info
            bmp = win32api.GetObject(hbmColor)

            if bmp.bmBits is None:
                raise ValueError("位图数据为空")

            img = Image.frombuffer("RGBA", (bmp.bmWidth, bmp.bmHeight), bmp.bmBits, "raw", "BGRA", 0, 1)
            
            # 简单的Alpha通道处理：如果图标不是32bpp（即没有内嵌alpha），则尝试从掩码创建
            if bmp.bmBitsPixel != 32:
                mask_bmp = win32api.GetObject(hbmMask)
                if mask_bmp.bmBitsPixel == 1:
                    mask = Image.frombuffer("L", (bmp.bmWidth, bmp.bmHeight), mask_bmp.bmBits, "raw", "L", 0, 1)
                    img.putalpha(mask)

            exe_name = os.path.splitext(os.path.basename(exe_path))[0]
            save_path = os.path.join(save_dir, f"{exe_name}_icon.png")
            img.save(save_path, "PNG")
            logging.info(f"成功提取图标并保存到: {save_path}")
            saved_path = save_path
        
        except Exception as e:
            logging.error(f"保存图标时出错: {e}")
            # 保存失败，返回None，finally块会负责清理
            return None
        
        finally:
            # 释放为保存图标而创建的位图资源
            if hbmMask: win32gui.DeleteObject(hbmMask)
            if hbmColor: win32gui.DeleteObject(hbmColor)

    finally:
        # 5. 确保销毁所有提取出的图标句柄
        for hicon in hicons_to_destroy:
            try: win32gui.DestroyIcon(hicon)
            except Exception: pass
            
    return saved_path

class CyberChefDialog(QDialog):
    """CyberChef 对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CyberChef 编解码")
        self.setMinimumSize(1000, 700)
        layout = QVBoxLayout(self)
        
        # 创建工具栏
        toolbar = QHBoxLayout()
        self.copy_btn = QPushButton("复制结果")
        self.clear_btn = QPushButton("清空")
        toolbar.addWidget(self.copy_btn)
        toolbar.addWidget(self.clear_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 创建 WebView
        self.webview = QWebEngineView(self)
        # 优化本地路径引用
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cyberchef_index = os.path.join(current_dir, "project", "CyberChef", "index.html")
        if os.path.exists(cyberchef_index):
            url = QUrl.fromLocalFile(cyberchef_index)
            self.webview.setUrl(url)
        else:
            self.webview.setUrl(QUrl("https://btsrk.me/"))
        layout.addWidget(self.webview)
        
        # 连接信号
        self.copy_btn.clicked.connect(self.copy_result)
        self.clear_btn.clicked.connect(self.clear_result)
    
    def copy_result(self):
        """复制结果"""
        self.webview.page().runJavaScript(
            "document.getElementById('output-text').value",
            self.handle_copy_result
        )
    
    def handle_copy_result(self, result):
        """处理复制结果"""
        if result:
            QApplication.clipboard().setText(result)
            QMessageBox.information(self, "提示", "已复制到剪贴板")
    
    def clear_result(self):
        """清空结果"""
        self.webview.page().runJavaScript(
            "document.getElementById('input-text').value = '';"
            "document.getElementById('output-text').value = '';"
        )

class AddToolDialog(QDialog):
    """添加工具对话框"""
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("添加/编辑工具")
        self.setMinimumWidth(600)
        self.categories = categories
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: transparent;")
        
        # Container with shadow
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("""
            QWidget {
                background: #fdfdfe;
                border-radius: 12px;
            }
        """)
        main_layout.addWidget(container)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 20)
        container_layout.setSpacing(0)
        
        # --- Custom Title Bar ---
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        
        title_text = QLabel("添加/编辑工具")
        title_text.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()

        # Draggability
        self.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.offset = event.globalPosition().toPoint() - self.pos()
        def mouseMoveEvent(event):
            if self.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self.offset)
        def mouseReleaseEvent(event):
            self.offset = None
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent
        
        container_layout.addWidget(title_bar)
        
        # --- Form Layout ---
        form_layout = QFormLayout()
        form_layout.setContentsMargins(25, 20, 25, 20)
        form_layout.setSpacing(18)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # --- Widgets ---
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.path_edit = QLineEdit()
        self.path_btn = QPushButton("📂")
        self.icon_edit = QLineEdit()
        self.icon_btn = QPushButton("🖼️")
        self.extract_icon_btn = QPushButton("✨ 提取") # 新增提取按钮
        self.category_combo = QComboBox()
        self.args_edit = QLineEdit()
        self.desc_edit = QTextEdit()
        
        # --- Styling ---
        common_style = """
            QLineEdit, QTextEdit, QComboBox {
                background: #f1f3f5;
                color: #212529;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #764ba2;
                background: #fdfdfe;
            }
            QLabel {
                color: #495057;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton {
                background: #e9ecef;
                color: #495057;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #dee2e6;
            }
            QPushButton:hover { background: #dee2e6; }
        """
        self.setStyleSheet(self.styleSheet() + common_style)

        # Tool Name
        self.name_edit.setPlaceholderText("例如: MyCoolTool")
        form_layout.addRow("工具名称:", self.name_edit)
        
        # Tool Type
        self.type_combo.addItems(["GUI应用", "命令行", "java8图形化", "java11图形化", "java8", "java11", "python", "powershell", "批处理", "VBS脚本", "网页", "文件夹"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form_layout.addRow("工具类型:", self.type_combo)
        
        # Tool Path
        path_layout = QHBoxLayout()
        self.path_edit.setPlaceholderText("选择工具路径或输入URL")
        self.path_btn.setFixedSize(40, 40)
        self.path_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.path_btn.setToolTip("浏览文件或文件夹")
        self.path_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.path_btn)
        form_layout.addRow("工具路径:", path_layout)
        
        # Icon Path
        icon_layout = QHBoxLayout()
        self.icon_edit.setPlaceholderText("可选: 选择一个漂亮的图标")
        self.icon_btn.setFixedSize(40, 40)
        self.icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_btn.setToolTip("选择图标文件")
        self.icon_btn.clicked.connect(self.browse_icon)
        
        self.extract_icon_btn.setFixedSize(80, 40)
        self.extract_icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.extract_icon_btn.setToolTip("从上方填写的EXE/DLL路径中提取图标")
        self.extract_icon_btn.clicked.connect(self.extract_icon)
        if not IS_WINDOWS:
            self.extract_icon_btn.setEnabled(False)
            self.extract_icon_btn.setToolTip("该功能仅支持Windows系统")

        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(self.icon_btn)
        icon_layout.addWidget(self.extract_icon_btn)
        form_layout.addRow("图标路径:", icon_layout)
        
        # Category
        self.category_combo.addItems(categories)
        self.category_combo.setEditable(True)
        form_layout.addRow("工具分类:", self.category_combo)
        
        # Arguments
        self.args_edit.setPlaceholderText("可选: 输入启动参数")
        form_layout.addRow("启动参数:", self.args_edit)
        
        # Description
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("可选: 简单的描述一下这个工具")
        form_layout.addRow("工具描述:", self.desc_edit)
        
        container_layout.addLayout(form_layout)
        
        # --- Buttons ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 25, 0)
        buttons_layout.addStretch()

        self.ok_button = QPushButton("✔️ 确定")
        self.cancel_button = QPushButton("❌ 取消")

        self.ok_button.setFixedSize(120, 40)
        self.cancel_button.setFixedSize(120, 40)
        
        self.ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        self.ok_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                color: white; border-radius: 20px; font-size: 14px; font-weight: bold; border: none;
            }
             QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38f9d7, stop:1 #43e97b); }
        """)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background: #e9ecef; color: #495057; border-radius: 20px; font-size: 14px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: #dee2e6; }
        """)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.ok_button)
        container_layout.addLayout(buttons_layout)

    def on_type_changed(self, type_text):
        """工具类型改变时的处理"""
        if type_text == "网页":
            self.path_edit.setText("http://")
            self.path_btn.setEnabled(False)
            self.args_edit.setEnabled(False)
        elif type_text == "文件夹":
            self.path_edit.setText("")
            self.path_btn.setEnabled(True)
            self.args_edit.setEnabled(False)
        else:
            self.path_btn.setEnabled(True)
            self.args_edit.setEnabled(True)
    
    def browse_path(self):
        """浏览路径"""
        type_text = self.type_combo.currentText()
        
        if type_text == "文件夹":
            path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        elif type_text in ["GUI应用", "命令行", "批处理"]:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择可执行文件", "", 
                "可执行文件 (*.exe *.bat *.cmd);;所有文件 (*)"
            )
        elif type_text in ["java8图形化", "java11图形化", "java8", "java11"]:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择JAR文件", "", 
                "JAR文件 (*.jar);;所有文件 (*)"
            )
        elif type_text == "python":
            path, _ = QFileDialog.getOpenFileName(
                self, "选择Python脚本", "", 
                "Python文件 (*.py);;所有文件 (*)"
            )
        elif type_text == "powershell":
            path, _ = QFileDialog.getOpenFileName(
                self, "选择PowerShell脚本", "", 
                "PowerShell文件 (*.ps1);;所有文件 (*)"
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "", "所有文件 (*)"
            )
        
        if path:
            self.path_edit.setText(path)
    
    def browse_icon(self):
        """浏览图标"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图标", "", 
            "图标文件 (*.ico *.png *.jpg *.jpeg);;所有文件 (*)"
        )
        if path:
            self.icon_edit.setText(path)
    
    def extract_icon(self):
        """从EXE文件中提取图标"""
        exe_path = self.path_edit.text().strip()
        if not exe_path or not exe_path.lower().endswith(('.exe', '.dll')):
            ConfirmDialog(self, title="提示", content='请先在上方"工具路径"中指定一个有效的.exe或.dll文件。', icon="ℹ️").exec()
            return
        
        if not os.path.exists(exe_path):
            ConfirmDialog(self, title="错误", content=f"文件不存在:\n{exe_path}", icon="❌").exec()
            return
            
        # 定义图标保存目录
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imgs', 'extracted_icons')
        
        # 调用辅助函数提取图标
        icon_path = extract_icon_from_exe(exe_path, save_dir)
        
        main_window = self.parent()

        if icon_path:
            self.icon_edit.setText(icon_path)
            if main_window and hasattr(main_window, 'status_label'):
                main_window.status_label.setText(f"✅ 成功从 {os.path.basename(exe_path)} 提取图标")
        else:
            if main_window and hasattr(main_window, 'status_label'):
                main_window.status_label.setText(f"❌ 提取失败: 无法从 {os.path.basename(exe_path)} 中提取图标")

    def get_tool_data(self):
        """获取工具数据"""
        type_mapping = {
            "GUI应用": "exe",
            "命令行": "exe", 
            "java8图形化": "java8_gui",
            "java11图形化": "java11_gui",
            "java8": "java8",
            "java11": "java11",
            "python": "python",
            "powershell": "powershell",
            "批处理": "batch",
            "VBS脚本": "vbs",
            "网页": "url",
            "文件夹": "folder"
        }
        
        return {
            "name": self.name_edit.text().strip(),
            "path": self.path_edit.text().strip(),
            "category": self.category_combo.currentText().strip(),
            "subcategory": "",  # 暂时保留，后续可以通过界面添加
            "tool_type": type_mapping.get(self.type_combo.currentText(), "exe"),
            "description": self.desc_edit.toPlainText().strip(),
            "icon_path": self.icon_edit.text().strip() or None,
            "color": "#000000",
            "launch_count": 0,
            "last_launch": None,
            "args": self.args_edit.text().strip()  # 新增启动参数字段
        }

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

class ToolCard(QWidget):
    """自定义工具卡片（与最近启动工具UI保持一致）"""
    _ICON_MAP = {
        "exe": "⚙️",
        "java8_gui": "☕",
        "java11_gui": "☕",
        "java8": "👨‍💻",
        "java11": "👨‍💻",
        "python": "🐍",
        "powershell": "💻",
        "batch": "📜",
        "url": "🌐",
        "folder": "📁",
        "placeholder": "📂"
    }

    def __init__(self, tool, launch_callback=None, parent=None):
        super().__init__(parent)
        self.tool = tool
        self.launch_callback = launch_callback
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("isCard", True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(80)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setStyleSheet("""
        QWidget[isCard="true"] {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 10px;
        }
        QWidget[isCard="true"]:hover {
            border: 1px solid #43e97b;
            background: #f8f9fa;
        }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # 左侧圆形图标区域
        icon_container = QLabel()
        icon_container.setFixedSize(48, 48)
        icon_container.setStyleSheet("background: #e9ecef; border-radius: 24px;")
        icon_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if tool.icon_path and os.path.exists(tool.icon_path):
            pixmap = QIcon(tool.icon_path).pixmap(32, 32)
            icon_container.setPixmap(pixmap)
        else:
            emoji = self._get_tool_icon(tool)
            icon_container.setText(f"<span style='font-size: 20px;'>{emoji}</span>")
        
        layout.addWidget(icon_container)

        # 中间信息区域
        info_container = QWidget()
        info_container.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        
        # 工具名称
        name_label = QLabel(tool.name)
        name_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #212529; background: transparent;")
        info_layout.addWidget(name_label)
        
        # 工具描述和统计信息
        desc_text = f"类型: {tool.tool_type}"
        if tool.description:
            desc_text += f" | {tool.description[:30]}{'...' if len(tool.description) > 30 else ''}"
        desc_text += f" | 启动: {tool.launch_count} 次"
        
        desc_label = QLabel(desc_text)
        desc_label.setStyleSheet("font-size: 11px; color: #6c757d; background: transparent;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        # 分类标签
        if tool.category:
            category_label = QLabel(f"📁 {tool.category}")
            category_label.setStyleSheet("""
                background: #e3f2fd; 
                color: #1976d2; 
                border-radius: 8px; 
                padding: 2px 8px; 
                font-size: 10px; 
                font-weight: bold;
                margin-top: 2px;
            """)
            info_layout.addWidget(category_label)
        
        layout.addWidget(info_container, 1)

        # 右侧启动按钮
        launch_btn = QPushButton("🚀 启动")
        launch_btn.setFixedSize(90, 36)
        launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        launch_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
                color: white; 
                border: none; 
                border-radius: 18px; 
                font-size: 13px; 
                font-weight: bold;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #764ba2, stop:1 #667eea); 
            }
            QPushButton:pressed {
                background: #5a67d8;
            }
        """)
        launch_btn.clicked.connect(lambda: self.launch_tool())
        layout.addWidget(launch_btn)

        # 悬浮提示（详细信息）
        tip = f"""工具名称: {tool.name}
类型: {tool.tool_type}
分类: {tool.category}
描述: {tool.description or '无'}
路径: {tool.path}
启动次数: {tool.launch_count}
最后启动: {tool.last_launch or '从未启动'}"""
        self.setToolTip(tip)

    def _get_tool_icon(self, tool):
        """根据工具类型获取图标"""
        return self._ICON_MAP.get(tool.tool_type, "🚀")

    def launch_tool(self):
        """启动工具"""
        if self.launch_callback:
            self.launch_callback(self.tool)

    def mouseDoubleClickEvent(self, event):
        """双击启动工具"""
        self.launch_tool()

    def show_context_menu(self, position):
        """显示工具卡片的右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 4px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 12px;
                border-radius: 4px;
                color: #495057;
            }
            QMenu::item:selected {
                background: #f8f9fa;
                color: #212529;
            }
            QMenu::separator {
                height: 1px;
                background: #e9ecef;
                margin: 4px 0;
            }
        """)
        
        # 启动工具
        launch_action = QAction("🚀 启动工具", self)
        launch_action.triggered.connect(self.launch_tool)
        menu.addAction(launch_action)
        
        menu.addSeparator()
        
        # 编辑工具
        edit_action = QAction("✏️ 编辑工具", self)
        edit_action.triggered.connect(self.edit_tool)
        menu.addAction(edit_action)
        
        # 打开所在文件夹
        open_folder_action = QAction("📁 打开所在文件夹", self)
        open_folder_action.triggered.connect(self.open_folder)
        menu.addAction(open_folder_action)
        
        # 打开命令行
        open_cmd_action = QAction("💻 打开命令行", self)
        open_cmd_action.triggered.connect(self.open_command_line)
        menu.addAction(open_cmd_action)
        
        menu.addSeparator()
        
        # 复制路径
        copy_path_action = QAction("📋 复制路径", self)
        copy_path_action.triggered.connect(self.copy_path)
        menu.addAction(copy_path_action)
        
        # 复制工具信息
        copy_info_action = QAction("📄 复制工具信息", self)
        copy_info_action.triggered.connect(self.copy_tool_info)
        menu.addAction(copy_info_action)
        
        menu.addSeparator()
        
        # 删除工具
        delete_action = QAction("🗑️ 删除工具", self)
        delete_action.triggered.connect(self.delete_tool)
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec(self.mapToGlobal(position))

    def edit_tool(self):
        """编辑工具"""
        # 获取主窗口实例
        main_window = self.window()
        if hasattr(main_window, 'edit_tool_card'):
            main_window.edit_tool_card(self.tool)

    def open_file_path(self):
        """打开文件路径"""
        if self.tool.tool_type == "url":
            # 如果是URL，直接打开
            QDesktopServices.openUrl(QUrl(self.tool.path))
        elif self.tool.tool_type == "folder":
            # 如果是文件夹，打开文件夹
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.tool.path))
        elif os.path.exists(self.tool.path):
            # 如果是文件，打开文件所在目录并选中文件
            folder = os.path.dirname(self.tool.path)
            if os.path.exists(folder):
                # 使用explorer打开文件夹并选中文件
                subprocess.run(["explorer", "/select,", self.tool.path])
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "路径不存在", f"文件路径不存在:\n{self.tool.path}")

    def open_folder(self):
        """打开所在文件夹"""
        if self.tool.tool_type == "folder":
            folder_path = self.tool.path
        else:
            folder_path = os.path.dirname(self.tool.path)
        
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "路径不存在", f"文件夹路径不存在:\n{folder_path}")

    def open_command_line(self):
        """打开命令行"""
        if self.tool.tool_type == "folder":
            path = self.tool.path
        else:
            path = os.path.dirname(self.tool.path)
            
        if not os.path.isdir(path):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "路径无效", f"无法打开命令行，路径不是一个有效的文件夹:\n{path}")
            return

        # 定义创建标志
        CREATE_NEW_CONSOLE = 0x00000010

        # 按优先级尝试不同的终端
        terminal_options = [
            {"cmd": ["wt.exe", "-d", path], "args": {}, "name": "Windows Terminal"},
            {"cmd": ["pwsh.exe", "-NoExit"], "args": {"cwd": path}, "name": "PowerShell Core"},
            {"cmd": ["powershell.exe", "-NoExit"], "args": {"cwd": path}, "name": "Windows PowerShell"},
            {"cmd": ["cmd.exe"], "args": {"cwd": path}, "name": "Command Prompt"}
        ]

        for option in terminal_options:
            try:
                subprocess.Popen(option["cmd"], creationflags=CREATE_NEW_CONSOLE, **option["args"])
                import logging
                logging.info(f"成功使用 {option['name']} 打开路径: {path}")
                return
            except FileNotFoundError:
                import logging
                logging.info(f"未找到 {option['name']}，尝试下一个...")
            except Exception as e:
                import logging
                logging.warning(f"启动 {option['name']} 失败: {e}，尝试下一个...")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "错误", "无法打开任何终端。请检查您的系统配置。")

    def copy_path(self):
        """复制路径到剪贴板"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.tool.path)
        main_window = self.window()
        if hasattr(main_window, 'status_label'):
            main_window.status_label.setText(f"📋 已复制路径: {self.tool.path}")

    def copy_tool_info(self):
        """复制工具信息到剪贴板"""
        from PyQt6.QtWidgets import QApplication
        info = f"""工具名称: {self.tool.name}
类型: {self.tool.tool_type}
分类: {self.tool.category}
描述: {self.tool.description or '无'}
路径: {self.tool.path}
启动次数: {self.tool.launch_count}
最后启动: {self.tool.last_launch or '从未启动'}"""
        
        clipboard = QApplication.clipboard()
        clipboard.setText(info)
        main_window = self.window()
        if hasattr(main_window, 'status_label'):
            main_window.status_label.setText(f"📋 已复制工具 '{self.tool.name}' 的信息到剪贴板")

    def delete_tool(self):
        """删除工具"""
        dlg = ConfirmDialog(self, title="确认删除", content=f"确定要删除工具 '<span style='color:#43e97b'>{self.tool.name}</span>' 吗？", icon="🗑️", yes_text="是，删除", no_text="取消")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # 获取主窗口实例
            main_window = self.window()
            if hasattr(main_window, 'delete_tool_card'):
                main_window.delete_tool_card(self.tool)

class MainWindow(QMainWindow):
    """主窗口"""
    # 为工作线程添加信号
    startSearch = pyqtSignal(list, str)
    startIconLoad = pyqtSignal(int, str, str)
    startToolLaunch = pyqtSignal(object, bool)
    startPipInstall = pyqtSignal(object, str)
    startConfigSave = pyqtSignal(dict)

    def __init__(self):
        logging.info("初始化主窗口...")
        super().__init__()
        self.config = Config()
        self.cache_manager = CacheManager()
        self.theme_manager = ThemeManager()  # 添加主题管理器
        self._initial_load_done = False
        self.nav_buttons = {}  # 存储导航按钮
        self.init_workers()
        self.init_ui()
        self.load_data()
        logging.info("主窗口初始化完成")
        # 启动时强制modern_light并apply_theme
        self.config.theme = "modern_light"
        self.apply_theme()
        # 启动时检测环境变量
        QTimer.singleShot(100, self.check_env_paths)
    
    def check_env_paths(self):
        """检测环境变量配置和有效性"""
        import os
        missing = []
        if not self.config.python_path:
            missing.append("Python解释器路径")
        if not self.config.java8_path:
            missing.append("Java8路径")
        if not self.config.java11_path:
            missing.append("Java11路径")
        if missing:
            msg = f"⚠️ 请在设置菜单中配置环境变量: {', '.join(missing)}"
            self.statusBar().showMessage(msg, 15000)  # 显示15秒

    def _is_exe_valid(self, path):
        import os
        if not path:
            return False
        if os.path.isabs(path):
            return os.path.isfile(path)
        from shutil import which
        return which(path) is not None

    def showEvent(self, event):
        """在窗口首次显示时加载初始数据，避免布局问题"""
        super().showEvent(event)
        if not self._initial_load_done:
            self._initial_load_done = True
            # 延迟50ms执行，确保布局已经计算完毕
            QTimer.singleShot(50, self.refresh_outline_and_tools)

    def init_workers(self):
        """初始化后台工作线程"""
        # --- 搜索线程 ---
        self.search_thread = QThread()
        self.search_worker = SearchWorker()
        self.search_worker.moveToThread(self.search_thread)
        self.startSearch.connect(self.search_worker.search)
        self.search_worker.resultsReady.connect(self.handle_search_results)
        self.search_thread.start()
        
        # --- 图标加载线程 ---
        self.icon_loader_thread = QThread()
        self.icon_loader_worker = IconLoaderWorker()
        self.icon_loader_worker.moveToThread(self.icon_loader_thread)
        self.startIconLoad.connect(self.icon_loader_worker.load_icon)
        self.icon_loader_worker.iconReady.connect(self.set_tool_icon)
        self.icon_loader_thread.start()
        
        # --- 工具启动线程 ---
        self.tool_launcher_thread = QThread()
        self.tool_launcher_worker = ToolLauncherWorker()
        self.tool_launcher_worker.moveToThread(self.tool_launcher_thread)
        self.startToolLaunch.connect(self.tool_launcher_worker.launch_tool)
        self.tool_launcher_worker.toolLaunched.connect(self.handle_tool_launched)
        self.tool_launcher_worker.installationRequired.connect(self.handle_installation_required)
        self.tool_launcher_thread.start()
        
        # --- Pip安装线程 ---
        self.pip_installer_thread = QThread()
        self.pip_installer_worker = PipInstallerWorker()
        self.pip_installer_worker.moveToThread(self.pip_installer_thread)
        self.startPipInstall.connect(self.pip_installer_worker.install)
        self.pip_installer_worker.installationStarted.connect(self.handle_installation_started)
        self.pip_installer_worker.installationProgress.connect(self.handle_installation_progress)
        self.pip_installer_worker.installationFinished.connect(self.handle_installation_finished)
        self.pip_installer_thread.start()
        
        # --- 配置保存线程 ---
        self.config_saver_thread = QThread()
        self.config_saver_worker = ConfigSaverWorker()
        self.config_saver_worker.moveToThread(self.config_saver_thread)
        self.startConfigSave.connect(self.config_saver_worker.save_config)
        self.config_saver_worker.configSaved.connect(self.handle_config_saved)
        self.config_saver_thread.start()
        
        # --- 进程监控线程 ---
        self.process_monitor_thread = QThread()
        self.process_monitor_worker = ProcessMonitorWorker()
        self.process_monitor_worker.moveToThread(self.process_monitor_thread)
        self.process_monitor_worker.processStatusChanged.connect(self.handle_process_status)
        self.process_monitor_thread.started.connect(self.process_monitor_worker.start_monitoring)
        self.process_monitor_thread.start()
        
        # --- 搜索防抖计时器 ---
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300) # 300ms延迟
        self.search_timer.timeout.connect(self.trigger_search)
        
        # --- 配置保存防抖计时器 ---
        self.config_save_timer = QTimer(self)
        self.config_save_timer.setSingleShot(True)
        self.config_save_timer.setInterval(500) # 500ms延迟
        self.config_save_timer.timeout.connect(self.trigger_config_save)
        
        # --- 内存优化定时器 ---
        self.memory_optimize_timer = QTimer(self)
        self.memory_optimize_timer.setInterval(30000) # 每30秒优化一次内存
        self.memory_optimize_timer.timeout.connect(self.optimize_memory)
        self.memory_optimize_timer.start()
        
        logging.info("后台工作线程初始化完成")
    
    def handle_tool_launched(self, tool_name, success, result):
        """处理工具启动结果"""
        if success:
            if result.isdigit():  # 返回的是进程ID
                self.process_monitor_worker.add_process(tool_name, int(result))
            self.status_label.setText(f"✅ 已启动: {tool_name}")
            # 更新启动统计
            self.update_tool_stats(tool_name)
        else:
            QMessageBox.critical(self, "启动失败", f"启动 {tool_name} 失败: {result}")
            self.status_label.setText(f"❌ 启动失败: {tool_name}")
    
    def handle_config_saved(self, success, error_msg):
        """处理配置保存结果"""
        if not success:
            logging.error(f"配置保存失败: {error_msg}")
            QMessageBox.warning(self, "配置保存失败", f"配置保存失败: {error_msg}")
    
    def handle_process_status(self, tool_name, pid, is_running):
        """处理进程状态变化"""
        if not is_running:
            logging.info(f"进程已结束: {tool_name} (PID: {pid})")
    
    def update_tool_stats(self, tool_name):
        """更新工具启动统计"""
        for tool_dict in self.config.tools:
            if tool_dict.get('name') == tool_name:
                tool_dict['launch_count'] = tool_dict.get('launch_count', 0) + 1
                tool_dict['last_launch'] = datetime.now().isoformat()
                break
        
        # 添加到最近使用列表
        self.config.add_to_recent(tool_name)
        
        # 触发配置保存
        self.schedule_config_save()
        
        # 更新UI
        self.update_status_stats()
    
    def schedule_config_save(self):
        """调度配置保存（防抖）"""
        self.config_save_timer.start()
    
    def trigger_config_save(self):
        """触发配置保存"""
        config_data = {
            "tools": self.config.tools,
            "theme": self.config.theme,
            "view_mode": self.config.view_mode,
            "recent_tools": self.config.recent_tools,
            "show_status_bar": self.config.show_status_bar,
            "auto_refresh": self.config.auto_refresh,
            "search_history": self.config.search_history
        }
        self.startConfigSave.emit(config_data)
    
    def init_ui(self):
        """初始化界面（重构为左侧固定导航栏）"""
        logging.info("开始初始化界面...")
        self.setWindowTitle("SecuHub - 智能程序启动")
        self.setMinimumSize(1200, 800)

        # 分页参数
        # self.tools_per_page = 20
        # self.current_page = 1
        # self.total_pages = 1
        # self.current_tools = []  # 当前显示的工具列表

        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 创建主布局
        layout = QHBoxLayout(main_widget)

        # 创建分割器
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.setChildrenCollapsible(False)
        layout.addWidget(self.main_splitter)

        # 左侧导航栏
        nav_panel = QWidget()
        nav_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        nav_panel.setStyleSheet("""
            QWidget {
                background: #ffffff;
                border-right: 1px solid #e9ecef;
            }
        """)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(16)
        
        # 导航标题
        nav_title = QLabel("导航")
        nav_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #495057;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        """)
        nav_layout.addWidget(nav_title)
        
        # 动态创建导航按钮
        for nav_item in self.config.navigation_items:
            btn = QPushButton(f"{nav_item.get('icon', '➡️')} {nav_item.get('name', '未命名')}")
            btn.setCheckable(True)
            btn.clicked.connect(partial(self.switch_nav, nav_item['id']))
            btn.setStyleSheet("""
                QPushButton {
                    background: #f8f9fa;
                    color: #495057;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 12px 16px;
                    font-size: 14px;
                    font-weight: 600;
                    text-align: left;
                }
                QPushButton:hover {
                    background: #e9ecef;
                    border-color: #dee2e6;
                }
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                    color: white;
                    border-color: #43e97b;
                }
            """)
            nav_layout.addWidget(btn)
            self.nav_buttons[nav_item['id']] = btn
        
        nav_layout.addStretch()
        
        # 底部信息
        bottom_info = QLabel("SecuHub v1.0")
        bottom_info.setStyleSheet("""
            font-size: 11px;
            color: #adb5bd;
            text-align: center;
            padding: 10px 0;
            border-top: 1px solid #e9ecef;
        """)
        bottom_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(bottom_info)
        
        self.main_splitter.addWidget(nav_panel)

        # 右侧内容区（后续填充树形大纲和工具列表/CyberChef/辅助工具）
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        self.main_splitter.addWidget(self.right_panel)
        self.main_splitter.setSizes([200, 1000]) # 设置初始比例，左侧导航约占20%

        # 初始化导航状态，默认选中第一个
        if self.config.navigation_items:
            first_nav_id = self.config.navigation_items[0]['id']
            # 如果默认就是安全工具，先排序
            if first_nav_id == 'safe':
                self.config.tools.sort(key=lambda x: x.get('launch_count', 0), reverse=True)
            self.switch_nav(first_nav_id)
        else:
            # 处理没有导航项的极端情况
            placeholder = QLabel("没有配置导航项，请检查config.json")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.right_layout.addWidget(placeholder)

        # 创建菜单栏
        self.create_menu()
        # 创建状态栏
        self.create_status_bar()
        # 设置样式
        self.apply_theme()
        logging.info("界面初始化完成")

        # 在UI初始化后绑定搜索输入信号
        self.search_input.textChanged.connect(self.on_search_text_changed)

        # 为主窗口添加右键菜单支持
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def toggle_outline_panel(self):
        """切换目录大纲面板的显示/隐藏"""
        is_visible = not self.outline_tree.isVisible()
        self.outline_tree.setVisible(is_visible)
        self.toggle_outline_btn.setChecked(is_visible)

    def switch_nav(self, nav_id):
        """切换导航"""
        # 更新按钮状态
        for item_id, button in self.nav_buttons.items():
            button.setChecked(item_id == nav_id)

        # 清空右侧内容区
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # 根据 nav_id 切换页面内容
        if nav_id == 'safe':
            # --- 顶部搜索栏 ---
            search_bar = QWidget()
            search_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            search_bar.setStyleSheet("""
                QWidget {
                    background: #ffffff;
                    border-bottom: 1px solid #e9ecef;
                }
            """)
            search_bar_layout = QHBoxLayout(search_bar)
            search_bar_layout.setContentsMargins(20, 16, 20, 16)
            search_bar_layout.setSpacing(12)
            
            # 搜索图标
            search_icon = QLabel("🔍")
            search_icon.setStyleSheet("font-size: 16px; color: #6c757d;")
            search_bar_layout.addWidget(search_icon)
            
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("搜索工具名称、描述或分类...")
            self.search_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.search_input.setStyleSheet("""
                QLineEdit {
                    background: #f8f9fa;
                    color: #495057;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 10px 12px;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    background: #ffffff;
                    border: 2px solid #43e97b;
                }
                QLineEdit::placeholder {
                    color: #adb5bd;
                }
            """)
            
            # 添加搜索历史功能
            self.search_input.returnPressed.connect(self.on_search_enter_pressed)
            self.search_input.textChanged.connect(self.on_search_text_changed)
            
            # 添加快捷键支持
            self.search_input.installEventFilter(self)
            
            search_bar_layout.addWidget(self.search_input)
            
            # 搜索统计
            self.search_stats = QLabel("")
            self.search_stats.setStyleSheet("""
                font-size: 12px;
                color: #6c757d;
                padding: 0 8px;
            """)
            search_bar_layout.addWidget(self.search_stats)
            
            search_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.right_layout.addWidget(search_bar, 0)

            # --- 下方QSplitter（左目录大纲，右工具中心）---
            self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
            self.content_splitter.setHandleWidth(2)
            self.content_splitter.setChildrenCollapsible(False)
            self.content_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # 左侧目录大纲
            self.outline_tree = QTreeWidget()
            self.outline_tree.setHeaderHidden(True)
            self.outline_tree.itemClicked.connect(self.on_outline_clicked)
            self.outline_tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.outline_tree.setIndentation(10)  # 控制缩进，为折叠图标留出空间
            self.outline_tree.setStyleSheet("""
QTreeWidget {
    background: #ffffff;
    border: none;
    font-size: 12px;
    color: #34495e;
    padding: 2px 0px;
    outline: 0px;
}
QTreeWidget::item {
    height: 22px;
    border-radius: 4px;
    margin: 0px 5px;
    border: 1px solid transparent;
    padding-left: 5px; /* 移除固定的左内边距，由缩进控制 */
}
QTreeWidget::item:hover {
    background: transparent;
}
QTreeWidget::item:selected {
    background: transparent;
    color: #1c6ef3;
    font-weight: 600;
    border: none;
}
QTreeWidget::branch {
    image: none; /* 隐藏默认的虚线 */
}
QTreeWidget::indicator:unchecked {
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2Yzc1N2QiIHN0cm9rZS13aWR0aD0iMi4yIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1bGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSI5IDYgMTUgMTIgOSAxOCI+PC9wb2x5bGluZT48L3N2Zz4=);
}
QTreeWidget::indicator:checked {
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2Yzc1N2QiIHN0cm9rZS13aWR0aD0iMi4yIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1bGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSI2IDkgMTIgMTUgMTggOSI+PC9wb2x5bGluZT48L3N2Zz4=);
}
""")
            self.content_splitter.addWidget(self.outline_tree)

            # 右侧工具中心
            self.tools_area = QScrollArea()
            self.tools_area.setWidgetResizable(True)
            self.tools_area.setStyleSheet("""
                QScrollArea {
                    background: #f8f9fa;
                    border: none;
                }
            """)
            self.tools_container = QWidget()
            self.tools_container.setStyleSheet("""
                QWidget {
                    background: #f8f9fa;
                }
            """)
            self.tools_vbox = QVBoxLayout(self.tools_container)
            self.tools_vbox.setContentsMargins(20, 20, 20, 20)
            self.tools_vbox.setSpacing(10)
            self.tools_area.setWidget(self.tools_container)
            self.content_splitter.addWidget(self.tools_area)

            self.right_layout.addWidget(self.content_splitter, 1)
            self.right_layout.setStretch(0, 0)
            self.right_layout.setStretch(1, 1)
            # 设置初始比例，左侧目录大纲20%，右侧工具80%
            self.content_splitter.setSizes([int(self.right_panel.width()*0.2), int(self.right_panel.width()*0.8)])

            # 刷新数据，按启动次数排序
            if self._initial_load_done:
                # 工具按launch_count降序
                self.config.tools.sort(key=lambda x: x.get('launch_count', 0), reverse=True)
                self.refresh_outline_and_tools()
        elif nav_id == 'code':
            self.show_cyberchef()
        elif nav_id == 'assist':
            # --- 辅助工具页面 ---
            assist_container = QWidget()
            assist_layout = QVBoxLayout(assist_container)
            assist_layout.setContentsMargins(0, 0, 0, 0)
            assist_layout.setSpacing(0)
            # 顶部tab按钮区
            self.assist_tab_bar = QHBoxLayout()
            self.assist_tab_bar.setContentsMargins(16, 16, 16, 0)
            self.assist_tab_bar.setSpacing(12)
            self.assist_tabs = []
            self.btn_shellgen = QPushButton("反弹shell生成")
            self.btn_shellgen.setCheckable(True)
            self.btn_shellgen.setChecked(True)
            self.btn_shellgen.clicked.connect(lambda: self.switch_assist_tab('shellgen'))
            tab_btn_style = """
            QPushButton {
                background: #fff;
                color: #222;
                border: none;
                border-bottom: 3px solid transparent;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 36px;
            }
            QPushButton:checked {
                color: #2196f3;
                border-bottom: 3px solid #2196f3;
                background: #f7fafd;
            }
            QPushButton:hover {
                background: #f2f6fa;
            }
            """
            self.btn_shellgen.setStyleSheet(tab_btn_style)
            self.assist_tab_bar.addWidget(self.btn_shellgen)
            self.assist_tabs.append(self.btn_shellgen)
            self.btn_java_encode = QPushButton("Java_Exec_Encode")
            self.btn_java_encode.setCheckable(True)
            self.btn_java_encode.setChecked(False)
            self.btn_java_encode.clicked.connect(lambda: self.switch_assist_tab('java_encode'))
            self.btn_java_encode.setStyleSheet(tab_btn_style)
            self.assist_tab_bar.addWidget(self.btn_java_encode)
            self.assist_tabs.append(self.btn_java_encode)
            # 新增命令查询Tab按钮
            self.btn_memo = QPushButton("命令查询")
            self.btn_memo.setCheckable(True)
            self.btn_memo.setChecked(False)
            self.btn_memo.clicked.connect(lambda: self.switch_assist_tab('memo'))
            self.btn_memo.setStyleSheet(tab_btn_style)
            self.assist_tab_bar.addWidget(self.btn_memo)
            self.assist_tabs.append(self.btn_memo)
            self.assist_tab_bar.addStretch()
            assist_layout.addLayout(self.assist_tab_bar)
            self.assist_content = QStackedWidget()
            self.shellgen_webview = QWebEngineView()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            shellgen_path = os.path.join(current_dir, "project", "reverse-shell", "index.html")
            if os.path.exists(shellgen_path):
                url = QUrl.fromLocalFile(shellgen_path)
                self.shellgen_webview.setUrl(url)
            else:
                self.shellgen_webview.setUrl(QUrl("https://btsrk.me/"))
            self.assist_content.addWidget(self.shellgen_webview)
            self.java_encode_webview = QWebEngineView()
            self.clipboard_bridge = ClipboardBridge()
            channel = QWebChannel(self.java_encode_webview.page())
            self.java_encode_webview.page().setWebChannel(channel)
            channel.registerObject("qt_bridge", self.clipboard_bridge)
            java_encode_path = os.path.join(current_dir, "project", "java-encode", "index.html")
            if os.path.exists(java_encode_path):
                url = QUrl.fromLocalFile(java_encode_path)
                self.java_encode_webview.setUrl(url)
            else:
                self.java_encode_webview.setUrl(QUrl("https://gchq.github.io/CyberChef/"))
            self.assist_content.addWidget(self.java_encode_webview)
            # 命令查询Tab内容页
            self.memo_widget = MemoTabWidget()
            self.assist_content.addWidget(self.memo_widget)
            assist_layout.addWidget(self.assist_content)
            self.right_layout.addWidget(assist_container)
            self.current_assist_tab = 'java_encode'
        else:
            # 未来可以扩展为动态加载不同类型的页面
            # 当前为未知导航项创建一个空白页
            nav_item_name = "未知"
            for item in self.config.navigation_items:
                if item['id'] == nav_id:
                    nav_item_name = item['name']
                    break
            placeholder = QLabel(f"'{nav_item_name}' 页面正在建设中...")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.right_layout.addWidget(placeholder)

    def on_search_text_changed(self, text):
        """当搜索框文本变化时，启动/重置防抖计时器"""
        # 清空之前的搜索结果统计
        if hasattr(self, 'search_stats'):
            self.search_stats.setText("")
        self.search_timer.start()

    def trigger_search(self):
        """计时器结束后，触发后台搜索"""
        search_text = self.search_input.text().strip()
        if not search_text:
            # 空搜索时显示所有工具并清空统计
            self.update_tools_list_for_outline()
            if hasattr(self, 'search_stats'):
                self.search_stats.setText("")
            return
        
        # 添加到搜索历史
        if search_text and hasattr(self.config, 'add_search_history'):
            self.config.add_search_history(search_text)
        
        all_tools_data = self.config.tools
        self.current_page = 1  # 搜索时重置到第一页
        self.startSearch.emit(all_tools_data, search_text)

    def handle_search_results(self, results):
        """用后台线程的搜索结果更新UI"""
        tools_to_show = [Tool.from_dict(r) for r in results]
        self.show_tools_list(tools_to_show)
        
        # 更新搜索统计信息
        search_text = self.search_input.text().strip()
        if search_text and hasattr(self, 'search_stats'):
            total_tools = len(self.config.tools)
            found_tools = len(results)
            if found_tools == 0:
                self.search_stats.setText(f"未找到匹配的工具 (共 {total_tools} 个)")
            else:
                self.search_stats.setText(f"找到 {found_tools} 个工具 (共 {total_tools} 个)")
        elif hasattr(self, 'search_stats'):
            self.search_stats.setText("")

    def refresh_outline_and_tools(self):
        """根据所有工具的分类字段动态生成树形大纲（支持多级），并显示所有工具"""
        self.outline_tree.clear()
        
        # 添加"所有工具"项
        all_tools_item = QTreeWidgetItem(["所有工具"])
        all_tools_item.setData(0, Qt.ItemDataRole.UserRole, "show_all") # 特殊标记
        all_tools_item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon))
        self.outline_tree.addTopLevelItem(all_tools_item)
        
        # 构建支持多级的分类树结构
        tree_dict = {}
        for t in self.config.tools:
            # 使用strip()去除前后空格，并过滤掉空部分
            parts = [p.strip() for p in t.get('category', '').split('/') if p.strip()]
            if not parts:
                continue
            
            current_level = tree_dict
            for part in parts:
                current_level = current_level.setdefault(part, {})

        # 递归函数，用于将字典树添加到QTreeWidget
        def add_items_to_tree(parent_item, children):
            for name, sub_children in sorted(children.items()):
                child_item = QTreeWidgetItem([name])
                parent_item.addChild(child_item)
                if sub_children:
                    add_items_to_tree(child_item, sub_children)
                # else:  # 删除无下级分类时添加隐藏子项的逻辑
                #     placeholder = QTreeWidgetItem()
                #     placeholder.setHidden(True)
                #     child_item.addChild(placeholder)

        # 遍历顶层分类并添加到树中
        for name, children in sorted(tree_dict.items()):
            top_level_item = QTreeWidgetItem([name])
            self.outline_tree.addTopLevelItem(top_level_item)
            if children:
                add_items_to_tree(top_level_item, children)
            # else:  # 删除无下级分类时添加隐藏子项的逻辑
            #     placeholder = QTreeWidgetItem()
            #     placeholder.setHidden(True)
            #     top_level_item.addChild(placeholder)
        
        # 默认折叠所有节点
        self.outline_tree.collapseAll()
        
        # 默认显示所有工具
        self.update_tools_list_for_outline()

    def on_outline_clicked(self, item):
        """点击树形大纲分类，显示对应工具（支持多级）"""
        # 检查是否点击了"所有工具"
        if item.data(0, Qt.ItemDataRole.UserRole) == "show_all":
            self.update_tools_list_for_outline()
            return
            
        # 获取完整分类路径
        path = []
        cur = item
        while cur:
            path.insert(0, cur.text(0))
            cur = cur.parent()
        
        # 拼接成前缀，用于匹配
        cat_prefix = '/'.join(path)
        
        # 筛选出所有分类以该前缀开头的工具
        tools = [Tool.from_dict(t) for t in self.config.tools if t.get('category', '').startswith(cat_prefix)]
        
        self.show_tools_list(tools)
        # 仅在存在right_stack和tools_page时切换页面，避免AttributeError
        if hasattr(self, 'right_stack') and hasattr(self, 'tools_page'):
            self.right_stack.setCurrentWidget(self.tools_page)

    def update_tools_list_for_outline(self):
        """显示所有工具（或可根据需要显示默认分类）"""
        tools = [Tool.from_dict(t) for t in self.config.tools]
        self.show_tools_list(tools)
        # 清空搜索统计
        if hasattr(self, 'search_stats'):
            self.search_stats.setText("")

    def show_tools_list(self, tools):
        clear_layout(self.tools_vbox)
        
        # 添加工具卡片
        for tool in tools:
            card = ToolCard(tool, launch_callback=self.launch_tool_card)
            self.tools_vbox.addWidget(card)
        
        self.tools_vbox.addStretch(1)  # 添加弹性空间，确保卡片从上往下排列

    def set_tool_icon(self, row, tool_path, icon):
        """Slot to set a lazy-loaded icon on a list item."""
        if row >= self.tools_vbox.count():
            return  # 行越界，列表可能已更新
            
        item = self.tools_vbox.item(row)
        if item:
            # 验证item是否仍然是当初请求图标的那个工具
            item_tool = item.data(Qt.ItemDataRole.UserRole)
            if item_tool and item_tool.path == tool_path:
                item.setIcon(icon)
                # 缓存图标以提高性能
                if item_tool.icon_path:
                    icon_cache_key = f"icon_{hash(item_tool.icon_path)}"
                    self.cache_manager.set(icon_cache_key, icon)
    
    def optimize_memory(self):
        """优化内存使用"""
        # 清理缓存中的旧条目
        if len(self.cache_manager.cache) > self.cache_manager.max_size * 0.8:
            # 当缓存使用超过80%时，清理最旧的20%条目
            items_to_remove = int(self.cache_manager.max_size * 0.2)
            for _ in range(items_to_remove):
                if self.cache_manager.access_order:
                    oldest_key = self.cache_manager.access_order.pop(0)
                    if oldest_key in self.cache_manager.cache:
                        del self.cache_manager.cache[oldest_key]
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        logging.info("内存优化完成")

    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        add_tool_action = QAction("添加工具", self)
        add_tool_action.setShortcut(QKeySequence("Ctrl+N"))
        add_tool_action.triggered.connect(self.add_tool)
        file_menu.addAction(add_tool_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出配置", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_config)
        file_menu.addAction(export_action)
        
        import_action = QAction("导入配置", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self.import_config)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 主题菜单
        theme_menu = menubar.addMenu("主题")
        
        # 现代化主题
        modern_light_action = QAction("🌞 现代浅色", self)
        modern_light_action.triggered.connect(partial(self.set_theme, "modern_light"))
        theme_menu.addAction(modern_light_action)
        
        modern_dark_action = QAction("🌙 现代深色", self)
        modern_dark_action.triggered.connect(partial(self.set_theme, "modern_dark"))
        theme_menu.addAction(modern_dark_action)
        
        # 新增主题
        # tranquil_green_action = QAction("🌿 静谧绿", self)
        # tranquil_green_action.triggered.connect(partial(self.set_theme, "tranquil_green"))
        # theme_menu.addAction(tranquil_green_action)

        # deep_ocean_action = QAction("🌊 深海蓝", self)
        # deep_ocean_action.triggered.connect(partial(self.set_theme, "deep_ocean"))
        # theme_menu.addAction(deep_ocean_action)
        
        # 科技风主题
        cyberpunk_action = QAction("🤖 科技风", self)
        cyberpunk_action.triggered.connect(partial(self.set_theme, "cyberpunk"))
        theme_menu.addAction(cyberpunk_action)
        
        # 新增主题
        sunset_orange_action = QAction("🌅 日落橙", self)
        sunset_orange_action.triggered.connect(partial(self.set_theme, "sunset_orange"))
        theme_menu.addAction(sunset_orange_action)
        
        midnight_purple_action = QAction("🌌 午夜紫", self)
        midnight_purple_action.triggered.connect(partial(self.set_theme, "midnight_purple"))
        theme_menu.addAction(midnight_purple_action)
        
        forest_green_action = QAction("🌲 森林绿", self)
        forest_green_action.triggered.connect(partial(self.set_theme, "forest_green"))
        theme_menu.addAction(forest_green_action)
        
        ice_blue_action = QAction("❄️ 冰蓝", self)
        ice_blue_action.triggered.connect(partial(self.set_theme, "ice_blue"))
        theme_menu.addAction(ice_blue_action)
        
        theme_menu.addSeparator()
        
        # 主题预览功能
        # preview_action = QAction("👁️ 主题预览", self)
        # preview_action.triggered.connect(self.show_theme_preview)
        # theme_menu.addAction(preview_action)
        
        theme_menu.addSeparator()
        
        # # 统计菜单
        # stats_menu = menubar.addMenu("统计")
        
        # # 总工具数
        # total_tools_action = QAction("总工具数", self)
        # total_tools_action.triggered.connect(self.show_total_tools)
        # stats_menu.addAction(total_tools_action)
        
        # # 最近启动的工具
        # recent_tools_action = QAction("最近启动的工具", self)
        # recent_tools_action.triggered.connect(self.show_recent_tools)
        # stats_menu.addAction(recent_tools_action)
        
        # stats_menu.addSeparator()
        
        # # 刷新统计
        # refresh_stats_action = QAction("刷新统计", self)
        # refresh_stats_action.setShortcut(QKeySequence("F5"))
        # refresh_stats_action.triggered.connect(self.refresh_data)
        # stats_menu.addAction(refresh_stats_action)
        
        # 直接添加关于菜单项到菜单栏
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        menubar.addAction(about_action)
        
        # 添加快捷键
        self.setup_shortcuts()
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置")
        env_action = QAction("环境变量配置", self)
        env_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(env_action)
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # 搜索快捷键
        search_shortcut = QAction(self)
        search_shortcut.setShortcut(QKeySequence("Ctrl+F"))
        search_shortcut.triggered.connect(self.focus_search)
        self.addAction(search_shortcut)
        
        # 刷新快捷键
        refresh_shortcut = QAction(self)
        refresh_shortcut.setShortcut(QKeySequence("F5"))
        refresh_shortcut.triggered.connect(self.refresh_data)
        self.addAction(refresh_shortcut)
        
        # 全屏快捷键
        fullscreen_shortcut = QAction(self)
        fullscreen_shortcut.setShortcut(QKeySequence("F11"))
        fullscreen_shortcut.triggered.connect(self.toggle_fullscreen)
        self.addAction(fullscreen_shortcut)
    
    def focus_search(self):
        """聚焦到搜索框"""
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def refresh_data(self):
        """刷新数据（移除category_tree相关逻辑）"""
        self.update_status_stats()
        # 只刷新工具大纲和工具列表
        self.refresh_outline_and_tools()
        self.status_label.setText("数据已刷新")
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
            self.status_label.setText("退出全屏模式")
        else:
            self.showFullScreen()
            self.status_label.setText("进入全屏模式")
    
    def show_about(self):
        """显示关于对话框（现代化UI）"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        dialog.setMinimumSize(480, 600)

        # 主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部渐变标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        title_icon = QLabel("💡")
        title_icon.setStyleSheet("font-size: 26px; color: white; background: transparent;")
        title_layout.addWidget(title_icon)
        title_text = QLabel("关于 SecuHub")
        title_text.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background: transparent; margin-left: 8px;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.18); border: none; border-radius: 18px; color: white; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background: rgba(255,255,255,0.32); }
            QPushButton:pressed { background: rgba(0,0,0,0.12); }
        """)
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        # 拖动支持
        dialog.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                dialog.offset = event.globalPosition().toPoint() - dialog.pos()
        def mouseMoveEvent(event):
            if dialog.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                dialog.move(event.globalPosition().toPoint() - dialog.offset)
        def mouseReleaseEvent(event):
            dialog.offset = None
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent
        main_layout.addWidget(title_bar)

        # 主体内容卡片
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background: #fff;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                padding: 0;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(18)

        # 大标题
        big_title = QLabel("SecuHub - 智能程序启动")
        big_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1da1f2; margin-bottom: 8px;")
        big_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(big_title)

        # 版本与作者
        meta = QLabel("版本：<b>1.0</b>  &nbsp;|&nbsp;  作者：<a href='https://github.com/z50n6' style='color:#1da1f2;text-decoration:none;'>z50n6</a>")
        meta.setOpenExternalLinks(True)
        meta.setStyleSheet("font-size: 14px; color: #34495e; margin-bottom: 8px;")
        meta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(meta)

        # 分割线
        line = QWidget()
        line.setFixedHeight(2)
        line.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7); border-radius: 1px;")
        card_layout.addWidget(line)

        # 功能简介
        about_text = QLabel(
            """
            <div style='font-size:15px;line-height:1.8;color:#34495e;'>
            <b>主要功能：</b><br>
            • 工具管理、分类组织、快速启动<br>
            • CyberChef集成、辅助脚本<br>
            • 多种工具类型支持：GUI、命令行、Java、Python、PowerShell、网页、文件夹等<br>
            </div>
            """
        )
        about_text.setStyleSheet("font-size: 15px; color: #34495e;")
        about_text.setWordWrap(True)
        card_layout.addWidget(about_text)

        # 快捷键说明
        shortcut_title = QLabel("<b>快捷键：</b>")
        shortcut_title.setStyleSheet("font-size: 15px; color: #1da1f2; margin-top: 10px;")
        card_layout.addWidget(shortcut_title)
        shortcut_text = QLabel(
            """
            <div style='font-size:14px;line-height:1.7;color:#495057;'>
            • <b>Ctrl+N</b>：添加工具<br>
            • <b>Ctrl+F</b>：搜索<br>
            • <b>F5</b>：刷新<br>
            • <b>F11</b>：全屏切换<br>
            </div>
            """
        )
        shortcut_text.setStyleSheet("font-size: 14px; color: #495057;")
        shortcut_text.setWordWrap(True)
        card_layout.addWidget(shortcut_text)

        # 关闭按钮
        btn = QPushButton("关闭")
        btn.setMinimumSize(140, 44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1da1f2, stop:1 #0d8bd9);
                color: #fff;
                border-radius: 22px;
                font-size: 17px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d8bd9, stop:1 #1da1f2);
            }
        """)
        btn.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)

        main_layout.addWidget(card)
        dialog.exec()
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态信息标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label, 1) # 添加拉伸因子
        
        # 安装进度条
        self.install_progress_bar = QProgressBar()
        self.install_progress_bar.setVisible(False)
        self.install_progress_bar.setFixedWidth(200)
        self.status_bar.addPermanentWidget(self.install_progress_bar)
        
        # 工具统计信息
        self.stats_label = QLabel("")
        self.status_bar.addPermanentWidget(self.stats_label)
        
        # 更新统计信息
        self.update_status_stats()
    
    def update_status_stats(self):
        """更新状态栏统计信息"""
        total_tools = len(self.config.tools)
        total_nav_items = len(self.config.navigation_items)
        total_launches = sum(tool.get("launch_count", 0) for tool in self.config.tools)
        
        stats_text = f"工具: {total_tools} | 导航: {total_nav_items} | 启动: {total_launches}"
        self.stats_label.setText(stats_text)
    
    def load_data(self):
        """加载数据（已不再需要分类树）"""
        pass
    
    def update_category_tree(self):
        """已废弃：分类树相关逻辑移除"""
        pass
    
    def update_tools_list(self, category=None):
        """更新工具列表，支持分页和全部工具展示"""
        pass
    def prev_page(self):
        pass
    def next_page(self):
        pass
    
    def _create_tool_item(self, tool):
        """创建自定义工具卡片"""
        item = QListWidgetItem()
        card = ToolCard(tool, launch_callback=self.launch_tool_card)
        item.setSizeHint(card.sizeHint())
        item.setData(Qt.ItemDataRole.UserRole, tool)
        self.tools_vbox.addItem(item, 0, 0)
        self.tools_vbox.setItemWidget(item, card)
    
    def _get_tool_icon(self, tool):
        """根据工具类型获取图标"""
        icon_map = {
            "exe": "⚙️",
            "java8_gui": "☕",
            "java11_gui": "☕",
            "java8": "👨‍💻",
            "java11": "👨‍💻",
            "python": "🐍",
            "powershell": "💻",
            "batch": "📜",
            "url": "🌐",
            "folder": "📁",
            "placeholder": "📂"
        }
        return icon_map.get(tool.tool_type, "🚀")
    
    def _get_tool_status(self, tool):
        """获取工具状态"""
        if tool.tool_type == "placeholder":
            return "空分类", QColor(150, 150, 150)
        
        # 检查工具路径是否存在
        if tool.tool_type in ["url", "folder"]:
            return "可用", QColor(0, 150, 0)
        elif tool.tool_type in ["java8", "java11", "java8_gui", "java11_gui"]:
            # 检查Java环境
            try:
                subprocess.run(["java", "-version"], capture_output=True, check=True)
                return "可用", QColor(0, 150, 0)
            except:
                return "需Java环境", QColor(255, 100, 0)
        elif tool.tool_type == "python":
            # 检查Python环境
            try:
                subprocess.run(["python", "--version"], capture_output=True, check=True)
                return "可用", QColor(0, 150, 0)
            except:
                return "需Python环境", QColor(255, 100, 0)
        elif tool.tool_type == "powershell":
            return "可用", QColor(0, 150, 0)
        else:
            # 检查文件是否存在
            if os.path.exists(tool.path):
                return "可用", QColor(0, 150, 0)
            else:
                return "文件不存在", QColor(255, 0, 0)
    
    def on_category_clicked(self, item):
        """分类点击处理"""
        category_name = item.text(0)
        logging.info(f"点击分类: {category_name}")
        if category_name == "编码与解码":
            logging.info("切换到CyberChef页面")
            self.right_stack.setCurrentWidget(self.cyberchef_page)
            self.cyberchef_webview.setFocus()
        else:
            self.current_page = 1
            self.update_tools_list(category_name)
            self.right_stack.setCurrentWidget(self.tools_page)
            # 如果该分类下没有工具，显示提示
            if not self.current_tools:
                empty_item = QListWidgetItem("📂 此分类暂无工具")
                empty_item.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Normal))
                empty_item.setForeground(QColor(150, 150, 150))
                empty_item.setToolTip("点击右键菜单可以添加工具到此分类")
                self.tools_vbox.addItem(empty_item, 0, 0)
                self.tools_vbox.setItemWidget(empty_item, ToolCard(Tool(name="", path="", category="", subcategory="", tool_type="placeholder", description="", icon_path=None, color="#000000", launch_count=0, args="")))
    
    def on_tool_item_clicked(self, item):
        """工具项点击处理"""
        # 如果点击的是工具项，则启动工具
        tool = item.data(Qt.ItemDataRole.UserRole)
        if tool:
            self.launch_tool(item)
    
    def _launch_and_update_stats(self, tool_to_launch):
        """统一处理工具启动、统计更新和配置保存（已废弃，使用新的后台启动机制）"""
        # 使用新的后台启动机制
        self.startToolLaunch.emit(tool_to_launch)
        return True

    def launch_tool(self, item):
        """启动工具"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
            
        if tool.tool_type == "placeholder":
            QMessageBox.information(self, "提示", "这是一个空分类的占位符，请添加实际工具到此分类。")
            return
            
        # 使用新的后台启动机制
        self.startToolLaunch.emit(tool, True)
    
    def edit_tool(self, item):
        """编辑工具"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        
        # 动态提取所有已存在的分类路径作为建议
        existing_categories = sorted(list(set(
            t.get('category', '').strip()
            for t in self.config.tools
            if t.get('category', '').strip()
        )))
        dialog = AddToolDialog(existing_categories, self)
        
        # 设置当前值
        type_mapping_reverse = {
            "exe": "GUI应用",
            "java8_gui": "java8图形化",
            "java11_gui": "java11图形化",
            "java8": "java8",
            "java11": "java11",
            "python": "python",
            "powershell": "powershell",
            "batch": "批处理",
            "url": "网页",
            "folder": "文件夹"
        }
        
        dialog.name_edit.setText(tool.name)
        dialog.path_edit.setText(tool.path)
        dialog.category_combo.setCurrentText(tool.category)
        dialog.args_edit.setText(tool.args)
        dialog.icon_edit.setText(tool.icon_path or "")
        dialog.desc_edit.setPlainText(tool.description)
        
        # 设置工具类型
        tool_type = type_mapping_reverse.get(tool.tool_type, "GUI应用")
        dialog.type_combo.setCurrentText(tool_type)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool_data = dialog.get_tool_data()
            tool_data["launch_count"] = tool.launch_count
            tool_data["last_launch"] = tool.last_launch
            
            # 更新工具数据
            index = self.config.tools.index(tool.to_dict())
            self.config.tools[index] = tool_data
            self.config.save_config()
            self.update_category_tree()  # 更新分类树
            self.update_tools_list()  # 重新加载当前分类的工具
    
    def delete_tool(self, item):
        """删除工具"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
            
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除工具 '{tool.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 更稳妥地删除工具，避免list.remove(x): x not in list
            for idx, t in enumerate(self.config.tools):
                if (
                    t.get('name') == tool.name and
                    t.get('path') == tool.path and
                    t.get('category') == tool.category
                ):
                    del self.config.tools[idx]
                    break
            self.config.save_config()
            self.update_tools_list()  # 重新加载当前分类的工具
    
    def open_tool_folder(self, item):
        """打开工具所在文件夹"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        
        path_to_check = tool.path
        
        # 如果是文件，获取其所在目录；如果是目录，则使用其本身
        if tool.tool_type == 'folder':
             folder_to_open = path_to_check
        else:
             folder_to_open = os.path.dirname(path_to_check)

        if os.path.exists(folder_to_open) and os.path.isdir(folder_to_open):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_to_open))
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "路径不存在", f"无法打开文件夹，路径不是一个有效的文件夹:\n{folder_to_open}")
    
    def open_tool_cmd(self, item):
        """打开工具命令行, 优先使用Windows Terminal, 其次PowerShell, 最后cmd"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
            
        if tool.tool_type == "folder":
            path = tool.path
        else:
            path = os.path.dirname(tool.path)
            
        if not os.path.isdir(path):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "路径无效", f"无法打开命令行，路径不是一个有效的文件夹:\n{path}")
            return

        # Define creation flags for a new console window
        CREATE_NEW_CONSOLE = 0x00000010

        # Commands to try, in order of preference.
        # The first element is the command list, the second is a dict of extra Popen args.
        terminal_options = [
            {"cmd": ["wt.exe", "-d", path], "args": {}, "name": "Windows Terminal"},
            {"cmd": ["pwsh.exe", "-NoExit"], "args": {"cwd": path}, "name": "PowerShell Core"},
            {"cmd": ["powershell.exe", "-NoExit"], "args": {"cwd": path}, "name": "Windows PowerShell"},
            {"cmd": ["cmd.exe"], "args": {"cwd": path}, "name": "Command Prompt"}
        ]

        for option in terminal_options:
            try:
                subprocess.Popen(option["cmd"], creationflags=CREATE_NEW_CONSOLE, **option["args"])
                logging.info(f"成功使用 {option['name']} 打开路径: {path}")
                return
            except FileNotFoundError:
                import logging
                logging.info(f"未找到 {option['name']}，尝试下一个...")
            except Exception as e:
                import logging
                logging.warning(f"启动 {option['name']} 失败: {e}，尝试下一个...")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "错误", "无法打开任何终端。请检查您的系统配置。")
    
    def show_cyberchef(self):
        """显示CyberChef页面，兼容新版右侧内容区"""
        # 清空右侧内容区
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        # 每次都新建WebView，避免切换后不显示
        self.cyberchef_webview = QWebEngineView()
        self.cyberchef_webview.setMinimumSize(800, 600)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cyberchef_index = os.path.join(current_dir, "project", "CyberChef", "index.html")
        if os.path.exists(cyberchef_index):
            url = QUrl.fromLocalFile(cyberchef_index)
            self.cyberchef_webview.setUrl(url)
        else:
            self.cyberchef_webview.setUrl(QUrl("https://gchq.github.io/CyberChef/"))
        self.cyberchef_webview.loadFinished.connect(self.on_cyberchef_loaded)
        self.right_layout.addWidget(self.cyberchef_webview)
    
    def set_theme(self, theme_name):
        self.config.theme = theme_name
        self.config.save_config()
        self.apply_theme()
    
    def apply_theme(self):
        """应用主题"""
        theme = self.config.theme
        qss = self.theme_manager.load_theme(theme)
        scrollbar_qss = self.theme_manager.load_scrollbar(theme)
        self.setStyleSheet(qss + scrollbar_qss)
    
    def show_theme_preview(self):
        """显示主题预览对话框"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        dialog.setMinimumSize(800, 600)
        # 主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # 标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        title_icon = QLabel("🎨")
        title_icon.setStyleSheet("font-size: 26px; color: white; background: transparent;")
        title_layout.addWidget(title_icon)
        title_text = QLabel("主题预览")
        title_text.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background: transparent; margin-left: 8px;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.18); border: none; border-radius: 18px; color: white; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background: rgba(255,255,255,0.32); }
            QPushButton:pressed { background: rgba(0,0,0,0.12); }
        """)
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        # 拖动支持
        dialog.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                dialog.offset = event.globalPosition().toPoint() - dialog.pos()
        def mouseMoveEvent(event):
            if dialog.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                dialog.move(event.globalPosition().toPoint() - dialog.offset)
        def mouseReleaseEvent(event):
            dialog.offset = None
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent
        main_layout.addWidget(title_bar)
        # 主体内容
        content = QWidget()
        content.setStyleSheet("""
            QWidget {
                background: #fff;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
            }
        """)
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        # 左侧主题列表
        theme_list = QListWidget()
        theme_list.setFixedWidth(200)
        theme_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background: #1da1f2;
                color: white;
            }
            QListWidget::item:hover {
                background: #f7f9fa;
            }
        """)
        # 右侧预览区域
        preview_area = QWidget()
        preview_layout = QVBoxLayout(preview_area)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(15)
        # 预览标题
        preview_title = QLabel("主题预览")
        preview_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        preview_layout.addWidget(preview_title)
        # 预览内容区域
        preview_content = QWidget()
        preview_content.setStyleSheet("border: 1px solid #e1e8ed; border-radius: 8px; padding: 20px;")
        preview_content_layout = QVBoxLayout(preview_content)
        preview_content_layout.setSpacing(15)
        # 模拟按钮
        test_button = QPushButton("测试按钮")
        test_button.setFixedSize(120, 40)
        preview_content_layout.addWidget(test_button)
        # 模拟输入框
        test_input = QLineEdit()
        test_input.setPlaceholderText("测试输入框")
        test_input.setFixedHeight(35)
        preview_content_layout.addWidget(test_input)
        # 模拟下拉框
        test_combo = QComboBox()
        test_combo.addItems(["选项1", "选项2", "选项3"])
        test_combo.setFixedHeight(35)
        preview_content_layout.addWidget(test_combo)
        # 模拟文本区域
        test_text = QTextEdit()
        test_text.setPlaceholderText("测试文本区域")
        test_text.setFixedHeight(100)
        preview_content_layout.addWidget(test_text)
        # 应用按钮
        apply_btn = QPushButton("应用此主题")
        apply_btn.setFixedSize(120, 40)
        preview_content_layout.addWidget(apply_btn)
        preview_layout.addWidget(preview_content)
        preview_layout.addStretch()
        # 添加到主布局
        content_layout.addWidget(theme_list)
        content_layout.addWidget(preview_area)
        main_layout.addWidget(content)
        # 填充主题列表
        current_theme = self.config.theme
        for theme_name in self.theme_manager.get_theme_names():
            display_name = self.theme_manager.get_theme_display_name(theme_name)
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, theme_name)
            theme_list.addItem(item)
            if theme_name == current_theme:
                theme_list.setCurrentItem(item)
        # 主题切换事件
        def on_theme_selected(item):
            theme_name = item.data(Qt.ItemDataRole.UserRole)
            qss = self.theme_manager.load_theme(theme_name)
            scrollbar_qss = self.theme_manager.load_scrollbar(theme_name)
            dialog.setStyleSheet(qss + scrollbar_qss)
        theme_list.currentItemChanged.connect(on_theme_selected)
        # 应用主题事件
        def apply_selected_theme():
            current_item = theme_list.currentItem()
            if current_item:
                theme_name = current_item.data(Qt.ItemDataRole.UserRole)
                self.set_theme(theme_name)
                dialog.accept()
        apply_btn.clicked.connect(apply_selected_theme)
        # 初始应用当前主题样式
        on_theme_selected(theme_list.currentItem())
        dialog.exec()
    def export_config(self):
        """导出配置，包含所有工具及分类信息"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "", "JSON文件 (*.json)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({
                        "tools": self.config.tools,
                        "theme": self.config.theme,
                        "view_mode": self.config.view_mode
                    }, f, ensure_ascii=False, indent=2)
                self.status_label.setText(f"✅ 配置已成功导出到: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def import_config(self):
        """导入配置，自动刷新树形大纲和工具列表"""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.config.tools = data.get("tools", [])
                self.config.theme = data.get("theme", "modern_light")
                self.config.view_mode = data.get("view_mode", "list")
                self.config.save_config()
                self.refresh_outline_and_tools()
                self.apply_theme()
                self.status_label.setText(f"✅ 配置已从 {os.path.basename(path)} 成功导入")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def show_category_context_menu(self, position):
        item = self.category_tree.itemAt(position)
        menu = QMenu()
        if item:
            rename_action = QAction("重命名", self)
            rename_action.triggered.connect(partial(self.rename_category, item))
            menu.addAction(rename_action)

            delete_action = QAction("删除", self)
            delete_action.triggered.connect(partial(self.delete_category, item))
            menu.addAction(delete_action)

            add_sub_action = QAction("添加子分类", self)
            add_sub_action.triggered.connect(partial(self.add_subcategory, item))
            menu.addAction(add_sub_action)
        else:
            add_action = QAction("添加主分类", self)
            add_action.triggered.connect(self.add_category)
            menu.addAction(add_action)
        menu.exec(self.category_tree.viewport().mapToGlobal(position))

    def rename_category(self, item):
        old_name = item.text(0)
        new_name, ok = QInputDialog.getText(self, "重命名分类", "请输入新名称:", text=old_name)
        if ok and new_name and new_name != old_name:
            # 更新分类列表
            if item.parent() is None:
                # 主分类
                if new_name in self.config.categories:
                    QMessageBox.warning(self, "错误", "该分类已存在")
                    return
                idx = self.config.categories.index(old_name)
                self.config.categories[idx] = new_name
                # 更新所有工具的分类字段
                for tool in self.config.tools:
                    if tool["category"] == old_name:
                        tool["category"] = new_name
            else:
                # 子分类
                parent_name = item.parent().text(0)
                for tool in self.config.tools:
                    if tool["category"] == parent_name and tool["subcategory"] == old_name:
                        tool["subcategory"] = new_name
            self.config.save_config()
            self.update_category_tree()
            self.update_tools_list()

    def delete_category(self, item):
        name = item.text(0)
        if item.parent() is None:
            # 主分类
            reply = QMessageBox.question(self, "确认删除", f"确定要删除主分类 '{name}' 及其所有子分类和工具吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.config.categories.remove(name)
                # 删除所有相关工具
                self.config.tools = [tool for tool in self.config.tools if tool["category"] != name]
                self.config.save_config()
                self.update_category_tree()
                self.update_tools_list()
        else:
            # 子分类
            parent_name = item.parent().text(0)
            reply = QMessageBox.question(self, "确认删除", f"确定要删除子分类 '{name}' 及其所有工具吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                for tool in self.config.tools:
                    if tool["category"] == parent_name and tool["subcategory"] == name:
                        tool["subcategory"] = ""
                self.config.save_config()
                self.update_category_tree()
                self.update_tools_list()

    def add_subcategory(self, item):
        if item.parent() is not None:
            QMessageBox.warning(self, "提示", "暂不支持多级子分类")
            return
        parent_name = item.text(0)
        sub_name, ok = QInputDialog.getText(self, "添加子分类", f'请输入"{parent_name}"下的新子分类名称:')
        if ok and sub_name:
            # 检查是否已存在
            for tool in self.config.tools:
                if tool["category"] == parent_name and tool["subcategory"] == sub_name:
                    QMessageBox.warning(self, "错误", "该子分类已存在")
                    return
            
            # 创建一个空的占位工具来显示二级分类
            placeholder_tool = {
                "name": f"[{sub_name}] - 空分类",
                "path": "",
                "category": parent_name,
                "subcategory": sub_name,
                "tool_type": "placeholder",
                "description": f"这是 {sub_name} 分类的占位符，可以添加工具到此分类",
                "icon_path": None,
                "color": "#000000",
                "launch_count": 0,
                "last_launch": None,
                "args": ""
            }
            
            self.config.tools.append(placeholder_tool)
            self.config.save_config()
            
            # 刷新当前分类的工具列表以显示新的二级分类
            self.update_tools_list(parent_name)

    def resizeEvent(self, event):
        """窗口大小变化事件，兼容新版右侧内容区"""
        super().resizeEvent(event)
        # 兼容新版：如果右侧内容区有CyberChef页面则自适应
        if hasattr(self, 'cyberchef_webview') and self.cyberchef_webview.parent() == self.right_panel:
            self.cyberchef_webview.resize(self.right_panel.size())
        if hasattr(self, 'tools_area') and hasattr(self, 'tools_vbox'):
            if hasattr(self, 'current_tools'):
                self.show_tools_list(self.current_tools)

    def on_cyberchef_loaded(self, success):
        """CyberChef加载完成后的处理"""
        if success:
            logging.info("CyberChef加载成功")
            # 注入更强力的JS，自动均分三栏并触发resize
            js = '''
            (function() {
                let splitters = document.querySelectorAll('.vsplit, .hsplit');
                splitters.forEach(function(splitter) {
                    let children = Array.from(splitter.children);
                    children.forEach(function(child) {
                        child.style.width = (100 / children.length) + '%';
                        child.style.flex = '1 1 0%';
                        child.style.minWidth = '0';
                    });
                    window.dispatchEvent(new Event('resize'));
                });
            })();
            '''
            self.cyberchef_webview.page().runJavaScript(js)
        else:
            logging.error("CyberChef加载失败")
            self.cyberchef_webview.setUrl(QUrl("https://gchq.github.io/CyberChef/"))

    def rename_subcategory(self, item):
        """重命名二级分类"""
        # 从显示文本中提取分类名称（去掉图标）
        old_name = item.text(0).replace("📁 ", "").replace("📂 ", "")
        new_name, ok = QInputDialog.getText(
            self, "重命名分类", "请输入新的分类名称:", text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            # 获取当前选中的一级分类
            current_category_item = self.category_tree.currentItem()
            if not current_category_item:
                return
            category_name = current_category_item.text(0)
            
            # 更新所有相关工具的子分类字段
            for tool in self.config.tools:
                if tool["category"] == category_name and tool["subcategory"] == old_name:
                    tool["subcategory"] = new_name
            
            self.config.save_config()
            # 重新加载当前分类的工具列表
            self.update_tools_list(category_name)

    def custom_drag_enter_event(self, event):
        """自定义拖拽进入事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def custom_drag_move_event(self, event):
        """自定义拖拽移动事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def custom_drop_event(self, event):
        """自定义拖拽放置事件"""
        if not event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.ignore()
            return

        source_item = self.tools_tree.currentItem()
        if not source_item:
            event.ignore()
            return

        target_item = self.tools_tree.itemAt(event.position().toPoint())
        if not target_item:
            event.ignore()
            return

        # 拖动工具到二级分类
        if source_item.parent() is not None and target_item.parent() is None and target_item.childCount() > 0:
            tool = source_item.data(0, Qt.ItemDataRole.UserRole)
            if tool:
                subcategory_name = target_item.text(0).replace("📁 ", "").replace("📂 ", "")
                current_category_item = self.category_tree.currentItem()
                if current_category_item:
                    category_name = current_category_item.text(0)
                    for t in self.config.tools:
                        if t["name"] == tool.name and t["category"] == category_name:
                            t["subcategory"] = subcategory_name
                            break
                    self.config.save_config()
                    self.update_tools_list(category_name)
            event.acceptProposedAction()
            return

        # 二级分类之间拖动
        if (source_item.parent() is None and source_item.childCount() > 0 and
            target_item.parent() is None and target_item.childCount() > 0):
            source_index = self.tools_tree.indexOfTopLevelItem(source_item)
            target_index = self.tools_tree.indexOfTopLevelItem(target_item)
            if source_index != target_index:
                self.tools_tree.takeTopLevelItem(source_index)
                self.tools_tree.insertTopLevelItem(target_index, source_item)
                current_category_item = self.category_tree.currentItem()
                if current_category_item:
                    category_name = current_category_item.text(0)
                    self.reorder_subcategories(category_name)
            event.acceptProposedAction()
            return

        # 其他情况不允许
        event.ignore()

    def reorder_subcategories(self, category_name):
        """重新排序二级分类"""
        # 获取当前树中的所有二级分类顺序
        subcategory_order = []
        for i in range(self.tools_tree.topLevelItemCount()):
            item = self.tools_tree.topLevelItem(i)
            if item.childCount() > 0:  # 这是一个二级分类
                subcategory_name = item.text(0).replace("📁 ", "").replace("📂 ", "")
                subcategory_order.append(subcategory_name)
        
        # 重新组织工具数据，按照新的顺序
        reorganized_tools = []
        
        # 先添加没有子分类的工具
        for tool in self.config.tools:
            if tool["category"] == category_name and not tool["subcategory"]:
                reorganized_tools.append(tool)
        
        # 按照新顺序添加有子分类的工具
        for subcategory in subcategory_order:
            for tool in self.config.tools:
                if tool["category"] == category_name and tool["subcategory"] == subcategory:
                    reorganized_tools.append(tool)
        
        # 更新配置中的工具列表
        # 先移除当前分类的所有工具
        self.config.tools = [tool for tool in self.config.tools if tool["category"] != category_name]
        # 再添加重新组织的工具
        self.config.tools.extend(reorganized_tools)
        
        self.config.save_config()

    def add_tool_to_subcategory(self, subcategory_name):
        """添加工具到指定子分类"""
        # 获取当前选中的一级分类
        current_category_item = self.category_tree.currentItem()
        if not current_category_item:
            return
        category_name = current_category_item.text(0)
        
        # 打开添加工具对话框，并预设子分类
        dialog = AddToolDialog(self.config.categories, self)
        dialog.category_combo.setCurrentText(category_name)
        # 这里需要添加一个子分类输入框，暂时用文本提示
        dialog.setWindowTitle(f"添加工具到 {subcategory_name} 分类")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool_data = dialog.get_tool_data()
            tool_data["subcategory"] = subcategory_name  # 强制设置子分类
            
            # 检查是否添加了新分类
            new_category = tool_data["category"]
            if new_category not in self.config.categories:
                self.config.categories.append(new_category)
                logging.info(f"添加新分类: {new_category}")
            
            self.config.tools.append(tool_data)
            self.config.save_config()
            self.update_category_tree()  # 更新分类树
            
            # 如果当前选中的是工具所属的分类，则刷新工具列表
            if current_category_item.text(0) == tool_data["category"]:
                self.update_tools_list(tool_data["category"])
    
    def delete_placeholder_subcategory(self, placeholder_tool):
        """删除占位符子分类"""
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除空分类 '{placeholder_tool.subcategory}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 删除占位符工具
            self.config.tools.remove(placeholder_tool.to_dict())
            self.config.save_config()
            
            # 刷新当前分类的工具列表
            current_category_item = self.category_tree.currentItem()
            if current_category_item:
                category_name = current_category_item.text(0)
                self.update_tools_list(category_name)

    def show_total_tools(self):
        """显示总工具数统计（重新设计现代化UI）"""
        total_tools = len(self.config.tools)
        total_nav_items = len(self.config.navigation_items)
        total_launches = sum(tool.get("launch_count", 0) for tool in self.config.tools)
        
        # 计算更多统计信息
        active_tools = sum(1 for tool in self.config.tools if tool.get("launch_count", 0) > 0)
        avg_launches = total_launches / total_tools if total_tools > 0 else 0
        
        # 计算使用率
        usage_rate = (active_tools / total_tools * 100) if total_tools > 0 else 0
        
        # 创建现代化对话框
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setWindowTitle("📊 工具统计面板")
        dialog.setMinimumSize(800, 500)
        dialog.setMaximumSize(1000, 600)
        
        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        dialog.move((screen.width() - dialog.width()) // 2,
                   (screen.height() - dialog.height()) // 2)
        
        # 主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部标题栏
        title_bar = QWidget()
        title_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        title_icon = QLabel("📊")
        title_icon.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(title_icon)
        
        title_text = QLabel("工具统计面板")
        title_text.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            margin-left: 10px;
        """)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        # Make window draggable
        dialog.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                dialog.offset = event.globalPosition().toPoint() - dialog.pos()

        def mouseMoveEvent(event):
            if dialog.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                dialog.move(event.globalPosition().toPoint() - dialog.offset)

        def mouseReleaseEvent(event):
            dialog.offset = None
        
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 15px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        
        main_layout.addWidget(title_bar)
        
        # 内容区域
        content_widget = QWidget()
        content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content_widget.setStyleSheet("""
            QWidget {
                background: #f8f9fa;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # 主要统计卡片行
        main_stats_layout = QHBoxLayout()
        main_stats_layout.setSpacing(15)
        
        # 创建主要统计卡片
        main_stats = [
            {
                "title": "总工具数",
                "value": str(total_tools),
                "icon": "🛠️",
                "color": "#667eea",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2)",
                "description": "已配置的工具总数"
            },
            {
                "title": "总导航数",
                "value": str(total_nav_items),
                "icon": "🧭",
                "color": "#f093fb",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f093fb, stop:1 #f5576c)",
                "description": "主导航项数量"
            },
            {
                "title": "总启动次数",
                "value": str(total_launches),
                "icon": "🚀",
                "color": "#4facfe",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4facfe, stop:1 #00f2fe)",
                "description": "累计启动次数"
            }
        ]
        
        for stat in main_stats:
            card = self._create_stat_card(stat)
            main_stats_layout.addWidget(card)
        
        content_layout.addLayout(main_stats_layout)
        
        # 次要统计卡片行
        secondary_stats_layout = QHBoxLayout()
        secondary_stats_layout.setSpacing(15)
        
        # 创建次要统计卡片
        secondary_stats = [
            {
                "title": "活跃工具",
                "value": f"{active_tools}",
                "icon": "⭐",
                "color": "#43e97b",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7)",
                "description": f"使用率: {usage_rate:.1f}%"
            },
            {
                "title": "平均启动",
                "value": f"{avg_launches:.1f}",
                "icon": "📈",
                "color": "#fa709a",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fa709a, stop:1 #fee140)",
                "description": "每个工具平均启动次数"
            },
            {
                "title": "使用状态",
                "value": "正常" if total_tools > 0 else "无工具",
                "icon": "✅" if total_tools > 0 else "⚠️",
                "color": "#a8edea" if total_tools > 0 else "#fed6e3",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #a8edea, stop:1 #fed6e3)" if total_tools > 0 else "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fed6e3, stop:1 #a8edea)",
                "description": "系统运行状态"
            }
        ]
        
        for stat in secondary_stats:
            card = self._create_stat_card(stat)
            secondary_stats_layout.addWidget(card)
        
        content_layout.addLayout(secondary_stats_layout)
        
        # 详细信息区域
        details_group = QGroupBox("📋 详细信息")
        details_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background: #f8f9fa;
            }
        """)
        
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(15, 20, 15, 15)
        details_layout.setSpacing(10)
        
        # 详细信息文本
        details_text = f"""
        <div style="font-size: 13px; line-height: 1.6; color: #6c757d;">
        <b>📊 统计概览：</b><br>
        • 当前共配置了 <span style="color: #667eea; font-weight: bold;">{total_tools}</span> 个工具<br>
        • 分布在 <span style="color: #f093fb; font-weight: bold;">{total_nav_items}</span> 个导航中<br>
        • 累计启动 <span style="color: #4facfe; font-weight: bold;">{total_launches}</span> 次<br>
        • 活跃工具占比 <span style="color: #43e97b; font-weight: bold;">{usage_rate:.1f}%</span><br>
        • 平均每个工具启动 <span style="color: #fa709a; font-weight: bold;">{avg_launches:.1f}</span> 次<br>
        </div>
        """
        
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        details_layout.addWidget(details_label)
        
        content_layout.addWidget(details_group)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新统计")
        refresh_btn.setFixedSize(120, 40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38f9d7, stop:1 #43e97b);
            }
            QPushButton:pressed {
                background: #3dd16a;
            }
        """)
        refresh_btn.clicked.connect(lambda: self.refresh_stats_and_close(dialog))
        
        # 导出按钮
        export_btn = QPushButton("📤 导出报告")
        export_btn.setFixedSize(120, 40)
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38f9d7, stop:1 #43e97b);
            }
            QPushButton:pressed {
                background: #3dd16a;
            }
        """)
        export_btn.clicked.connect(lambda: self.export_stats_report())
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        
        content_layout.addLayout(button_layout)
        
        main_layout.addWidget(content_widget)
        
        dialog.exec()
    
    def _create_stat_card(self, stat_data):
        """创建统计卡片"""
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setFixedSize(200, 120)
        card.setStyleSheet(f"""
            QWidget {{
                background: {stat_data['gradient']};
                border-radius: 12px;
                color: white;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # 图标和标题
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        icon_label = QLabel(stat_data['icon'])
        icon_label.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(stat_data['title'])
        title_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: rgba(255, 255, 255, 0.9);
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 数值
        value_label = QLabel(stat_data['value'])
        value_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # 描述
        desc_label = QLabel(stat_data['description'])
        desc_label.setStyleSheet("""
            font-size: 10px;
            color: rgba(255, 255, 255, 0.8);
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        return card
    
    def export_stats_report(self):
        """导出统计报告"""
        try:
            total_tools = len(self.config.tools)
            total_nav_items = len(self.config.navigation_items)
            total_launches = sum(tool.get("launch_count", 0) for tool in self.config.tools)
            active_tools = sum(1 for tool in self.config.tools if tool.get("launch_count", 0) > 0)
            avg_launches = total_launches / total_tools if total_tools > 0 else 0
            usage_rate = (active_tools / total_tools * 100) if total_tools > 0 else 0
            
            # 生成报告内容
            report_content = f"""
SecuHub 工具统计报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 基础统计 ===
总工具数: {total_tools}
总导航数: {total_nav_items}
总启动次数: {total_launches}
活跃工具数: {active_tools}
平均启动次数: {avg_launches:.1f}
使用率: {usage_rate:.1f}%

=== 分类统计 ===
"""
            
            # 按分类统计
            category_stats = {}
            for tool in self.config.tools:
                category = tool.get('category', '未分类')
                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'launches': 0}
                category_stats[category]['count'] += 1
                category_stats[category]['launches'] += tool.get('launch_count', 0)
            
            for category, stats in sorted(category_stats.items()):
                report_content += f"{category}: {stats['count']} 个工具, {stats['launches']} 次启动\n"
            
            report_content += f"""
=== 最常用工具 (前10名) ===
"""
            
            # 最常用工具
            sorted_tools = sorted(self.config.tools, key=lambda x: x.get('launch_count', 0), reverse=True)
            for i, tool in enumerate(sorted_tools[:10], 1):
                report_content += f"{i}. {tool.get('name', 'Unknown')}: {tool.get('launch_count', 0)} 次启动\n"
            
            # 保存报告
            path, _ = QFileDialog.getSaveFileName(
                self, "导出统计报告", f"SecuHub_统计报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 
                "文本文件 (*.txt)"
            )
            
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                QMessageBox.information(self, "导出成功", f"统计报告已导出到:\n{path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出统计报告时发生错误:\n{str(e)}")
    
    def refresh_stats_and_close(self, dialog):
        """刷新统计并关闭对话框"""
        self.update_status_stats()
        dialog.accept()
        self.show_total_tools()
    
    def show_recent_tools(self):
        """显示最近启动的工具（优化UI，支持图标和点击执行）"""
        if not self.config.recent_tools:
            QMessageBox.information(self, "最近启动的工具", "暂无最近启动的工具")
            return

        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        dialog.setWindowTitle("🕒 最近启动的工具")
        dialog.setMinimumSize(800, 600)

        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        dialog.move((screen.width() - dialog.width()) // 2,
                   (screen.height() - dialog.height()) // 2)

        # Main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom Title Bar
        title_bar = QWidget()
        title_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)

        title_icon = QLabel("🕒")
        title_icon.setStyleSheet("font-size: 24px; color: white;")
        title_layout.addWidget(title_icon)

        title_text = QLabel("最近启动的工具")
        title_text.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-left: 10px;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()

        # Draggability
        dialog.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                dialog.offset = event.globalPosition().toPoint() - dialog.pos()
        def mouseMoveEvent(event):
            if dialog.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                dialog.move(event.globalPosition().toPoint() - dialog.offset)
        def mouseReleaseEvent(event):
            dialog.offset = None
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255, 255, 255, 0.2); border: none; border-radius: 15px; color: white; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background: rgba(255, 255, 255, 0.3); }
            QPushButton:pressed { background: rgba(255, 255, 255, 0.1); }
        """)
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        main_layout.addWidget(title_bar)

        # Content Area
        content_widget = QWidget()
        content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content_widget.setStyleSheet("""
            QWidget {
                background: #f8f9fa;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Scroll Area for the list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: #e9ecef; width: 8px; margin: 0px 0px 0px 0px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #ced4da; min-height: 20px; border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
        """)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 5, 0) # Right margin for scrollbar
        list_layout.setSpacing(10)
        
        # Populate list
        for i, tool_name in enumerate(self.config.recent_tools[:20], 1):
            tool = next((Tool.from_dict(t) for t in self.config.tools if t["name"] == tool_name), None)
            if tool:
                tool_item_card = self._create_recent_tool_card(tool, i, dialog)
                list_layout.addWidget(tool_item_card)
        
        list_layout.addStretch(1)
        scroll_area.setWidget(list_container)
        content_layout.addWidget(scroll_area)

        # Bottom button area
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        clear_button = QPushButton("🗑️ 清空历史")
        clear_button.setFixedSize(120, 40)
        clear_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fa709a, stop:1 #fee140);
                color: white; border: none; border-radius: 20px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fee140, stop:1 #fa709a); }
        """)
        clear_button.clicked.connect(lambda: self.clear_recent_history(dialog))
        bottom_layout.addWidget(clear_button)
        bottom_layout.addStretch()
        content_layout.addLayout(bottom_layout)

        main_layout.addWidget(content_widget)
        dialog.exec()
    
    def _create_recent_tool_card(self, tool, index, parent_dialog):
        """Creates a styled card widget for a recent tool."""
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setMinimumHeight(80)
        # Add a property to make it easy to find for double-click event handling if needed later
        card.setProperty("isCard", True)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet("""
            QWidget[isCard="true"] {
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 10px;
            }
            QWidget[isCard="true"]:hover {
                border: 1px solid #43e97b;
                background: #f8f9fa;
            }
        """)
        
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)
        card_layout.setSpacing(15)

        # Index
        index_label = QLabel(f"{index:02d}")
        index_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ced4da; background: transparent;")
        index_label.setFixedWidth(30)
        card_layout.addWidget(index_label)

        # Icon
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setStyleSheet("background: #e9ecef; border-radius: 24px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if tool.icon_path and os.path.exists(tool.icon_path):
            pixmap = QIcon(tool.icon_path).pixmap(32, 32)
            icon_label.setPixmap(pixmap)
        else:
            emoji = self._get_tool_icon(tool)
            icon_label.setText(f"<span style='font-size: 24px;'>{emoji}</span>")
            
        card_layout.addWidget(icon_label)

        # Info
        info_container = QWidget()
        info_container.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        name_label = QLabel(tool.name)
        name_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #212529; background: transparent;")
        desc_label = QLabel(f"类型: {tool.tool_type} | 启动: {tool.launch_count} 次")
        desc_label.setStyleSheet("font-size: 11px; color: #6c757d; background: transparent;")
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        card_layout.addWidget(info_container, 1)

        # Launch Button
        launch_btn = QPushButton("🚀 启动")
        launch_btn.setFixedSize(90, 36)
        launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        launch_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
                color: white; border: none; border-radius: 18px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #764ba2, stop:1 #667eea); }
        """)
        launch_btn.clicked.connect(lambda: self.launch_tool_from_recent(tool, parent_dialog))
        card_layout.addWidget(launch_btn)

        # Double click to launch
        card.mouseDoubleClickEvent = lambda event: self.launch_tool_from_recent(tool, parent_dialog)

        return card
    
    def launch_tool_from_recent(self, tool, dialog):
        """从最近工具列表启动工具"""
        self.startToolLaunch.emit(tool, True)
        dialog.accept() # 启动成功后关闭对话框
    
    def clear_recent_history(self, dialog):
        """清空最近使用历史（美化确认弹窗按钮）"""
        dlg = ConfirmDialog(self, title="确认清空", content="确定要清空最近使用历史吗？", icon="🗑️", yes_text="是", no_text="否")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.config.recent_tools.clear()
            self.config.save_config()
            dialog.accept()
            QMessageBox.information(self, "清空完成", "最近使用历史已清空")
    
    def show_favorites(self):
        """显示收藏工具"""
        if not self.config.favorites:
            QMessageBox.information(self, "收藏工具", "暂无收藏的工具")
            return
        
        favorites_text = "⭐ 收藏工具\n\n"
        for i, tool_name in enumerate(self.config.favorites, 1):
            favorites_text += f"{i}. {tool_name}\n"
        
        QMessageBox.information(self, "收藏工具", favorites_text)
    
    def search_tools(self, text):
        """搜索工具(此方法已废弃,逻辑由多线程工作者替代)"""
        pass
    
    def _create_search_tool_item(self, tool):
        """创建搜索结果的工具项"""
        item = self.tools_vbox.findItems(tool.name, Qt.MatchFlag.MatchExactly)
        if item:
             self.show_tools_list([tool])

    def launch_tool_card(self, tool):
        """卡片启动按钮回调"""
        # 兼容原有启动逻辑
        self.startToolLaunch.emit(tool, True)
    
    def show_context_menu(self, position):
        """显示工具右键菜单，支持卡片视图和空白区域新增工具"""
        # 获取点击位置的widget
        widget = self.childAt(position)
        
        # 查找是否点击了ToolCard
        tool_card = None
        while widget and not isinstance(widget, ToolCard):
            widget = widget.parent()
        if widget:
            tool_card = widget
        
        menu = QMenu(self)
        
        if tool_card:
            # 点击了工具卡片，显示工具相关菜单
            tool = tool_card.tool
            
            # 启动工具
            launch_action = menu.addAction("🚀 启动工具")
            launch_action.triggered.connect(tool_card.launch_tool)
            
            menu.addSeparator()
            
            # 编辑工具
            edit_action = menu.addAction("✏️ 编辑工具")
            edit_action.triggered.connect(tool_card.edit_tool)
            
            # 删除工具
            delete_action = menu.addAction("🗑️ 删除工具")
            delete_action.triggered.connect(tool_card.delete_tool)
            
            menu.addSeparator()
            
            # 打开工具文件夹
            open_folder_action = menu.addAction("📁 打开文件夹")
            open_folder_action.triggered.connect(tool_card.open_folder)
            
            # 打开命令行
            open_cmd_action = menu.addAction("💻 打开命令行")
            open_cmd_action.triggered.connect(tool_card.open_command_line)
            
            # 复制路径
            copy_path_action = menu.addAction("📋 复制路径")
            copy_path_action.triggered.connect(tool_card.copy_path)
            
            # 复制工具信息
            copy_info_action = menu.addAction("📄 复制工具信息")
            copy_info_action.triggered.connect(tool_card.copy_tool_info)
            
        else:
            # 点击了空白区域，显示新增工具等选项
            add_tool_action = menu.addAction("➕ 新增工具")
            add_tool_action.triggered.connect(self.add_tool)
            
            menu.addSeparator()
            
            # 刷新工具列表
            refresh_action = menu.addAction("🔄 刷新列表")
            refresh_action.triggered.connect(self.refresh_outline_and_tools)
            
            # 显示统计信息
            stats_action = menu.addAction("📊 显示统计")
            stats_action.triggered.connect(self.show_total_tools)
            
            # 显示最近工具
            recent_action = menu.addAction("⏰ 最近使用")
            recent_action.triggered.connect(self.show_recent_tools)
        
        menu.exec(self.mapToGlobal(position))

    def edit_tool(self, item):
        """编辑工具，支持修改分类，保存后自动刷新大纲"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        dialog = AddToolDialog([], self)
        dialog.name_edit.setText(tool.name)
        dialog.path_edit.setText(tool.path)
        dialog.category_combo.setEditText(tool.category)
        dialog.args_edit.setText(tool.args)
        dialog.icon_edit.setText(tool.icon_path or "")
        dialog.desc_edit.setPlainText(tool.description)
        # 设置工具类型
        type_mapping_reverse = {
            "exe": "GUI应用",
            "java8_gui": "java8图形化",
            "java11_gui": "java11图形化",
            "java8": "java8",
            "java11": "java11",
            "python": "python",
            "powershell": "powershell",
            "batch": "批处理",
            "url": "网页",
            "folder": "文件夹"
        }
        tool_type = type_mapping_reverse.get(tool.tool_type, "GUI应用")
        dialog.type_combo.setCurrentText(tool_type)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool_data = dialog.get_tool_data()
            tool_data["launch_count"] = tool.launch_count
            tool_data["last_launch"] = tool.last_launch
            # 更新工具数据
            for idx, t in enumerate(self.config.tools):
                if (t.get('name') == tool.name and t.get('path') == tool.path and t.get('category') == tool.category):
                    self.config.tools[idx] = tool_data
                    break
            self.config.save_config()
            self.refresh_outline_and_tools()
            self.status_label.setText(f"✅ 工具 '{tool_data['name']}' 添加成功")

    def add_tool(self):
        """新增工具，保存后自动刷新大纲"""
        # 动态提取所有已存在的分类路径作为建议
        existing_categories = sorted(list(set(
            tool.get('category', '').strip()
            for tool in self.config.tools
            if tool.get('category', '').strip()
        )))
        dialog = AddToolDialog(existing_categories, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool_data = dialog.get_tool_data()
            self.config.tools.append(tool_data)
            self.config.save_config()
            self.refresh_outline_and_tools()
            # 请在这里添加下面这行
            self.status_label.setText(f"✅ 工具 '{tool_data['name']}' 已添加")

    def delete_tool(self, item):
        """删除工具，自动刷新大纲"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除工具 '{tool.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # 从配置中删除工具
            for idx, t in enumerate(self.config.tools):
                if (t.get('name') == tool.name and 
                    t.get('path') == tool.path and 
                    t.get('category') == tool.category):
                    del self.config.tools[idx]
                    break
            
            self.config.save_config()
            self.refresh_outline_and_tools()
            self.status_label.setText(f"🗑️ 工具 '{tool.name}' 已删除")

    def open_tool_folder(self, item, all_paths=False):
        """打开工具所有路径文件夹"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        paths = [tool.path]
        if all_paths and hasattr(tool, 'extra_paths'):
            paths += tool.extra_paths
        for path in paths:
            folder = os.path.dirname(path)
            if os.path.exists(folder):
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
            self.config.save_config()
            self.refresh_outline_and_tools()
            self.status_label.setText(f"✅ 工具 '{tool.name}' 已更新")

    def open_tool_cmd(self, item):
        """打开工具所在路径命令行"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        folder = os.path.dirname(tool.path)
        if os.path.exists(folder):
            subprocess.Popen(["cmd", "/k", f"cd /d {folder}"])
    
    def add_favorite(self, tool_name):
        """添加到收藏"""
        self.config.add_to_favorites(tool_name)
        self.update_status_stats()
        self.status_label.setText(f"已添加 '{tool_name}' 到收藏")
    
    def remove_favorite(self, tool_name):
        """从收藏中移除"""
        self.config.remove_from_favorites(tool_name)
        self.update_status_stats()
        self.status_label.setText(f"已从收藏中移除 '{tool_name}'")

    def switch_assist_tab(self, tab_name):
        """切换辅助工具tab"""
        for btn in self.assist_tabs:
            btn.setChecked(False)
        if tab_name == 'shellgen':
            self.btn_shellgen.setChecked(True)
            self.assist_content.setCurrentIndex(0)
            self.current_assist_tab = 'shellgen'
        elif tab_name == 'java_encode':
            self.btn_java_encode.setChecked(True)
            self.assist_content.setCurrentIndex(1)
            self.current_assist_tab = 'java_encode'
        elif tab_name == 'memo':
            self.btn_memo.setChecked(True)
            self.assist_content.setCurrentIndex(2)
            self.current_assist_tab = 'memo'

    def closeEvent(self, event):
        """处理窗口关闭事件，安全地终止工作线程"""
        logging.info("正在关闭应用程序，请稍候...")
        
        # 停止所有定时器
        self.search_timer.stop()
        self.config_save_timer.stop()
        self.memory_optimize_timer.stop()
        
        # 停止所有工作线程
        self.search_thread.quit()
        self.icon_loader_thread.quit()
        self.tool_launcher_thread.quit()
        self.config_saver_thread.quit()
        self.process_monitor_worker.stop_monitoring()
        self.process_monitor_thread.quit()
        
        # 等待线程安全退出
        threads_to_wait = [
            (self.search_thread, "搜索线程"),
            (self.icon_loader_thread, "图标加载线程"),
            (self.tool_launcher_thread, "工具启动线程"),
            (self.config_saver_thread, "配置保存线程"),
            (self.pip_installer_thread, "Pip安装线程"),
            (self.process_monitor_thread, "进程监控线程")
        ]
        
        for thread, name in threads_to_wait:
            if not thread.wait(1000):  # 等待1秒
                logging.warning(f"{name}未能及时停止。")
        
        # 清空缓存
        self.cache_manager.clear()
        
        super().closeEvent(event)

    def handle_installation_required(self, tool, target):
        """处理Python依赖安装请求"""
        self.startPipInstall.emit(tool, target)

    def handle_installation_started(self, tool_name):
        """处理安装开始事件"""
        self.install_progress_bar.setVisible(True)
        self.install_progress_bar.setRange(0, 0)  # 设置为不确定模式
        self.status_label.setText(f"为 {tool_name} 开始安装依赖...")

    def handle_installation_progress(self, tool_name, message):
        """处理安装进度更新"""
        self.status_label.setText(f"[{tool_name}] {message}")

    def handle_installation_finished(self, tool_name, success, error_msg, tool):
        """处理安装完成事件"""
        self.install_progress_bar.setVisible(False)
        self.install_progress_bar.setRange(0, 100) # 重置
        if success:
            self.status_label.setText(f"✅ {tool_name} 依赖安装成功，正在重新启动...")
            # 重新启动，跳过依赖检查
            self.startToolLaunch.emit(tool, False)
        else:
            self.status_label.setText(f"❌ {tool_name} 依赖安装失败: {error_msg}")
            QMessageBox.critical(self, "安装失败", f"为 {tool_name} 安装依赖失败: \n{error_msg}")

    def toggle_outline_panel(self):
        """折叠/展开目录大纲"""
        # 获取当前分割器宽度
        sizes = self.content_splitter.sizes()
        if sizes[1] < 50:
            # 展开
            total = sum(sizes)
            self.content_splitter.setSizes([int(total*0.8), int(total*0.2)])
            self.toggle_outline_btn.setText('<')
        else:
            # 折叠
            self.content_splitter.setSizes([sum(sizes), 0])
            self.toggle_outline_btn.setText('>')

    def on_search_enter_pressed(self):
        """搜索框回车键处理"""
        search_text = self.search_input.text().strip()
        if search_text:
            # 添加到搜索历史
            if hasattr(self.config, 'add_search_history'):
                self.config.add_search_history(search_text)
            # 立即触发搜索
            self.search_timer.stop()
            self.trigger_search()

    def eventFilter(self, obj, event):
        """事件过滤器，处理搜索框快捷键"""
        if obj == self.search_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                # 上箭头：显示搜索历史
                self.show_search_history()
                return True
            elif event.key() == Qt.Key.Key_Down:
                # 下箭头：清除搜索
                self.search_input.clear()
                return True
            elif event.key() == Qt.Key.Key_Escape:
                # ESC：清除搜索并显示所有工具
                self.search_input.clear()
                self.update_tools_list_for_outline()
                return True
        return super().eventFilter(obj, event)

    def show_search_history(self):
        """显示搜索历史"""
        if not hasattr(self.config, 'search_history') or not self.config.search_history:
            return
        
        # 创建搜索历史菜单
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self.search_input)
        menu.setStyleSheet("""
            QMenu {
                background: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #f8f9fa;
            }
        """)
        
        # 添加搜索历史项
        for i, history_item in enumerate(self.config.search_history[:10]):  # 最多显示10个
            action = menu.addAction(f"🔍 {history_item}")
            action.triggered.connect(lambda checked, text=history_item: self.search_input.setText(text))
        
        if self.config.search_history:
            menu.addSeparator()
            clear_action = menu.addAction("🗑️ 清空搜索历史")
            clear_action.triggered.connect(self.clear_search_history)
        
        # 显示菜单
        menu.exec(self.search_input.mapToGlobal(self.search_input.rect().bottomLeft()))

    def clear_search_history(self):
        """清空搜索历史"""
        if hasattr(self.config, 'search_history'):
            self.config.search_history.clear()
            self.config.save_config()

    def launch_tool_card(self, tool):
        """卡片启动按钮回调"""
        # 兼容原有启动逻辑
        self.startToolLaunch.emit(tool, True)
    
    def edit_tool_card(self, tool):
        """编辑工具卡片"""
        if not tool:
            return
        
        # 动态提取所有已存在的分类路径作为建议
        existing_categories = sorted(list(set(
            t.get('category', '').strip()
            for t in self.config.tools
            if t.get('category', '').strip()
        )))
        dialog = AddToolDialog(existing_categories, self)
        
        # 设置当前值
        dialog.name_edit.setText(tool.name)
        dialog.path_edit.setText(tool.path)
        dialog.category_combo.setCurrentText(tool.category)
        dialog.args_edit.setText(tool.args)
        dialog.icon_edit.setText(tool.icon_path or "")
        dialog.desc_edit.setPlainText(tool.description)
        
        # 设置工具类型
        type_mapping_reverse = {
            "exe": "GUI应用",
            "java8_gui": "java8图形化",
            "java11_gui": "java11图形化",
            "java8": "java8",
            "java11": "java11",
            "python": "python",
            "powershell": "powershell",
            "batch": "批处理",
            "url": "网页",
            "folder": "文件夹"
        }
        
        tool_type = type_mapping_reverse.get(tool.tool_type, "GUI应用")
        dialog.type_combo.setCurrentText(tool_type)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool_data = dialog.get_tool_data()
            tool_data["launch_count"] = tool.launch_count
            tool_data["last_launch"] = tool.last_launch
            
            # 更新工具数据
            for idx, t in enumerate(self.config.tools):
                if (t.get('name') == tool.name and 
                    t.get('path') == tool.path and 
                    t.get('category') == tool.category):
                    self.config.tools[idx] = tool_data
                    break
            
            self.config.save_config()
            self.refresh_outline_and_tools()
            self.status_label.setText(f"✅ 工具 '{tool.name}' 已更新")

    def delete_tool_card(self, tool):
        """删除工具卡片（确认步骤已在上游处理）"""
        if not tool:
            return
        
        # 从配置中删除工具
        for idx, t in enumerate(self.config.tools):
            if (t.get('name') == tool.name and 
                t.get('path') == tool.path and 
                t.get('category') == tool.category):
                del self.config.tools[idx]
                break
        
        self.config.save_config()
        self.refresh_outline_and_tools()
        self.status_label.setText(f"🗑️ 工具 '{tool.name}' 已删除")

    def refresh_download_cmd_table(self):
        """刷新文件下载命令表格"""
        import os
        import json
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'file-download-command.json')
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                cmd_list = json.load(f)
        except Exception:
            cmd_list = []
        self.download_cmd_table.setRowCount(len(cmd_list))
        for row, cmd in enumerate(cmd_list):
            name_item = QTableWidgetItem(cmd.get('name', ''))
            name_item.setToolTip(cmd.get('name', ''))
            self.download_cmd_table.setItem(row, 0, name_item)
            cmd_item = QTableWidgetItem(cmd.get('command', ''))
            cmd_item.setToolTip(cmd.get('command', ''))
            self.download_cmd_table.setItem(row, 1, cmd_item)
            meta = ','.join(cmd.get('meta', []))
            meta_item = QTableWidgetItem(meta)
            meta_item.setToolTip(meta)
            self.download_cmd_table.setItem(row, 2, meta_item)
            # 操作列
            op_widget = QWidget()
            op_layout = QHBoxLayout(op_widget)
            op_layout.setContentsMargins(0, 0, 0, 0)
            op_layout.setSpacing(6)
            edit_btn = QPushButton("编辑")
            edit_btn.setStyleSheet("font-size:13px;")
            edit_btn.clicked.connect(lambda _, r=row: self.edit_download_cmd(r))
            del_btn = QPushButton("删除")
            del_btn.setStyleSheet("font-size:13px;")
            del_btn.clicked.connect(lambda _, r=row: self.delete_download_cmd(r))
            op_layout.addWidget(edit_btn)
            op_layout.addWidget(del_btn)
            op_layout.addStretch()
            self.download_cmd_table.setCellWidget(row, 3, op_widget)
        self.download_cmd_table.resizeRowsToContents()

    def edit_download_cmd(self, row):
        import os, json
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'file-download-command.json')
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                cmd_list = json.load(f)
        except Exception:
            cmd_list = []
        if row < 0 or row >= len(cmd_list):
            return
        dialog = AddDownloadCommandDialog(self, data=cmd_list[row])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cmd_data = dialog.get_cmd_data()
            if not cmd_data['name'] or not cmd_data['command']:
                QMessageBox.warning(self, "提示", "命令名称和内容不能为空！")
                return
            cmd_list[row] = cmd_data
            try:
                with open(data_path, 'w', encoding='utf-8') as f:
                    json.dump(cmd_list, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", "命令已更新！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
            self.refresh_download_cmd_table()

    def delete_download_cmd(self, row):
        import os, json
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'file-download-command.json')
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                cmd_list = json.load(f)
        except Exception:
            cmd_list = []
        if row < 0 or row >= len(cmd_list):
            return
        reply = QMessageBox.question(self, "确认删除", f"确定要删除命令 '{cmd_list[row].get('name','')}' 吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del cmd_list[row]
            try:
                with open(data_path, 'w', encoding='utf-8') as f:
                    json.dump(cmd_list, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", "命令已删除！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
            self.refresh_download_cmd_table()
    def show_settings_dialog(self):
        try:
            print("[DEBUG] 打开SettingsDialog弹窗")
            self.config.load_config()  # 优化：每次弹窗前都重新加载配置
            dialog = SettingsDialog(self.config, self)
            result = dialog.exec()
            print(f"[DEBUG] SettingsDialog弹窗关闭，result={result}")
        except Exception as e:
            print(f"[ERROR] 打开SettingsDialog弹窗异常: {e}")

class AddDownloadCommandDialog(QDialog):
    """添加/编辑文件下载命令对话框"""
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("添加/编辑文件下载命令")
        self.setMinimumWidth(480)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: transparent;")
        # 容器
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("""
            QWidget {
                background: #fdfdfe;
                border-radius: 12px;
            }
        """)
        main_layout.addWidget(container)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 20)
        container_layout.setSpacing(0)
        # 标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        title_text = QLabel("添加/编辑文件下载命令")
        title_text.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("background: transparent; color: white; border: none; font-size: 18px;")
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        # 拖动支持
        self.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.offset = event.globalPosition().toPoint() - self.pos()
        def mouseMoveEvent(event):
            if self.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self.offset)
        def mouseReleaseEvent(event):
            self.offset = None
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent
        container_layout.addWidget(title_bar)
        # 表单区
        form_layout = QFormLayout()
        form_layout.setContentsMargins(25, 20, 25, 20)
        form_layout.setSpacing(18)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        # 名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入命令名称")
        form_layout.addRow("命令名称:", self.name_edit)
        # 命令内容
        self.cmd_edit = QTextEdit()
        self.cmd_edit.setPlaceholderText("请输入命令内容")
        self.cmd_edit.setMinimumHeight(100)
        form_layout.addRow("命令内容:", self.cmd_edit)
        # 适用系统
        self.os_combo = QComboBox()
        self.os_combo.addItems(["All", "windows", "linux"])
        form_layout.addRow("适用系统:", self.os_combo)
        container_layout.addLayout(form_layout)
        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.ok_btn = QPushButton("✔️ 确定")
        self.cancel_btn = QPushButton("❌ 取消")
        self.ok_btn.setFixedSize(120, 40)
        self.cancel_btn.setFixedSize(120, 40)
        self.ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                color: white; border-radius: 20px; font-size: 14px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38f9d7, stop:1 #43e97b); }
        """)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e9ecef; color: #495057; border-radius: 20px; font-size: 14px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: #dee2e6; }
        """)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        container_layout.addLayout(btn_layout)
        # 编辑模式填充
        if data:
            self.name_edit.setText(data.get('name', ''))
            self.cmd_edit.setPlainText(data.get('command', ''))
            meta = data.get('meta', ['All'])
            if meta and isinstance(meta, list):
                self.os_combo.setCurrentText(meta[0])
    def get_cmd_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "command": self.cmd_edit.toPlainText().strip(),
            "meta": [self.os_combo.currentText()]
        }

def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if widget:
            widget.setParent(None)
        elif child_layout:
            clear_layout(child_layout)

# ========== 命令查询Tab主结构 ==========
class MemoTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("font-size:15px;font-family:'Microsoft YaHei',微软雅黑,Arial,sans-serif;")
        self.main_window = self.window() if isinstance(self.window(), QMainWindow) else None
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # Tab栏
        self.tab_bar = QHBoxLayout()
        self.tab_bar.setContentsMargins(0, 0, 0, 0)
        self.tab_bar.setSpacing(0)
        self.btn_file = QPushButton("文件下载命令")
        self.btn_file.setCheckable(True)
        self.btn_file.setChecked(True)
        self.btn_file.clicked.connect(lambda: self.switch_tab('file'))
        self.btn_red = QPushButton("红队命令")
        self.btn_red.setCheckable(True)
        self.btn_red.setChecked(False)
        self.btn_red.clicked.connect(lambda: self.switch_tab('red'))
        self.btn_webshell = QPushButton("WebShell一句话")
        self.btn_webshell.setCheckable(True)
        self.btn_webshell.setChecked(False)
        self.btn_webshell.clicked.connect(lambda: self.switch_tab('webshell'))
        tab_btn_style = """
        QPushButton {
            background: #fff;
            color: #222;
            border: none;
            border-bottom: 3px solid transparent;
            font-size: 14px;
            font-weight: bold;
            padding: 10px 36px;
        }
        QPushButton:checked {
            color: #2196f3;
            border-bottom: 3px solid #2196f3;
            background: #f7fafd;
        }
        QPushButton:hover {
            background: #f2f6fa;
        }
        """
        self.btn_file.setStyleSheet(tab_btn_style)
        self.btn_red.setStyleSheet(tab_btn_style)
        self.btn_webshell.setStyleSheet(tab_btn_style)
        self.tab_bar.addWidget(self.btn_file)
        self.tab_bar.addWidget(self.btn_red)
        self.tab_bar.addWidget(self.btn_webshell)
        self.tab_bar.addStretch()
        main_layout.addLayout(self.tab_bar)
        # 分割线
        line = QWidget()
        line.setFixedHeight(2)
        line.setStyleSheet("background:#e0e0e0;margin-bottom:0px;")
        main_layout.addWidget(line)
        # 顶部操作区
        op_layout = QHBoxLayout()
        op_layout.setContentsMargins(16, 12, 16, 12)
        op_layout.setSpacing(8)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索命令/描述...")
        self.search_edit.setFixedHeight(32)
        self.search_edit.setStyleSheet(
            "QLineEdit{font-size:15px;font-family:'Microsoft YaHei',微软雅黑,Arial,sans-serif;"
            "border-radius:8px;background:#fff;padding:6px 12px;border:1px solid #e0e0e0;}"
            "QLineEdit:focus{border:1.5px solid #2196f3;background:#f7fafd;}"
        )
        op_layout.addWidget(self.search_edit, 2)
        # 新增：webshell密码输入框
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("连接密码（默认：saury）")
        self.pass_edit.setFixedHeight(32)
        self.pass_edit.setText("saury")
        self.pass_edit.setStyleSheet(
            "QLineEdit{font-size:15px;font-family:'Microsoft YaHei',微软雅黑,Arial,sans-serif;"
            "border-radius:8px;background:#fff;padding:6px 12px;border:1px solid #e0e0e0;}"
            "QLineEdit:focus{border:1.5px solid #2196f3;background:#f7fafd;}"
        )
        self.pass_edit.setVisible(False)
        op_layout.addWidget(self.pass_edit, 1)
        self.os_combo = QComboBox()
        self.os_combo.addItems(["All", "windows", "linux"])
        self.os_combo.setFixedWidth(90)
        combo_style = (
            "QComboBox{font-size:15px;font-family:'Microsoft YaHei',微软雅黑,Arial,sans-serif;"
            "border-radius:8px;padding:4px 12px;border:1px solid #e0e0e0;}"
            "QComboBox:focus{border:1.5px solid #2196f3;}"
            "QComboBox:hover{box-shadow:0 0 4px #2196f322;}"
        )
        self.os_combo.setStyleSheet(combo_style)
        op_layout.addWidget(self.os_combo)
        self.encode_combo = QComboBox()
        self.encode_combo.addItems(["None", "url", "base64", "双url"])
        self.encode_combo.setFixedWidth(90)
        self.encode_combo.setStyleSheet(combo_style)
        op_layout.addWidget(self.encode_combo)
        op_layout.addStretch()
        self.add_btn = QPushButton("添加命令")
        self.add_btn.setFixedSize(110, 36)
        btn_style = (
            "QPushButton{font-size:15px;font-family:'Microsoft YaHei',微软雅黑,Arial,sans-serif;"
            "font-weight:bold;background:qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);"
            "color:white;border-radius:18px;padding:0 18px;min-width:100px;min-height:36px;}"
            "QPushButton:hover{background:qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38f9d7, stop:1 #43e97b);transform:scale(1.04);}" 
        )
        self.add_btn.setStyleSheet(btn_style)
        op_layout.addWidget(self.add_btn)
        self.copy_btn = QPushButton("复制当前命令")
        self.copy_btn.setFixedSize(120, 36)
        self.copy_btn.setStyleSheet(btn_style)
        op_layout.addWidget(self.copy_btn)
        main_layout.addLayout(op_layout)
        # 信号连接
        self.search_edit.textChanged.connect(self.on_search)
        self.os_combo.currentTextChanged.connect(self.on_search)
        self.encode_combo.currentTextChanged.connect(self.on_search)
        self.add_btn.clicked.connect(self.add_command)
        self.copy_btn.clicked.connect(self.copy_current_command)
        self.pass_edit.textChanged.connect(self.on_search)  # 新增：密码输入变化时刷新
        # 内容区
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(16, 0, 16, 0)
        content_layout.setSpacing(16)
        self.list_widget = MemoCommandList(self)
        self.list_widget.setMinimumWidth(320)
        self.list_widget.setMaximumWidth(320)
        content_layout.addWidget(self.list_widget, 0)
        self.detail_widget = MemoCommandDetail(self)
        content_layout.addWidget(self.detail_widget, 1)
        main_layout.addLayout(content_layout, 1)
        # 修复首次进入不显示数据
        self.list_widget.detail_widget = self.detail_widget
        self.list_widget.filter_commands()
        # 保证首次进入tab逻辑和UI刷新
        self.switch_tab('file')
    def switch_tab(self, tab):
        self.btn_file.setChecked(tab == 'file')
        self.btn_red.setChecked(tab == 'red')
        self.btn_webshell.setChecked(tab == 'webshell')
        self.encode_combo.setVisible(tab == 'file')
        if tab == 'webshell':
            self.os_combo.setVisible(False)
            self.encode_combo.setVisible(False)
            self.pass_edit.setVisible(True)
            self.search_edit.setVisible(True)
        elif tab == 'file':
            self.os_combo.setVisible(True)
            self.os_combo.clear()
            self.os_combo.addItems(["All", "windows", "linux"])
            self.encode_combo.setVisible(True)
            self.pass_edit.setVisible(False)
            self.search_edit.setVisible(True)
        else:
            self.os_combo.setVisible(True)
            self.os_combo.clear()
            self.os_combo.addItems(["All", "windows", "linux"])
            self.encode_combo.setVisible(False)
            self.pass_edit.setVisible(False)
            self.search_edit.setVisible(True)
        self.list_widget.set_mode(tab)
        self.on_search()
        self.detail_widget.clear()
        self.list_widget.detail_widget = self.detail_widget
    def on_search(self):
        keyword = self.search_edit.text().strip()
        os_type = self.os_combo.currentText()
        encode = self.encode_combo.currentText() if self.encode_combo.isVisible() else 'None'
        self.list_widget.filter_commands(keyword, os_type, encode)
    def add_command(self):
        self.list_widget.add_command()
    def edit_command(self, row):
        dialog = MemoCommandDialog(self.list_widget.current_mode, data=self.list_widget.all_cmds[row], parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cmd_data = dialog.get_cmd_data()
            if not cmd_data['name'] or not cmd_data['command']:
                self.show_status("⚠️ 命令名称和内容不能为空！")
                return
            self.list_widget.all_cmds[row] = cmd_data
            self.list_widget.save_and_refresh()
            self.show_status("✅ 命令已更新")
    def delete_command(self, row):
        from PyQt6.QtWidgets import QMessageBox
        if row < 0 or row >= len(self.list_widget.all_cmds):
            return
        reply = QMessageBox.question(self, "确认删除", f"确定要删除命令 '{self.list_widget.all_cmds[row].get('name','')}' 吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.list_widget.all_cmds[row]
            self.list_widget.save_and_refresh()
            self.show_status("🗑️ 命令已删除")
    def show_status(self, msg):
        # 状态栏提示
        mainwin = self.window() if isinstance(self.window(), QMainWindow) else None
        if mainwin and hasattr(mainwin, 'status_label'):
            mainwin.status_label.setText(msg)
    def copy_current_command(self):
        # 复制当前选中命令内容
        cur_row = self.list_widget.currentRow() - 1  # 因为有表头
        if cur_row < 0 or cur_row >= len(self.list_widget.all_cmds):
            return
        cmd = self.list_widget.all_cmds[cur_row]
        encode = self.encode_combo.currentText() if self.encode_combo.isVisible() else 'None'
        content = cmd.get('command', '')
        if encode == 'url':
            from urllib.parse import quote
            content = quote(content)
        elif encode == 'base64':
            import base64
            content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        elif encode == '双url':
            from urllib.parse import quote
            content = quote(quote(content))
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(content)
        self.show_status("📋 命令已复制")

class MemoCommandList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("font-size:15px;font-family:'Microsoft YaHei',微软雅黑,Arial,sans-serif;background:#f8fafd;border:none;")
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setFixedWidth(320)
        self.detail_widget = None
        self.current_mode = 'file'  # 'file' or 'red' or 'webshell'
        self.all_cmds = []
        self.parent_tab = parent
        self.itemClicked.connect(self.on_item_clicked)
    def set_mode(self, mode):
        self.current_mode = mode
        self.load_data()
        # 自动刷新详情
        if self.count() > 1 and self.detail_widget:
            self.setCurrentRow(1)
            self.detail_widget.show_detail(self.item(1).data(Qt.ItemDataRole.UserRole))
    def load_data(self):
        import os, json
        self.clear()
        if self.current_mode == 'file':
            self.data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'file-download-command.json')
        elif self.current_mode == 'webshell':
            self.data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'WebShell.json')
        else:
            self.data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'redcmd.json')
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.all_cmds = json.load(f)
        except Exception:
            self.all_cmds = []
        self.filter_commands()
    def filter_commands(self, keyword='', os_type='All', encode='None'):
        self.clear()
        # ====== 表头实现 ======
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(8, 0, 8, 0)
        header_layout.setSpacing(0)
        name_header = QLabel("Name")
        name_header.setStyleSheet("font-size:13px;font-weight:bold;padding-left:2px;color:#222;")
        op_header = QLabel("操作")
        op_header.setStyleSheet("font-size:13px;font-weight:bold;color:#222;text-align:right;")
        header_layout.addWidget(name_header)
        header_layout.addStretch()
        header_layout.addWidget(op_header)
        header_widget.setStyleSheet("background:#f7fafd;border-bottom:1px solid #e0e0e0;height:32px;")
        header_item = QListWidgetItem()
        header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        header_item.setSizeHint(header_widget.sizeHint())
        self.addItem(header_item)
        self.setItemWidget(header_item, header_widget)
        # ====== 数据行 ======
        filtered = []
        if self.current_mode == 'webshell':
            # 只对name字段模糊搜索
            passwd = self.parent_tab.pass_edit.text() if self.parent_tab and hasattr(self.parent_tab, 'pass_edit') else 'saury'
            for cmd in self.all_cmds:
                name = cmd.get('name', '').lower()
                if keyword and keyword.lower() not in name:
                    continue
                # 动态替换命令内容中的saury为自定义密码
                cmd_copy = dict(cmd)
                cmd_copy['command'] = cmd_copy.get('command', '').replace('saury', passwd)
                filtered.append(cmd_copy)
        else:
            for cmd in self.all_cmds:
                meta = ','.join(cmd.get('meta', [])) if 'meta' in cmd else cmd.get('os', 'All')
                if os_type != 'All' and os_type not in meta:
                    continue
                text = (cmd.get('name','') + cmd.get('command','') + cmd.get('desc','')).lower()
                if keyword and keyword.lower() not in text:
                    continue
                filtered.append(cmd)
        for idx, cmd in enumerate(filtered):
            item_widget = QWidget()
            layout = QHBoxLayout(item_widget)
            layout.setContentsMargins(8, 0, 8, 0)
            layout.setSpacing(4)
            name_label = QLabel(cmd.get('name', '未命名'))
            name_label.setStyleSheet("font-size:13px;min-width:120px;max-width:240px;")
            name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            layout.addWidget(name_label)
            layout.addStretch()
            # 按钮组整体靠右
            btn_group = QWidget()
            btn_layout = QHBoxLayout(btn_group)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(4)
            edit_btn = QPushButton("编辑")
            edit_btn.setFixedSize(32, 22)
            edit_btn.setStyleSheet('''
                QPushButton {
                    background: #e3f0ff;
                    color: #2196f3;
                    border: none;
                    border-radius: 5px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 0;
                    min-width: 0;
                }
                QPushButton:hover {
                    background: #b6dbff;
                }
            ''')
            edit_btn.clicked.connect(lambda _, r=idx: self.parent_tab.edit_command(r))
            del_btn = QPushButton("移除")
            del_btn.setFixedSize(32, 22)
            del_btn.setStyleSheet('''
                QPushButton {
                    background: #ffdddd;
                    color: #e74c3c;
                    border: none;
                    border-radius: 5px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 0;
                    min-width: 0;
                }
                QPushButton:hover {
                    background: #ffb3b3;
                }
            ''')
            del_btn.clicked.connect(lambda _, r=idx: self.parent_tab.delete_command(r))
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            btn_group.setLayout(btn_layout)
            layout.addWidget(btn_group, 0, Qt.AlignmentFlag.AlignRight)
            item_widget.setLayout(layout)
            # 斑马纹和hover
            bg = '#fff' if idx % 2 == 0 else '#f7fafd'
            item_widget.setStyleSheet(f'''QWidget{{background:{bg};min-height:28px;}} QWidget:hover{{background:#f0f6ff;}}''')
            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, (cmd, encode, idx))
            self.addItem(item)
            self.setItemWidget(item, item_widget)
        # 自动选中首行数据
        if self.count() > 1:
            self.setCurrentRow(1)
            if self.detail_widget:
                self.detail_widget.show_detail(self.item(1).data(Qt.ItemDataRole.UserRole))
    def on_item_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if self.detail_widget and data is not None:
            self.detail_widget.show_detail(data)
    def save_and_refresh(self):
        import json
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.all_cmds, f, ensure_ascii=False, indent=2)
        self.load_data()
    def add_command(self):
        dialog = MemoCommandDialog(self.current_mode, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cmd_data = dialog.get_cmd_data()
            if not cmd_data['name'] or not cmd_data['command']:
                if self.parent_tab:
                    self.parent_tab.show_status("⚠️ 命令名称和内容不能为空！")
                return
            self.all_cmds.append(cmd_data)
            self.save_and_refresh()
            if self.parent_tab:
                self.parent_tab.show_status("✅ 命令已添加")

class MemoCommandDetail(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_tab = parent
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        # 工具名称与表头完全对齐（隐藏标题）
        self.title = QLabel()
        self.title.setFixedHeight(0)
        self.title.setVisible(False)
        layout.addWidget(self.title)
        # 只保留内容显示区域，不再添加任何复制按钮
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet("font-size:15px;background:#fff;border-radius:8px;")
        layout.addWidget(self.text, 1)
        self._cur_row = -1
        self._cur_cmd = None
        self._cur_encode = 'None'
    def copy_command(self):
        if not self._cur_cmd:
            return
        import PyQt6.QtWidgets
        clipboard = PyQt6.QtWidgets.QApplication.clipboard()
        content = self.text.toPlainText()
        clipboard.setText(content)
        if self.parent_tab:
            self.parent_tab.show_status("📋 命令已复制")
    def edit_command(self):
        if self.parent_tab and self._cur_row >= 0:
            self.parent_tab.edit_command(self._cur_row)
    def delete_command(self):
        if self.parent_tab and self._cur_row >= 0:
            self.parent_tab.delete_command(self._cur_row)
    def clear(self):
        self.title.setText("")
        self.text.setPlainText("")
        self._cur_row = -1
        self._cur_cmd = None
        self._cur_encode = 'None'
    def show_detail(self, data):
        if isinstance(data, tuple):
            cmd, encode, row = data
        else:
            cmd, encode, row = data, 'None', -1
        self._cur_cmd = cmd
        self._cur_row = row
        self._cur_encode = encode
        # self.title.setText(cmd.get('name', ''))  # 不再显示标题
        content = cmd.get('command', '')
        # 新增：webshell模式下动态替换密码
        passwd = 'saury'
        if self.parent_tab and hasattr(self.parent_tab, 'parent_tab') and self.parent_tab.parent_tab:
            if hasattr(self.parent_tab.parent_tab, 'pass_edit'):
                passwd = self.parent_tab.parent_tab.pass_edit.text()
        if self.parent_tab and hasattr(self.parent_tab, 'parent_tab') and self.parent_tab.parent_tab and self.parent_tab.parent_tab.list_widget.current_mode == 'webshell':
            content = content.replace('saury', passwd)
        if encode == 'url':
            from urllib.parse import quote
            content = quote(content)
        elif encode == 'base64':
            import base64
            content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        elif encode == '双url':
            from urllib.parse import quote
            content = quote(quote(content))
        self.text.setPlainText(content)

class MemoCommandDialog(QDialog):
    def __init__(self, mode, data=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("添加命令" if data is None else "编辑命令")
        self.setMinimumWidth(600)
        self.setObjectName("addCmdDialog")
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: transparent;")
        # 容器
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("""
            QWidget {
                background: #fdfdfe;
                border-radius: 12px;
            }
        """)
        main_layout.addWidget(container)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 20)
        container_layout.setSpacing(0)
        # 标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        title_text = QLabel("添加命令" if data is None else "编辑命令")
        title_text.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("background: transparent; color: white; border: none; font-size: 18px;")
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        # 拖动支持
        self.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.offset = event.globalPosition().toPoint() - self.pos()
        def mouseMoveEvent(event):
            if self.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self.offset)
        def mouseReleaseEvent(event):
            self.offset = None
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent
        container_layout.addWidget(title_bar)
        # 表单区
        form_layout = QFormLayout()
        form_layout.setContentsMargins(25, 20, 25, 20)
        form_layout.setSpacing(18)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        # 名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入命令名称")
        form_layout.addRow("命令名称:", self.name_edit)
        # 命令内容
        self.cmd_edit = QTextEdit()
        self.cmd_edit.setPlaceholderText("请输入命令内容")
        self.cmd_edit.setMinimumHeight(100)
        form_layout.addRow("命令内容:", self.cmd_edit)
        # 适用系统
        self.os_combo = QComboBox()
        self.os_combo.addItems(["All", "windows", "linux"])
        form_layout.addRow("适用系统:", self.os_combo)
        container_layout.addLayout(form_layout)
        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("✔️ 确定")
        self.cancel_btn = QPushButton("❌ 取消")
        self.save_btn.setFixedSize(120, 40)
        self.cancel_btn.setFixedSize(120, 40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                color: white; border-radius: 20px; font-size: 14px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38f9d7, stop:1 #43e97b); }
        """)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e9ecef; color: #495057; border-radius: 20px; font-size: 14px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: #dee2e6; }
        """)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        container_layout.addLayout(btn_layout)
        # 编辑模式填充
        if data:
            self.name_edit.setText(data.get('name', ''))
            self.cmd_edit.setPlainText(data.get('command', ''))
            meta = data.get('meta', ['All'])
            if meta and isinstance(meta, list):
                self.os_combo.setCurrentText(meta[0])
    def open_config_folder(self):
        import os
        import subprocess
        config_path = os.path.abspath(os.path.dirname(__file__))
        if os.name == 'nt':
            os.startfile(config_path)
        else:
            subprocess.Popen(['xdg-open', config_path])

    def get_cmd_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "command": self.cmd_edit.toPlainText().strip(),
            "meta": [self.os_combo.currentText()]
        }

# ========== 环境变量设置对话框 ==========
class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        print("[DEBUG] 进入SettingsDialog.__init__")
        super().__init__(parent)
        print("[DEBUG] super().__init__ 完成")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumWidth(540)
        self.config = config
        self.setWindowTitle("环境变量配置")
        print("[DEBUG] 基本属性设置完成")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: transparent;")
        print("[DEBUG] main_layout 创建完成")
        # 优化浏览按钮样式（提前定义）
        browse_btn_style = """
            QPushButton {
                background: #fff;
                color: #00c48f;
                font-size: 16px;
                font-weight: bold;
                border: none !important;
                outline: none !important;
                min-width: 48px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: #f2fdfb;
                color: #009e6d;
                border: none !important;
                outline: none !important;
            }
            QPushButton:pressed {
                background: #e6f7f3;
                color: #007a54;
                border: none !important;
                outline: none !important;
            }
        """
        print("[DEBUG] browse_btn_style 定义完成")
        # 容器
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("""
            QWidget {
                background: #fdfdfe;
                border-radius: 14px;
            }
        """)
        main_layout.addWidget(container)
        print("[DEBUG] container 创建并添加到main_layout")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 20)
        container_layout.setSpacing(0)
        print("[DEBUG] container_layout 创建完成")
        # 标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(18, 0, 18, 0)
        title_text = QLabel("环境变量配置")
        title_text.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("background: transparent; color: white; border: none; font-size: 18px;")
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        container_layout.addWidget(title_bar)
        print("[DEBUG] 标题栏创建完成")
        # 表单区
        form_layout = QFormLayout()
        form_layout.setContentsMargins(30, 24, 30, 18)
        form_layout.setSpacing(18)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        print("[DEBUG] form_layout 创建完成")
        # Python
        self.python_edit = QLineEdit()
        self.python_edit.setPlaceholderText("如: C:/Python311/python.exe 或 python")
        self.python_edit.setText(config.python_path or "")
        self.python_btn = QPushButton("📁")
        self.python_btn.setToolTip("选择文件")
        self.python_btn.setFixedSize(60, 32)
        self.python_btn.setStyleSheet(browse_btn_style)
        self.python_btn.clicked.connect(self.browse_python)
        py_layout = QHBoxLayout()
        py_layout.addWidget(self.python_edit)
        py_layout.addWidget(self.python_btn)
        form_layout.addRow("Python路径:", py_layout)
        print("[DEBUG] Python行创建完成")
        # Java8
        self.java8_edit = QLineEdit()
        self.java8_edit.setPlaceholderText("如: C:/Program Files/Java/jdk8/bin/java.exe")
        self.java8_edit.setText(config.java8_path or "")
        self.java8_btn = QPushButton("📁")
        self.java8_btn.setToolTip("选择文件")
        self.java8_btn.setFixedSize(60, 32)
        self.java8_btn.setStyleSheet(browse_btn_style)
        self.java8_btn.clicked.connect(self.browse_java8)
        j8_layout = QHBoxLayout()
        j8_layout.addWidget(self.java8_edit)
        j8_layout.addWidget(self.java8_btn)
        form_layout.addRow("Java8路径:", j8_layout)
        print("[DEBUG] Java8行创建完成")
        # Java11
        self.java11_edit = QLineEdit()
        self.java11_edit.setPlaceholderText("如: C:/Program Files/Java/jdk-11/bin/java.exe")
        self.java11_edit.setText(config.java11_path or "")
        self.java11_btn = QPushButton("📁")
        self.java11_btn.setToolTip("选择文件")
        self.java11_btn.setFixedSize(60, 32)
        self.java11_btn.setStyleSheet(browse_btn_style)
        self.java11_btn.clicked.connect(self.browse_java11)
        j11_layout = QHBoxLayout()
        j11_layout.addWidget(self.java11_edit)
        j11_layout.addWidget(self.java11_btn)
        form_layout.addRow("Java11路径:", j11_layout)
        print("[DEBUG] Java11行创建完成")
        container_layout.addLayout(form_layout)
        print("[DEBUG] 表单区添加完成")
        # ========== 按钮区 ==========
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 18, 0, 0)
        btn_layout.addStretch()
        self.save_btn = QPushButton("保存")
        self.save_btn.setFixedSize(120, 40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #00c48f;
                color: white; border-radius: 20px; font-size: 16px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: #009e6d; }
        """)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(120, 40)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e9ecef; color: #495057; border-radius: 20px; font-size: 16px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: #dee2e6; }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        container_layout.addLayout(btn_layout)

        # 初始化输入框内容
        self.refresh_env_fields()

    def refresh_env_fields(self):
        """刷新环境变量输入框内容"""
        self.python_edit.setText(self.config.python_path or "")
        self.java8_edit.setText(self.config.java8_path or "")
        self.java11_edit.setText(self.config.java11_path or "")

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_env_fields()

    def save_settings(self):
        # 保存输入内容到config
        self.config.python_path = self.python_edit.text().strip()
        self.config.java8_path = self.java8_edit.text().strip()
        self.config.java11_path = self.java11_edit.text().strip()
        self.config.save_config()
        self.accept()

    # ========== 支持窗口拖动 ==========
    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
        except Exception as e:
            pass  # 防止极端情况下拖动报错

    def mouseMoveEvent(self, event):
        try:
            if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
                self.move(event.globalPos() - self._drag_pos)
                event.accept()
        except Exception as e:
            pass

    def browse_python(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择Python解释器", "", "可执行文件 (*.exe);;所有文件 (*)")
        if path:
            self.python_edit.setText(path)
    def browse_java8(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择Java8可执行文件", "", "可执行文件 (*.exe);;所有文件 (*)")
        if path:
            self.java8_edit.setText(path)
    def browse_java11(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择Java11可执行文件", "", "可执行文件 (*.exe);;所有文件 (*)")
        if path:
            self.java11_edit.setText(path)

if __name__ == "__main__":
    logging.info("程序开始运行...")
    app = QApplication(sys.argv)
    logging.info("创建 QApplication 实例...")
    window = MainWindow()
    logging.info("创建主窗口...")
    window.show()
    logging.info("显示主窗口...")
    sys.exit(app.exec()) 
    