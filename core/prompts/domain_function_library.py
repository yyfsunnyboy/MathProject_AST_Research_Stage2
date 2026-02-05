# ============================================================================
# Domain-Based 標準函數庫
# [V47.14] 為每個數學領域定義標準工具函數，強制 LLM 引用而非自創
# ============================================================================
"""
此模組定義了各個數學領域的標準工具函數。
所有 LLM（Gemini / 14B / 7B）在生成代碼時，必須引用這些預定義函數，禁止自創同名或類似功能的函數。

Domain 分類：
1. Polynomial (多項式): 多項式運算、求導、因式分解
2. Geometry (幾何): 點、線、圓、三角形運算
3. Trigonometry (三角函數): 角度轉換、三角恆等式
4. Algebra (代數): 方程組、不等式、絕對值
5. Probability (機率): 排列組合、機率計算
6. Vector (向量): 向量運算、內積外積
7. Calculus (微積分): 導數、極值、應用問題

⚠️ 命名規範（參考 Example_Program_Research.py）：
1. 全局工具函數（系統預載）：fmt_num(), to_latex(), clean_latex_output(), safe_choice()
2. Domain 輔助函數（下方定義）：_poly_to_latex(), _differentiate_poly() 等（以 _ 開頭）
3. 變量命名約定：q = 題目字符串, a = 答案字符串
4. 返回格式（固定）：
   return {
       'question_text': q,
       'correct_answer': a,
       'answer': a,         # ⚠️ 必須同時包含此鍵
       'mode': 1
   }

⚠️ 代碼安全規範（避免無限迴圈）：
1. 禁止使用 while 迴圈生成不重複隨機元素
2. 優先使用「洗牌 + 切片」模式：
   ```python
   # ✅ 正確：先洗牌，再切片
   available = list(range(max_val + 1))
   random.shuffle(available)
   selected = available[:num_needed]
   ```
3. 如果確實需要 while，必須確保條件可達成：
   ```python
   # 確保 num_terms <= 可選數量
   num_terms = random.randint(3, min(5, max_degree + 1))
   ```
"""

# ============================================================================
# Domain 1: POLYNOMIAL (多項式)
# ============================================================================

