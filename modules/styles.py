# ========== 现代浅色主题样式 ==========

MODERN_LIGHT_THEME = """
    QMainWindow { background: #fafbfc; }
    QWidget { background: #fafbfc; color: #2c3e50; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
    QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { 
        background: #ffffff; color: #2c3e50; border: 1px solid #e1e8ed; border-radius: 6px; 
        padding: 8px; font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus { 
        border: 2px solid #1da1f2; background: #ffffff; 
    }
    QPushButton, QDialogButtonBox QPushButton, QMessageBox QPushButton { 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1da1f2, stop:1 #0d8bd9); 
        color: #fff; 
        border-radius: 8px; 
        padding: 8px 16px; 
        font-weight: 600; 
        font-size: 13px;
        border: none;
        min-width: 80px;
    }
    QPushButton:hover, QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover { 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d8bd9, stop:1 #1da1f2); 
    }
    QPushButton:pressed, QDialogButtonBox QPushButton:pressed, QMessageBox QPushButton:pressed { 
        background: #0c7bb8; 
    }
    QPushButton:disabled, QDialogButtonBox QPushButton:disabled, QMessageBox QPushButton:disabled {
        background: #b0b0b0;
        color: #f5f5f5;
    }
    QDialog, QMessageBox, QInputDialog {
        background: #fff;
        border-radius: 14px;
    }
    QLabel, QTextBrowser {
        font-family: 'Microsoft YaHei', '微软雅黑', Arial;
    }
    QMenuBar { background: #ffffff; color: #2c3e50; border-bottom: 1px solid #e1e8ed; }
    QMenuBar::item:selected { background: #f7f9fa; border-radius: 4px; }
    QMenu { background: #ffffff; color: #2c3e50; border: 1px solid #e1e8ed; border-radius: 6px; padding: 4px; }
    QMenu::item:selected { background: #f7f9fa; border-radius: 4px; }

    /* 现代化滚动条样式 */
    QScrollBar:vertical {
        width: 8px;
        background: transparent;
        margin: 0px 2px 0px 2px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #d1d5db;
        min-height: 30px;
        border-radius: 4px;
        border: none;
    }
    QScrollBar::handle:vertical:hover {
        background: #9ca3af;
    }
    QScrollBar::handle:vertical:pressed {
        background: #6b7280;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
        background: none;
        border: none;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

    QScrollBar:horizontal {
        height: 8px;
        background: transparent;
        margin: 2px 0px 2px 0px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal {
        background: #d1d5db;
        min-width: 30px;
        border-radius: 4px;
        border: none;
    }
    QScrollBar::handle:horizontal:hover {
        background: #9ca3af;
    }
    QScrollBar::handle:horizontal:pressed {
        background: #6b7280;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
        background: none;
        border: none;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
"""
