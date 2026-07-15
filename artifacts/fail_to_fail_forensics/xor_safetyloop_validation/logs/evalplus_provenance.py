import platform
import sys

import evalplus
from evalplus.data import get_human_eval_plus_hash, get_mbpp_plus_hash
from evalplus.data.humaneval import HUMANEVAL_PLUS_VERSION
from evalplus.data.mbpp import MBPP_PLUS_VERSION


print(f"evalplus={evalplus.__version__}")
print(f"humaneval_version={HUMANEVAL_PLUS_VERSION}")
print(f"humaneval_hash={get_human_eval_plus_hash()}")
print(f"mbpp_version={MBPP_PLUS_VERSION}")
print(f"mbpp_hash={get_mbpp_plus_hash()}")
print(f"python={sys.version.split()[0]}")
print(f"platform={platform.platform()}")
