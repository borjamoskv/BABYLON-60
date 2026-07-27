from algopy import UInt64, ensure_budget
from algopy.arc4 import ARC4Contract, abimethod


class OpUp(ARC4Contract):
    @abimethod
    def ensure_budget(self, budget: UInt64) -> None:
        ensure_budget(budget)
