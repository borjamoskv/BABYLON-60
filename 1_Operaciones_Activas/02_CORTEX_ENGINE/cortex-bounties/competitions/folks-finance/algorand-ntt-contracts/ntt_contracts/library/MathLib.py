from algopy import UInt64, subroutine
from algopy.arc4 import UInt8

@subroutine
def max_uint8(a: UInt8, b: UInt8) -> UInt8:
    return a if a > b else b

@subroutine
def min_uint8(a: UInt8, b: UInt8) -> UInt8:
    return a if a < b else b

@subroutine
def max_uint64(a: UInt64, b: UInt64) -> UInt64:
    return a if a > b else b

@subroutine
def min_uint64(a: UInt64, b: UInt64) -> UInt64:
    return a if a < b else b
