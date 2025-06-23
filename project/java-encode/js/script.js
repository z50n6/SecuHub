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
        this.initCommandTypeOptions();
        this.initEncodeTypeOptions();
        this.bindEvents();
        this.updateOutput();
        this.updateStatus('就绪');
        this.isInitialized = true;
    }

    initCommandTypeOptions() {
        const cmdTypeSelect = document.getElementById('cmdType');
        if (cmdTypeSelect) {
            const options = [
                { value: 'bash', label: 'Bash' },
                { value: 'sh', label: 'Sh' },
                { value: 'powershell', label: 'PowerShell' },
                { value: 'python', label: 'Python' },
                { value: 'perl', label: 'Perl' },
                { value: 'cmd', label: 'CMD' }
            ];
            cmdTypeSelect.innerHTML = '';
            options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.label;
                cmdTypeSelect.appendChild(option);
            });
            cmdTypeSelect.value = 'bash';
            // 绑定change事件
            cmdTypeSelect.addEventListener('change', (e) => {
                this.cmdType = e.target.value;
                this.updateOutput();
                this.updateStatus(`已选择命令类型: ${cmdTypeSelect.options[cmdTypeSelect.selectedIndex].text}`);
            });
        }
    }

    initEncodeTypeOptions() {
        const encodeTypeSelect = document.getElementById('encodeType');
        if (encodeTypeSelect) {
            encodeTypeSelect.value = 'none';
            encodeTypeSelect.addEventListener('change', (e) => {
                this.encodeType = e.target.value;
                this.updateOutput();
                this.updateStatus(`已选择编码类型: ${encodeTypeSelect.options[encodeTypeSelect.selectedIndex].text}`);
            });
        }
    }

    bindEvents() {
        // 命令类型选择器
        this.bindCommandTypeSelector();
        
        // 编码类型选择器
        this.bindEncodeTypeSelector();
        
        // 输入框事件
        this.bindInputEvents();
        
        // 编码按钮
        this.bindEncodeButton();
        
        // 复制按钮
        this.bindCopyButton();
        
        // 全局点击事件
        this.bindGlobalEvents();
    }

    bindCommandTypeSelector() {
        const btn = document.getElementById('cmdTypeSelectBtn');
        const list = document.getElementById('cmdTypeSelectList');
        const container = document.getElementById('custom-cmdtype-select');

        btn?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown(container, list);
        });

        list?.querySelectorAll('li').forEach(li => {
            li.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectCommandType(li);
            });
        });
    }

    bindEncodeTypeSelector() {
        const btn = document.getElementById('encodeSelectBtn');
        const list = document.getElementById('encodeSelectList');
        const container = document.getElementById('custom-encode-select');

        btn?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown(container, list);
        });

        list?.querySelectorAll('li').forEach(li => {
            li.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectEncodeType(li);
            });
        });
    }

    bindInputEvents() {
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
    }

    bindEncodeButton() {
        const encodeBtn = document.getElementById('encodeBtn');
        encodeBtn?.addEventListener('click', () => {
            this.encodeFinalCmd();
        });
    }

    bindCopyButton() {
        const copyBtn = document.getElementById('copyBtn');
        copyBtn?.addEventListener('click', () => {
            this.copyOutput('finalCmd');
        });
    }

    bindGlobalEvents() {
        document.addEventListener('click', () => {
            this.closeAllDropdowns();
        });
    }

    toggleDropdown(container, list) {
        const isOpen = container.classList.contains('open');
        
        this.closeAllDropdowns();
        
        if (!isOpen) {
            container.classList.add('open');
            list.style.display = 'block';
            
            // 更新aria属性
            const btn = container.querySelector('button');
            if (btn) {
                btn.setAttribute('aria-expanded', 'true');
            }
        }
    }

    closeAllDropdowns() {
        const dropdowns = document.querySelectorAll('.custom-select');
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('open');
            const list = dropdown.querySelector('.select-list');
            if (list) {
                list.style.display = 'none';
            }
            
            const btn = dropdown.querySelector('button');
            if (btn) {
                btn.setAttribute('aria-expanded', 'false');
            }
        });
    }

    selectCommandType(li) {
        this.cmdType = li.getAttribute('data-value');
        const btn = document.getElementById('cmdTypeSelectBtn');
        const textSpan = btn?.querySelector('.select-text');
        
        if (textSpan) {
            textSpan.textContent = li.textContent;
        }
        
        // 更新选中状态
        this.updateSelectedState('cmdTypeSelectList', li);
        this.closeAllDropdowns();
        this.updateOutput();
        this.updateStatus(`已选择命令类型: ${li.textContent}`);
    }

    selectEncodeType(li) {
        this.encodeType = li.getAttribute('data-value');
        const btn = document.getElementById('encodeSelectBtn');
        const textSpan = btn?.querySelector('.select-text');
        
        if (textSpan) {
            textSpan.textContent = li.textContent;
        }
        
        // 更新选中状态
        this.updateSelectedState('encodeSelectList', li);
        this.closeAllDropdowns();
        this.updateStatus(`已选择编码类型: ${li.textContent}`);
    }

    updateSelectedState(listId, selectedLi) {
        const list = document.getElementById(listId);
        if (list) {
            list.querySelectorAll('li').forEach(li => {
                li.classList.remove('selected');
                li.setAttribute('aria-selected', 'false');
            });
            selectedLi.classList.add('selected');
            selectedLi.setAttribute('aria-selected', 'true');
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
        const charCount = document.getElementById('charCount');
        if (charCount) {
            charCount.textContent = `${inputCmd.length} 字符`;
        }
    }

    getOutputCmd(type, input) {
        if (!input) return '';
        
        try {
            const b64 = this.base64Encode(input);
            
            switch(type) {
                case 'bash':
                    return `bash -c {echo,${b64}}|{base64,-d}|{bash,-i}`;
                    
                case 'sh':
                    return `sh -c $@|sh . echo ${this.escapeShell(input)}`;
                    
                case 'powershell':
                    return this.getPowerShellCommand(input);
                    
                case 'python':
                    return `python -c exec('${b64}'.decode('base64'))`;
                    
                case 'perl':
                    return `perl -MMIME::Base64 -e eval(decode_base64('${b64}'))`;
                    
                case 'cmd':
                    return this.getCmdCommand(input);
                    
                default:
                    return input;
            }
        } catch (error) {
            console.error('生成输出命令时出错:', error);
            this.updateStatus('生成命令时出错', 'error');
            return input;
        }
    }

    getPowerShellCommand(input) {
        try {
            // 使用UTF-16LE编码
            const encoder = new TextEncoder();
            const utf16le = new Uint8Array(input.length * 2);
            
            for (let i = 0; i < input.length; i++) {
                const charCode = input.charCodeAt(i);
                utf16le[i * 2] = charCode & 0xFF;
                utf16le[i * 2 + 1] = (charCode >> 8) & 0xFF;
            }
            
            const pwsh_b64 = btoa(String.fromCharCode(...utf16le));
            return `powershell.exe -NonI -W Hidden -NoP -Exec Bypass -Enc ${pwsh_b64}`;
        } catch (error) {
            console.error('PowerShell编码错误:', error);
            return `powershell.exe -Command "${this.escapePowerShell(input)}"`;
        }
    }

    getCmdCommand(input) {
        const escaped = this.escapeCmd(input);
        return `cmd /c "${escaped}"`;
    }

    escapeShell(str) {
        return str.replace(/(["'$`\\])/g, '\\$1');
    }

    escapePowerShell(str) {
        return str.replace(/(["'$`\\])/g, '`$1');
    }

    escapeCmd(str) {
        return str.replace(/"/g, '""');
    }

    encodeByType(str, type) {
        if (!str) return '';
        
        try {
            switch(type) {
                case 'none':
                    return str;
                case 'url':
                    return this.urlEncode(str);
                case 'double_url':
                    return this.doubleUrlEncode(str);
                case 'base64':
                    return this.base64Encode(str);
                case 'hex':
                    return this.hexEncode(str);
                default:
                    return str;
            }
        } catch (error) {
            console.error('编码时出错:', error);
            this.updateStatus('编码时出错', 'error');
            return str;
        }
    }

    base64Encode(str) {
        try {
            // 兼容中文和特殊字符的base64编码
            return btoa(unescape(encodeURIComponent(str)));
        } catch (error) {
            console.error('Base64编码错误:', error);
            return str;
        }
    }

    base64Decode(str) {
        try {
            return decodeURIComponent(escape(atob(str)));
        } catch (error) {
            console.error('Base64解码错误:', error);
            return str;
        }
    }

    urlEncode(str) {
        return encodeURIComponent(str);
    }

    doubleUrlEncode(str) {
        return encodeURIComponent(encodeURIComponent(str));
    }

    hexEncode(str) {
        return Array.from(str).map(char => 
            char.charCodeAt(0).toString(16).padStart(2, '0')
        ).join('');
    }

    encodeFinalCmd() {
        const outputCmd = document.getElementById('outputCmd')?.value || '';
        const finalCmdElement = document.getElementById('finalCmd');
        if (finalCmdElement) {
            finalCmdElement.value = this.encodeByType(outputCmd, this.encodeType);
        }
        this.updateStatus('已完成编码');
    }

    async copyOutput(id) {
        const output = document.getElementById(id);
        if (!output || !output.value) {
            this.updateStatus('没有内容可复制', 'warning');
            return;
        }
        
        try {
            // 优先使用Qt桥接
            if (this.qtBridge && typeof this.qtBridge.copy === 'function') {
                this.qtBridge.copy(output.value);
            } else if (navigator.clipboard && window.isSecureContext) {
                // 使用现代Clipboard API
                await navigator.clipboard.writeText(output.value);
            } else {
                // 降级到传统方法
                output.select();
                document.execCommand('copy');
            }
            
            this.showCopySuccess();
            this.updateStatus('已复制到剪贴板');
        } catch (error) {
            console.error('复制失败:', error);
            this.updateStatus('复制失败', 'error');
        }
    }

    showCopySuccess() {
        const btn = document.getElementById('copyBtn');
        if (!btn) return;
        
        const btnText = btn.querySelector('.btn-text');
        const originalText = btnText?.textContent || '复制编码结果';
        
        btn.classList.add('copy-success');
        btn.disabled = true;
        
        if (btnText) {
            btnText.textContent = '已复制';
        }
        
        setTimeout(() => {
            btn.classList.remove('copy-success');
            btn.disabled = false;
            if (btnText) {
                btnText.textContent = originalText;
            }
        }, 1500);
    }

    updateStatus(message, type = 'info') {
        const statusText = document.getElementById('statusText');
        if (statusText) {
            statusText.textContent = message;
            statusText.className = `status-text status-${type}`;
        }
    }

    // 公共方法，供外部调用
    static getInstance() {
        if (!CommandEncoder.instance) {
            CommandEncoder.instance = new CommandEncoder();
        }
        return CommandEncoder.instance;
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    const app = CommandEncoder.getInstance();
    
    // 初始化Qt Bridge
    if (typeof QWebChannel !== 'undefined') {
        new QWebChannel(qt.webChannelTransport, (channel) => {
            const bridge = channel.objects.qt_bridge;
            if (bridge) {
                app.setQtBridge(bridge);
                app.updateStatus('已连接到应用', 'success');
                console.log("Successfully connected to Qt bridge.");
            } else {
                console.error("Qt bridge object (qt_bridge) not found.");
                app.updateStatus('连接应用失败', 'error');
            }
        });
    } else {
        console.log("QWebChannel not found, running in standard browser mode.");
    }
});

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CommandEncoder;
} 