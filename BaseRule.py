import os
from typing import List, Callable, Union, Dict, Any

from pymake.builderrors import BuildError

class BaseRule:

    def __init__(self, name):

        self.name = name
        self.prerequisites: List[str] = []
        self.settings: List[str] = []

        self.force_rebuild = False

    def __str__(self) -> str:
        return "Rule[ %s: %s]" % ( ', '.join(self.name), ', '.join(self.prerequisites))

    def setForceRebuild(self, force_rebuild: bool):
        self.force_rebuild = force_rebuild

    def forceRebuild(self):
        return self.force_rebuild

    def addSetting(self, setting: str) -> None:
        self.settings.append(setting)

    def getSettings(self) -> List[str]:
        return self.settings

    def addPrerequisite(self, prerequisite: Union["BaseRule", str]) -> None:
        if isinstance(prerequisite, str):
            self.prerequisites.append( prerequisite )
        else:
            self.prerequisites.append( prerequisite.name )

    def getPrerequisites(self) -> List[str]:
        return self.prerequisites

    def exists(self) -> bool:
        return False

    def getLastBuildTime(self) -> int:
        return -1

    def build(self, settings_values: Dict[str, Any]) -> None:
        raise BuildError("Cannot build %s." % self.name)
