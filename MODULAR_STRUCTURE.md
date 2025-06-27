# SecuHub 模块化结构说明

## 概述

SecuHub 已从单一的大型 `launcher.py` 文件重构为模块化结构，提高了代码的可维护性、可读性和可扩展性。

## 目录结构

```
SecuHub/
├── main.py                    # 主入口文件
├── launcher.py               # 原始文件（保留作为备份）
├── core/                     # 核心模块
│   ├── __init__.py
│   ├── config.py            # 配置管理
│   ├── theme_manager.py     # 主题管理
│   ├── tool.py              # 工具类定义
│   └── cache_manager.py     # 缓存管理
├── workers/                  # 工作线程模块
│   ├── __init__.py
│   ├── pip_installer.py     # pip安装器
│   ├── search_worker.py     # 搜索工作线程
│   ├── icon_loader.py       # 图标加载器
│   ├── tool_launcher.py     # 工具启动器
│   ├── config_saver.py      # 配置保存器
│   └── process_monitor.py   # 进程监控器
├── ui/                       # 用户界面模块
│   ├── __init__.py
│   ├── dialogs.py           # 对话框类
│   ├── widgets.py           # 自定义组件
│   └── main_window.py       # 主窗口
├── utils/                    # 工具模块
│   ├── __init__.py
│   ├── icon_extractor.py    # 图标提取
│   └── clipboard_bridge.py  # 剪贴板桥接
└── 其他文件和目录...
```

## 模块说明

### 1. 核心模块 (core/)

#### `config.py`
- **功能**: 配置管理
- **主要类**: `Config`
- **职责**: 
  - 加载/保存配置文件
  - 管理应用程序设置
  - 处理最近使用记录
  - 管理搜索历史

#### `theme_manager.py`
- **功能**: 主题管理
- **主要类**: `ThemeManager`
- **职责**:
  - 自动发现可用主题
  - 加载主题文件
  - 管理主题显示名称

#### `tool.py`
- **功能**: 工具类定义
- **主要类**: `Tool`
- **职责**:
  - 定义工具数据结构
  - 提供序列化/反序列化方法

#### `cache_manager.py`
- **功能**: 缓存管理
- **主要类**: `CacheManager`
- **职责**:
  - 提供LRU缓存功能
  - 优化性能

### 2. 工作线程模块 (workers/)

#### `pip_installer.py`
- **功能**: Python包安装
- **主要类**: `PipInstallerWorker`
- **职责**:
  - 在后台安装Python依赖
  - 处理requirements.txt文件
  - 提供安装进度反馈

#### `search_worker.py`
- **功能**: 搜索功能
- **主要类**: `SearchWorker`
- **职责**:
  - 在后台执行工具搜索
  - 实现智能搜索算法
  - 按相关性排序结果

#### `icon_loader.py`
- **功能**: 图标加载
- **主要类**: `IconLoaderWorker`
- **职责**:
  - 异步加载工具图标
  - 优化UI响应性能

#### `tool_launcher.py`
- **功能**: 工具启动
- **主要类**: `ToolLauncherWorker`
- **职责**:
  - 启动各种类型的工具
  - 处理依赖检查
  - 错误处理和反馈

#### `config_saver.py`
- **功能**: 配置保存
- **主要类**: `ConfigSaverWorker`
- **职责**:
  - 异步保存配置
  - 防止UI阻塞

#### `process_monitor.py`
- **功能**: 进程监控
- **主要类**: `ProcessMonitorWorker`
- **职责**:
  - 监控已启动的进程
  - 跟踪进程状态变化

### 3. 用户界面模块 (ui/)

#### `dialogs.py`
- **功能**: 对话框组件
- **主要类**:
  - `ConfirmDialog`: 确认对话框
  - `CyberChefDialog`: CyberChef工具对话框
  - `AddToolDialog`: 添加工具对话框
  - `AddDownloadCommandDialog`: 下载命令对话框
  - `MemoCommandDialog`: 备忘录命令对话框

#### `widgets.py`
- **功能**: 自定义组件
- **主要类**:
  - `ToolCard`: 工具卡片组件
  - `MemoTabWidget`: 备忘录标签页组件
  - `MemoCommandList`: 备忘录命令列表
  - `MemoCommandDetail`: 备忘录命令详情

#### `main_window.py`
- **功能**: 主窗口
- **主要类**: `MainWindow`
- **职责**:
  - 应用程序主界面
  - 协调各个模块
  - 处理用户交互

### 4. 工具模块 (utils/)

#### `icon_extractor.py`
- **功能**: 图标提取
- **主要函数**: `extract_icon_from_exe()`
- **职责**:
  - 从EXE文件中提取图标
  - 保存为PNG格式

#### `clipboard_bridge.py`
- **功能**: 剪贴板桥接
- **主要类**: `ClipboardBridge`
- **职责**:
  - 提供给JavaScript的剪贴板接口
  - 跨语言数据传递

## 优势

### 1. 可维护性
- 代码按功能分组，易于定位和修改
- 每个模块职责单一，降低复杂度
- 清晰的依赖关系

### 2. 可扩展性
- 新功能可以独立添加到相应模块
- 模块间松耦合，便于扩展
- 支持插件化架构

### 3. 可测试性
- 每个模块可以独立测试
- 便于编写单元测试
- 提高代码质量

### 4. 团队协作
- 不同开发者可以并行开发不同模块
- 减少代码冲突
- 提高开发效率

## 迁移指南

### 从原始文件迁移
1. 保留原始的 `launcher.py` 作为备份
2. 使用新的 `main.py` 作为入口点
3. 根据需要逐步迁移功能到相应模块

### 添加新功能
1. 确定功能所属的模块类别
2. 在相应模块中添加代码
3. 更新模块的 `__init__.py` 文件
4. 在主窗口中集成新功能

## 注意事项

1. **导入路径**: 确保所有模块的导入路径正确
2. **依赖关系**: 注意模块间的依赖关系，避免循环导入
3. **配置管理**: 统一使用 `Config` 类管理配置
4. **错误处理**: 在各个模块中实现适当的错误处理
5. **日志记录**: 使用统一的日志系统记录信息

## 未来计划

1. 添加更多单元测试
2. 实现插件系统
3. 优化性能
4. 添加国际化支持
5. 改进错误处理机制 