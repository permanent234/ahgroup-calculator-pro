/**
 * Calculator Pro Frontend - Tech Neon Edition
 * 支持高级符号运算、微积分、矩阵、图片公式识别等
 */

// ===== Calculator Elements =====
const exprInput = document.getElementById('exprInput');
const resultArea = document.getElementById('resultArea');
const statusArea = document.getElementById('statusArea');
const historyList = document.getElementById('historyList');
const clearBtn = document.getElementById('clearBtn');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const modeSelector = document.getElementById('modeSelector');
const modeDesc = document.getElementById('modeDesc');
const varInputWrap = document.getElementById('varInputWrap');
const varInput = document.getElementById('varInput');
const boundsWrap = document.getElementById('boundsWrap');
const lowerBound = document.getElementById('lowerBound');
const upperBound = document.getElementById('upperBound');

// ===== OCR Elements =====
const dropZone = document.getElementById('dropZone');
const imageUpload = document.getElementById('imageUpload');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const removeImage = document.getElementById('removeImage');
const ocrBtn = document.getElementById('ocrBtn');
const ocrLoading = document.getElementById('ocrLoading');
const ocrResult = document.getElementById('ocrResult');
const applyResult = document.getElementById('applyResult');
const ocrHistoryList = document.getElementById('ocrHistoryList');
const clearOcrHistory = document.getElementById('clearOcrHistory');

const API_BASE = '/api';

let currentMode = 'eval';
let currentOcrImage = null;

const MODE_DESCRIPTIONS = {
    'eval': '计算表达式的数值结果，如: 1+2*pow(3,2)',
    'simplify': '化简代数表达式，如: (x^2-1)/(x-1)',
    'factor': '因式分解多项式，如: x^2-1',
    'expand': '展开括号表达式，如: (x+1)^2',
    'solve': '求解方程，如: x^2-4=0',
    'diff': '对表达式求导，如: x^3+2*x',
    'integrate': '计算不定积分，如: x^2+1',
    'definite': '计算定积分，需输入上下限',
    'matrix': '矩阵运算，如: [[1,2],[3,4]]+[[5,6],[7,8]]',
    'det': '计算矩阵行列式，如: [[1,2],[3,4]]',
    'inv': '计算矩阵逆，如: [[1,2],[3,4]]',
    'transpose': '矩阵转置，如: [[1,2],[3,4]]',
    'trig': '三角函数化简/展开，如: sin(x)^2+cos(x)^2',
    'latex': '输出LaTeX格式，如: (x^2+1)/(x-1)',
    'limit': '计算极限，如: sin(x)/x (x->0)',
    'taylor': '泰勒展开，如: sin(x) (在x=0处展开)',
    'series': '级数求和，如: 1/n^2 (n=1到inf)',
    'eigen': '矩阵特征值，如: [[1,2],[3,4]]',
    'rank': '矩阵秩，如: [[1,2],[3,4]]',
};

// ===== Input Helpers =====

function insertText(text) {
    const start = exprInput.selectionStart;
    const end = exprInput.selectionEnd;
    const value = exprInput.value;
    exprInput.value = value.substring(0, start) + text + value.substring(end);
    exprInput.focus();
    const newPos = start + text.length;
    exprInput.setSelectionRange(newPos, newPos);
}

function backspace() {
    const start = exprInput.selectionStart;
    const end = exprInput.selectionEnd;
    if (start === end) {
        if (start > 0) {
            exprInput.value = exprInput.value.substring(0, start - 1) + exprInput.value.substring(end);
            exprInput.setSelectionRange(start - 1, start - 1);
        }
    } else {
        exprInput.value = exprInput.value.substring(0, start) + exprInput.value.substring(end);
        exprInput.setSelectionRange(start, start);
    }
    exprInput.focus();
}

function clearAll() {
    exprInput.value = '';
    resultArea.textContent = '—';
    resultArea.className = 'result-text';
    statusArea.textContent = '';
    exprInput.focus();
}

// ===== Mode Switching =====

function setMode(mode) {
    currentMode = mode;

    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    modeDesc.textContent = MODE_DESCRIPTIONS[mode] || '';

    const needsVar = ['diff', 'integrate', 'definite', 'solve', 'limit', 'taylor', 'series'].includes(mode);
    varInputWrap.style.display = needsVar ? 'flex' : 'none';

    boundsWrap.style.display = mode === 'definite' ? 'flex' : 'none';
}

