from abc import ABC, abstractmethod
from algopy import ARC4Contract, UInt64, gtxn
from algopy.arc4 import Bool, Struct,UInt16, abimethod

from ...types import ARC4UInt8, MessageDigest, MessageId, TransceiverInstructions, UniversalAddress


# Structs
class NttManagerPeer(Struct):
    peer_contract: UniversalAddress
    decimals: ARC4UInt8


class INttManager(ARC4Contract, ABC):
    @abstractmethod
    @abimethod
    def transfer(
        self,
        fee_payment: gtxn.PaymentTransaction,
        send_token: gtxn.AssetTransferTransaction,
        amount: UInt64,
        recipient_chain: UInt16,
        recipient: UniversalAddress
    ) -> MessageId:
        """Transfer a given amount to a recipient on a given chain. Function exposes full parameters available for any
        customisation needed. Uses default values for unexposed parameters.

        Args:
            fee_payment: Payment transaction to pay for delivery costs
            send_token: Asset transfer transaction to lock/burn token
            amount: The amount to transfer
            recipient_chain: The wormhole chain id to transfer to
            recipient: The recipient address

        Returns:
            The message id of the transfer
        """
        pass

    @abstractmethod
    @abimethod
    def transfer_full(
        self,
        fee_payment: gtxn.PaymentTransaction,
        send_token: gtxn.AssetTransferTransaction,
        amount: UInt64,
        recipient_chain: UInt16,
        recipient: UniversalAddress,
        should_queue: Bool,
        transceiver_instructions: TransceiverInstructions,
    ) -> MessageId:
        """Transfer a given amount to a recipient on a given chain. Function exposes full parameters available for any
        customisation needed.

        Args:
            fee_payment: Payment transaction to pay for delivery costs
            send_token: Asset transfer transaction to lock/burn token
            amount: The amount to transfer
            recipient_chain: The wormhole chain id to transfer to
            recipient: The recipient address
            should_queue: Whether the transfer should be queued if the outbound limit is hit
            transceiver_instructions: The instructions to use for each transceiver. Must follow the same order as
                                      it's stored in the transceiver manager

        Returns:
            The message id of the transfer
        """
        pass

    @abstractmethod
    @abimethod
    def complete_outbound_queued_transfer(
        self,
        fee_payment: gtxn.PaymentTransaction,
        message_id: MessageId,
    ) -> MessageId:
        """Complete an outbound transfer that's been queued.

        Args:
            fee_payment: Payment transaction to pay for delivery costs
            message_id: The Ntt defined identifier for a message to send

        Returns:
            The message id of the transfer
        """
        pass

    @abstractmethod
    @abimethod
    def cancel_outbound_queued_transfer(self, message_id: MessageId) -> None:
        """Cancels an outbound transfer that's been queued.

        Args:
            message_id: The Ntt defined identifier for a message to send
        """
        pass

    @abstractmethod
    @abimethod
    def complete_inbound_queued_transfer(self, message_digest: MessageDigest) -> None:
        """Complete an inbound queued transfer.

        Args:
            message_digest: Unique identifier of the message received.
        """
        pass

    @abstractmethod
    @abimethod(readonly=True)
    def get_ntt_manager_peer(self, chain_id: UInt16) -> NttManagerPeer:
        """Returns registered peer contract for a given chain.

        Args:
            chain_id: The chain id to get the peer of.

        Returns:
            The ntt manager peer
        """
        pass
