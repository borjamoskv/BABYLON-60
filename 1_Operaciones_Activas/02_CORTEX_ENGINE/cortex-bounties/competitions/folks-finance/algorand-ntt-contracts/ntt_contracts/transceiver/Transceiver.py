from abc import ABC, abstractmethod
from algopy import Bytes, Global, GlobalState, Txn, UInt64, gtxn, op, subroutine
from algopy.arc4 import Struct, abi_call, abimethod, emit

from folks_contracts.library.Upgradeable import Upgradeable
from .. import errors as err
from ..types import Bytes32, MessageReceived, MessageToSend
from .interfaces.ITransceiverManager import ITransceiverManager
from .interfaces.ITransceiver import ITransceiver


# Events
class MessageSent(Struct):
    message_id: Bytes32


class Transceiver(ITransceiver, Upgradeable, ABC):
    """Transceivers are responsible for sending and receiving messages between chains.

    The abstract smart contract provides the common implementation for all Transceivers. A concrete implementation of
    Transceiver must implement the subroutines `_quote_delivery_price` and `_send_message`. In addition, a new method
    with the logic to receive a message.
    """
    def __init__(self) -> None:
        Upgradeable.__init__(self)
        self.transceiver_manager = GlobalState(UInt64)

    @abimethod(create="require")
    def create(self, transceiver_manager: UInt64, min_upgrade_delay: UInt64) -> None: # type: ignore[override]
        Upgradeable.create(self, min_upgrade_delay)
        self.transceiver_manager.value = transceiver_manager

    @abimethod(readonly=True)
    def quote_delivery_price(self, message: MessageToSend, transceiver_instruction: Bytes) -> UInt64:
        return self._quote_delivery_price(message, transceiver_instruction)

    @abimethod
    def send_message(
        self,
        fee_payment: gtxn.PaymentTransaction,
        message: MessageToSend,
        transceiver_instruction: Bytes,
    ) -> None:
        # check caller is TransceiverManager
        transceiver_manager_address, exists = op.AppParamsGet.app_address(self.transceiver_manager.value)
        assert exists, err.TRANSCEIVER_MANAGER_ADDRESS_UNKNOWN
        assert transceiver_manager_address == Txn.sender, err.TRANSCEIVER_MANAGER_CALLER

        # check payment
        assert fee_payment.receiver == Global.current_application_address, err.FEE_PAYMENT_RECEIVER_UNKNOWN
        assert fee_payment.amount == self._quote_delivery_price(message, transceiver_instruction), err.FEE_PAYMENT_AMOUNT_INCORRECT

        # send message according to concrete transceiver implementation
        self._send_message(fee_payment.amount, message, transceiver_instruction)

        # emit event
        emit(MessageSent(message.id))

    @subroutine
    def _deliver_message(self, message: MessageReceived) -> None:
        """Forward a delivered message to the TransceiverManager. Internally called by the concrete Transceiver
        implementation in their respective "receive message" method.

         Args:
             message: The message received
         """
        abi_call(
            ITransceiverManager.attestation_received,
            message,
            app_id=self.transceiver_manager.value,
            fee=0,
        )

    @abstractmethod
    @subroutine
    def _quote_delivery_price(self, message: MessageToSend, transceiver_instruction: Bytes) -> UInt64:
        """Abstract internal method called by the `quote_delivery_price` method. Namely, should implement the logic to
        fetch the delivery price to send a message through the respective GMP used by the concrete Transceiver.

        Args:
            message: The message to send
            transceiver_instruction: The instructions to use for the transceiver

        Returns:
            The delivery quote
        """
        pass

    @abstractmethod
    @subroutine
    def _send_message(self, total_fee: UInt64, message: MessageToSend, transceiver_instruction: Bytes) -> None:
        """Abstract internal method called by the `send_message` method. Namely, should implement the logic to send a
        message through the respective GMP used by the concrete Transceiver.

        Args:
            total_fee: The total amount of ALGO paid to cover the fees
            message: The message to send
            transceiver_instruction: The instructions to use for the transceiver
        """
        pass