POLYNOMIAL_HELPERS = r"""
# ===== 多項式標準函數庫 =====

# 🔴 答案格式：純多項式逗號分隔（例："36x^2+10,72x"）
#    ✅ 用 _format_polynomial_for_answer() 組答案，再 ','.join()
#    ❌ 禁止：_deriv_symbol_plain() 只用於題目，不用於答案
#    ❌ 禁止：換行分隔 '\n'.join()

def _coeffs_to_terms(coeffs):
    '''係數列表 [a_n,...,a_0] → terms [(c,e),...]'''
    degree = len(coeffs) - 1
    return [(coeffs[i], degree - i) for i in range(len(coeffs))]

def _poly_to_latex(terms):
    '''terms → LaTeX (不含$)，例: [(3,2),(-5,0)] → "3x^{2} - 5"'''
    if not terms:
        return '0'
    parts = []
    for i, (c, e) in enumerate(sorted(terms, key=lambda x: x[1], reverse=True)):
        if c == 0:
            continue
        sign = '' if i == 0 else (' + ' if c > 0 else ' - ')
        abs_c = abs(c)
        coeff_str = '' if (abs_c == 1 and e > 0) else str(abs_c)
        if e == 0:
            var_str = str(abs_c)
        elif e == 1:
            var_str = f'{coeff_str}x' if coeff_str else 'x'
        else:
            var_str = f'{coeff_str}x^{{{e}}}' if coeff_str else f'x^{{{e}}}'
        parts.append(f'{sign}{var_str}')
    return ''.join(parts).strip()

def _poly_to_plain(terms):
    '''terms → 純文本答案格式 (無空格)，例: "3x^2-5"'''
    if not terms:
        return '0'
    parts = []
    for i, (c, e) in enumerate(sorted(terms, key=lambda x: x[1], reverse=True)):
        if c == 0:
            continue
        sign = '' if i == 0 else ('+' if c > 0 else '-')
        abs_c = abs(c)
        coeff_str = '' if (abs_c == 1 and e > 0) else str(abs_c)
        if e == 0:
            var_str = str(abs_c)
        elif e == 1:
            var_str = f'{coeff_str}x' if coeff_str else 'x'
        else:
            var_str = f'{coeff_str}x^{e}' if coeff_str else f'x^{e}'
        parts.append(f'{sign}{var_str}')
    return ''.join(parts).strip()

def _differentiate_poly(terms, order=1):
    '''求導 order 次，返回新 terms'''
    result = list(terms)
    for _ in range(order):
        new_terms = []
        for c, e in result:
            if e > 0:
                new_c = c * e
                if abs(new_c) > 10000:
                    raise ValueError(f"Coefficient {new_c} exceeds limit")
                new_terms.append((new_c, e - 1))
        result = new_terms
    return result

def _deriv_symbol_latex(order):
    '''導數符號 LaTeX: f'(x), f''(x), f^{(n)}(x)'''
    if order == 1:
        return "f'(x)"
    elif order == 2:
        return "f''(x)"
    else:
        return f"f^{{({order})}}(x)"

def _deriv_symbol_plain(order):
    '''導數符號純文本: f'(x), f''(x), f^(n)(x)'''
    if order == 1:
        return "f'(x)"
    elif order == 2:
        return "f''(x)"
    else:
        return f"f^({order})(x)"

def _format_polynomial_for_answer(terms):
    '''Format polynomial terms for answer display - use plain text, no LaTeX brackets
    Examples:
      _format_polynomial_for_answer([(36, 3), (27, 2), (16, 1)]) → "36x^3+27x^2+16x"
      _format_polynomial_for_answer([(216, 1), (54, 0)]) → "216x+54"
    '''
    return _poly_to_plain(terms)
"""

# ============================================================================
# Domain 2: GEOMETRY (幾何)
# ============================================================================

GEOMETRY_HELPERS = """
# ===== 幾何標準函數庫 =====

def _distance_2d(x1, y1, x2, y2):
    '''計算兩點距離'''
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def _midpoint_2d(x1, y1, x2, y2):
    '''計算中點座標'''
    return ((x1 + x2) / 2, (y1 + y2) / 2)

def _slope(x1, y1, x2, y2):
    '''計算斜率（處理垂直線）'''
    if x2 == x1:
        return None  # 垂直線
    return (y2 - y1) / (x2 - x1)

def _line_equation_latex(m, b):
    '''生成直線方程式 y = mx + b 的 LaTeX'''
    if m is None:
        return "x = ..."  # 需要額外處理
    b_str = f" + {b}" if b >= 0 else f" - {abs(b)}"
    return f"y = {m}x{b_str}"

def _point_to_line_dist(px, py, a, b, c):
    '''點到直線 ax + by + c = 0 的距離'''
    return abs(a * px + b * py + c) / math.sqrt(a**2 + b**2)
"""

# ============================================================================
# Domain 3: TRIGONOMETRY (三角函數)
# ============================================================================

TRIGONOMETRY_HELPERS = """
# ===== 三角函數標準函數庫 =====

def _deg_to_rad(degrees):
    '''角度轉弧度'''
    return degrees * math.pi / 180

def _rad_to_deg(radians):
    '''弧度轉角度'''
    return radians * 180 / math.pi

def _normalize_angle(theta, unit='deg'):
    '''正規化角度到 [0, 360) 或 [0, 2π)'''
    if unit == 'deg':
        return theta % 360
    else:
        return theta % (2 * math.pi)

def _trig_value_latex(func_name, angle, exact=True):
    '''生成三角函數值的 LaTeX（支持特殊角精確值）'''
    # 實現特殊角的精確值輸出，例如 sin(30°) = 1/2
    pass
"""

