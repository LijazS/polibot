from typing import get_type_hints

from polibot.strategies.base import Strategy


def test_strategy_contract_only_emits_proposals() -> None:
    assert "execute" not in Strategy.__dict__
    assert "submit_order" not in Strategy.__dict__
    return_type = str(get_type_hints(Strategy.evaluate)["return"])
    assert "OpportunityProposal" in return_type

