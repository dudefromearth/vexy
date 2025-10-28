from abc import ABC, abstractmethod
from typing import Dict, Any

class AbstractAssembler(ABC):
    @abstractmethod
    def assemble(self) -> Dict[str, Any]:
        """Assemble and return the transport data dict."""
        pass