# Java命令编码工具 - 优化版本

一个现代化的Web工具，用于将各种命令转换为不同编码格式，支持多种Shell环境和编码方式。

## ✨ 新特性

### 🎨 现代化UI设计
- **响应式设计**: 完美适配桌面、平板和手机
- **深色主题支持**: 自动适应系统主题偏好
- **CSS变量系统**: 易于定制和维护
- **流畅动画**: 优雅的过渡效果和交互反馈
- **无障碍支持**: 完整的ARIA标签和键盘导航

### 🚀 增强功能
- **新增CMD支持**: 支持Windows CMD命令编码
- **Hex编码**: 新增十六进制编码选项
- **智能错误处理**: 完善的错误提示和状态反馈
- **字符计数**: 实时显示输入字符数量
- **快捷键支持**: Ctrl+Enter快速编码
- **现代剪贴板API**: 更可靠的复制功能

### 💻 技术优化
- **ES6+语法**: 使用现代JavaScript特性
- **面向对象设计**: 清晰的代码结构和模块化
- **性能优化**: 防抖处理、懒加载、内存管理
- **错误边界**: 完善的异常处理机制
- **向后兼容**: 保持原有API兼容性

## 🛠️ 支持的命令类型

| 类型 | 描述 | 示例输出 |
|------|------|----------|
| **Bash** | Linux/Unix Bash shell | `bash -c {echo,d2hvYW1p}\|{base64,-d}\|{bash,-i}` |
| **Sh** | 标准Shell | `sh -c $@\|sh . echo whoami` |
| **PowerShell** | Windows PowerShell | `powershell.exe -NonI -W Hidden -NoP -Exec Bypass -Enc <base64>` |
| **Python** | Python脚本 | `python -c exec('d2hvYW1p'.decode('base64'))` |
| **Perl** | Perl脚本 | `perl -MMIME::Base64 -e eval(decode_base64('d2hvYW1p'))` |
| **CMD** | Windows命令提示符 | `cmd /c "whoami"` |

## 🔐 支持的编码格式

| 编码类型 | 描述 | 示例 |
|----------|------|------|
| **None** | 无编码 | `bash -c {echo,d2hvYW1p}\|{base64,-d}\|{bash,-i}` |
| **URL编码** | 标准URL编码 | `bash%20-c%20%7Becho%2Cd2hvYW1p%7D%7C%7Bbase64%2C-d%7D%7C%7Bbash%2C-i%7D` |
| **双URL编码** | 双重URL编码 | `bash%2520-c%2520%257Becho%252Cd2hvYW1p%257D%257C%257Bbase64%252C-d%257D%257C%257Bbash%252C-i%257D` |
| **Base64编码** | Base64编码 | `YmFzaCAtYyB7ZWNobyxkNmh2WVdHcH18e2Jhc2U2NCwtZH18e2Jhc2gsLWl9` |
| **Hex编码** | 十六进制编码 | `62617368202d63207b6563686f2c64326876595747707d7c7b6261736536342c2d647d7c7b626173682c2d697d` |

## 🎯 使用场景

### 渗透测试
- 绕过WAF和IDS检测
- 混淆恶意命令
- 测试不同编码方式的绕过效果

### 系统管理
- 远程命令执行
- 自动化脚本部署
- 安全审计和测试

### 开发调试
- 命令编码测试
- 不同环境兼容性验证
- 安全编码实践

## 🚀 快速开始

1. **打开工具**: 在浏览器中打开 `index.html`
2. **选择命令类型**: 从下拉菜单选择目标Shell环境
3. **输入命令**: 在输入框中输入要编码的命令
4. **选择编码**: 选择需要的编码格式
5. **生成结果**: 点击"编码"按钮生成最终命令
6. **复制使用**: 点击"复制编码结果"按钮复制到剪贴板

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + Enter` | 快速编码 |
| `Tab` | 在输入框间切换 |
| `Esc` | 关闭下拉菜单 |

## 🎨 主题定制

工具支持多种主题模式：

- **浅色主题**: 默认主题，适合日间使用
- **深色主题**: 自动适应系统偏好，护眼友好
- **高对比度**: 为视觉障碍用户优化

## 📱 响应式设计

- **桌面端**: 完整功能，最佳体验
- **平板端**: 适配中等屏幕，保持功能完整
- **手机端**: 垂直布局，触摸友好

## 🔧 技术栈

- **HTML5**: 语义化标签，无障碍支持
- **CSS3**: 变量系统，Grid/Flexbox布局，动画效果
- **ES6+**: 类、箭头函数、模板字符串、异步处理
- **现代API**: Clipboard API, TextEncoder等

## 🐛 浏览器兼容性

| 浏览器 | 版本要求 | 支持状态 |
|--------|----------|----------|
| Chrome | 60+ | ✅ 完全支持 |
| Firefox | 55+ | ✅ 完全支持 |
| Safari | 12+ | ✅ 完全支持 |
| Edge | 79+ | ✅ 完全支持 |
| IE | 11 | ⚠️ 部分支持 |

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📞 支持

如果您遇到问题或有建议，请：

1. 查看 [Issues](../../issues) 页面
2. 创建新的 Issue
3. 联系维护者

---

**注意**: 本工具仅用于合法的安全测试和教育目的。请遵守相关法律法规，不要用于非法活动。 