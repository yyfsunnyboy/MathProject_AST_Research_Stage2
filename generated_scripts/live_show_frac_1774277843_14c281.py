from core.fraction_domain_functions import FractionFunctionHelper

_FRAC_HELPER = FractionFunctionHelper()
_FRAC_CONFIG = {'family': 'frac_eval_expression', 'source_text': '(-2\\frac{3}{4})+1\\frac{2}{7}', 'expr': '(-2 3/4)+1 2/7', 'ellipsis': False}

def generate(level=1, **kwargs):
    runtime_config = _FRAC_HELPER.build_runtime_config(_FRAC_CONFIG, level=level, **kwargs)
    return _FRAC_HELPER.generate_from_config(runtime_config)

def check(user_answer, correct_answer):
    return _FRAC_HELPER.check_answer(_FRAC_CONFIG, user_answer, correct_answer)
