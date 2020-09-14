import os
from typing import List, Dict, Any

from pymake.BaseRule import BaseRule

class PhoneyRule(BaseRule):
    def __init__(self, names):
        BaseRule.__init__(self, names)

    def exists(self) -> bool:
        return False

    def build(self, settings_values: Dict[str, Any]) -> None:
        pass
