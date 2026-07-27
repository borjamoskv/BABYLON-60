from algopy import UInt64
from algopy.arc4 import ARC4Contract, UInt8, abimethod

from ...types import TrimmedAmount
from .. import TrimmedAmountLib


class TrimmedAmountLibExposed(ARC4Contract):
    @abimethod(readonly=True)
    def scale(self, amt: UInt64, from_decimals: UInt8, to_decimals: UInt8) -> UInt64:
        return TrimmedAmountLib.scale(amt, from_decimals, to_decimals)

    @abimethod(readonly=True)
    def trim(self, amt: UInt64, from_decimals: UInt8, to_decimals: UInt8) -> TrimmedAmount:
        return TrimmedAmountLib.trim(amt, from_decimals, to_decimals)

    @abimethod(readonly=True)
    def untrim(self, amt: TrimmedAmount, to_decimals: UInt8) -> UInt64:
        return TrimmedAmountLib.untrim(amt, to_decimals)
