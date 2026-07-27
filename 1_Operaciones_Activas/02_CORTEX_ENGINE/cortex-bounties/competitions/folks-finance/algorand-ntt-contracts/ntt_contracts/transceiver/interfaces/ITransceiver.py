from abc import ABC, abstractmethod
from algopy import ARC4Contract, Bytes, String, UInt64, gtxn
from algopy.arc4 import abimethod

from ...types import MessageToSend


class ITransceiver(ARC4Contract, ABC):
    """Transceivers are responsible for sending and receiving messages between chains.

    The interface for receiving messages is not enforced by this contract. Instead, inheriting contracts should
    implement their own receiving logic, based on the verification model and logic associated with message handling.
    """
    @abstractmethod
    @abimethod(readonly=True)
    def get_transceiver_type(self) -> String:
        """Returns the string type of the transceiver. E.g. "wormhole", "axelar", etc.

        Returns:
            The transceiver type
        """
        pass

    @abstractmethod
    @abimethod(readonly=True)
    def quote_delivery_price(self, message: MessageToSend, transceiver_instruction: Bytes) -> UInt64:
        """Fetch the delivery price for a given message.

        Args:
            message: The message to send
            transceiver_instruction: The instructions to use for the transceiver

        Returns:
            The delivery quote
        """
        pass

    @abstractmethod
    @abimethod
    def send_message(
        self,
        fee_payment: gtxn.PaymentTransaction,
        message: MessageToSend,
        transceiver_instruction: Bytes,
    ) -> None:
        """Send a message to another chain.

        Args:
            fee_payment: Payment transaction to pay for delivery costs
            message: The message to send
            transceiver_instruction: The instructions to use for the transceiver
        """
        pass
