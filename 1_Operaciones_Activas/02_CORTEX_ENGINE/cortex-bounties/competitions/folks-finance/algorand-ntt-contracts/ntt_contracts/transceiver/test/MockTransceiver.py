from algopy import Bytes, GlobalState, String, UInt64, subroutine
from algopy.arc4 import DynamicBytes, Struct, abimethod, emit

from ...types import ARC4UInt64, Bytes32, MessageToSend, MessageReceived
from ..Transceiver import Transceiver


# Events
class InternalQuoteDeliveryPrice(Struct):
    message_id: Bytes32
    transceiver_instruction: DynamicBytes

class InternalSendMessage(Struct):
    total_fee: ARC4UInt64
    message_id: Bytes32
    transceiver_instruction: DynamicBytes


class MockTransceiver(Transceiver):
    def __init__(self) -> None:
        super().__init__()
        self.message_fee = GlobalState(UInt64)

    @abimethod
    def initialise(self) -> None:
        Transceiver.initialise(self)

    @abimethod(create="require")
    def create( # type: ignore[override]
        self,
        transceiver_manager: UInt64,
        message_fee: UInt64,
        min_upgrade_delay: UInt64
    ) -> None:
        Transceiver.create(self, transceiver_manager, min_upgrade_delay)
        self.message_fee.value = message_fee

    @abimethod(readonly=True)
    def get_transceiver_type(self) -> String:
        return String("mock")

    @abimethod
    def deliver_message(self, message: MessageReceived) -> None:
        self._deliver_message(message)

    @subroutine
    def _quote_delivery_price(self, message: MessageToSend, transceiver_instruction: Bytes) -> UInt64:
        emit(InternalQuoteDeliveryPrice(message.id, DynamicBytes(transceiver_instruction)))
        return self.message_fee.value

    @subroutine
    def _send_message(self, total_fee: UInt64, message: MessageToSend, transceiver_instruction: Bytes) -> None:
        emit(InternalSendMessage(ARC4UInt64(total_fee), message.id, DynamicBytes(transceiver_instruction)))
