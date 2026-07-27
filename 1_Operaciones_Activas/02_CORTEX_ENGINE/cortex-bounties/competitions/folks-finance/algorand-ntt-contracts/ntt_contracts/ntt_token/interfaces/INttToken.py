from abc import ABC, abstractmethod
from algopy import ARC4Contract, UInt64
from algopy.arc4 import Address, Struct, abimethod

from ...types import ARC4UInt64


# Events
class Minted(Struct):
    receiver: Address
    amount: ARC4UInt64


class INttToken(ARC4Contract, ABC):
    @abstractmethod
    @abimethod(readonly=True)
    def get_asset_id(self) -> UInt64:
        pass

    @abstractmethod
    @abimethod
    def mint(self, receiver: Address, amount: UInt64) -> None:
        pass

    @abstractmethod
    @abimethod
    def set_minter(self, new_minter: Address) -> None:
        pass
