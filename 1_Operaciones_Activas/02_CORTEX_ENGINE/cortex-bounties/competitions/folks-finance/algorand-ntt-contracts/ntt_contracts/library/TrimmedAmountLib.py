from algopy import UInt64, subroutine
from algopy.arc4 import UInt8

from ..types import ARC4UInt64, TrimmedAmount
from . import MathLib


"""Library to handle token amounts with different decimals.

Amounts represented in VAAs are capped at 8 decimals. This means that any amount that's given as having more decimals 
is truncated to 8 decimals. On the way out, these amount have to be scaled back to the original decimal amount. 

Uses the TrimmedAmount type which is a named tuple of a token amount and its decimals.

The subroutines `trim` and `untrim` take care of convertion to/from this type given the original amount's decimals.
"""
TRIMMED_DECIMALS = 8

@subroutine
def scale(amt: UInt64, from_decimals: UInt8, to_decimals: UInt8) -> UInt64:
    if from_decimals == to_decimals:
        return amt
    elif from_decimals > to_decimals:
        return amt // (10 ** (from_decimals.as_uint64() - to_decimals.as_uint64()))
    else:
        return amt * (10 ** (to_decimals.as_uint64() - from_decimals.as_uint64()))

@subroutine
def trim(amt: UInt64, from_decimals: UInt8, to_decimals: UInt8) -> TrimmedAmount:
    """Trim the amount to target decimals. The actual resulting decimals is the minimum of from_decimals, to_decimals
    and TRIMMED_DECIMALS.

    Args:
        amt: The amount to be trimmed
        from_decimals: The original decimals of the amount
        to_decimals: The target decimals of the amount
    """
    actual_to_decimals = MathLib.min_uint8(MathLib.min_uint8(UInt8(TRIMMED_DECIMALS), from_decimals), to_decimals)
    amount_scaled = scale(amt, from_decimals, actual_to_decimals)
    return TrimmedAmount(ARC4UInt64(amount_scaled), actual_to_decimals)

@subroutine
def untrim(amt: TrimmedAmount, to_decimals: UInt8) -> UInt64:
    """Untrim the amount to target decimals.

    Args:
        amt: The amount to be untrimmed
        to_decimals: The target decimals of the amount

    Raises:
        OverflowError: If the raw integer overflows
    """
    return scale(amt.amount.as_uint64(), amt.decimals, to_decimals)
