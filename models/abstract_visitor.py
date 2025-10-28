from abc import ABC, abstractmethod
from typing import Dict, Any

class AbstractBuilder(ABC):
    @abstractmethod
    def build(self) -> Dict[str, Any]:
        pass

class AbstractVisitor(ABC):
    @abstractmethod
    def visit_chain(self, chain: Dict[str, Any]) -> Any:
        """Visit the chain and return introspected data (e.g., totals, range)."""
        pass