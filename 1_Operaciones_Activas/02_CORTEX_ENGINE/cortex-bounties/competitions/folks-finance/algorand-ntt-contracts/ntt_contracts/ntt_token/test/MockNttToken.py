from algopy import Global, GlobalState, UInt64, itxn
from algopy.arc4 import Address, abimethod, emit

from ...types import ARC4UInt64
from ..interfaces.INttToken import Minted, INttToken


class MockNttToken(INttToken):
    def __init__(self) -> None:
        self.asset_id = GlobalState(UInt64)

    @abimethod
    def set_asset_id(self, asset_id: UInt64) -> None:
        self.asset_id.value = asset_id

        # opt into asset
        itxn.AssetTransfer(
            xfer_asset=asset_id,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
            fee=0,
        ).submit()

    @abimethod(readonly=True)
    def get_asset_id(self) -> UInt64:
        return self.asset_id.value

    @abimethod
    def mint(self, receiver: Address, amount: UInt64) -> None:
        emit(Minted(receiver, ARC4UInt64(amount)))

    @abimethod
    def set_minter(self, new_minter: Address) -> None:
        pass
