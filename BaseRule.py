import os
from typing import List, Callable

from pymake.builderrors import BuildError

class BaseRule:

    def __init__(self, name):

        self.name = name
        self.prerequisites = []

        self.force_rebuild = False

    def __str__(self) -> str:
        return "Rule[ %s: %s]" % ( ', '.join(self.name), ', '.join(self.prerequisites))

    def setForceRebuild(self, force_rebuild: bool):
        self.force_rebuild = force_rebuild

    def forceRebuild(self):
        return self.force_rebuild

    def addPrerequisite(self, prerequisite: str) -> None:
        self.prerequisites.append( prerequisite )

    def getPrerequisites(self) -> List[str]:
        return self.prerequisites

    def exists(self) -> bool:
        return False

    def getLastBuildTime(self) -> int:
        return -1

    def build(self) -> None:
        raise BuildError("Cannot build %s." % self.name)
