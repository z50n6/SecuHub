# ToolCard 右键菜单功能说明

## 功能概述

为工具卡片（ToolCard）添加了完整的右键菜单功能，提供丰富的工具管理操作。

## 右键菜单选项

### 🚀 启动工具
- **功能**: 启动选中的工具
- **快捷键**: 双击卡片也可以启动
- **说明**: 与启动按钮功能相同

### ✏️ 编辑工具
- **功能**: 打开工具编辑对话框
- **支持修改**: 
  - 工具名称
  - 工具路径
  - 工具类型
  - 分类
  - 启动参数
  - 图标路径
  - 描述信息
- **说明**: 编辑后自动保存并刷新界面

### 📂 打开文件路径
- **功能**: 根据工具类型智能打开路径
- **支持类型**:
  - URL: 直接打开网页
  - 文件夹: 打开文件夹
  - 文件: 打开文件所在目录并选中文件
- **说明**: 使用Windows资源管理器

### 📁 打开所在文件夹
- **功能**: 打开工具文件所在的文件夹
- **说明**: 适用于所有工具类型

### 💻 打开命令行
- **功能**: 在工具所在目录打开命令行
- **支持终端**:
  1. Windows Terminal (优先)
  2. PowerShell Core
  3. Windows PowerShell
  4. Command Prompt
- **说明**: 自动检测可用的终端程序

### 📋 复制路径
- **功能**: 复制工具路径到剪贴板
- **说明**: 方便在其他程序中使用

### 📄 复制工具信息
- **功能**: 复制完整的工具信息到剪贴板
- **包含信息**:
  - 工具名称
  - 类型
  - 分类
  - 描述
  - 路径
  - 启动次数
  - 最后启动时间

### 🗑️ 删除工具
- **功能**: 删除工具（带确认对话框）
- **说明**: 删除后自动刷新界面

## 技术实现

### 核心类修改

#### ToolCard 类
```python
class ToolCard(QWidget):
    def __init__(self, tool, launch_callback=None, parent=None):
        # 启用自定义右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def show_context_menu(self, position):
        # 创建并显示右键菜单
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction, QDesktopServices
        from PyQt6.QtCore import QUrl
```

#### MainWindow 类
```python
class MainWindow(QMainWindow):
    def edit_tool_card(self, tool):
        # 处理工具编辑
        
    def delete_tool_card(self, tool):
        # 处理工具删除
```

### 菜单样式

右键菜单采用现代化设计：
- 白色背景
- 圆角边框
- 悬停效果
- 图标标识
- 分隔线

## 使用方法

1. **右键点击工具卡片** - 显示完整菜单
2. **双击卡片** - 快速启动工具
3. **选择菜单项** - 执行相应操作

## 兼容性

- ✅ 支持所有工具类型
- ✅ 兼容现有工具数据
- ✅ 自动保存配置
- ✅ 界面自动刷新

## 测试验证

运行测试脚本验证功能：
```bash
python final_test.py
```

## 注意事项

1. **删除操作不可撤销** - 删除前会显示确认对话框
2. **路径验证** - 打开文件夹前会验证路径是否存在
3. **终端检测** - 自动检测系统中可用的终端程序
4. **权限要求** - 某些操作可能需要管理员权限

## 更新日志

- **2025-06-21**: 添加完整的右键菜单功能
  - 支持编辑、删除、路径操作
  - 添加命令行打开功能
  - 支持复制工具信息
  - 优化菜单样式和用户体验
  - **修复导入错误** - 将QAction从PyQt6.QtGui正确导入

## 问题修复

### 导入错误修复
- **问题**: `ImportError: cannot import name 'QAction' from 'PyQt6.QtWidgets'`
- **原因**: QAction应该从PyQt6.QtGui导入，而不是PyQt6.QtWidgets
- **修复**: 更新导入语句为 `from PyQt6.QtGui import QAction, QDesktopServices`
- **状态**: ✅ 已修复

### 方法缺失修复
- **问题**: `AttributeError: 'ToolCard' object has no attribute 'show_context_menu'`
- **原因**: ToolCard类缺少右键菜单相关方法
- **修复**: 添加完整的右键菜单方法和相关功能
- **状态**: ✅ 已修复 