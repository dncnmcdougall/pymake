import os
from typing import List, Callable, Union, Dict, Any

from pymake.builderrors import BuildError

class BaseRule:

    def __init__(self, names):
        assert len(names) >= 1, 'At least one target must be specified.'

        self.names = names
        self.prerequisites: List[str] = []
        self.settings: List[str] = []

        self.force_rebuild = False

    def __str__(self) -> str:
        if len(self.prerequisites) == 0:
            return "%s" % ( ', '.join(self.names))
        else:
            return "%s: %s" % ( ', '.join(self.names), ', '.join(self.prerequisites))

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
            self.prerequisites.extend( prerequisite.names )

    def getPrerequisites(self) -> List[str]:
        return self.prerequisites

    def exists(self) -> bool:
        return False

    def getLastBuildTime(self) -> int:
        return -1

    def build(self, settings_values: Dict[str, Any]) -> None:
        raise BuildError("Cannot build %s." % str(self))
