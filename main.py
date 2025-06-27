"""
SecuHub 主入口文件
模块化重构后的应用程序入口点
"""

import sys
import os
import logging
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

# 导入核心模块
from core import Config, ThemeManager, Tool, CacheManager

# 导入工作线程模块
from workers import (
    PipInstallerWorker, SearchWorker, IconLoaderWorker, 
    ToolLauncherWorker, ConfigSaverWorker, ProcessMonitorWorker
)

# 导入工具模块
from utils import extract_icon_from_exe, ClipboardBridge

# 导入UI模块
from ui import (
    ConfirmDialog, CyberChefDialog, AddToolDialog, 
    AddDownloadCommandDialog, MemoCommandDialog,
    ToolCard, MemoTabWidget, MemoCommandList, MemoCommandDetail,
    MainWindow
)

# 配置路径
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# 日志初始化
def setup_logging():
    """设置日志系统"""
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

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logging.info("启动 SecuHub 应用程序...")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("SecuHub")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("SecuHub")
    
    # 初始化核心组件
    logging.info("初始化核心组件...")
    config = Config()
    theme_manager = ThemeManager()
    cache_manager = CacheManager()
    
    # 创建主窗口
    logging.info("创建主窗口...")
    window = MainWindow()
    
    # 应用主题
    theme_manager.load_theme(config.theme)
    
    # 显示窗口
    window.show()
    logging.info("应用程序启动完成")
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 