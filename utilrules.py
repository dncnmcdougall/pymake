import os
from typing import List, Dict, Any

from pymake.BaseRule import BaseRule

class PhoneyRule(BaseRule):
    def __init__(self, name):
        BaseRule.__init__(self, name)

    def exists(self) -> bool:
        return False

    def build(self, settings_values: Dict[str, Any]) -> None:
        pass
