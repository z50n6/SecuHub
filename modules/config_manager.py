import os
import json
import logging
from PyQt6.QtCore import QSettings
from collections import defaultdict

class Config:
    """配置管理类"""
    def __init__(self):
        logging.info("初始化配置...")
        self.settings = QSettings("SecuHub", "SecuHub")
        self.config_file = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'config.json')
        # 新增环境变量字段
        self.python_path = ""
        self.java8_path = ""
        self.java11_path = ""
        self.load_config()
    
    def get_data_dir(self):
        """获取data目录的绝对路径"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

    def get_website_data_dir(self):
        """获取data/website目录的绝对路径"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'website')

    def load_config(self):
        """加载配置"""
        logging.info("加载配置...")
        # 定义默认导航项
        default_nav_items = [
            {"id": "safe", "name": "安全工具", "icon": "🛡️"},
            {"id": "code", "name": "编码与解码", "icon": "🔧"},
            {"id": "assist", "name": "辅助工具", "icon": "🛠️"},
            {"id": "webnav", "name": "网站导航", "icon": "🌐"},
            {"id": "vuln_manager", "name": "漏洞库管理", "icon": "🔎"} # 新增漏洞库管理
        ]
        # 首先尝试从JSON文件加载
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tools = data.get("tools", [])
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
            {"id": "assist", "name": "辅助工具", "icon": "🛠️"},
            {"id": "webnav", "name": "网站导航", "icon": "🌐"},
            {"id": "vuln_manager", "name": "漏洞库管理", "icon": "🔎"} # 新增漏洞库管理
        ]
    
        self.tools = self.settings.value("tools", [])
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
            # ===== 新增：保存后校验 =====
            with open(self.config_file, 'r', encoding='utf-8') as f:
                verify_data = json.load(f)
                if verify_data.get("java11_path", "") != self.java11_path or \
                   verify_data.get("python_path", "") != self.python_path or \
                   verify_data.get("java8_path", "") != self.java8_path:
                    return "环境变量保存失败，请检查写入权限或磁盘空间！"
            return None  # 保存成功
        except Exception as e:
            logging.error(f"保存到JSON文件失败: {e}")
            return f"保存到JSON文件失败: {e}"
    
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
