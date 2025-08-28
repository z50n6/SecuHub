import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QLineEdit, QSizePolicy
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage

class CyberChefDialog(QDialog):
    """CyberChef 对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CyberChef")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint) # 允许最大化和最小化
        
        self.layout = QVBoxLayout(self)

        self.url_bar = QLineEdit(self)
        self.url_bar.setPlaceholderText("Enter URL or search term")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.layout.addWidget(self.url_bar)

        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl.fromLocalFile(f"{os.path.abspath('project/CyberChef/index.html')}"))
        self.layout.addWidget(self.webview)

        self.nav_layout = QHBoxLayout()
        self.back_button = QPushButton("⬅️ 后退")
        self.back_button.clicked.connect(self.webview.back)
        self.nav_layout.addWidget(self.back_button)

        self.forward_button = QPushButton("➡️ 前进")
        self.forward_button.clicked.connect(self.webview.forward)
        self.nav_layout.addWidget(self.forward_button)

        self.refresh_button = QPushButton("🔄 刷新")
        self.refresh_button.clicked.connect(self.webview.reload)
        self.nav_layout.addWidget(self.refresh_button)

        self.home_button = QPushButton("🏠 主页")
        self.home_button.clicked.connect(self.go_home)
        self.nav_layout.addWidget(self.home_button)
        self.nav_layout.addStretch()

        self.layout.addLayout(self.nav_layout)

        self.webview.urlChanged.connect(self.update_url_bar)
        self.webview.loadFinished.connect(self.update_buttons)
    
    def navigate_to_url(self):
        url_text = self.url_bar.text()
        if not url_text:
            self.go_home()
            return

        if "." in url_text and " " not in url_text: # 简单的判断是否为URL
            if not url_text.startswith(("http://", "https://")):
                url_text = "http://" + url_text
            url = QUrl(url_text)
        else: # 否则进行搜索
            search_url = QUrl(f"https://www.google.com/search?q={QUrl.toPercentEncoding(url_text.strip())}")
            url = search_url
        self.webview.setUrl(url)

    def go_home(self):
        self.webview.setUrl(QUrl.fromLocalFile(f"{os.path.abspath('project/CyberChef/index.html')}"))

    def update_url_bar(self, url):
        self.url_bar.setText(url.toString())

    def update_buttons(self, ok):
        self.back_button.setEnabled(self.webview.history().canGoBack())
        self.forward_button.setEnabled(self.webview.history().canGoForward())
