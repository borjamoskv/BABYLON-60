from abc import ABC
from algopy import Account, GlobalState, UInt64, itxn, op
from algopy.arc4 import Address, abimethod, emit

from folks_contracts.library.extensions.InitialisableWithCreator import InitialisableWithCreator
from folks_contracts.library.Upgradeable import Upgradeable
from .. import constants as const
from ..types import ARC4UInt64, Bytes16
from .interfaces.INttToken import Minted, INttToken


# Reference implementation of NttToken
class NttToken(INttToken, Upgradeable, InitialisableWithCreator, ABC):
    def __init__(self) -> None:
        Upgradeable.__init__(self)
        InitialisableWithCreator.__init__(self)

        self.asset_id = GlobalState(UInt64)

    @abimethod(readonly=True)
    def get_asset_id(self) -> UInt64:
        return self.asset_id.value

    @abimethod
    def mint(self, receiver: Address, amount: UInt64) -> None:
        self._only_initialised()
        self._check_sender_role(self.minter_role())

        # send asset
        itxn.AssetTransfer(
            xfer_asset=self.asset_id.value,
            asset_receiver=Account(receiver.bytes),
            asset_amount=amount,
            fee=0,
        ).submit()

        emit(Minted(receiver, ARC4UInt64(amount)))

    @abimethod
    def set_minter(self, new_minter: Address) -> None:
        self._only_initialised()
        self.grant_role(self.minter_role(), new_minter)

    @abimethod(readonly=True)
    def minter_role(self) -> Bytes16:
        return Bytes16.from_bytes(op.extract(op.keccak256(b"MINTER"), 0, const.BYTES16_LENGTH))
