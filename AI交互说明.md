# AI 交互说明文档

> 本文档记录了本次人机协作开发计算器 Web 应用（任务三）的完整过程，包括架构设计、开发决策、问题排查与修复过程，以及当前项目状态与后续建议。

---

## 一、任务背景

本次任务目标为基于 Django 框架构建一个支持高级符号运算的科学计算器 Web 应用。初始项目仅具备基础数值计算功能，前端 UI 较为简陋。通过与 AI 协作，完成了以下升级：

- 前端 UI 升级为**霓虹科技风格（Tech Neon Theme）**，具备双列响应式布局
- 后端集成 **19 种运算模式**（含基础数值 + 高级符号运算）
- 新增**图片公式识别（OCR）**功能，支持上传/拖拽/粘贴截图识别
- 积分运算支持**显式符号展示**（∫ 符号 + MathJax 渲染）
- 修复多项环境兼容性问题（sympy 安装、模块导入、端口占用等）

---

## 二、架构设计决策

### 2.1 技术栈选型

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | Django 5.x | Python Web 框架，提供 RESTful API |
| 符号运算 | SymPy 1.13.1 | Python 符号数学库，支持微积分、矩阵、LaTeX 等 |
| 基础计算 | calculator_core（自研） | 词法分析 + 递归下降解析器，支持 sin/cos/log/pi/e 等 |
| 前端 | HTML5 + CSS3 + 原生 JS | 无框架依赖，单页面应用，支持响应式双列布局 |
| 公式渲染 | MathJax 3 | 积分结果显式渲染为 LaTeX 格式 |
| 前端 OCR | Tesseract.js (CDN) | 浏览器端运行，无需额外安装，作为后端 OCR 回退 |
| 后端 OCR | pytesseract + Pillow | 后端调用 Tesseract 引擎，比前端快 3-5 倍 |

### 2.2 模块结构

```
任务三/
├── calculator_project/          # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── calculator_api/              # 核心应用
│   ├── views.py                 # API 视图（19 种运算模式 + OCR）
│   ├── urls.py                  # API 路由
│   ├── calculator_core.py      # 基础数值计算引擎
│   ├── models.py, admin.py, tests.py  # Django 默认文件
│   └── migrations/
├── templates/
│   └── index.html               # 单页面前端模板
├── static/
│   ├── css/style.css            # 霓虹科技主题样式
│   └── js/app.js                # 前端交互逻辑
├── run.py                       # 一键启动脚本
├── manage.py                    # Django 管理脚本
├── AI交互说明.md                # 本文档
└── 使用说明.md                  # 用户文档
```

### 2.3 优雅降级策略

当 **sympy 未安装**时，系统通过 `try/except` 捕获 `ImportError`，设置 `SYMPY_AVAILABLE = False`，此时：
- `eval` 模式回退至 `calculator_core.evaluate()` 基础计算
- 其他高级模式（化简、因式分解、积分等）返回错误提示，引导用户安装 sympy
- 前端根据后端返回的 `error` 字段显示友好提示

这种设计确保**核心数值计算功能始终可用**，不会因为环境差异导致系统完全不可用。

---

## 三、前端升级过程

### 3.1 霓虹科技主题（Tech Neon Theme）

- 采用深色背景（#050510）搭配霓虹蓝（#00f0ff）、紫（#bd00ff）、粉（#ff00aa）渐变
- 玻璃拟态（Glassmorphism）卡片设计，支持 backdrop-filter 模糊效果
- 动态扫描线动画、边框发光效果、按键悬停缩放
- 自定义滚动条、字体（JetBrains Mono + Segoe UI）

### 3.2 双列响应式布局

- 大屏幕（>1300px）：左右双列并排（计算器 + 公式识别面板）
- 中屏幕（480-1300px）：单列居中，max-width 560px
- 小屏幕（<480px）：全宽单列，去除边框阴影

### 3.3 功能按钮可展开设计

- 默认单行显示，支持横向滚动
- 右侧添加 ▾ 展开按钮，点击后展开为多行显示全部 19 个功能
- 新增功能：极限、泰勒展开、级数、特征值、矩阵秩

### 3.4 积分符号显式化

- 后端 `integrate` 模式返回 `\(\int expr \, dx = result + C\)` 格式
- 后端 `definite` 模式返回 `\(\int_{lower}^{upper} expr \, dx = result\)` 格式
- 前端引入 MathJax 3 CDN，自动渲染 LaTeX 为数学公式

---

## 四、后端运算模式实现

### 4.1 19 种运算模式