modeSelector.addEventListener('click', (e) => {
    if (e.target.classList.contains('mode-btn')) {
        setMode(e.target.dataset.mode);
        exprInput.focus();
    }
});

// ===== API Calls =====

async function apiAdvanced(expression, mode, varName, lower, upper) {
    const body = { expression, mode };
    if (varName) body.var = varName;
    if (lower !== '') body.lower = lower;
    if (upper !== '') body.upper = upper;

    const res = await fetch(`${API_BASE}/advanced/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    return res.json();
}

async function apiCalculate(expression) {
    const res = await fetch(`${API_BASE}/calculate/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expression }),
    });
    return res.json();
}

async function apiValidate(expression) {
    const res = await fetch(`${API_BASE}/validate/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expression }),
    });
    return res.json();
}

async function apiHistory() {
    const res = await fetch(`${API_BASE}/history/`);
    return res.json();
}

async function apiClearHistory() {
    const res = await fetch(`${API_BASE}/clear-history/`, { method: 'POST' });
    return res.json();
}

// ===== UI Updates =====

function setResult(text, type) {
    resultArea.textContent = '';
    resultArea.className = 'result-text' + (type ? ' ' + type : '');
    
    // For integral modes, render with MathJax
    if (currentMode === 'integrate' || currentMode === 'definite') {
        if (!type && text !== '—' && text !== '计算中...') {
            resultArea.innerHTML = text;
            if (window.MathJax && window.MathJax.typesetPromise) {
                window.MathJax.typesetPromise([resultArea]).catch(err => {
                    // 如果 MathJax 渲染失败，回退到纯文本
                    resultArea.textContent = text.replace(/\\[()]/g, '');
                });
            }
            return;
        }
    }
    resultArea.textContent = text;
}

function setStatus(text, color) {
    statusArea.textContent = text;
    statusArea.style.color = color || '';
}

// ===== Calculation =====

async function calculate() {
    const expr = exprInput.value.trim();
    if (!expr) {
        setResult('请输入表达式', 'error');
        setStatus('');
        return;
    }

    setResult('计算中...', '');
    setStatus('');

    try {
        let data;
        if (currentMode === 'eval') {
            data = await apiCalculate(expr);
        } else {
            const varName = varInput.value.trim() || 'x';
            const lower = lowerBound.value.trim();
            const upper = upperBound.value.trim();
            data = await apiAdvanced(expr, currentMode, varName, lower, upper);
        }

        if (data.error) {
            setResult(data.error, 'error');
            setStatus('');
        } else {
            setResult(data.result, 'success');
            setStatus('');
            await loadHistory();
        }
    } catch (err) {
        setResult('网络请求失败', 'error');
        setStatus('请检查后端服务是否运行');
    }
}

async function validateLive() {
    const expr = exprInput.value.trim();
    if (!expr) {
        setStatus('');
        return;
    }
    try {
        const data = await apiValidate(expr);
        if (data.valid) {
            setStatus('✓ 表达式合法', 'var(--success)');
        } else {
            setStatus('✗ ' + data.message, 'var(--warning)');
        }
    } catch {
        setStatus('');
    }
}

// ===== History =====

function renderHistory(history) {
    if (!history || history.length === 0) {
        historyList.innerHTML = '<div class="empty">暂无计算记录</div>';
        return;
    }

    const modeLabels = {
        'eval': '数值', 'simplify': '化简', 'factor': '因式', 'expand': '展开',
        'solve': '方程', 'diff': '求导', 'integrate': '积分', 'definite': '定积分',
        'matrix': '矩阵', 'det': '行列式', 'inv': '逆矩阵', 'transpose': '转置',
        'trig': '三角', 'latex': 'LaTeX', 'limit': '极限', 'taylor': '泰勒',
        'series': '级数', 'eigen': '特征值', 'rank': '秩',
    };

    historyList.innerHTML = history.map(item => {
        const isError = item.error !== null && item.error !== undefined;
        const label = modeLabels[item.mode] || item.mode;
        return `
            <div class="history-item ${isError ? 'error' : ''}" data-expr="${escapeHtml(item.expression)}" data-mode="${item.mode}">
                <span class="mode-tag">${label}</span>
                <span class="expr">${escapeHtml(item.expression)}</span>
                <span class="res">${isError ? '错误' : escapeHtml(String(item.result))}</span>
            </div>
        `;
    }).join('');

    historyList.querySelectorAll('.history-item').forEach(el => {
        el.addEventListener('click', () => {
            exprInput.value = el.dataset.expr;
            if (el.dataset.mode) {
                setMode(el.dataset.mode);
            }
            exprInput.focus();
        });
    });
}

async function loadHistory() {
    try {
        const data = await apiHistory();
        renderHistory(data.history);
    } catch {
        // ignore
    }
}

async function clearHistory() {
    try {
        await apiClearHistory();
        renderHistory([]);
    } catch {
        setStatus('清空历史失败', 'var(--error)');
    }
}

// ===== Utilities =====

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== OCR Functions =====

// OCR History
let _ocrHistory = JSON.parse(localStorage.getItem('ocr_history') || '[]');
const MAX_OCR_HISTORY = 20;

function _saveOcrHistory() {
    localStorage.setItem('ocr_history', JSON.stringify(_ocrHistory));
}

function addOcrHistory(text, success) {
    _ocrHistory.unshift({ text, success, time: new Date().toLocaleString() });
    if (_ocrHistory.length > MAX_OCR_HISTORY) {
        _ocrHistory = _ocrHistory.slice(0, MAX_OCR_HISTORY);
    }
    _saveOcrHistory();
    renderOcrHistory();
}

function renderOcrHistory() {
    if (!_ocrHistory || _ocrHistory.length === 0) {
        ocrHistoryList.innerHTML = '<div class="empty">暂无识别记录</div>';
        return;
    }
    ocrHistoryList.innerHTML = _ocrHistory.map((item, i) => `
        <div class="history-item" data-text="${escapeHtml(item.text)}" data-index="${i}">
            <span class="mode-tag ${item.success ? '' : 'error'}">${item.success ? '成功' : '失败'}</span>
            <span class="expr">${escapeHtml(item.text)}</span>
            <span class="res" style="font-size:0.65rem;color:var(--text-muted)">${item.time}</span>
        </div>
    `).join('');

    ocrHistoryList.querySelectorAll('.history-item').forEach(el => {
        el.addEventListener('click', () => {
            exprInput.value = el.dataset.text;
            exprInput.focus();
        });
    });
}

function clearOcrHistoryFn() {
    _ocrHistory = [];
    _saveOcrHistory();
    renderOcrHistory();
}

// Image upload handlers
dropZone.addEventListener('click', () => imageUpload.click());

imageUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleImageFile(file);
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleImageFile(file);
    }
});

function handleImageFile(file) {
    currentOcrImage = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        dropZone.style.display = 'none';
        imagePreview.style.display = 'flex';
        ocrBtn.disabled = false;
        ocrResult.textContent = '—';
        applyResult.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

removeImage.addEventListener('click', () => {
    currentOcrImage = null;
    previewImg.src = '';
    dropZone.style.display = 'block';
    imagePreview.style.display = 'none';
    ocrBtn.disabled = true;
    ocrResult.textContent = '—';
    applyResult.style.display = 'none';
    imageUpload.value = '';
});

// Paste handler: allow Ctrl+V to paste image from clipboard anywhere on the page
document.addEventListener('paste', (e) => {
    const items = e.clipboardData && e.clipboardData.items;
    if (!items) return;

    for (const item of items) {
        if (item.type.startsWith('image/')) {
            e.preventDefault();
            const file = item.getAsFile();
            if (file) {
                handleImageFile(file);
                // Auto-recognize after a short delay to allow image rendering
                setTimeout(() => {
                    if (ocrBtn.disabled === false) {
                        doOcr();
                    }
                }, 400);
            }
            break;
        }
    }
});

// OCR Recognition — Backend-first, fallback to frontend Tesseract.js
async function doOcr() {
    if (!currentOcrImage) return;

    ocrBtn.style.display = 'none';
    ocrLoading.style.display = 'flex';
    ocrResult.textContent = '—';
    applyResult.style.display = 'none';

    try {
        // 1. Try backend OCR first (much faster, no model download)
        ocrResult.textContent = '上传图片到后端识别...';
        const base64 = previewImg.src;
        const backendRes = await fetch(`${API_BASE}/ocr/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: base64 }),
        });
        const backendData = await backendRes.json();

        if (backendData.result && !backendData.error) {
            const cleaned = cleanOcrText(backendData.result);
            ocrResult.textContent = cleaned || '未能识别出公式';
            addOcrHistory(cleaned || backendData.result, !!cleaned);
            applyResult.style.display = cleaned ? 'flex' : 'none';
            ocrBtn.style.display = 'flex';
            ocrLoading.style.display = 'none';
            return;
        }

        // Backend unavailable or failed — fallback to frontend Tesseract.js
        ocrResult.textContent = '后端不可用，切换前端识别...';
        await doFrontendOcr();
    } catch (err) {
        // Network error — fallback to frontend
        ocrResult.textContent = '网络错误，切换前端识别...';
        await doFrontendOcr();
    }
}

