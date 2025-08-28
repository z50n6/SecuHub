import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QMessageBox, QAbstractItemView, QHeaderView,
                             QMenu, QLineEdit, QTextEdit, QLabel, QComboBox,
                             QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from .vuln_data_manager import VulnDataManager
import os

class VulnManagerUI(QWidget):
    status_message_signal = pyqtSignal(str, str) # message, type (e.g., 'info', 'success', 'warning', 'error')

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()
        self.load_vulnerabilities()

    def init_ui(self):
        self.setWindowTitle('漏洞库管理')

        button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1da1f2, stop:1 #0d8bd9); /* 蓝色渐变 */
                color: #fff;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d8bd9, stop:1 #1da1f2); /* 鼠标悬停时反转渐变或略有变化 */
            }
            QPushButton:pressed {
                background: #0c7bb8; /* 按下时的深蓝色 */
            }
            QPushButton:disabled {
                background: #b0b0b0;
                color: #f5f5f5;
            }
        """

        main_layout = QHBoxLayout()

        # Left panel for vulnerability list
        left_panel = QVBoxLayout()
        self.vuln_table = QTableWidget()
        self.vuln_table.setColumnCount(3) # 漏洞名称, 风险等级, 漏洞危害
        self.vuln_table.setHorizontalHeaderLabels(['漏洞名称', '风险等级', '漏洞危害'])
        self.vuln_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.vuln_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.vuln_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vuln_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vuln_table.customContextMenuRequested.connect(self.show_context_menu)
        self.vuln_table.itemSelectionChanged.connect(self.display_vuln_details)


        left_panel.addWidget(self.vuln_table)

        # Buttons for list management
        list_buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton('新增漏洞')
        self.add_btn.clicked.connect(self.add_vuln)
        self.add_btn.setStyleSheet(button_style)
        self.delete_btn = QPushButton('删除选中')
        self.delete_btn.clicked.connect(self.delete_selected_vuln)
        self.delete_btn.setStyleSheet(button_style)
        self.load_yaml_btn = QPushButton('加载 YAML')
        self.load_yaml_btn.clicked.connect(self.load_yaml_file)
        self.load_yaml_btn.setStyleSheet(button_style)
        self.save_yaml_btn = QPushButton('保存 YAML')
        self.save_yaml_btn.clicked.connect(self.save_yaml_file)
        self.save_yaml_btn.setStyleSheet(button_style)
        self.save_as_yaml_btn = QPushButton('另存为 YAML')
        self.save_as_yaml_btn.clicked.connect(self.save_as_yaml_file)
        self.save_as_yaml_btn.setStyleSheet(button_style)
        list_buttons_layout.addWidget(self.add_btn)
        list_buttons_layout.addWidget(self.delete_btn)
        list_buttons_layout.addWidget(self.load_yaml_btn)
        list_buttons_layout.addWidget(self.save_yaml_btn)
        list_buttons_layout.addWidget(self.save_as_yaml_btn)
        list_buttons_layout.addStretch() # 新增这一行
        left_panel.addLayout(list_buttons_layout)


        # Right panel for vulnerability details
        right_panel = QVBoxLayout()
        
        self.name_label = QLabel('漏洞名称:')
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('漏洞名称')

        self.harm_label = QLabel('漏洞危害:')
        self.harm_input = QTextEdit()
        self.harm_input.setPlaceholderText('漏洞危害')
        self.harm_input.setFixedHeight(50)

        self.risk_label = QLabel('风险等级:')
        self.risk_combo = QComboBox()
        self.risk_combo.addItems(['高危', '中危', '低危'])


        self.desc_label = QLabel('漏洞描述:')
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText('漏洞描述')


        self.sugg_label = QLabel('建议/修复:')
        self.sugg_input = QTextEdit()
        self.sugg_input.setPlaceholderText('建议/修复')

        right_panel.addWidget(self.name_label)
        right_panel.addWidget(self.name_input)
        right_panel.addWidget(self.harm_label)
        right_panel.addWidget(self.harm_input)
        right_panel.addWidget(self.risk_label)
        right_panel.addWidget(self.risk_combo)
        right_panel.addWidget(self.desc_label)
        right_panel.addWidget(self.desc_input)
        right_panel.addWidget(self.sugg_label)
        right_panel.addWidget(self.sugg_input)
        
        # 重新添加编辑按钮到右侧面板的底部
        edit_details_btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton('编辑')
        self.edit_btn.clicked.connect(self.edit_vuln)
        self.edit_btn.setStyleSheet(button_style)
        edit_details_btn_layout.addWidget(self.edit_btn)
        right_panel.addLayout(edit_details_btn_layout)
        
        # right_panel.addStretch() # 将所有内容推到顶部，使底部的按钮与最下端对齐 (删除这一行)


        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 3) # 右侧面板占据更多空间 (例如 1:3 比例)

        self.setLayout(main_layout)

    def load_vulnerabilities(self):
        self.vuln_table.setRowCount(0)
        vulnerabilities = self.data_manager.get_all_vulnerabilities()
        self.vuln_table.setRowCount(len(vulnerabilities))
        for i, vuln in enumerate(vulnerabilities):
            self.vuln_table.setItem(i, 0, QTableWidgetItem(vuln.get('name', '')))
            self.vuln_table.setItem(i, 1, QTableWidgetItem(vuln.get('risklevel', '')))
            self.vuln_table.setItem(i, 2, QTableWidgetItem(vuln.get('harm', '')))

    def display_vuln_details(self):
        selected_items = self.vuln_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            vuln = self.data_manager.get_vulnerability_by_index(row)
            if vuln:
                self.name_input.setText(vuln.get('name', ''))
                self.harm_input.setText(vuln.get('harm', ''))
                self.risk_combo.setCurrentText(vuln.get('risklevel', ''))
                self.desc_input.setText(vuln.get('description', ''))
                self.sugg_input.setText(vuln.get('suggustion', ''))
        else:
            self.clear_detail_fields()

    def clear_detail_fields(self):
        self.name_input.clear()
        self.harm_input.clear()
        self.risk_combo.setCurrentIndex(0)
        self.desc_input.clear()
        self.sugg_input.clear()

    def add_vuln(self):
        # For simplicity, adding a blank vulnerability. User can then edit it.
        new_vuln = {
            'name': '新增漏洞',
            'harm': '',
            'description': '',
            'risklevel': '低危',
            'suggustion': ''
        }
        self.data_manager.add_vulnerability(new_vuln)
        self.load_vulnerabilities()
        # Select the newly added row
        self.vuln_table.selectRow(len(self.data_manager.get_all_vulnerabilities()) - 1)
        self.display_vuln_details()


    def edit_vuln(self):
        selected_items = self.vuln_table.selectedItems()
        if not selected_items:
            self.status_message_signal.emit('请选择一个漏洞进行编辑。', 'warning')
            return

        row = selected_items[0].row()
        new_vuln_data = {
            'name': self.name_input.text(),
            'harm': self.harm_input.toPlainText(),
            'description': self.desc_input.toPlainText(),
            'risklevel': self.risk_combo.currentText(),
            'suggustion': self.sugg_input.toPlainText()
        }
        self.data_manager.update_vulnerability(row, new_vuln_data)
        self.load_vulnerabilities()
        self.status_message_signal.emit('漏洞信息已更新。', 'success')

    def delete_selected_vuln(self):
        selected_items = self.vuln_table.selectedItems()
        if not selected_items:
            self.status_message_signal.emit('请选择一个漏洞进行删除。', 'warning')
            return

        row = selected_items[0].row()
        self.data_manager.delete_vulnerability(row)
        self.load_vulnerabilities()
        self.clear_detail_fields()
        self.status_message_signal.emit('漏洞已删除。', 'success')

    def show_context_menu(self, pos):
        item = self.vuln_table.itemAt(pos)
        if item:
            menu = QMenu(self)
            copy_name_action = menu.addAction('复制漏洞名称')
            copy_desc_action = menu.addAction('复制漏洞描述')
            copy_sugg_action = menu.addAction('复制修复建议')
            
            action = menu.exec(self.vuln_table.mapToGlobal(pos))

            row = item.row()
            vuln = self.data_manager.get_vulnerability_by_index(row)

            if action == copy_name_action:
                QApplication.clipboard().setText(vuln.get('name', ''))
            elif action == copy_desc_action:
                QApplication.clipboard().setText(vuln.get('description', ''))
            elif action == copy_sugg_action:
                QApplication.clipboard().setText(vuln.get('suggustion', ''))

    def load_yaml_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "加载 YAML 文件", "", "YAML Files (*.yaml *.yml)")
        if file_path:
            try:
                self.data_manager.file_path = file_path # 更新数据管理器的文件路径
                self.data_manager.vulnerabilities = self.data_manager._load_data() # 重新加载数据
                self.load_vulnerabilities()
                self.status_message_signal.emit(f"文件 {os.path.basename(file_path)} 加载成功。", 'success')
            except Exception as e:
                self.status_message_signal.emit(f"加载文件失败: {e}", 'error')

    def save_yaml_file(self):
        if not self.data_manager.file_path:
            self.save_as_yaml_file()
            return
        try:
            self.data_manager._save_data()
            self.status_message_signal.emit(f"文件 {os.path.basename(self.data_manager.file_path)} 保存成功。", 'success')
        except Exception as e:
            self.status_message_signal.emit(f"保存文件失败: {e}", 'error')

    def save_as_yaml_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "另存为 YAML 文件", "", "YAML Files (*.yaml *.yml)")
        if file_path:
            try:
                self.data_manager.file_path = file_path # 更新数据管理器的文件路径
                self.data_manager._save_data()
                self.status_message_signal.emit(f"文件 {os.path.basename(file_path)} 另存为成功。", 'success')
            except Exception as e:
                self.status_message_signal.emit(f"另存为文件失败: {e}", 'error')
