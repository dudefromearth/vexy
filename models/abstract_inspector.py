from abc import ABC, abstractmethod
from typing import Dict, Any

class AbstractInspector(ABC):
    @abstractmethod
    def inspect(self, data: Dict[str, Any]) -> Any:
        """Inspect data and return queried results (e.g., totals, range)."""
        pass