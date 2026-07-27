from algopy import Global, UInt64, itxn
from algopy.arc4 import Address, abimethod

from .NttToken import NttToken


class NttTokenExisting(NttToken):
    def __init__(self) -> None:
        NttToken.__init__(self)

    @abimethod
    def initialise(self, admin: Address, asset_id: UInt64) -> None: # type: ignore[override]
        NttToken.initialise(self)
        self._grant_role(self.default_admin_role(), admin)
        self._grant_role(self.upgradable_admin_role(), admin)

        # opt into asset
        itxn.AssetTransfer(
            xfer_asset=asset_id,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
            fee=0,
        ).submit()

        # set existing asset
        self.asset_id.value = asset_id
