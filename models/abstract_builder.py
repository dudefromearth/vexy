from abc import ABC, abstractmethod
from typing import Dict, Any

class AbstractBuilder(ABC):
    @abstractmethod
    def build(self) -> Dict[str, Any]:
        """Build and return the transport data dict."""
        pass