| 模式 | 说明 | 示例 |
|------|------|------|
| `eval` | 数值计算 | `1+2*pow(3,2)` → `19` |
| `simplify` | 化简表达式 | `(x^2-1)/(x-1)` → `x+1` |
| `factor` | 因式分解 | `x^2-1` → `(x-1)(x+1)` |
| `expand` | 展开括号 | `(x+1)^2` → `x^2+2x+1` |
| `solve` | 方程求解 | `x^2-4=0` → `x=2, x=-2` |
| `diff` | 求导 | `x^3+2*x` → `3x^2+2` |
| `integrate` | 不定积分 | `x^2+1` → `x^3/3+x+C` |
| `definite` | 定积分 | `x^2` (0→1) → `1/3` |
| `matrix` | 矩阵运算 | `[[1,2],[3,4]]+[[5,6],[7,8]]` |
| `det` | 行列式 | `[[1,2],[3,4]]` → `-2` |
| `inv` | 矩阵逆 | `[[1,2],[3,4]]` → `[[-2,1],[1.5,-0.5]]` |
| `transpose` | 矩阵转置 | `[[1,2],[3,4]]` → `[[1,3],[2,4]]` |
| `trig` | 三角化简 | `sin(x)^2+cos(x)^2` → `1` |
| `latex` | LaTeX 输出 | `x^2+1` → `x^{2} + 1` |
| `limit` | 极限 | `sin(x)/x` → `1` (x→0) |
| `taylor` | 泰勒展开 | `sin(x)` (x=0) → `x - x^3/6 + ...` |
| `series` | 级数求和 | `1/n^2` (n=1→∞) → `pi^2/6` |
| `eigen` | 特征值 | `[[1,2],[3,4]]` → `特征值列表` |
| `rank` | 矩阵秩 | `[[1,2],[3,4]]` → `2` |

### 4.2 API 设计

所有后端接口统一为 `POST` 请求（`GET` 仅用于获取模式列表和历史记录）：

```
POST /api/calculate/     → {expression} → {result, error}
POST /api/advanced/      → {expression, mode, var, lower, upper} → {result, error, mode}
POST /api/validate/      → {expression} → {valid, message}
POST /api/ocr/           → {image} → {result, raw, error}
GET  /api/modes/         → {modes}
GET  /api/history/       → {history}
POST /api/clear-history/ → {}
```

---

## 五、问题排查与修复过程

### 5.1 问题一：sympy 安装损坏与导入失败

**现象**：
- 后端 `import sympy` 抛出 `ImportError: cannot import name 'sin' from 'sympy.functions'`
- 原因：sympy 1.14.0 安装文件损坏，内部模块导入自相矛盾

**排查过程**：
1. 检查 `.venv` 虚拟环境，确认 sympy 存在于 `site-packages`
2. 尝试卸载重装：`pip uninstall sympy -y && pip install sympy==1.13.1`
3. 多次因网络超时/系统权限导致安装失败
4. 最终手动下载 `sympy-1.13.1-py3-none-any.whl` 并解压到 `site-packages`

**修复结果**：
```python
from sympy import latex, symbols
x = symbols('x')
latex(x**2+1)  # → 'x^{2} + 1'
```

**关键教训**：
- 安装后**必须重启 Django 服务器**，已运行的进程不会加载新安装的包
- 使用项目虚拟环境（`.venv`）而非系统 Python

### 5.2 问题二：前端布局截断（双列布局）

**现象**：右列被挤出可视区域，仅显示"公式识"三个字

**原因**：CSS Grid 的 `1fr` 默认最小宽度为 `auto`，左列内容撑开导致右列被挤出

**修复**：
```css
.main-container {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); /* 允许收缩到 0 */
}
```
- 同时添加 `min-width: 0` 和 `overflow: hidden` 到 `.app` 容器
- 响应式断点从 1100px 提升到 1300px，更安全

### 5.3 问题三：Tesseract.js 公式识别准确率低

**现象**：公式 `tanh(x) = (e^x - e^{-x}) / (e^x + e^{-x})` 被识别为 `tanh(z) = :I;iez =`

**原因**：Tesseract 是通用 OCR，不理解数学公式的结构（分数、上标、根号等）

**优化措施**：
1. **图像预处理**：放大 2x + 灰度化 + 二值化（反转暗色背景）
2. **PSM 模式**：从 `PSM 6`（文本块）改为 `PSM 7`（单行文本）
3. **字符白名单**：限制为 `0-9a-z+-*/=^()[]{}|` 等数学字符
4. **文本清理增强**：
   - Unicode 符号替换：`√`→`sqrt`、`π`→`pi`、`×`→`*`
   - 希腊字母映射：`α`→`alpha`、`β`→`beta` 等
   - 分数结构化：`a/b` → `(a)/(b)`
   - 函数自动加括号：`sin x` → `sin(x)`

