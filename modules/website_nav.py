import os
import json
import re
from collections import defaultdict
from urllib.parse import urlparse
import requests

from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QScrollArea, QGridLayout, QSizePolicy,
    QMenu, QDialog, QComboBox, QFormLayout, QCompleter, QFileDialog,
    QMessageBox, QSpacerItem
)
from PyQt6.QtCore import Qt, QUrl, QTimer, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QDesktopServices, QAction
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest

from modules.config_manager import Config
from modules.dialogs import ConfirmDialog
class WebsiteNavWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName("websiteNavWidget")
        self.config = Config()
        self.data = self.load_data()
        self.category_tree = None
        self.card_area = None
        self.card_layout = None
        self.current_category = None
        self.icon_cache_dir = self.config.get_website_data_dir() # 使用Config获取正确路径
        if not os.path.exists(self.icon_cache_dir):
            os.makedirs(self.icon_cache_dir)
        self.init_ui()
        from PyQt6.QtCore import QTimer
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self._do_search(self.search_input.text()) if hasattr(self, 'search_input') else None)

    def load_data(self):
        import json
        import os
        from modules.config_manager import Config
        data_dir = Config().get_data_dir()
        data_path = os.path.join(data_dir, 'website_flat.json')
        if not os.path.exists(data_path):
            return []
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def group_by_category(self):
        from collections import defaultdict
        cats = defaultdict(list)
        for item in self.data:
            cats[item['category']].append(item)
        return cats

    def get_theme_card_style(self):
        # 现代浅色主题卡片样式
        return "background: #fff; color: #2c3e50; border: 1px solid #e1e8ed;"

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 先创建右侧卡片区主部件和布局
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(0)

        # 顶部搜索栏（先于滚动区添加）
        search_bar = QWidget()
        search_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        search_bar.setStyleSheet("""
            QWidget {
                background: #ffffff;
                border-bottom: 1px solid #e9ecef;
            }
        """)
        search_bar_layout = QHBoxLayout(search_bar)
        search_bar_layout.setContentsMargins(10, 8, 10, 8)
        search_bar_layout.setSpacing(8)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 16px; color: #6c757d;")
        search_bar_layout.addWidget(search_icon)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索网站名称、描述或分类...")
        self.search_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #f8f9fa;
                color: #495057;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 8px 10px;
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
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.on_search_enter_pressed)
        self.search_input.installEventFilter(self)
        search_bar_layout.addWidget(self.search_input)
        self.search_stats = QLabel("")
        self.search_stats.setStyleSheet("font-size: 12px; color: #6c757d; padding: 0 8px;")
        search_bar_layout.addWidget(self.search_stats)
        search_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        right_layout.addWidget(search_bar, 0)

        # 滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")
        scroll_content = QWidget()
        self.card_layout = QGridLayout(scroll_content)
        self.card_layout.setSpacing(18)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)

        # 左侧分类树
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setFixedWidth(220)
        self.category_tree.setStyleSheet("""
            QTreeWidget {
                border:none; background:transparent; font-size:13px; font-weight:bold; font-family:'Microsoft YaHei','微软雅黑',Arial;
            }
            QTreeWidget::item {
                height: 36px;
                padding-left: 8px;
                border-radius: 6px;
                margin: 2px 4px;
            }
            QTreeWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                color: #ffffff;
                border: none;
                font-weight: bold;
            }
            QTreeWidget::item:hover {
                background: #f0f9ff;
                color: #1e40af;
                border: none;
            }
        """)
        self.category_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.category_tree.customContextMenuRequested.connect(self.show_category_context_menu)
        self.category_tree.itemClicked.connect(self.on_category_clicked)
        main_layout.addWidget(self.category_tree)
        main_layout.addWidget(right_widget)
        self.setLayout(main_layout)
        self.build_category_tree()
        self.category_tree.expandAll()
        # 默认选中第一个分类
        if self.category_tree.topLevelItemCount() > 0:
            self.category_tree.setCurrentItem(self.category_tree.topLevelItem(0))
            self.on_category_clicked(self.category_tree.topLevelItem(0))
        # 右键菜单（空白区）
        scroll_content.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        scroll_content.customContextMenuRequested.connect(self.show_blank_context_menu)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent, Qt
        if obj == self.search_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.search_input.clear()
                self.on_search_text_changed("")
                return True
        return super().eventFilter(obj, event)

    def on_search_enter_pressed(self):
        self.search_timer.stop()
        self._do_search(self.search_input.text())
    def on_search_text_changed(self, text):
        self.search_timer.start(200)  # 200ms防抖
    def _do_search(self, text):
        text = text.strip().lower()
        if not text:
            self.search_stats.setText("")
            self.refresh_cards()
            return
        results = []
        for item in self.data:
            name = item.get('name', '').lower()
            remark = item.get('remark', '').lower()
            category = item.get('category', '').lower()
            if text in name or text in remark or text in category:
                results.append(item)
        self.refresh_cards(items=results)
        total = len(self.data)
        found = len(results)
        if found == 0:
            self.search_stats.setText(f"未找到匹配的导航 (共 {total} 个)")
        else:
            self.search_stats.setText(f"找到 {found} 个导航 (共 {total} 个)")
    # def on_search_text_changed(self, text):
    #     text = text.strip().lower()
    #     if not text:
    #         # 显示当前分类全部
    #         self.search_stats.setText("")
    #         self.refresh_cards()
    #         return
    #     # 搜索逻辑：名称、描述、分类模糊匹配
    #     results = []
    #     for item in self.data:
    #         name = item.get('name', '').lower()
    #         remark = item.get('remark', '').lower()
    #         category = item.get('category', '').lower()
    #         if text in name or text in remark or text in category:
    #             results.append(item)
    #     self.refresh_cards(items=results)
    #     total = len(self.data)
    #     found = len(results)
    #     if found == 0:
    #         self.search_stats.setText(f"未找到匹配的导航 (共 {total} 个)")
    #     else:
    #         self.search_stats.setText(f"找到 {found} 个导航 (共 {total} 个)")
    def build_category_tree(self):
        self.category_tree.clear()
        cats = self.group_by_category()
        # 支持 type1/type2
        tree = {}
        for cat in cats:
            parts = cat.split('/')
            if len(parts) == 1:
                tree.setdefault(parts[0], {})
            elif len(parts) == 2:
                tree.setdefault(parts[0], {})[parts[1]] = cat
        for k, v in tree.items():
            parent = QTreeWidgetItem([k])
            if v:
                for sub, full in v.items():
                    child = QTreeWidgetItem([sub])
                    child.setData(0, Qt.ItemDataRole.UserRole, full)
                    parent.addChild(child)
            else:
                parent.setData(0, Qt.ItemDataRole.UserRole, k)
            self.category_tree.addTopLevelItem(parent)
        # 默认选中"漏洞平台"
        for i in range(self.category_tree.topLevelItemCount()):
            item = self.category_tree.topLevelItem(i)
            if item.text(0) == "漏洞平台":
                self.category_tree.setCurrentItem(item)
                self.on_category_clicked(item)
                break

    def on_category_clicked(self, item):
        cat = item.data(0, Qt.ItemDataRole.UserRole)
        if not cat:
            cat = item.text(0)
        # 一级分类（有子项）显示所有以cat开头的内容
        if item.childCount() > 0:
            all_items = [d for d in self.data if d['category'].startswith(cat)]
            self.current_category = cat
            self.refresh_cards(items=all_items)
        else:
            self.current_category = cat
            self.refresh_cards()

    def refresh_cards(self, items=None):
        # 清空卡片区
        while self.card_layout.count():
            child = self.card_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        if items is None:
            cats = self.group_by_category()
            items = cats.get(self.current_category, [])
        from collections import defaultdict
        group_map = defaultdict(list)
        for item in items:
            cat = item['category']
            parts = cat.split('/')
            if len(parts) == 2:
                group_map[parts[1]].append(item)
            else:
                group_map[parts[0]].append(item)
        row = 0
        for group, group_items in group_map.items():
            # 分组标题左对齐，间距更协调
            title = QLabel(group)
            title.setStyleSheet("font-size:18px;font-weight:bold;color:#00c48f;margin:18px 0 8px 0;text-align:left;")
            self.card_layout.addWidget(title, row, 0, 1, 6)
            row += 1
            # 卡片流式紧凑排列
            for idx, item in enumerate(group_items):
                card = self.create_card(item)
                r, c = divmod(idx, 6)
                self.card_layout.addWidget(card, row + r, c)
            row += (len(group_items) + 5) // 6
        # 填充空白区域，保证底部对齐
        self.card_layout.setRowStretch(row, 1)
        self.card_layout.setColumnStretch(6, 1)

   
    def create_card(self, item):
        card = QWidget()
        card.setFixedSize(180, 80)
        # 极简风格：无任何边框，hover时只有背景色和阴影
        card.setStyleSheet("""
            QWidget{
                border-radius:14px;
                background:rgba(255,255,255,0.97);
                border:none;
                margin:0;
                transition: box-shadow 0.2s;
            }
            QWidget:hover{
                background:#f2f6fa;
                box-shadow:0 2px 8px 0 rgba(60,60,60,0.08);
                border:none;
            }
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)
        # icon
        icon_label = QLabel()
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background:transparent;")
        self.load_icon(item['icon'], icon_label)
        layout.addWidget(icon_label)
        # 右侧信息
        info_layout = QVBoxLayout()
        name = QLabel(item['name'])
        name.setStyleSheet("font-size:15px;font-weight:bold;color:#222;")
        remark = QLabel(item.get('remark', ''))
        remark.setStyleSheet("font-size:11px;color:#888;")
        remark.setWordWrap(True)
        info_layout.addWidget(name)
        info_layout.addWidget(remark)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(lambda pos, i=item: self.show_card_context_menu(card, i, pos))
        card.mouseDoubleClickEvent = lambda e, url=item['url']: self.open_url(url)
        return card
    def load_icon(self, icon_path, label):
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        import os
        import hashlib
        # 统一本地缓存
        if icon_path.startswith('http'):
            ext = os.path.splitext(icon_path)[-1]
            if not ext or len(ext) > 5:
                ext = '.ico'
            fname = hashlib.md5(icon_path.encode('utf-8')).hexdigest() + ext
            local_path = os.path.join(self.icon_cache_dir, fname)
            if not os.path.exists(local_path):
                try:
                    resp = requests.get(icon_path, timeout=3)
                    with open(local_path, 'wb') as f:
                        f.write(resp.content)
                except Exception:
                    label.setText('🌐')
                    return
            if os.path.exists(local_path):
                pixmap = QPixmap(local_path)
                if not pixmap.isNull():
                    label.setPixmap(pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                else:
                    label.setText('🌐')
            else:
                label.setText('🌐')
        else:
            local_path = icon_path
            if not os.path.isabs(local_path):
                local_path = os.path.join(os.path.dirname(__file__), 'data', 'Icon', icon_path)
            if os.path.exists(local_path):
                pixmap = QPixmap(local_path)
                if not pixmap.isNull():
                    label.setPixmap(pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                else:
                    label.setText('🖼️')
            else:
                label.setText('🖼️')

    def show_card_context_menu(self, card, item, pos):
        menu = QMenu(card)
        edit_action = QAction('✏️ 编辑', card)
        delete_action = QAction('🗑️ 删除', card)
        edit_action.triggered.connect(lambda: self.edit_nav(item))
        delete_action.triggered.connect(lambda: self.delete_nav(item))
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec(card.mapToGlobal(pos))
    def show_category_context_menu(self, pos):
        item = self.category_tree.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        del_action = QAction("🗑️ 删除该分类下所有网址", self)
        del_action.triggered.connect(lambda: self.delete_category_urls(item))
        menu.addAction(del_action)
        menu.exec(self.category_tree.viewport().mapToGlobal(pos))
    def delete_category_urls(self, item):
        # 判断一级还是二级
        if item.parent() is None:
            # 一级分类
            cat = item.text(0)
            # 删除所有以cat开头的
            before = len(self.data)
            self.data = [d for d in self.data if not d['category'].startswith(cat)]
            after = len(self.data)
            msg = f"已删除 {before - after} 条属于“{cat}”的导航"
        else:
            # 二级分类
            parent_cat = item.parent().text(0)
            sub_cat = item.text(0)
            full_cat = f"{parent_cat}/{sub_cat}"
            before = len(self.data)
            self.data = [d for d in self.data if d['category'] != full_cat]
            after = len(self.data)
            # msg = f"已删除 {before - after} 条属于“{full_cat}”的导航"
            # msg = f"🗑️ 已删除 {before - after} 条属于“{cat}”的导航"
            msg = f"🗑️ 已删除 {before - after} 条属于“{full_cat}”的导航"
        
        self.save_data()
        self.data = self.load_data()
        self.build_category_tree()
        self.category_tree.expandAll()
        self.refresh_cards()
        # 状态栏提示替代弹窗
        mainwin = self.window()
        if hasattr(mainwin, 'statusBar') and mainwin.statusBar():
            mainwin.statusBar().showMessage(msg, 8000)
        else:
            from PyQt6.QtWidgets import QToolTip
            QToolTip.showText(self.mapToGlobal(self.rect().center()), msg, self, self.rect(), 4000)

    def show_blank_context_menu(self, pos):
        menu = QMenu(self)
        add_action = QAction('➕ 添加新导航', self)
        add_action.triggered.connect(self.add_nav)
        menu.addAction(add_action)
        menu.exec(self.mapToGlobal(pos))

    def open_url(self, url):
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))

    def edit_nav(self, item):
        # 弹窗编辑，保存后刷新
        dialog = WebsiteNavEditDialog(self, categories={d['category'] for d in self.data}, data=item)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            # 找到并替换原数据
            for i, d in enumerate(self.data):
                if d is item or (d['category'] == item['category'] and d['name'] == item['name'] and d['url'] == item['url']):
                    self.data[i] = new_data
                    break
            self.save_data()
            # 重新加载数据并刷新界面
            self.data = self.load_data()
            self.build_category_tree()
            self.category_tree.expandAll()
            # 重新选中当前分类
            if self.current_category:
                self.refresh_cards()
            else:
                # 默认选中第一个分类
                if self.category_tree.topLevelItemCount() > 0:
                    self.category_tree.setCurrentItem(self.category_tree.topLevelItem(0))
                    self.on_category_clicked(self.category_tree.topLevelItem(0))

    def delete_nav(self, item):
        # 优化删除后保存并刷新，弹窗UI更友好
        dlg = ConfirmDialog(
            self,
            title="⚠️ 确认删除",
            content=(
                f"<div style='font-size:16px;line-height:1.8;'>"
                f"确定要<strong style='color:#ff4d4f;'>永久删除</strong>导航<br>"
                f"<span style='color:#43e97b;font-weight:bold;font-size:18px;'>『{item['name']}』</span> 吗？"
                f"<br><span style='color:gray;font-size:13px;'>{item['url']}</span>"
                f"</div>"
            ),
            icon="🗑️",
            yes_text="是，永久删除",
            no_text="取消操作"
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.data = [d for d in self.data if not (d['category'] == item['category'] and d['name'] == item['name'] and d['url'] == item['url'])]
            self.save_data()
            # 重新加载数据并刷新界面
            self.data = self.load_data()
            self.build_category_tree()
            self.category_tree.expandAll()
            # 重新选中当前分类
            if self.current_category:
                self.refresh_cards()
            else:
                # 默认选中第一个分类
                if self.category_tree.topLevelItemCount() > 0:
                    self.category_tree.setCurrentItem(self.category_tree.topLevelItem(0))
                    self.on_category_clicked(self.category_tree.topLevelItem(0))

    def add_nav(self):
        # 弹窗添加，保存后刷新
        dialog = WebsiteNavEditDialog(self, categories={d['category'] for d in self.data})
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            self.data.append(new_data)
            self.save_data()
            # 重新加载数据并刷新界面
            self.data = self.load_data()
            self.build_category_tree()
            self.category_tree.expandAll()
            # 重新选中当前分类
            if self.current_category:
                self.refresh_cards()
            else:
                # 默认选中第一个分类
                if self.category_tree.topLevelItemCount() > 0:
                    self.category_tree.setCurrentItem(self.category_tree.topLevelItem(0))
                    self.on_category_clicked(self.category_tree.topLevelItem(0))

    def save_data(self):
        import json
        import os
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'website_flat.json')
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
class IconLoader(QObject):
    icon_loaded = pyqtSignal(QPixmap, QLabel)

    def __init__(self, url, label):
        super().__init__()
        self.url = url
        self.label = label

    def run(self):
        try:
            resp = requests.get(self.url, timeout=3)
            pixmap = QPixmap()
            pixmap.loadFromData(resp.content)
            self.icon_loaded.emit(pixmap, self.label)
        except Exception:
            pass

class WebsiteNavEditDialog(QDialog):
    def __init__(self, parent=None, categories=None, data=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("网站导航编辑" if data else "添加网站导航")
        self.setMinimumWidth(600)
        self.categories = categories or []

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: transparent;")

        # 卡片容器
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("""
            QWidget {
                background: #fff;
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
        title_text = QLabel("网站导航编辑" if data else "添加网站导航")
        title_text.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: white; border: none; font-size: 18px; }
            QPushButton:hover { background: rgba(255,255,255,0.32); }
            QPushButton:pressed { background: rgba(0,0,0,0.12); }
        """)
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

        # 分类
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.categories)
        self.category_combo.setEditable(True)
        form_layout.addRow("分类:", self.category_combo)
        # 名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入网站名称")
        form_layout.addRow("名称:", self.name_edit)
        # 描述
        self.remark_edit = QLineEdit()
        self.remark_edit.setPlaceholderText("可选，网站描述信息")
        form_layout.addRow("描述:", self.remark_edit)
        # 网址
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("请输入网址，如 https://xxx.com")
        form_layout.addRow("网址:", self.url_edit)
        # 图标
        icon_layout = QHBoxLayout()
        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("可选，支持本地或网络图片")
        self.icon_btn = QPushButton("选择图片")
        self.icon_btn.setFixedSize(40, 40)
        self.icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_btn.clicked.connect(self.choose_icon)
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(self.icon_btn)
        form_layout.addRow("图标:", icon_layout)
        container_layout.addLayout(form_layout)

        # 按钮区
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

        # 编辑模式填充
        if data:
            self.category_combo.setCurrentText(data.get('category', ''))
            self.name_edit.setText(data.get('name', ''))
            self.remark_edit.setText(data.get('remark', ''))
            self.url_edit.setText(data.get('url', ''))
            self.icon_edit.setText(data.get('icon', ''))

    def choose_icon(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "选择图标", "", "图标文件 (*.ico *.png *.jpg *.jpeg);;所有文件 (*)")
        if path:
            
            self.icon_edit.setText(path)
