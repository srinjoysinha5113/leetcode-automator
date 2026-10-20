from typing import Dict, List, Tuple

class TimeMap:

    def __init__(self):
        self.map: Dict[str, Dict[int, str]] = {}

    def set(self, key: str, value: str, timestamp: int) -> None:
        if key not in self.map:
            self.map[key] = {}
        self.map[key][timestamp] = value

    def get(self, key: str, timestamp: int) -> str:
        if key not in self.map or timestamp not in self.map[key]:
            return ""
        return self.map[key][timestamp]