import math

class Token:
    """词法单元"""
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return f"Token({self.type}, {self.value})"
        return f"Token({self.type})"


# 支持的函数和常量映射
MATH_FUNCS = {
    'pow': lambda a, b: a ** b,
    'sin': lambda a: math.sin(a),
    'cos': lambda a: math.cos(a),
    'tan': lambda a: math.tan(a),
    'asin': lambda a: math.asin(a),
    'acos': lambda a: math.acos(a),
    'atan': lambda a: math.atan(a),
    'log': lambda a: math.log10(a),
    'ln': lambda a: math.log(a),
    'exp': lambda a: math.exp(a),
    'sqrt': lambda a: math.sqrt(a),
    'abs': lambda a: abs(a),
    'floor': lambda a: math.floor(a),
    'ceil': lambda a: math.ceil(a),
    'round': lambda a: round(a),
    'deg': lambda a: math.degrees(a),
    'rad': lambda a: math.radians(a),
}

MATH_CONSTS = {
    'pi': math.pi,
    'e': math.e,
}

SINGLE_ARG_FUNCS = {'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'log', 'ln', 'exp', 'sqrt', 'abs', 'floor', 'ceil', 'round', 'deg', 'rad'}
DOUBLE_ARG_FUNCS = {'pow'}

class Tokenizer:
    """词法分析器：将输入字符串拆分为 Token 列表"""
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def skip_spaces(self):
        """跳过空白字符"""
        while self.pos < self.length and self.text[self.pos] == ' ':
            self.pos += 1

    def number(self):
        """解析数字（整数或浮点数）"""
        self.skip_spaces()
        start = self.pos
        has_dot = False
        while self.pos < self.length and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
            if self.text[self.pos] == '.':
                if has_dot:
                    break
                has_dot = True
            self.pos += 1
        num_str = self.text[start:self.pos]
        if not num_str:
            raise ValueError("Expected number")
        return float(num_str) if has_dot else int(num_str)

    def identifier(self):
        """解析标识符（函数名或常量名）"""
        self.skip_spaces()
        start = self.pos
        while self.pos < self.length and (self.text[self.pos].isalpha() or self.text[self.pos] == '_'):
            self.pos += 1
        return self.text[start:self.pos]

    def tokenize(self):
        """将表达式字符串转换为 Token 列表"""
        tokens = []
        while self.pos < self.length:
            self.skip_spaces()
            if self.pos >= self.length:
                break

            ch = self.text[self.pos]

            if ch.isdigit():
                tokens.append(Token('NUMBER', self.number()))
            elif ch == '+':
                tokens.append(Token('PLUS'))
                self.pos += 1
            elif ch == '-':
                tokens.append(Token('MINUS'))
                self.pos += 1
            elif ch == '*':
                tokens.append(Token('MULTIPLY'))
                self.pos += 1
            elif ch == '/':
                tokens.append(Token('DIVIDE'))
                self.pos += 1
            elif ch == '^':
                tokens.append(Token('POWER'))
                self.pos += 1
            elif ch == '(':
                tokens.append(Token('LPAREN'))
                self.pos += 1
            elif ch == ')':
                tokens.append(Token('RPAREN'))
                self.pos += 1
            elif ch == ',':
                tokens.append(Token('COMMA'))
                self.pos += 1
            elif ch.isalpha():
                ident = self.identifier()
                if ident in MATH_FUNCS:
                    tokens.append(Token('IDENTIFIER', ident))
                elif ident in MATH_CONSTS:
                    tokens.append(Token('NUMBER', MATH_CONSTS[ident]))
                else:
                    raise ValueError(f"Unknown function or constant: '{ident}'")
            else:
                raise ValueError(f"Invalid character: '{ch}'")

        tokens.append(Token('EOF'))
        return tokens


class Parser:
    """语法分析器：递归下降解析 Token 列表并求值"""
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        """获取当前 Token"""
        return self.tokens[self.pos]

    def advance(self):
        """前进到下一个 Token"""
        self.pos += 1

    def expect(self, type_):
        """期望当前 Token 为指定类型，否则报错"""
        if self.current().type != type_:
            raise ValueError(f"Expected '{type_}', but found '{self.current().type}'")
        self.advance()

    def parse(self):
        """入口：解析整个表达式"""
        result = self.expression()
        if self.current().type != 'EOF':
            raise ValueError(f"Unexpected token '{self.current().type}' at end of expression")
        return result

    # expression = term { ('+' | '-') term }
    def expression(self):
        left = self.term()
        while self.current().type in ('PLUS', 'MINUS'):
            op = self.current().type
            self.advance()
            right = self.term()
            if op == 'PLUS':
                left = left + right
            else:
                left = left - right
        return left

    # term = power { ('*' | '/') power }
    def term(self):
        left = self.power()
        while self.current().type in ('MULTIPLY', 'DIVIDE'):
            op = self.current().type
            self.advance()
            right = self.power()
            if op == 'MULTIPLY':
                left = left * right
            else:
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                left = left / right
        return left

    # power = unary [ '^' power ]  （右结合）
    def power(self):
        left = self.unary()
        if self.current().type == 'POWER':
            self.advance()
            right = self.power()  # 递归实现右结合
            left = left ** right
        return left

    # unary = ('+' | '-') unary | primary
    def unary(self):
        if self.current().type in ('PLUS', 'MINUS'):
            op = self.current().type
            self.advance()
            operand = self.unary()
            return operand if op == 'PLUS' else -operand
        return self.primary()

    # primary = number | '(' expression ')' | func_call
    def primary(self):
        token = self.current()

        if token.type == 'NUMBER':
            self.advance()
            return token.value

        elif token.type == 'LPAREN':
            self.advance()
            val = self.expression()
            self.expect('RPAREN')
            return val

        elif token.type == 'IDENTIFIER':
            func_name = token.value
            self.advance()
            self.expect('LPAREN')

            if func_name in SINGLE_ARG_FUNCS:
                # 单参数函数
                arg = self.expression()
                self.expect('RPAREN')
                return MATH_FUNCS[func_name](arg)
            elif func_name in DOUBLE_ARG_FUNCS:
                # 双参数函数
                if self.current().type == 'COMMA':
                    left = 0
                else:
                    left = self.expression()
                self.expect('COMMA')
                right = self.expression()
                self.expect('RPAREN')
                return MATH_FUNCS[func_name](left, right)
            else:
                raise ValueError(f"Unsupported function: '{func_name}'")

        else:
            raise ValueError(f"Unexpected token: '{token.type}'")


def evaluate(expr):
    """对外接口：计算表达式字符串的值"""
    tokenizer = Tokenizer(expr)
    tokens = tokenizer.tokenize()
    parser = Parser(tokens)
    return parser.parse()
