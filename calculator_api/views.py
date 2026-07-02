import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .calculator_core import evaluate

# sympy 可选导入（高级符号运算需要）
try:
    import sympy as sp
    from sympy import symbols, simplify, factor, solve, diff, integrate, Matrix, sin, cos, tan, asin, acos, atan, log, exp, pi, E, sqrt, Rational, latex, expand, trigsimp, expand_trig, limit, oo, summation, Symbol, Integral
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    sp = None

# 内存历史记录（生产环境应使用数据库）
_calc_history = []
_MAX_HISTORY = 50


def _add_history(expression, result, error=None, mode='eval'):
    """添加计算记录到内存历史"""
    global _calc_history
    _calc_history.insert(0, {
        'expression': expression,
        'result': result,
        'error': error,
        'mode': mode,
    })
    if len(_calc_history) > _MAX_HISTORY:
        _calc_history = _calc_history[:_MAX_HISTORY]


# ===== 基础计算 API =====

@csrf_exempt
def calculate_api(request):
    """基础数值计算 API"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求体必须是有效的 JSON'}, status=400)

    expression = data.get('expression', '').strip()
    if not expression:
        return JsonResponse({'error': '请输入表达式'})

    try:
        result = evaluate(expression)
        _add_history(expression, str(result), None, 'eval')
        return JsonResponse({'result': str(result), 'error': None, 'mode': 'eval'})
    except ZeroDivisionError as e:
        _add_history(expression, None, str(e), 'eval')
        return JsonResponse({'result': None, 'error': f'除零错误: {e}'})
    except ValueError as e:
        _add_history(expression, None, str(e), 'eval')
        return JsonResponse({'result': None, 'error': f'表达式错误: {e}'})
    except Exception as e:
        _add_history(expression, None, str(e), 'eval')
        return JsonResponse({'result': None, 'error': f'计算错误: {e}'})


# ===== 高级计算 API =====

@csrf_exempt
def advanced_api(request):
    """高级符号运算 API
    
    支持的 mode:
    - eval:       数值计算
    - simplify:   表达式化简
    - factor:     因式分解
    - solve:      方程求解
    - diff:       求导
    - integrate:  不定积分
    - definite:   定积分
    - matrix:     矩阵运算
    - det:        行列式
    - inv:        矩阵逆
    - transpose:  矩阵转置
    - trig:       三角函数化简/展开
    - expand:     表达式展开
    - latex:      LaTeX 输出
    """
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求体必须是有效的 JSON'}, status=400)

    expression = data.get('expression', '').strip()
    mode = data.get('mode', 'eval').strip().lower()
    var = data.get('var', 'x').strip()
    lower = data.get('lower', '')
    upper = data.get('upper', '')

    if not expression:
        return JsonResponse({'error': '请输入表达式'})

    if not SYMPY_AVAILABLE and mode != 'eval':
        return JsonResponse({'result': None, 'error': '高级符号运算需要安装 sympy（当前环境未安装）', 'mode': mode})

    try:
        result = _process_advanced(expression, mode, var, lower, upper)
        _add_history(expression, str(result), None, mode)
        return JsonResponse({'result': str(result), 'error': None, 'mode': mode})
    except Exception as e:
        _add_history(expression, None, str(e), mode)
        return JsonResponse({'result': None, 'error': str(e), 'mode': mode})
    except Exception as e:
        _add_history(expression, None, str(e), mode)
        return JsonResponse({'result': None, 'error': str(e), 'mode': mode})


def _process_advanced(expr, mode, var='x', lower='', upper=''):
    """处理高级运算"""
    
    # 定义常用符号
    x = symbols(var)
    
    # 预处理表达式
    expr = expr.replace('^', '**')
    
    if mode == 'eval':
        # 数值计算：优先用 sympy 精确计算，不可用则回退到基础计算器
        if SYMPY_AVAILABLE:
            parsed = sp.sympify(expr)
            return sp.N(parsed)
        else:
            return evaluate(expression)
    
    elif mode == 'simplify':
        # 表达式化简
        parsed = sp.sympify(expr)
        return simplify(parsed)
    
    elif mode == 'factor':
        # 因式分解
        parsed = sp.sympify(expr)
        return factor(parsed)
    
    elif mode == 'expand':
        # 表达式展开
        parsed = sp.sympify(expr)
        return expand(parsed)
    
    elif mode == 'solve':
        # 方程求解
        # 支持 '=' 和 '==' 分隔
        if '=' in expr and '==' not in expr:
            expr = expr.replace('=', '==')
        parsed = sp.sympify(expr)
        solutions = solve(parsed, x)
        if not solutions:
            return "无解"
        return "; ".join([str(s) for s in solutions])
    
    elif mode == 'diff':
        # 求导
        parsed = sp.sympify(expr)
        return diff(parsed, x)
    
    elif mode == 'integrate':
        # 不定积分 - 显式积分符号
        parsed = sp.sympify(expr)
        result = integrate(parsed, x)
        latex_expr = latex(parsed)
        latex_result = latex(result)
        return f"\\(\\int {latex_expr} \\, d{x} = {latex_result} + C\\)"
    
    elif mode == 'definite':
        # 定积分 - 显式积分符号（上下限）
        if not lower or not upper:
            raise ValueError('定积分需要输入下限和上限')
        parsed = sp.sympify(expr)
        a_val = sp.sympify(lower)
        b_val = sp.sympify(upper)
        result = integrate(parsed, (x, a_val, b_val))
        latex_expr = latex(parsed)
        latex_a = latex(a_val)
        latex_b = latex(b_val)
        latex_result = latex(result)
        return f"\\(\\int_{{{latex_a}}}^{{{latex_b}}} {latex_expr} \\, d{x} = {latex_result}\\)"
    
    elif mode == 'matrix':
        # 矩阵运算（直接解析矩阵表达式）
        return _process_matrix(expr)
    
    elif mode == 'det':
        # 行列式
        mat = _parse_matrix(expr)
        return mat.det()
    
    elif mode == 'inv':
        # 矩阵逆
        mat = _parse_matrix(expr)
        return mat.inv()
    
    elif mode == 'transpose':
        # 矩阵转置
        mat = _parse_matrix(expr)
        return mat.T
    
    elif mode == 'trig':
        # 三角函数化简/展开
        parsed = sp.sympify(expr)
        expanded = expand_trig(parsed)
        simplified = trigsimp(parsed)
        if expanded == simplified:
            return simplified
        return f"展开: {expanded}\n化简: {simplified}"
    
    elif mode == 'latex':
        # LaTeX 输出
        parsed = sp.sympify(expr)
        return latex(parsed)
    
    elif mode == 'limit':
        # 极限计算
        parsed = sp.sympify(expr)
        return sp.limit(parsed, x, 0)
    
    elif mode == 'taylor':
        # 泰勒展开 (在 x=0 处展开到 6 阶)
        parsed = sp.sympify(expr)
        return sp.series(parsed, x, 0, 6).removeO()
    
    elif mode == 'series':
        # 级数求和
        parsed = sp.sympify(expr)
        return sp.summation(parsed, (x, 1, oo))
    
    elif mode == 'eigen':
        # 矩阵特征值
        mat = _parse_matrix(expr)
        return mat.eigenvals()
    
    elif mode == 'rank':
        # 矩阵秩
        mat = _parse_matrix(expr)
        return mat.rank()
    
    else:
        raise ValueError(f'不支持的运算模式: {mode}')


def _preprocess_matrix_expr(expr_str):
    """将 [[a,b],[c,d]] 格式转换为 Matrix([[a,b],[c,d]]) 格式"""
    import ast
    result = []
    i = 0
    n = len(expr_str)
    while i < n:
        if expr_str[i:i+2] == '[[':
            depth = 0
            start = i
            j = i
            while j < n:
                if expr_str[j] == '[':
                    depth += 1
                elif expr_str[j] == ']':
                    depth -= 1
                    if depth == 0 and j > start + 1:
                        matrix_str = expr_str[start:j+1]
                        try:
                            ast.literal_eval(matrix_str)
                            result.append(f"Matrix({matrix_str})")
                        except:
                            result.append(matrix_str)
                        i = j + 1
                        break
                j += 1
            else:
                result.append(expr_str[i])
                i += 1
        else:
            result.append(expr_str[i])
            i += 1
    return ''.join(result)


def _parse_matrix(expr_str):
    """解析矩阵字符串，支持 [[a,b],[c,d]] 格式"""
    expr_str = _preprocess_matrix_expr(expr_str.strip())
    try:
        result = sp.sympify(expr_str)
        return result
    except Exception as e:
        raise ValueError(f'矩阵解析失败: {e}。请使用格式如 [[1,2],[3,4]]')


def _process_matrix(expr_str):
    """处理矩阵表达式"""
    expr_str = _preprocess_matrix_expr(expr_str.strip())
    try:
        result = sp.sympify(expr_str)
        return result
    except Exception:
        raise ValueError('矩阵表达式解析失败。请确保格式正确，如 [[1,2],[3,4]] + [[5,6],[7,8]]')


# ===== 历史记录 API =====

def history_api(request):
    """获取计算历史 API"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)
    return JsonResponse({'history': _calc_history[:20]})


