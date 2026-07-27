from algopy import Bytes, String, UInt64, itxn
from algopy.arc4 import Address, abimethod

from .NttToken import NttToken


class NttTokenNew(NttToken):
    def __init__(self) -> None:
        NttToken.__init__(self)

    @abimethod
    def initialise(  # type: ignore[override]
        self,
        admin: Address,
        total: UInt64,
        decimals: UInt64,
        asset_name: String,
        unit_name: String,
        url: String,
        metadata_hash: Bytes,
    ) -> UInt64:
        NttToken.initialise(self)
        self._grant_role(self.default_admin_role(), admin)
        self._grant_role(self.upgradable_admin_role(), admin)

        # create asset
        asset_txn = itxn.AssetConfig(
            asset_name=asset_name,
            unit_name=unit_name,
            total=total,
            decimals=decimals,
            url=url,
            metadata_hash=metadata_hash,
            fee=0,
        ).submit()

        # set new asset
        self.asset_id.value = asset_txn.created_asset.id
        return self.asset_id.value