// Image preprocessing for better OCR on math formulas
function preprocessImage(src) {
    return new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
            const canvas = document.createElement('canvas');
            // Scale up 2x for better recognition of small symbols
            const scale = 2;
            canvas.width = img.width * scale;
            canvas.height = img.height * scale;
            const ctx = canvas.getContext('2d');

            // Draw scaled image
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;

            // Convert to grayscale and apply adaptive thresholding
            for (let i = 0; i < data.length; i += 4) {
                const r = data[i];
                const g = data[i + 1];
                const b = data[i + 2];
                // Grayscale
                let gray = 0.299 * r + 0.587 * g + 0.114 * b;
                // Invert if background is dark (light text on dark bg)
                gray = 255 - gray;
                // Threshold: make it pure black/white
                gray = gray > 128 ? 255 : 0;
                data[i] = data[i + 1] = data[i + 2] = gray;
            }

            ctx.putImageData(imageData, 0, 0);
            resolve(canvas.toDataURL('image/png'));
        };
        img.src = src;
    });
}

async function doFrontendOcr() {
    try {
        ocrResult.textContent = '预处理图片...';
        // Preprocess image for better formula recognition
        const processedImage = await preprocessImage(previewImg.src);

        ocrResult.textContent = '识别中...';
        const { data: { text } } = await Tesseract.recognize(
            processedImage,
            'eng',
            {
                // PSM 6: Assume a single uniform block of text
                // PSM 7: Treat the image as a single text line
                tessedit_pageseg_mode: '7',
                // Whitelist common math characters to reduce misrecognition
                tessedit_char_whitelist: '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/=^()[]{}|.,;:!?~<>\\\'"#$%&@ _',
                logger: m => {
                    if (m.status === 'recognizing text') {
                        ocrResult.textContent = `识别中... ${Math.round(m.progress * 100)}%`;
                    } else if (m.status === 'loading language traineddata') {
                        ocrResult.textContent = `加载模型... ${Math.round(m.progress * 100)}%`;
                    }
                }
            }
        );

        const cleaned = cleanOcrText(text);
        ocrResult.textContent = cleaned || '未能识别出公式';
        addOcrHistory(cleaned || text, !!cleaned);
        applyResult.style.display = cleaned ? 'flex' : 'none';
    } catch (err) {
        ocrResult.textContent = '识别失败: ' + err.message;
        addOcrHistory('识别失败', false);
        applyResult.style.display = 'none';
    } finally {
        ocrBtn.style.display = 'flex';
        ocrLoading.style.display = 'none';
    }
}

