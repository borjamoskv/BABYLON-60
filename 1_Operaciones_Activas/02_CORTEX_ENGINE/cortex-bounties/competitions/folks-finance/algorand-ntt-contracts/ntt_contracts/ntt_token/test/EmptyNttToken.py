from algopy import UInt64
from algopy.arc4 import Address, abimethod

from ..NttToken import NttToken


class EmptyNttToken(NttToken):
    def __init__(self) -> None:
        NttToken.__init__(self)

    @abimethod
    def initialise(self, admin: Address, asset_id: UInt64) -> None: # type: ignore[override]
        super().initialise()
        self._grant_role(self.default_admin_role(), admin)
        self.asset_id.value = asset_id