@csrf_exempt
def clear_history_api(request):
    """清空历史记录 API"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)
    global _calc_history
    _calc_history = []
    return JsonResponse({'success': True})


# ===== 验证 API =====

@csrf_exempt
def validate_api(request):
    """验证表达式语法 API"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求体必须是有效的 JSON'}, status=400)

    expression = data.get('expression', '').strip()
    if not expression:
        return JsonResponse({'valid': False, 'message': '空表达式'})

    # 基础字符检查
    allowed_pattern = re.compile(r'^[\d\s\+\-\*\/\^\(\)\,\.a-zA-Z\[\]\=\;\:]+$')
    if not allowed_pattern.match(expression):
        return JsonResponse({'valid': False, 'message': '包含非法字符'})

    # 括号匹配检查
    stack = []
    for ch in expression:
        if ch in '([{':
            stack.append(ch)
        elif ch in ')]}':
            if not stack:
                return JsonResponse({'valid': False, 'message': '括号不匹配：多余的右括号'})
            stack.pop()
    if stack:
        return JsonResponse({'valid': False, 'message': '括号不匹配：存在未闭合的左括号'})

    # 尝试用计算器解析验证
    try:
        if SYMPY_AVAILABLE:
            sp.sympify(expression.replace('^', '**'))
        else:
            evaluate(expression)
        return JsonResponse({'valid': True, 'message': '表达式合法'})
    except Exception as e:
        return JsonResponse({'valid': False, 'message': f'语法错误: {e}'})


