from abc import ABC, abstractmethod
from algopy import ARC4Contract, UInt64, gtxn
from algopy.arc4 import Address, Bool, DynamicArray, Struct, abimethod

from ...types import (
    ARC4UInt16,
    ARC4UInt64,
    MessageDigest,
    MessageId,
    MessageReceived,
    MessageToSend,
    TransceiverInstructions,
    UniversalAddress,
)


# Events
class MessageHandlerAdded(Struct):
    message_handler: ARC4UInt64
    admin: Address

class TransceiverAdded(Struct):
    message_handler: ARC4UInt64
    transceiver: ARC4UInt64

class TransceiverRemoved(Struct):
    message_handler: ARC4UInt64
    transceiver: ARC4UInt64

class MessageSent(Struct):
    message_handler: ARC4UInt64
    transceiver: ARC4UInt64
    message_id: MessageId

class AttestationReceived(Struct):
    message_id: MessageId
    source_chain_id: ARC4UInt16
    source_address: UniversalAddress
    message_handler: ARC4UInt64
    message_digest: MessageDigest
    num_attestations: ARC4UInt64


class ITransceiverManager(ARC4Contract, ABC):
    @abstractmethod
    @abimethod
    def add_message_handler(self, message_handler_admin: Address) -> Bool:
        """Set new transceiver manager.

        Care should be taken when setting the transceiver manager to avoid a scenario where in-flight messages can't
        be executed. If the configured transceiver is connected to the old transceiver manager then the messages will
        be attested in that old transceiver manager. Then the threshold for the messages' attestations would not be
        met in the new transceiver, so they would never be able to get executed.

        Args:
            message_handler_admin: The admin for the message handler

        Returns:
            True if the message handler was added or false if it was already added
        """
        pass

    @abstractmethod
    @abimethod
    def add_transceiver(self, message_handler: UInt64, transceiver: UInt64) -> None:
        """Add a transceiver to a given message handler.

        Args:
            message_handler: The message handler to configure
            transceiver: The transceiver to add
        """
        pass

    @abstractmethod
    @abimethod
    def remove_transceiver(self, message_handler: UInt64, transceiver: UInt64) -> None:
        """Remove a transceiver fom a given message handler.

        Args:
            message_handler: The message handler to configure
            transceiver: The transceiver to remove
        """
        pass

    @abstractmethod
    @abimethod(readonly=True)
    def get_handler_transceivers(self, message_handler: UInt64) -> DynamicArray[ARC4UInt64]:
        """Get an iterable list of transceivers configured for the given message handler.

        Args:
            message_handler: The message handler to get the transceivers of

        Returns:
            The transceiver list
        """
        pass

    @abstractmethod
    @abimethod(readonly=True)
    def quote_delivery_prices(
        self,
        message_handler: UInt64,
        message: MessageToSend,
        transceiver_instructions: TransceiverInstructions,
    ) -> UInt64:
        """Fetch the total delivery price to send a message through the configured transceiver(s).

        Args:
            message_handler: The message handler to send a message for
            message: The message to send
            transceiver_instructions: The instructions to use for each transceiver

        Returns:
            The total delivery price
        """
        pass

    @abstractmethod
    @abimethod
    def send_message_to_transceivers(
        self,
        fee_payment: gtxn.PaymentTransaction,
        message: MessageToSend,
        transceiver_instructions: TransceiverInstructions,
    ) -> None:
        """Called by a message handler to send a message through its configured transceiver(s).

        Args:
            fee_payment: The ALGO payment to cover the total delivery price
            message: The message to send
            transceiver_instructions: The instructions to use for each transceiver
        """
        pass

    @abstractmethod
    @abimethod
    def attestation_received(self, message: MessageReceived) -> None:
        """Called by a configured transceiver to attest to the fact that a message was received for a given message
        handler. The message handler is responsible for implementing its own logic for the attestations required.

        Args:
            message: The message received, including the message handler
        """
        pass

    @abstractmethod
    @abimethod(readonly=True)
    def message_attestations(self, message_digest: MessageDigest) -> UInt64:
        """The number of attestations the given message has received.

         Args:
             message_digest: Unique identifier of the message received.

         Returns:
             Number of attestations from transceivers.
         """
        pass

    @abstractmethod
    @abimethod(readonly=True)
    def has_transceiver_attested(self, message_digest: MessageDigest, transceiver: UInt64) -> Bool:
        """Returns whether the transceiver has attested to the message

         Args:
             message_digest: Unique identifier of the message received.
             transceiver: The transceiver to check for attestation

         Returns:
             Whether the transceiver has attested to the message
         """
        pass

    @abstractmethod
    @abimethod(readonly=True)
    def calculate_message_digest(self, message: MessageReceived) -> MessageDigest:
        """Calculate a unique identifier of the message received by taking a hash of its bytes.

        Note that this is different from the `message.id`. The `message.id` is user defined so offers no guarantees.
        The message digest cannot be manipulated and is guaranteed to be unique.

        Args:
            message: The message received

        Returns:
            Message digest
        """
        pass
