import os
import copy
from typing import List, Callable, Dict, Any

from pymake.BaseRule import BaseRule

def modtime(path):
    return os.stat(path).st_mtime_ns

class FileExistsRule(BaseRule):

    def __init__(self, names):
        BaseRule.__init__(self, names)

    def exists(self) -> bool:
        for name in self.names:
            if not os.path.exists(name):
                return False
        else:
            return True

    def getLastBuildTime(self) -> int:
        if not self.exists():
            return -1
        return min([modtime(name) for name in self.names])

class FileTouchRule(FileExistsRule):

    def __init__(self, names):
        BaseRule.__init__(self, names)

    def build(self, settings_values: Dict[str, Any]) -> None:
        try:
            for name in self.names:
                fle = open(name,'a')
                fle.close()
        except:
            raise

class GenericFileRule(FileTouchRule):

    def __init__(self, names):
        FileTouchRule.__init__(self, names)
        self.recipy = None

    def setRecipe(self, recipe: Callable[[str, List[str]], None]) -> None:
        self.recipe = recipe

    def build(self, settings_values: Dict[str, Any]) -> None:
        try:
            if len(self.names) == 1:
                self.recipe(self.names[0], copy.copy(self.prerequisites), settings_values)
            else:
                self.recipe(copy.copy(self.names), copy.copy(self.prerequisites), settings_values)
            assert self.exists(), 'The file %s should exist after the rule ran.' % (', '.join(self.names))
        except:
            print('Error when building: %s' % (', '.join(self.names)))
            raise
