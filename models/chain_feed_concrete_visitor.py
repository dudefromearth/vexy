from typing import Dict, Any, List  # Added import
from collections import defaultdict

from models.abstract_visitor import AbstractVisitor

class ChainFeedConcreteVisitor(AbstractVisitor):
    def visit_atm_range(self, chain: Dict[str, Any], spot: float, range_strikes: int = 50) -> List[Dict[str, Any]]:
        contracts = chain.get("contracts", [])
        return [c for c in contracts if abs(c.get("strike", 0) - spot) <= range_strikes]

    def visit_call_put_totals(self, chain: Dict[str, Any]) -> Dict[str, int]:
        contracts = chain.get("contracts", [])
        total = len(contracts)
        calls = sum(1 for c in contracts if c.get("contract_type", "call") == "call")
        puts = total - calls
        return {"total": total, "calls": calls, "puts": puts}

    def visit_gamma_oi_per_strike(self, chain: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        contracts = chain.get("contracts", [])
        gamma_oi = defaultdict(lambda: {"gamma": 0.0, "oi": 0})
        for c in contracts:
            strike = str(c.get("strike", 0))
            gamma_oi[strike]["gamma"] += c.get("gamma", 0)
            gamma_oi[strike]["oi"] += c.get("open_interest", 0)
        return dict(gamma_oi)

    def visit_chain(self, chain: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "atm_range": self.visit_atm_range(chain, spot=450),
            "totals": self.visit_call_put_totals(chain),
            "gamma_oi": self.visit_gamma_oi_per_strike(chain)
        }