# ============================================================================
# Domain 4: ALGEBRA (代數)
# ============================================================================

ALGEBRA_HELPERS = """
# ===== 代數標準函數庫 =====

def _solve_linear_2x2(a1, b1, c1, a2, b2, c2):
    '''
    解二元一次方程組
    a1*x + b1*y = c1
    a2*x + b2*y = c2
    返回: (x, y) 或 None（無解/無限多解）
    '''
    det = a1 * b2 - a2 * b1
    if det == 0:
        return None
    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det
    return (x, y)

def _quadratic_formula(a, b, c):
    '''
    求解一元二次方程 ax² + bx + c = 0
    返回: (x1, x2) 或 None（無實根）
    '''
    discriminant = b**2 - 4*a*c
    if discriminant < 0:
        return None
    x1 = (-b + math.sqrt(discriminant)) / (2*a)
    x2 = (-b - math.sqrt(discriminant)) / (2*a)
    return (x1, x2)
"""

# ============================================================================
# Domain 5: PROBABILITY (機率)
# ============================================================================

PROBABILITY_HELPERS = """
# ===== 機率標準函數庫 =====
# (已在 MASTER_SPEC 注入的工具中定義 nCr, nPr)

def _probability_latex(numerator, denominator):
    '''生成機率的 LaTeX 分數表示'''
    from fractions import Fraction
    frac = Fraction(numerator, denominator)
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"\\\\frac{{{frac.numerator}}}{{{frac.denominator}}}"
"""

# ============================================================================
# Domain 6: VECTOR (向量)
# ============================================================================

VECTOR_HELPERS = """
# ===== 向量標準函數庫 =====

def _vector_add(v1, v2):
    '''向量加法: (x1,y1) + (x2,y2)'''
    return (v1[0] + v2[0], v1[1] + v2[1])

def _vector_scalar_mult(k, v):
    '''純量乘法: k * (x,y)'''
    return (k * v[0], k * v[1])

def _vector_dot_product(v1, v2):
    '''內積: v1 · v2'''
    return v1[0] * v2[0] + v1[1] * v2[1]

def _vector_magnitude(v):
    '''向量長度: |v|'''
    return math.sqrt(v[0]**2 + v[1]**2)
"""

# ============================================================================
# Domain 7: CALCULUS (微積分)
# ============================================================================

CALCULUS_HELPERS = """
# ===== 微積分標準函數庫 =====
# (多項式微分已在 POLYNOMIAL_HELPERS 中定義)

def _find_critical_points(coeffs):
    '''
    找多項式的臨界點（一階導數為 0 的點）
    參數: coeffs = [a_n, a_{n-1}, ..., a_0] (降冪排列)
    返回: 臨界點列表
    '''
    # 實現求導 + 解方程
    pass

def _evaluate_poly(coeffs, x):
    '''計算多項式在 x 點的值'''
    result = 0
    for i, c in enumerate(coeffs):
        result += c * (x ** (len(coeffs) - 1 - i))
    return result
"""

# ============================================================================
# Domain 映射表
# ============================================================================

DOMAIN_MAP = {
    'polynomial': POLYNOMIAL_HELPERS,
    'geometry': GEOMETRY_HELPERS,
    'trigonometry': TRIGONOMETRY_HELPERS,
    'algebra': ALGEBRA_HELPERS,
    'probability': PROBABILITY_HELPERS,
    'vector': VECTOR_HELPERS,
    'calculus': CALCULUS_HELPERS,
}

# ============================================================================
# Skill → Domain 映射（精確匹配優先級最高）
# ============================================================================

