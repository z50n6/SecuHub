import os
import json
from urllib.parse import quote

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QComboBox, QListWidget, QListWidgetItem, QLabel, QTextEdit,
    QDialog, QApplication, QMessageBox, QDialogButtonBox, QFormLayout, QFrame, QMainWindow, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QColor

from modules.dialogs import ConfirmDialog

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
        from modules.config_manager import Config
        self.clear()
        data_dir = Config().get_data_dir()
        if self.current_mode == 'file':
            self.data_path = os.path.join(data_dir, 'file-download-command.json')
        elif self.current_mode == 'webshell':
            self.data_path = os.path.join(data_dir, 'WebShell.json')
        else:
            self.data_path = os.path.join(data_dir, 'RedCmd.json')
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
