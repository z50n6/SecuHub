import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QMessageBox, QAbstractItemView, QHeaderView,
                             QMenu, QLineEdit, QTextEdit, QLabel, QComboBox,
                             QFileDialog, QFrame, QFormLayout, QSpacerItem,
                             QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from .vuln_data_manager import VulnDataManager
import os
from PyQt6.QtGui import QColor # Added for QColor

class VulnManagerUI(QWidget):
    status_message_signal = pyqtSignal(str, str) # message, type (e.g., 'info', 'success', 'warning', 'error')

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()
        self.load_vulnerabilities()

    def init_ui(self):
        self.setWindowTitle('漏洞库管理')
        self.setStyleSheet("""
            QWidget { 
                font-family: "Microsoft YaHei", 微软雅黑, Arial, sans-serif;
                font-size: 14px;
                color: #333; 
                background-color: #F8F9FA; /* 整体浅灰色背景 */
            }
            /* 表格通用样式 */
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #ECECEC; /* 浅灰色边框 */
                border-radius: 8px;
                gridline-color: #e0e6ed;
                selection-background-color: #e3f0ff; /* 选中行背景 */
                selection-color: #2F54EB; /* 选中行文字颜色为深蓝色 */
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #f0f2f5;
                color: #333; /* 表头文字加深 */
                padding: 6px;
                border: 1px solid #e0e6ed;
                border-bottom: none;
                font-weight: bold; /* 表头文字加粗 */
                font-size: 13px;
            }
            QTableWidgetItem {
                padding: 8px;
                white-space: pre-wrap; /* 自动换行 */
            }
            QTableWidget::item:hover {
                background-color: #F0F2F7; /* 行 hover 时高亮 */
            }

            /* 右侧卡片容器样式 */
            QFrame#RightCardContainer { /* 使用ID选择器防止样式污染 */
                background-color: #ffffff;
                border-radius: 8px;
                /* PyQt不支持box-shadow，这里注释掉，如需类似效果需通过其他方式实现 */
                /* box-shadow: 0 2px 8px rgba(0,0,0,0.05); */
            }

            /* 输入框、文本域、下拉框通用样式 */
            QLineEdit, QTextEdit, QComboBox {
                background-color: #ffffff;
                border: 1px solid #e0e6ed;
                border-radius: 4px; /* 统一为4px圆角 */
                padding: 8px 12px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #2F54EB; /* 聚焦时深蓝色边框 */
                /* box-shadow: 0 0 5px rgba(47, 84, 235, 0.3); */
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
                width: 20px;
            }
            QComboBox::down-arrow {
                /* image: url(resources/arrow_down.png); */ /* 假设有一个向下箭头的图标 */
                width: 12px;
                height: 12px;
            }

            /* 标签样式 */
            QLabel.formLabel { /* 为表单标签定义一个类选择器 */
                font-size: 14px; 
                font-weight: bold; 
                color: #555; 
                margin-top: 5px; /* 调整间距 */
            }
        """
        )

        # 按钮通用样式
        button_base_style = """
            QPushButton {
                border-radius: 4px; /* 统一为4px圆角 */
                padding: 10px 20px;
                font-weight: 500;
                font-size: 14px;
                border: 1px solid transparent;
                min-width: 90px;
                transition: all 0.3s ease;
                /* box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); */
            }
            QPushButton:hover { 
                /* transform: translateY(-2px); */ /* PyQt不支持transform */
                /* box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); */
                opacity: 0.9; /* 悬停时略微透明 */
            }
            QPushButton:pressed {
                /* transform: translateY(1px); */
                opacity: 0.8; 
                /* box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15); */
            }
            QPushButton:disabled {
                background: #cccccc !important;
                color: #f5f5f5 !important;
                /* box-shadow: none; */
            }
        """

        # 主操作按钮 (新增、加载、保存、另存为) 主色调：深蓝色
        add_save_btn_style = button_base_style + """
            QPushButton {
                background: #2F54EB; /* 深蓝色 */
                color: white;
                border-color: #2F54EB;
            }
            QPushButton:hover { 
                background: #406FFF; /* 悬停时颜色变浅 */
                border-color: #406FFF;
            }
        """

        # 删除按钮 红色系
        delete_btn_style = button_base_style + """
            QPushButton {
                background: #FF4D4F; /* 鲜艳红色 */
                color: white;
                border-color: #FF4D4F;
            }
            QPushButton:hover { 
                background: #FF7875;
                border-color: #FF7875;
            }
        """
        
        # 编辑按钮 青色系
        edit_btn_style = button_base_style + """
            QPushButton {
                background: #00BBD3; /* 科技感青色 */
                color: white;
                border-color: #00BBD3;
            }
            QPushButton:hover { 
                background: #33DCEB;
                border-color: #33DCEB;
            }
        """

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 顶部内容区域：包含左侧列表和右侧详情
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15) # 左右面板之间增加间距

        # Left panel for vulnerability list
        left_panel_container = QFrame() # 使用QFrame作为左侧面板的容器，方便样式控制
        left_panel_container.setStyleSheet("background-color: #ffffff; border-radius: 8px; border: 1px solid #ECECEC;")
        left_panel_layout = QVBoxLayout(left_panel_container)
        left_panel_layout.setSpacing(10)
        left_panel_layout.setContentsMargins(15, 15, 15, 15)


        # 添加“漏洞列表”标题
        vuln_list_title = QLabel('漏洞列表')
        vuln_list_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 5px;")
        left_panel_layout.addWidget(vuln_list_title)

        self.vuln_table = QTableWidget()
        self.vuln_table.setColumnCount(4)
        self.vuln_table.setHorizontalHeaderLabels(['序号', '漏洞名称', '风险等级', '漏洞危害'])
        self.vuln_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.vuln_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.vuln_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vuln_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.vuln_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vuln_table.customContextMenuRequested.connect(self.show_context_menu)
        self.vuln_table.itemSelectionChanged.connect(self.display_vuln_details)
        # Table styles are now defined in the global stylesheet at the top
        
        left_panel_layout.addWidget(self.vuln_table)
        content_layout.addWidget(left_panel_container, 1)


        # Right panel for vulnerability details
        right_panel_container = QFrame() # 使用QFrame作为右侧面板的容器，模拟卡片效果
        right_panel_container.setObjectName("RightCardContainer") # 设置ID以便通过QSS选择器定位
        right_panel_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding) # 显式设置垂直扩展策略
        right_panel_layout = QVBoxLayout(right_panel_container)
        right_panel_layout.setContentsMargins(15, 15, 15, 15) # 表单内容内边距
        right_panel_layout.setSpacing(10) # 表单项之间间距

        # 表单内容布局
        details_form_layout = QFormLayout()
        details_form_layout.setContentsMargins(0, 0, 0, 0) # 移除QFormLayout自身的内边距
        details_form_layout.setSpacing(10)
        details_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft) # 标签左对齐
        details_form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft) # 表单内容顶部左对齐


        self.name_label = QLabel('漏洞名称:')
        self.name_label.setProperty('class', 'formLabel') # 设置属性以便通过QSS类选择器定位
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('漏洞名称')

        self.harm_label = QLabel('漏洞危害:')
        self.harm_label.setProperty('class', 'formLabel')
        self.harm_input = QTextEdit()
        self.harm_input.setPlaceholderText('漏洞危害')
        self.harm_input.setFixedHeight(70)

        self.risk_label = QLabel('风险等级:')
        self.risk_label.setProperty('class', 'formLabel')
        self.risk_combo = QComboBox()
        self.risk_combo.addItems(['高危', '中危', '低危'])

        self.desc_label = QLabel('漏洞描述:')
        self.desc_label.setProperty('class', 'formLabel')
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText('漏洞描述')
        self.desc_input.setFixedHeight(100)

        self.sugg_label = QLabel('建议/修复:')
        self.sugg_label.setProperty('class', 'formLabel')
        self.sugg_input = QTextEdit()
        self.sugg_input.setPlaceholderText('建议/修复')
        self.sugg_input.setFixedHeight(100)

        details_form_layout.addRow(self.name_label, self.name_input)
        details_form_layout.addRow(self.harm_label, self.harm_input)
        details_form_layout.addRow(self.risk_label, self.risk_combo)
        details_form_layout.addRow(self.desc_label, self.desc_input)
        details_form_layout.addRow(self.sugg_label, self.sugg_input)
        
        right_panel_layout.addLayout(details_form_layout)
        right_panel_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)) # 确保表单内容垂直占满

        content_layout.addWidget(right_panel_container, 1) # 右侧面板占据更多空间 (例如 1:1 比例)

        main_layout.addLayout(content_layout, 1)

        # 底部操作按钮区域
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.setContentsMargins(0, 0, 0, 0)
        bottom_buttons_layout.setSpacing(10)

        # 左侧的按钮
        self.add_btn = QPushButton('➕ 新增漏洞')
        self.add_btn.clicked.connect(self.add_vuln)
        self.add_btn.setStyleSheet(add_save_btn_style)
        self.delete_btn = QPushButton('🗑️ 删除选中')
        self.delete_btn.clicked.connect(self.delete_selected_vuln)
        self.delete_btn.setStyleSheet(delete_btn_style)
        self.load_yaml_btn = QPushButton('加载 YAML')
        self.load_yaml_btn.clicked.connect(self.load_yaml_file)
        self.load_yaml_btn.setStyleSheet(add_save_btn_style)
        self.save_yaml_btn = QPushButton('保存 YAML')
        self.save_yaml_btn.clicked.connect(self.save_yaml_file)
        self.save_yaml_btn.setStyleSheet(add_save_btn_style)
        self.save_as_yaml_btn = QPushButton('另存为 YAML')
        self.save_as_yaml_btn.clicked.connect(self.save_as_yaml_file)
        self.save_as_yaml_btn.setStyleSheet(add_save_btn_style)

        bottom_buttons_layout.addWidget(self.add_btn)
        bottom_buttons_layout.addWidget(self.delete_btn)
        bottom_buttons_layout.addWidget(self.load_yaml_btn)
        bottom_buttons_layout.addWidget(self.save_yaml_btn)
        bottom_buttons_layout.addWidget(self.save_as_yaml_btn)

        # 将编辑按钮添加到 bottom_buttons_layout 的最右侧
        bottom_buttons_layout.addStretch()
        self.edit_btn = QPushButton('编辑')
        self.edit_btn.clicked.connect(self.edit_vuln)
        self.edit_btn.setStyleSheet(edit_btn_style)
        bottom_buttons_layout.addWidget(self.edit_btn)

        main_layout.addLayout(bottom_buttons_layout)

        self.setLayout(main_layout)

    def _set_buttons_enabled_state(self, enabled):
        self.add_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        self.load_yaml_btn.setEnabled(enabled)
        self.save_yaml_btn.setEnabled(enabled)
        self.save_as_yaml_btn.setEnabled(enabled)
        self.edit_btn.setEnabled(enabled)

    def load_vulnerabilities(self):
        self.vuln_table.setRowCount(0)
        vulnerabilities = self.data_manager.get_all_vulnerabilities()
        self.vuln_table.setRowCount(len(vulnerabilities))
        for i, vuln in enumerate(vulnerabilities):
            # 添加序号列
            self.vuln_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            
            self.vuln_table.setItem(i, 1, QTableWidgetItem(vuln.get('name', '')))
            
            # 使用 QLabel 模拟 badge 效果
            risk_label = QLabel(vuln.get('risklevel', ''))
            risk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            risk_label.setStyleSheet("""
                QLabel {
                    background-color: %s;
                    color: white;
                    border-radius: 8px;
                    padding: 4px 8px; /* 调整内边距，使徽章更宽一点 */
                    font-weight: bold;
                    min-width: 50px; /* 确保最小宽度 */
                }
            """ % (
                "#FF4D4F" if vuln.get('risklevel', '') == '高危' else (
                "#FAAD14" if vuln.get('risklevel', '') == '中危' else (
                "#52C41A" if vuln.get('risklevel', '') == '低危' else "#909399"))
            ))
            self.vuln_table.setCellWidget(i, 2, risk_label)

            harm_text = vuln.get('harm', '')
            harm_item = QTableWidgetItem(harm_text)
            harm_item.setToolTip(harm_text) # 设置tooltip
            self.vuln_table.setItem(i, 3, harm_item)

    def display_vuln_details(self):
        selected_items = self.vuln_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            # 确保获取的是原始数据，因为表格中序号是新增的
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
        new_vuln = {
            'name': '新增漏洞',
            'harm': '',
            'description': '',
            'risklevel': '低危',
            'suggustion': ''
        }
        self.data_manager.add_vulnerability(new_vuln)
        self.load_vulnerabilities()
        self.vuln_table.selectRow(len(self.data_manager.get_all_vulnerabilities()) - 1)
        self.display_vuln_details()
        self.status_message_signal.emit('新漏洞已添加。', 'success')

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

        # reply = QMessageBox.question(self, '确认删除', '您确定要删除选中的漏洞吗？此操作不可撤销。',
        #                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        #
        # if reply == QMessageBox.StandardButton.No:
        #     self.status_message_signal.emit('删除操作已取消。', 'info')
        #     return

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
                self.status_message_signal.emit('漏洞名称已复制到剪贴板。', 'success')
            elif action == copy_desc_action:
                QApplication.clipboard().setText(vuln.get('description', ''))
                self.status_message_signal.emit('漏洞描述已复制到剪贴板。', 'success')
            elif action == copy_sugg_action:
                QApplication.clipboard().setText(vuln.get('suggustion', ''))
                self.status_message_signal.emit('修复建议已复制到剪贴板。', 'success')

    def load_yaml_file(self):
        self._set_buttons_enabled_state(False)
        self.status_message_signal.emit('正在加载 YAML 文件...', 'info')

        file_path, _ = QFileDialog.getOpenFileName(self, "加载 YAML 文件", "", "YAML Files (*.yaml *.yml)")
        if file_path:
            try:
                self.data_manager.file_path = file_path
                self.data_manager.vulnerabilities = self.data_manager._load_data()
                self.load_vulnerabilities()
                self.status_message_signal.emit(f"文件 {os.path.basename(file_path)} 加载成功。", 'success')
            except Exception as e:
                self.status_message_signal.emit(f"加载文件失败: {e}", 'error')
            finally:
                self._set_buttons_enabled_state(True)
        else:
            self._set_buttons_enabled_state(True)
            self.status_message_signal.emit('加载 YAML 文件已取消。', 'info')

    def save_yaml_file(self):
        if not self.data_manager.file_path:
            self.save_as_yaml_file()
            return
        
        self._set_buttons_enabled_state(False)
        self.status_message_signal.emit('正在保存 YAML 文件...', 'info')

        try:
            self.data_manager._save_data()
            self.status_message_signal.emit(f"文件 {os.path.basename(self.data_manager.file_path)} 保存成功。", 'success')
        except Exception as e:
            self.status_message_signal.emit(f"保存文件失败: {e}", 'error')
        finally:
            self._set_buttons_enabled_state(True)

    def save_as_yaml_file(self):
        self._set_buttons_enabled_state(False)
        self.status_message_signal.emit('正在另存为 YAML 文件...', 'info')

        file_path, _ = QFileDialog.getSaveFileName(self, "另存为 YAML 文件", "", "YAML Files (*.yaml *.yml)")
        if file_path:
            try:
                self.data_manager.file_path = file_path
                self.data_manager._save_data()
                self.status_message_signal.emit(f"文件 {os.path.basename(file_path)} 另存为成功。", 'success')
            except Exception as e:
                self.status_message_signal.emit(f"另存为文件失败: {e}", 'error')
            finally:
                self._set_buttons_enabled_state(True)
        else:
            self._set_buttons_enabled_state(True)
            self.status_message_signal.emit('另存为 YAML 文件已取消。', 'info')