SKILL_DOMAIN_MAPPING = {
    # ===== 多項式相關 =====
    'polynomial_def': ['polynomial'],
    'poly_op_add_sub_mult': ['polynomial'],
    'synthetic_division': ['polynomial'],
    'completing_square': ['polynomial', 'algebra'],
    
    # ===== 微積分相關 =====
    'ApplicationsOfDerivatives': ['polynomial', 'calculus'],
    'deriv_basic': ['polynomial', 'calculus'],
    'critical_points': ['polynomial', 'calculus'],
    'extreme_values': ['polynomial', 'calculus'],
    
    # ===== 幾何相關 =====
    'dist_formula_1d': ['geometry'],
    'dist_formula_2d': ['geometry'],
    'midpoint_formula': ['geometry'],
    'section_formula': ['geometry'],
    'centroid_formula': ['geometry'],
    'slope_definition': ['geometry'],
    'slope_general_form': ['geometry'],
    'parallel_lines_slope': ['geometry'],
    'perpendicular_lines_slope': ['geometry'],
    'point_slope_form': ['geometry'],
    'horiz_vert_lines': ['geometry'],
    'slope_intercept_form': ['geometry'],
    'intercept_form': ['geometry'],
    'eq_of_parallel_line': ['geometry'],
    'eq_of_perpendicular_line': ['geometry'],
    'distance_point_line': ['geometry'],
    'distance_parallel_lines': ['geometry'],
    
    # ===== 三角函數相關 =====
    'radian_deg_conv': ['trigonometry'],
    'arc_len_area': ['trigonometry'],
    'coterminal_angles': ['trigonometry'],
    'right_tri_trig': ['trigonometry'],
    'trig_basic_id': ['trigonometry'],
    'quadrant_trig': ['trigonometry'],
    'periodicity_trig': ['trigonometry'],
    'area_formula_sas': ['trigonometry'],
    'sine_law': ['trigonometry'],
    'cosine_law': ['trigonometry'],
    'trig_survey': ['trigonometry'],
    
    # ===== 代數相關 =====
    'abs_val_eq': ['algebra'],
    'abs_val_ineq_lt': ['algebra'],
    'abs_val_ineq_gt': ['algebra'],
    'quad_ineq_factorable': ['algebra'],
    'quad_ineq_discriminant': ['algebra'],
    'always_positive_cond': ['algebra'],
    'always_negative_cond': ['algebra'],
    'cross_multiplication': ['algebra'],
    'sys_linear_eq_geometry': ['algebra', 'geometry'],
    'linear_func_type': ['algebra'],
    'quad_func_prop': ['algebra'],
    'vertex_max_min': ['algebra'],
    
    # ===== 機率相關 =====
    'classical_probability': ['probability'],
    'conditional_probability': ['probability'],
    'permutation_basic': ['probability'],
    'combination_basic': ['probability'],
    
    # ===== 向量相關 =====
    'vector_def_add': ['vector'],
    'vector_coord_len': ['vector'],
    'vector_scalar_mult': ['vector'],
    'vector_dot_product': ['vector'],
}

