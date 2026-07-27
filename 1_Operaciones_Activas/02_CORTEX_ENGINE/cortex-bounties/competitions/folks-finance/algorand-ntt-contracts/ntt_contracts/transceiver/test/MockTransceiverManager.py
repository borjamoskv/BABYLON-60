from algopy import Bytes, Global, UInt64, gtxn, itxn, op
from algopy.arc4 import Address, Bool, DynamicArray, Struct, abi_call, abimethod, emit

from folks_contracts.library import BytesUtils
from ... import errors as err
from ...types import ARC4UInt64, Bytes32, TransceiverInstructions, MessageToSend, MessageReceived
from ..interfaces.ITransceiverManager import (
    ITransceiverManager,
    MessageHandlerAdded,
    TransceiverAdded,
    TransceiverRemoved,
    AttestationReceived,
)
from ..Transceiver import Transceiver


# Events
class InternalQuoteDeliveryPrices(Struct):
    message_handler: ARC4UInt64
    message_id: Bytes32
    transceiver_instruction: TransceiverInstructions

class MessageSentToTransceivers(Struct):
    message_handler: ARC4UInt64
    fee_payment_amount: ARC4UInt64
    fee_payment_receiver: Address
    message_id: Bytes32
    transceiver_instructions: TransceiverInstructions


class MockTransceiverManager(ITransceiverManager):
    def __init__(self) -> None:
        self._message_attestations = UInt64(0)
        self._message_digest = Bytes32.from_bytes(op.bzero(32))
        self._handler_transceivers = DynamicArray[ARC4UInt64]()
        self._total_delivery_price = UInt64(0)

    @abimethod
    def set_message_attestations(self, new_message_attestations: UInt64) -> None:
        self._message_attestations = new_message_attestations

    @abimethod
    def set_message_digest(self, new_message_digest: Bytes32) -> None:
        self._message_digest = new_message_digest.copy()

    @abimethod
    def set_handler_transceivers(self, new_handler_transceivers: DynamicArray[ARC4UInt64]) -> None:
        self._handler_transceivers = new_handler_transceivers.copy()

    @abimethod
    def set_total_delivery_price(self, new_total_delivery_price: UInt64) -> None:
        self._total_delivery_price = new_total_delivery_price

    @abimethod
    def add_message_handler(self, message_handler_admin: Address) -> Bool:
        message_handler = Global.caller_application_id
        emit(MessageHandlerAdded(ARC4UInt64(message_handler), message_handler_admin))
        return Bool(True)

    @abimethod
    def add_transceiver(self, message_handler: UInt64, transceiver: UInt64) -> None:
        emit(TransceiverAdded(ARC4UInt64(message_handler), ARC4UInt64(transceiver)))

    @abimethod
    def remove_transceiver(self, message_handler: UInt64, transceiver: UInt64) -> None:
        emit(TransceiverRemoved(ARC4UInt64(message_handler), ARC4UInt64(transceiver)))

    @abimethod(readonly=True)
    def get_handler_transceivers(self, message_handler: UInt64) -> DynamicArray[ARC4UInt64]:
        return self._handler_transceivers

    @abimethod(readonly=True)
    def quote_delivery_prices(
        self,
        message_handler: UInt64,
        message: MessageToSend,
        transceiver_instructions: TransceiverInstructions,
    ) -> UInt64:
        emit(InternalQuoteDeliveryPrices(ARC4UInt64(message_handler), message.id, transceiver_instructions))
        return self._total_delivery_price

    @abimethod
    def send_message_to_transceivers(
        self,
        fee_payment: gtxn.PaymentTransaction,
        message: MessageToSend,
        transceiver_instructions: TransceiverInstructions,
    ) -> None:
        message_handler = Global.caller_application_id
        emit(MessageSentToTransceivers(
            ARC4UInt64(message_handler),
            ARC4UInt64(fee_payment.amount),
            Address(fee_payment.receiver),
            message.id,
            transceiver_instructions,
        ))

    # custom method to send message to specific transceiver
    @abimethod
    def send_message(
        self,
        transceiver: UInt64,
        fee_amount: UInt64,
        message: MessageToSend,
        transceiver_instruction: Bytes
    ) -> None:
        transceiver_address, exists = op.AppParamsGet.app_address(transceiver)
        assert exists, err.TRANSCEIVER_ADDRESS_UNKNOWN

        fee_payment_txn = itxn.Payment(amount=fee_amount, receiver=transceiver_address, fee=0)
        abi_call(
            Transceiver.send_message,
            fee_payment_txn,
            message,
            transceiver_instruction,
            app_id=transceiver,
            fee=0,
        )

    # custom method to send message to specific transceiver with incorrect receiver for payment
    @abimethod
    def send_message_with_incorrect_payment(
        self,
        transceiver: UInt64,
        fee_amount: UInt64,
        message: MessageToSend,
        transceiver_instruction: Bytes
    ) -> None:
        fee_payment_txn = itxn.Payment(amount=fee_amount, receiver=Global.current_application_address, fee=0)
        abi_call(
            Transceiver.send_message,
            fee_payment_txn,
            message,
            transceiver_instruction,
            app_id=transceiver,
            fee=0,
        )

    @abimethod
    def attestation_received(self, message: MessageReceived) -> None:
        message_handler = BytesUtils.safe_convert_bytes32_to_uint64(message.handler_address.copy())
        message_digest = self.calculate_message_digest(message)
        new_num_attestations = self.message_attestations(message_digest) + 1

        emit(AttestationReceived(
            message.id,
            message.source_chain_id,
            message.source_address,
            ARC4UInt64(message_handler),
            message_digest,
            ARC4UInt64(new_num_attestations))
        )

    @abimethod(readonly=True)
    def message_attestations(self, message_digest: Bytes32) -> UInt64:
        return self._message_attestations

    @abimethod(readonly=True)
    def has_transceiver_attested(self, message_digest: Bytes32, transceiver: UInt64) -> Bool:
        return Bool(self._message_attestations > 0)

    @abimethod(readonly=True)
    def calculate_message_digest(self, message: MessageReceived) -> Bytes32:
        return self._message_digest
