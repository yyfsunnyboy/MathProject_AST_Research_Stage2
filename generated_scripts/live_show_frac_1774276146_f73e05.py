from core.fraction_domain_functions import FractionFunctionHelper

_FRAC_HELPER = FractionFunctionHelper()
_FRAC_CONFIG = {'family': 'frac_eval_expression', 'source_text': '9\\frac{1}{5}\\times239+9\\frac{1}{5}\\times(-39)', 'expr': '9(1/5)*239+9(1/5)*(-39)', 'ellipsis': False}

def generate(level=1, **kwargs):
    runtime_config = _FRAC_HELPER.build_runtime_config(_FRAC_CONFIG, level=level, **kwargs)
    return _FRAC_HELPER.generate_from_config(runtime_config)

def check(user_answer, correct_answer):
    return _FRAC_HELPER.check_answer(_FRAC_CONFIG, user_answer, correct_answer)