def get_required_domains(skill_id):
    """
    根據 skill_id 自動判斷需要注入哪些 domain 的函數庫
    [V47.13] 改進策略：優先級匹配 + 從資料庫章節信息推斷
    
    參數:
        skill_id: str, 例如 'gh_ApplicationsOfDerivatives'
    
    返回:
        list of str: 需要的 domain 列表，例如 ['polynomial', 'calculus']
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 移除前綴 'gh_' 或 'local_'
    clean_id = skill_id.replace('gh_', '').replace('local_', '')
    logger.info(f"🔍 Domain 識別: skill_id={skill_id}, clean_id={clean_id}")
    
    # ===== 優先級 1: 精確匹配（手動維護的高優先級映射）=====
    if clean_id in SKILL_DOMAIN_MAPPING:
        domains = SKILL_DOMAIN_MAPPING[clean_id]
        logger.info(f"   ✅ 優先級 1 - 精確匹配: {domains}")
        return domains
    
    # ===== 優先級 2: 從資料庫章節信息推斷 =====
    try:
        from models import db, SkillCurriculum
        from flask import current_app
        if current_app:
            curriculum = SkillCurriculum.query.filter_by(skill_id=clean_id).first()
            if curriculum:
                chapter = curriculum.chapter.lower()
                section = curriculum.section.lower()
                logger.info(f"   📚 章節信息: chapter={chapter}, section={section}")
                
                # 章節關鍵字映射
                if any(kw in chapter or kw in section for kw in ['多項式', '式的運算', 'polynomial']):
                    logger.info(f"   ✅ 優先級 2 - 章節匹配: ['polynomial']")
                    return ['polynomial']
                if any(kw in chapter or kw in section for kw in ['導數', '微分', '極值', 'derivative', 'calculus']):
                    logger.info(f"   ✅ 優先級 2 - 章節匹配: ['polynomial', 'calculus']")
                    return ['polynomial', 'calculus']
                if any(kw in chapter or kw in section for kw in ['直線', '斜率', '坐標', 'line', 'coordinate']):
                    logger.info(f"   ✅ 優先級 2 - 章節匹配: ['geometry']")
                    return ['geometry']
                if any(kw in chapter or kw in section for kw in ['三角', 'trigon', 'sin', 'cos']):
                    logger.info(f"   ✅ 優先級 2 - 章節匹配: ['trigonometry']")
                    return ['trigonometry']
                if any(kw in chapter or kw in section for kw in ['機率', 'probability']):
                    logger.info(f"   ✅ 優先級 2 - 章節匹配: ['probability']")
                    return ['probability']
                if any(kw in chapter or kw in section for kw in ['向量', 'vector']):
                    logger.info(f"   ✅ 優先級 2 - 章節匹配: ['vector']")
                    return ['vector']
                if any(kw in chapter or kw in section for kw in ['方程', 'equation', '不等式', 'inequality']):
                    logger.info(f"   ✅ 優先級 2 - 章節匹配: ['algebra']")
                    return ['algebra']
    except Exception as e:
        logger.debug(f"   ⚠️ 優先級 2 失敗 (資料庫不可用): {e}")
    
    # ===== 優先級 3: skill_id 關鍵字匹配（保守策略）=====
    domains = []
    clean_lower = clean_id.lower()
    
    # 多項式 & 微積分（高優先級，因為常見）
    if any(kw in clean_lower for kw in ['deriv', 'calculus', 'extreme', 'critical']):
        domains.extend(['polynomial', 'calculus'])
    elif any(kw in clean_lower for kw in ['poly', 'polynomial', 'factor', 'division']):
        domains.append('polynomial')
    
    # 幾何
    if any(kw in clean_lower for kw in ['distance', 'line', 'slope', 'midpoint', 'circle', 'triangle']):
        domains.append('geometry')
    
    # 三角函數
    if any(kw in clean_lower for kw in ['trig', 'sin', 'cos', 'tan', 'radian', 'angle']):
        domains.append('trigonometry')
    
    # 代數
    if any(kw in clean_lower for kw in ['equation', 'quadratic', 'linear', 'inequality', 'abs']):
        domains.append('algebra')
    
    # 機率
    if any(kw in clean_lower for kw in ['prob', 'permutation', 'combination', 'ncr', 'npr']):
        domains.append('probability')
    
    # 向量
    if any(kw in clean_lower for kw in ['vector', 'dot', 'cross']):
        domains.append('vector')
    
    if domains:
        logger.info(f"   ✅ 優先級 3 - 關鍵字匹配: {list(set(domains))}")
        return list(set(domains))
    
    # ===== 優先級 4: 默認策略（未匹配時）=====
    logger.info(f"   ⚠️ 優先級 4 - 默認策略: ['algebra']")
    return ['algebra']

def get_domain_helpers_code(domains):
    """
    獲取指定 domain 的所有標準函數代碼
    
    參數:
        domains: list of str, 例如 ['polynomial', 'calculus']
    
    返回:
        str: 合併後的函數定義代碼
    """
    code_parts = []
    for domain in domains:
        if domain in DOMAIN_MAP:
            code_parts.append(DOMAIN_MAP[domain])
    
    return '\n\n'.join(code_parts)
