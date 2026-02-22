
# ==============================================================================
# [AUTO-INJECTED RESOURCE] PolynomialOps
# ==============================================================================
class PolynomialOps:
    """多項式運算模組 - 四則運算與 LaTeX 格式化 (降冪係數列表)"""

    @staticmethod
    def normalize(coeffs):
        """移除前導零，例: [0, 0, 3, -1] -> [3, -1]；全零回傳 [0]"""
        if not coeffs:
            return [0]
        i = 0
        while i < len(coeffs) - 1 and coeffs[i] == 0:
            i += 1
        return list(coeffs[i:])

    @staticmethod
    def format_latex(coeffs, var='x'):
        """係數列表 (降冪) → LaTeX 字串，例: [3, -2, 1] → '3x^{2} - 2x + 1'"""
        coeffs = PolynomialOps.normalize(coeffs)
        if all(c == 0 for c in coeffs):
            return '0'
        degree = len(coeffs) - 1
        parts = []
        for i, c in enumerate(coeffs):
            d = degree - i
            if c == 0:
                continue
            abs_c = abs(c)
            coeff_str = '' if abs_c == 1 and d > 0 else str(abs_c)
            if d == 0:
                var_str = str(abs_c)
            elif d == 1:
                var_str = f'{coeff_str}{var}'
            else:
                var_str = f'{coeff_str}{var}^{{{d}}}'
            if not parts:
                sign_str = '-' if c < 0 else ''
            else:
                sign_str = ' - ' if c < 0 else ' + '
            parts.append(f'{sign_str}{var_str}')
        return ''.join(parts) if parts else '0'

    @staticmethod
    def format_plain(coeffs, var='x'):
        """係數列表 (降冪) → 純文字字串（用於答案），例: [3, -2, 1] → '3x^2-2x+1'"""
        coeffs = PolynomialOps.normalize(coeffs)
        if all(c == 0 for c in coeffs):
            return '0'
        degree = len(coeffs) - 1
        parts = []
        for i, c in enumerate(coeffs):
            d = degree - i
            if c == 0:
                continue
            abs_c = abs(c)
            coeff_str = '' if abs_c == 1 and d > 0 else str(abs_c)
            if d == 0:
                var_str = str(abs_c)
            elif d == 1:
                var_str = f'{coeff_str}{var}'
            else:
                var_str = f'{coeff_str}{var}^{d}'
            if not parts:
                sign_str = '-' if c < 0 else ''
            else:
                sign_str = '-' if c < 0 else '+'
            parts.append(f'{sign_str}{var_str}')
        return ''.join(parts) if parts else '0'

    @staticmethod
    def add(c1, c2):
        """多項式加法：輸入兩個係數列表，回傳結果係數列表"""
        max_len = max(len(c1), len(c2))
        p1 = [0] * (max_len - len(c1)) + list(c1)
        p2 = [0] * (max_len - len(c2)) + list(c2)
        return PolynomialOps.normalize([a + b for a, b in zip(p1, p2)])

    @staticmethod
    def sub(c1, c2):
        """多項式減法：c1 - c2"""
        max_len = max(len(c1), len(c2))
        p1 = [0] * (max_len - len(c1)) + list(c1)
        p2 = [0] * (max_len - len(c2)) + list(c2)
        return PolynomialOps.normalize([a - b for a, b in zip(p1, p2)])

    @staticmethod
    def mul(c1, c2):
        """多項式乘法"""
        if not c1 or not c2:
            return [0]
        result = [0] * (len(c1) + len(c2) - 1)
        for i, a in enumerate(c1):
            for j, b in enumerate(c2):
                result[i + j] += a * b
        return PolynomialOps.normalize(result)

    @staticmethod
    def random_poly(degree, range_val=(-5, 5)):
        """生成隨機多項式係數（最高項非零）"""
        choices_nonzero = [x for x in range(range_val[0], range_val[1] + 1) if x != 0]
        coeffs = []
        for i in range(degree + 1):
            if i == 0:
                coeffs.append(random.choice(choices_nonzero))
            else:
                coeffs.append(random.randint(range_val[0], range_val[1]))
        return coeffs


# ============================================================================
# [V2.5 新增] FractionOps - 分數標準函數庫
# ============================================================================

# [Global Aliases for PolynomialOps]
poly_normalize = PolynomialOps.normalize
poly_format_latex = PolynomialOps.format_latex
poly_format_plain = PolynomialOps.format_plain
poly_add = PolynomialOps.add
poly_sub = PolynomialOps.sub
poly_mul = PolynomialOps.mul
poly_random = PolynomialOps.random_poly


def generate(level=1, **kwargs):
    question_text = ''
    if level == 1:
        p1 = PolynomialOps.random_poly(2, (-5, 5))
        p2 = PolynomialOps.random_poly(2, (-5, 5))
        op = random.choice(['+', '-'])
        expr = PolynomialOps.format_latex(p1, 'x') + op + PolynomialOps.format_latex(p2, 'x')
        question_text = f'計算 {expr}。'
        result = PolynomialOps.sub(p1, p2) if op == '-' else PolynomialOps.add(p1, p2)
        answer = PolynomialOps.format_plain(result, 'x')
        correct_answer = answer
    elif level == 2:
        p1 = PolynomialOps.random_poly(2, (-5, 5))
        p2 = PolynomialOps.random_poly(2, (-5, 5))
        question_text = f"展開並化簡 ${PolynomialOps.format_latex(p1, 'x')}\\cdot{PolynomialOps.format_latex(p2, 'x')}$。"
        result = PolynomialOps.mul(p1, p2)
        answer = PolynomialOps.format_plain(result, 'x')
        correct_answer = answer
    elif level == 3:
        p1 = PolynomialOps.random_poly(2, (-5, 5))
        p2 = PolynomialOps.random_poly(2, (-5, 5))
        result = PolynomialOps.add(p1, p2)
        question_text = f"已知 $P_1 = {PolynomialOps.format_latex(p1, 'x')}$,$P_2 = {PolynomialOps.format_latex(p2, 'x')}$,求 $P_1 + P_2$。"
        answer = PolynomialOps.format_plain(result, 'x')
        correct_answer = answer
    return {'question_text': question_text, 'answer': answer, 'correct_answer': correct_answer, 'mode': level}