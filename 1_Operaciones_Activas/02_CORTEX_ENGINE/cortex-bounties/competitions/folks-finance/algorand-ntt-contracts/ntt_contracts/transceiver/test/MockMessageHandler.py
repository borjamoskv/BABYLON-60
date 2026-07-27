from algopy import ARC4Contract, Account, UInt64, itxn
from algopy.arc4 import Address, Bool, abimethod, abi_call

from ...types import TransceiverInstructions, MessageToSend
from ..interfaces.ITransceiverManager import ITransceiverManager


class MockMessageHandler(ARC4Contract):
    @abimethod
    def set_transceiver_manager(self, admin_in_transceiver_manager: Address, transceiver_manager: UInt64) -> Bool:
        was_added, txn = abi_call(
            ITransceiverManager.add_message_handler,
            admin_in_transceiver_manager,
            app_id=transceiver_manager,
            fee=0,
        )
        return was_added

    @abimethod
    def send_message_to_transceivers(
        self,
        fee_payment_amount: UInt64,
        fee_payment_receiver: Address,
        transceiver_manager: UInt64,
        message: MessageToSend,
        transceiver_instructions: TransceiverInstructions,
    ) -> None:
        abi_call(
            ITransceiverManager.send_message_to_transceivers,
            itxn.Payment(amount=fee_payment_amount, receiver=Account(fee_payment_receiver.bytes), fee=0),
            message,
            transceiver_instructions,
            app_id=transceiver_manager,
            fee=0,
        )
