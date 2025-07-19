/**
 * Java命令编码工具 - 优化版本
 * 支持多种编码格式的命令转换和优化
 */

class CommandEncoder {
    constructor() {
        this.cmdType = 'bash';
        this.encodeType = 'none';
        this.isInitialized = false;
        this.qtBridge = null;
        
        this.init();
    }

    setQtBridge(bridge) {
        this.qtBridge = bridge;
    }

    init() {
        this.bindEvents();
        this.updateOutput();
        this.updateStatus('就绪');
        this.isInitialized = true;
    }

    bindEvents() {
        // 命令类型选择器
        const cmdTypeSelect = document.getElementById('cmdType');
        if (cmdTypeSelect) {
            cmdTypeSelect.addEventListener('change', (e) => {
                this.cmdType = e.target.value;
                this.updateOutput();
                this.updateStatus(`已选择命令类型: ${e.target.options[e.target.selectedIndex].text}`);
            });
        }

        // 编码类型选择器
        const encodeTypeSelect = document.getElementById('encodeType');
        if (encodeTypeSelect) {
            encodeTypeSelect.addEventListener('change', (e) => {
                this.encodeType = e.target.value;
                this.updateOutput();
                this.updateStatus(`已选择编码类型: ${e.target.options[e.target.selectedIndex].text}`);
            });
        }

        // 输入框事件
        const inputCmd = document.getElementById('inputCmd');
        if (inputCmd) {
            inputCmd.addEventListener('input', () => {
                this.updateOutput();
                this.updateCharCount();
            });
            
            inputCmd.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 'Enter') {
                    this.encodeFinalCmd();
                }
            });
        }

        // 复制按钮
        const copyBtn = document.getElementById('copyBtn');
        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                this.copyOutput('finalCmd');
            });
        }
    }

    updateOutput() {
        const inputCmd = document.getElementById('inputCmd')?.value?.trim() || '';
        const outputCmd = this.getOutputCmd(this.cmdType, inputCmd);
        const outputElement = document.getElementById('outputCmd');
        if (outputElement) {
            outputElement.value = outputCmd;
        }
        // 编码结果
        const finalCmdElement = document.getElementById('finalCmd');
        if (finalCmdElement) {
            finalCmdElement.value = this.encodeByType(outputCmd, this.encodeType);
        }
        this.updateCharCount();
    }

    updateCharCount() {
        const inputCmd = document.getElementById('inputCmd')?.value || '';
        const charCount = inputCmd.length;
        this.updateStatus(`已连接到应用 ${charCount} 字符`);
    }

    getOutputCmd(type, input) {
        if (!input.trim()) return '';
        
        switch (type) {
            case 'bash':
                return `bash -c "${this.escapeShell(input)}"`;
            case 'sh':
                return `sh -c "${this.escapeShell(input)}"`;
            case 'powershell':
                return this.getPowerShellCommand(input);
            case 'python':
                return `python -c "${this.escapeShell(input)}"`;
            case 'perl':
                return `perl -e "${this.escapeShell(input)}"`;
            case 'cmd':
                return this.getCmdCommand(input);
            default:
                return input;
        }
    }

    getPowerShellCommand(input) {
        const escaped = this.escapePowerShell(input);
        return `powershell -Command "${escaped}"`;
    }

    getCmdCommand(input) {
        const escaped = this.escapeCmd(input);
        return `cmd /c "${escaped}"`;
    }

    escapeShell(str) {
        return str.replace(/"/g, '\\"').replace(/\$/g, '\\$');
    }

    escapePowerShell(str) {
        return str.replace(/"/g, '`"').replace(/\$/g, '`$');
    }

    escapeCmd(str) {
        return str.replace(/"/g, '""').replace(/%/g, '%%');
    }

    encodeByType(str, type) {
        if (!str) return '';
        
        switch (type) {
            case 'url':
                return this.urlEncode(str);
            case 'base64':
                return this.base64Encode(str);
            case 'double_url':
                return this.doubleUrlEncode(str);
            default:
                return str;
        }
    }

    base64Encode(str) {
        try {
            return btoa(unescape(encodeURIComponent(str)));
        } catch (e) {
            return str;
        }
    }

    base64Decode(str) {
        try {
            return decodeURIComponent(escape(atob(str)));
        } catch (e) {
            return str;
        }
    }

    urlEncode(str) {
        return encodeURIComponent(str);
    }

    doubleUrlEncode(str) {
        return encodeURIComponent(encodeURIComponent(str));
    }

    encodeFinalCmd() {
        const inputCmd = document.getElementById('inputCmd')?.value?.trim();
        if (inputCmd) {
            this.updateOutput();
            this.updateStatus('编码完成');
        }
    }

    async copyOutput(id) {
        const element = document.getElementById(id);
        if (!element || !element.value) {
            this.updateStatus('没有内容可复制', 'warning');
            return;
        }

        try {
            if (this.qtBridge) {
                this.qtBridge.copy(element.value);
                this.showCopySuccess();
            } else {
                // 降级到原生复制
                element.select();
                document.execCommand('copy');
                this.showCopySuccess();
            }
        } catch (error) {
            this.updateStatus('复制失败: ' + error.message, 'error');
        }
    }

    showCopySuccess() {
        const copyBtn = document.getElementById('copyBtn');
        if (copyBtn) {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = '复制成功!';
            copyBtn.style.background = '#22c55e';
            
            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.style.background = '';
            }, 1500);
        }
        this.updateStatus('已复制到剪贴板', 'success');
    }

    updateStatus(message, type = 'info') {
        const statusBar = document.getElementById('statusBar');
        if (statusBar) {
            statusBar.textContent = message;
        }
    }

    static getInstance() {
        if (!CommandEncoder.instance) {
            CommandEncoder.instance = new CommandEncoder();
        }
        return CommandEncoder.instance;
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    const encoder = CommandEncoder.getInstance();
    
    // 设置Qt桥接
    if (window.qt && window.qt.webChannelTransport) {
        new QWebChannel(qt.webChannelTransport, (channel) => {
            encoder.setQtBridge(channel.objects.bridge);
        });
    }
}); 