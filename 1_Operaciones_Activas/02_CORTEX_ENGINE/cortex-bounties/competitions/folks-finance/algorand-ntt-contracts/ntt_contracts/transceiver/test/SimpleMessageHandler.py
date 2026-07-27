from algopy import UInt64, subroutine
from algopy.arc4 import Address, Struct, abimethod, emit

from ...types import Bytes32, TransceiverInstructions, MessageToSend, MessageReceived
from ..MessageHandler import MessageHandler


# Events
class HandledMessage(Struct):
    message_digest: Bytes32
    message_id: Bytes32


class SimpleMessageHandler(MessageHandler):
    @abimethod
    def set_transceiver_manager(self, admin_in_transceiver_manager: Address, transceiver_manager: UInt64) -> None:
        self._set_transceiver_manager(admin_in_transceiver_manager, transceiver_manager)

    @abimethod
    def set_threshold(self, new_threshold: UInt64) -> None:
        self._set_threshold(new_threshold)

    @abimethod
    def send_message(self, message: MessageToSend, transceiver_instructions: TransceiverInstructions) -> UInt64:
        return self._send_message(message, transceiver_instructions)

    @subroutine
    def _handle_message(self, message_digest: Bytes32, message: MessageReceived) -> None:
        emit(HandledMessage(message_digest, message.id))
