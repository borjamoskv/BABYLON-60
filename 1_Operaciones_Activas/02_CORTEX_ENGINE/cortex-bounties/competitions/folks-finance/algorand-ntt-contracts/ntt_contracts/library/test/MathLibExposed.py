from algopy import UInt64
from algopy.arc4 import ARC4Contract, UInt8, abimethod

from .. import MathLib


class MathLibExposed(ARC4Contract):
    @abimethod(readonly=True)
    def max_uint8(self, a: UInt8, b: UInt8) -> UInt8:
        return MathLib.max_uint8(a, b)

    @abimethod(readonly=True)
    def min_uint8(self, a: UInt8, b: UInt8) -> UInt8:
        return MathLib.min_uint8(a, b)

    @abimethod(readonly=True)
    def max_uint64(self, a: UInt64, b: UInt64) -> UInt64:
        return MathLib.max_uint64(a, b)

    @abimethod(readonly=True)
    def min_uint64(self, a: UInt64, b: UInt64) -> UInt64:
        return MathLib.min_uint64(a, b)