function cleanOcrText(text) {
    // Clean up OCR text for math formulas
    let cleaned = text
        .replace(/\n/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

    // Remove common OCR artifacts
    cleaned = cleaned
        .replace(/[\u2013\u2014]/g, '-')   // en-dash, em-dash -> minus
        .replace(/[\u2212]/g, '-')        // unicode minus -> ascii minus
        .replace(/[\u00D7]/g, '*')        // multiplication sign -> *
        .replace(/[\u00F7]/g, '/')       // division sign -> /
        .replace(/[\u22C5]/g, '*')        // dot operator -> *
        .replace(/[\u0302]/g, '^')       // combining circumflex -> ^
        .replace(/[\u221A]/g, 'sqrt')    // sqrt symbol -> sqrt
        .replace(/[\u03C0]/g, 'pi')      // pi symbol -> pi
        .replace(/[\u221E]/g, 'inf')     // infinity -> inf
        .replace(/[\u03B1\u03B2\u03B3\u03B8\u03BB\u03BC\u03C3\u03C4\u03C6\u03C9]/g, (m) => {
            const map = {'\u03B1':'alpha','\u03B2':'beta','\u03B3':'gamma','\u03B8':'theta',
                         '\u03BB':'lambda','\u03BC':'mu','\u03C3':'sigma','\u03C4':'tau',
                         '\u03C6':'phi','\u03C9':'omega'};
            return map[m] || m;
        });

    // Structural corrections for math formulas
    cleaned = cleaned
        // Fix fractions: a / b -> (a)/(b) or keep as is if clear
        .replace(/([a-zA-Z0-9\)]+)\s*\/\s*([a-zA-Z0-9\(]+)/g, '($1)/($2)')
        // Fix exponents: e x -> e^x, but careful with words
        .replace(/\b(e)\s+([\(\[])/g, 'e^$2')  // e ( -> e^(
        .replace(/\b(sin|cos|tan|log|ln|exp|sqrt)\s+([a-zA-Z0-9\(])/g, '$1($2)')
        // Fix multiple carets
        .replace(/\^\s*\^/g, '^')
        // Remove extra spaces around operators
        .replace(/\s*([\+\-\*\/\=\^])\s*/g, '$1')
        // Fix parentheses spacing
        .replace(/\(\s+/g, '(')
        .replace(/\s+\)/g, ')')
        // Common function names
        .replace(/\bsin\b/g, 'sin')
        .replace(/\bcos\b/g, 'cos')
        .replace(/\btan\b/g, 'tan')
        .replace(/\bcot\b/g, 'cot')
        .replace(/\bsec\b/g, 'sec')
        .replace(/\bcsc\b/g, 'csc')
        .replace(/\blog\b/g, 'log')
        .replace(/\bln\b/g, 'ln')
        .replace(/\bexp\b/g, 'exp')
        .replace(/\bsqrt\b/g, 'sqrt')
        .replace(/\bdx\b/gi, 'dx')
        .replace(/\bpi\b/g, 'pi')
        .replace(/\btheta\b/g, 'theta')
        .replace(/\balpha\b/g, 'alpha')
        .replace(/\bbeta\b/g, 'beta')
        .replace(/\bgamma\b/g, 'gamma')
        // Fix common OCR misreadings
        .replace(/[oO]0\b/g, '0')  // o or O before 0 -> just 0
        .replace(/\b1([a-z])/g, 'l$1')  // 1 before letter might be l
        .replace(/\+\s*C/g, '+ C');

    // If result looks like garbage (too many non-math chars), return empty
    const mathChars = /[0-9a-zA-Z+\-\*\/=\^\(\)\[\]\{\}\.,;:!?~<>\\|#$%&@ _]/;
    const meaningfulChars = cleaned.split('').filter(c => mathChars.test(c)).length;
    if (meaningfulChars < cleaned.length * 0.5 && cleaned.length > 5) {
        // Too much garbage, try to extract only math-like parts
        cleaned = cleaned.replace(/[^0-9a-zA-Z+\-\*\/=\^\(\)\[\]\{\}\.,;:!?~<>\\|#$%&@ _]/g, '');
    }

    return cleaned;
}

applyResult.addEventListener('click', () => {
    const text = ocrResult.textContent;
    if (text && text !== '—' && text !== '未能识别出公式') {
        exprInput.value = text;
        exprInput.focus();
    }
});

ocrBtn.addEventListener('click', doOcr);

clearOcrHistory.addEventListener('click', clearOcrHistoryFn);

// ===== Event Listeners =====

// Keypad buttons (main)
document.querySelectorAll('#mainKeypad .key[data-value]').forEach(btn => {
    btn.addEventListener('click', () => {
        insertText(btn.dataset.value);
    });
});

// Advanced keypad buttons
document.querySelectorAll('#advancedKeypad .key[data-value]').forEach(btn => {
    btn.addEventListener('click', () => {
        insertText(btn.dataset.value);
    });
});

// Action buttons
document.querySelectorAll('.key[data-action]').forEach(btn => {
    btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        if (action === 'calculate') calculate();
        else if (action === 'backspace') backspace();
        else if (action === 'clear') clearAll();
    });
});

// Clear button
clearBtn.addEventListener('click', clearAll);

// Clear history button
clearHistoryBtn.addEventListener('click', clearHistory);

// Expand/collapse mode buttons
const expandModesBtn = document.getElementById('expandModesBtn');
if (expandModesBtn) {
    expandModesBtn.addEventListener('click', () => {
        modeSelector.classList.toggle('expanded');
        expandModesBtn.classList.toggle('expanded');
    });
}

// Keyboard input
exprInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        calculate();
    } else if (e.key === 'Escape') {
        clearAll();
    }
});

// Live validation debounce
let validateTimer = null;
exprInput.addEventListener('input', () => {
    clearTimeout(validateTimer);
    validateTimer = setTimeout(validateLive, 500);
});

// Variable input bounds - also trigger Enter calculation
varInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        calculate();
    }
});

lowerBound.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        calculate();
    }
});

upperBound.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        calculate();
    }
});

// ===== Init =====

setMode('eval');
loadHistory();
renderOcrHistory();
exprInput.focus();
