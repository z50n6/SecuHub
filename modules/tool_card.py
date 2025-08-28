import os
import subprocess
import logging
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMenu, QApplication, QMessageBox, QDialog
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices, QAction
from modules.dialogs import ConfirmDialog
class ToolCard(QWidget):
    """自定义工具卡片（与最近启动工具UI保持一致）"""
    _ICON_MAP = {
        "exe": "⚙️",
        "cmd": "🖥️",  # 或其它命令行图标
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
