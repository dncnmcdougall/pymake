from typing import Any, List, Dict
import json
from datetime import datetime

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
            self.dates[name] = int(datetime.now().timestamp() *1000)
        else:
            pass

    def getSettingValue(self, name: str) -> Any:
        assert name in self.values
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


