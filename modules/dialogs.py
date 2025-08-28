from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import Qt
# ========== 全局唯一美化弹窗 ConfirmDialog ==========

class ConfirmDialog(QDialog):
    def __init__(self, parent=None, title="提示", content="操作成功", icon="ℹ️", yes_text="确定", no_text=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumWidth(400)
        self.content_widget = QWidget(self)  # 假设你有这样一个内容区

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("QWidget { border: none; }")
        # self.setStyleSheet("background: transparent;")
        # self.content_widget.setStyleSheet("border: none;")        # 极简卡片容器
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("""
            QWidget {
                background: #fff;
                border-radius: 12px;
                /*border: 1px solid #e0e0e0;*/
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
