# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from core.routes.live_show import _recompute_correct_answer_from_question, _to_eval_expression_template, _extract_math_expr_from_question

q = r'計算 $160 \div [2 \times 9 - (-14)]$ 的值。'
print('Q:', q)
ans = _recompute_correct_answer_from_question(q)
print('Ans computed:', ans)

# Manual trace
expr = _extract_math_expr_from_question(q)
print('Expr:', expr)
eval_expr = _to_eval_expression_template(expr)
print('Eval Template Output:', eval_expr)
