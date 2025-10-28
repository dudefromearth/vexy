from typing import Dict, Any, List
from collections import defaultdict
from models.abstract_inspector import AbstractInspector

class ChainFeedInspector(AbstractInspector):
    def inspect_atm_range(self, data: Dict[str, Any], spot: float, range_strikes: int = 50) -> List[Dict[str, Any]]:
        contracts = data.get("contracts", [])
        return [c for c in contracts if abs(c.get("strike", 0) - spot) <= range_strikes]

    def inspect_call_put_totals(self, data: Dict[str, Any]) -> Dict[str, int]:
        contracts = data.get("contracts", [])
        total = len(contracts)
        calls = sum(1 for c in contracts if c.get("contract_type", "call") == "call")
        puts = total - calls
        return {"total": total, "calls": calls, "puts": puts}

    def inspect_gamma_oi_per_strike(self, data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        contracts = data.get("contracts", [])
        gamma_oi = defaultdict(lambda: {"gamma": 0.0, "oi": 0})
        for c in contracts:
            strike = str(c.get("strike", 0))
            gamma_oi[strike]["gamma"] += c.get("gamma", 0)
            gamma_oi[strike]["oi"] += c.get("open_interest", 0)
        return dict(gamma_oi)

    def inspect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "atm_range": self.inspect_atm_range(data, spot=450),
            "totals": self.inspect_call_put_totals(data),
            "gamma_oi": self.inspect_gamma_oi_per_strike(data)
        }