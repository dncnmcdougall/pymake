import os
from typing import List, Callable, Dict, Any

from pymake.BaseRule import BaseRule

def modtime(path):
    return os.stat(path).st_mtime_ns

class FileExistsRule(BaseRule):

    def __init__(self, name):
        BaseRule.__init__(self, name)

    def exists(self) -> bool:
        return os.path.exists(self.name)

    def getLastBuildTime(self) -> int:
        if not self.exists():
            return -1
        return  modtime(self.name)

class FileTouchRule(FileExistsRule):

    def __init__(self, name):
        BaseRule.__init__(self, name)

    def build(self, settings_values: Dict[str, Any]) -> None:
        try:
            fle = open(self.name,'a')
            fle.close()
        except:
            raise

class GenericFileRule(FileTouchRule):

    def __init__(self, name):
        FileTouchRule.__init__(self, name)
        self.recipy = None

    def setRecipe(self, recipe: Callable[[str, List[str]], None]) -> None:
        self.recipe = recipe

    def build(self, settings_values: Dict[str, Any]) -> None:
        try:
            self.recipe(self.name, self.prerequisites)
            assert self.exists()
        except:
            raise