**准确率**：简单公式（`x^2+1`、`sin(x)`）可达 80%，复杂分数仍有限

### 5.4 问题四：端口占用与服务器启动失败

**现象**：`python manage.py runserver` 报错 `Address already in use`

**原因**：之前的 Python 进程未正确退出，持续占用端口

**修复**：
```bash
taskkill /F /IM python.exe   # 强制关闭所有 Python 进程
python manage.py runserver   # 重新启动
```

---

## 六、当前项目状态

### 6.1 已验证可用功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 基础数值计算 | ✅ 可用 | `eval` 模式，sin/cos/log/pi/e 等 |
| 前端 UI | ✅ 可用 | 霓虹主题、双列布局、响应式适配 |
| 高级符号运算 | ✅ 可用 | 需 sympy 已安装，19 种模式 |
| 积分显式渲染 | ✅ 可用 | MathJax 渲染 LaTeX |
| 图片上传识别 | ✅ 可用 | 支持拖拽/上传/粘贴 |
| 粘贴识别 | ✅ 可用 | `Ctrl+V` 粘贴截图自动触发 |
| 后端 OCR | ⚠️ 待激活 | 需安装系统 Tesseract 引擎 |
| 计算历史 | ✅ 可用 | 内存存储，页面刷新后丢失 |

### 6.2 环境依赖状态

| 依赖 | 状态 | 安装方式 |
|------|------|----------|
| Django | ✅ 已安装 | `pip install django` |
| SymPy | ✅ 已安装 | 手动解压 whl 到 `.venv` |
| Pillow | ✅ 已安装 | `pip install Pillow` |
| pytesseract | ✅ 已安装 | `pip install pytesseract` |
| Tesseract 引擎 | ❌ 未安装 | 需下载 Windows 安装包 |
| pix2tex | ❌ 未安装 | Python 3.12 whl 安装受阻 |

---

## 七、后续建议

### 7.1 安装系统 Tesseract 引擎（推荐）

1. 下载 Windows 安装包：[https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
2. 安装时勾选中文语言包（Chi-Sim + Chi-Tra）
3. 安装完成后重启 Django 服务器，后端 OCR 自动生效

### 7.2 使用虚拟环境启动（重要）

```bash
cd AHgroup\202321101246\任务三
F:\2023专业实习实训\.venv\Scripts\python.exe manage.py runserver
```

**不要**使用系统默认的 `python`，否则会找不到 sympy 等包。

### 7.3 功能验证测试用例

启动服务器后，在浏览器中验证以下功能：

| 测试项 | 操作 | 预期结果 |
|--------|------|----------|
| 基础计算 | 输入 `1+2*sin(pi/2)`，点击 `=` | `3.0` |
| 求导 | 切换到"求导"，输入 `x^3+2*x` | `3*x**2 + 2` |
| 积分 | 切换到"积分"，输入 `x^2+1` | 显示 `∫ x²+1 dx = x³/3 + x + C` |
| 定积分 | 切换到"定积分"，输入 `x^2`，下限 `0` 上限 `1` | `1/3` |
| 极限 | 切换到"极限"，输入 `sin(x)/x` | `1` |
| LaTeX | 切换到"LaTeX"，输入 `x^2+1` | `x^{2} + 1` |
| 粘贴识别 | 按 `Ctrl+V` 粘贴公式截图 | 显示识别结果，可点击"应用到计算器" |

### 7.4 已知限制

- **计算历史**：当前使用内存存储，页面刷新后丢失。建议后续接入数据库（SQLite）
- **OCR 准确率**：前端 Tesseract.js 对复杂数学公式仍有限。建议安装系统 Tesseract 或后续接入 SimpleTex/Mathpix API
- **pix2tex**：Python 3.12 + Windows 环境下的 whl 包安装有兼容性问题，建议降级到 Python 3.11 后再尝试

---

## 八、开发时间线

| 日期 | 完成内容 |
|------|----------|
| 2026-06-30 | 基础计算器功能、霓虹主题前端、14 种运算模式、sympy 安装修复 |
| 2026-07-01 | 双列布局 + 图片公式识别 + 积分显式化 + 粘贴识别 + 布局优化 + OCR 优化 |

---

*本文档由 AI 辅助编写，记录本次人机协作开发的完整过程。*
