from typing import Any, List, Dict
import json
import time

class SettingNotFoundError(Exception):
    def __init__(self, setting):
        Exception.__init__(self, "Could not find a value for setting %s." % setting)

class Settings:
    def __init__(self):
        self.values = {}
        self.dates = {}

    def serialise(self, filename: str) -> None:
        data = {
                'values': self.values,
                'dates': self.dates
                }
        json.dump(data, open(filename, 'w'))

    def deserialise(self, filename: str) -> None:
        data = json.load( open(filename, 'r') )
        self.values = data['values']
        self.dates = data['dates']

    def setValue(self, name: str, value: Any) -> None:
        if name not in self.values or self.values[name] != value:
            self.values[name] = value
            self.dates[name] = time.time_ns()
        else:
            pass

    def getSettingValue(self, name: str) -> Any:
        if name not in self.values:
            raise SettingNotFoundError(name)
        return self.values[name]

    def getValuesForNames(self, names: List[str]) -> Dict[str, Any]:
        result = {}
        for name in names:
            result[name] = self.getSettingValue(name)
        return result

    def exists(self, name: str) -> bool:
        return name in self.values

    def getLastBuildTime(self, name: str) -> int:
        if not self.exists(name):
            return -1
        return self.dates[name]