# ===== OCR API =====

OCR_AVAILABLE = False
OCR_ERROR = ''
try:
    import pytesseract
    from PIL import Image
    import io
    import base64
    OCR_AVAILABLE = True
except ImportError as e:
    OCR_ERROR = str(e)


def _clean_ocr_text(text):
    """清理 OCR 识别出的数学公式文本"""
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = ' '.join(text.split())
    replacements = {
        '−': '-', '–': '-', '—': '-',
        '×': '*', '·': '*', '⋅': '*',
        '÷': '/',
        'π': 'pi', 'Pi': 'pi',
        'sqrt': 'sqrt', 'SQRT': 'sqrt',
        'sin': 'sin', 'cos': 'cos', 'tan': 'tan',
        'log': 'log', 'ln': 'log',
        'exp': 'exp',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


@csrf_exempt
def ocr_api(request):
    """图片公式识别 OCR API
    
    接收 base64 编码的图片，返回识别出的数学公式文本
    """
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    if not OCR_AVAILABLE:
        return JsonResponse({
            'result': None,
            'error': f'OCR 功能需要安装 pytesseract 和 Pillow。当前环境未安装。',
            'hint': '安装命令: pip install pytesseract Pillow'
        })

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求体必须是有效的 JSON'}, status=400)

    image_data = data.get('image', '')
    if not image_data:
        return JsonResponse({'error': '请提供图片数据'})

    try:
        # 支持 data:image/xxx;base64, 格式或纯 base64
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 使用 pytesseract 识别
        text = pytesseract.image_to_string(image, config='--psm 6')
        cleaned = _clean_ocr_text(text)
        
        return JsonResponse({
            'result': cleaned,
            'raw': text,
            'error': None,
        })
    except Exception as e:
        return JsonResponse({'result': None, 'error': f'OCR 识别失败: {e}'})


def modes_api(request):
    """获取所有支持的运算模式"""
    if request.method != 'GET':
        return JsonResponse({'error': '仅支持 GET 请求'}, status=405)
    
    modes = [
        {'id': 'eval', 'name': '数值计算', 'desc': '计算表达式的数值结果', 'icon': 'calculate'},
        {'id': 'simplify', 'name': '化简', 'desc': '化简代数表达式', 'icon': 'compress'},
        {'id': 'factor', 'name': '因式分解', 'desc': '将多项式因式分解', 'icon': 'split'},
        {'id': 'expand', 'name': '展开', 'desc': '展开括号表达式', 'icon': 'expand'},
        {'id': 'solve', 'name': '方程求解', 'desc': '求解方程，如 x**2-1=0', 'icon': 'search'},
        {'id': 'diff', 'name': '求导', 'desc': '对表达式求导', 'icon': 'trending_up'},
        {'id': 'integrate', 'name': '不定积分', 'desc': '计算不定积分', 'icon': 'functions'},
        {'id': 'definite', 'name': '定积分', 'desc': '计算定积分，需输入上下限', 'icon': 'integration_instructions'},
        {'id': 'matrix', 'name': '矩阵运算', 'desc': '矩阵加减乘运算', 'icon': 'grid_on'},
        {'id': 'det', 'name': '行列式', 'desc': '计算矩阵行列式', 'icon': 'detailed'},
        {'id': 'inv', 'name': '矩阵逆', 'desc': '计算矩阵的逆', 'icon': 'flip'},
        {'id': 'transpose', 'name': '转置', 'desc': '矩阵转置', 'icon': 'flip_to_front'},
        {'id': 'trig', 'name': '三角函数', 'desc': '三角函数化简与展开', 'icon': 'waves'},
        {'id': 'latex', 'name': 'LaTeX', 'desc': '输出 LaTeX 格式', 'icon': 'code'},
        {'id': 'limit', 'name': '极限', 'desc': '计算函数极限', 'icon': 'trending_flat'},
        {'id': 'taylor', 'name': '泰勒展开', 'desc': '在x=0处泰勒展开', 'icon': 'polymer'},
        {'id': 'series', 'name': '级数', 'desc': '级数求和', 'icon': 'sigma'},
        {'id': 'eigen', 'name': '特征值', 'desc': '计算矩阵特征值', 'icon': 'flash_on'},
        {'id': 'rank', 'name': '矩阵秩', 'desc': '计算矩阵的秩', 'icon': 'format_list_numbered'},
    ]
    return JsonResponse({'modes': modes})
