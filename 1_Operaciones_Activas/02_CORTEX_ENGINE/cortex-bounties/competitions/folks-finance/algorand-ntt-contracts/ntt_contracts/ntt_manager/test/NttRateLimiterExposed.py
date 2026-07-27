from algopy import UInt64
from algopy.arc4 import Address, Bool, UInt16, UInt256, abimethod

from ...types import Bytes32, TrimmedAmount, TransceiverInstructions
from ..NttRateLimiter import NttRateLimiter


class NttRateLimiterExposed(NttRateLimiter):
    @abimethod
    def add_outbound_chain(self, peer_chain_id: UInt16) -> None:
        self._add_bucket(self.inbound_bucket_id(peer_chain_id), UInt256(0), UInt64(0))

    @abimethod
    def enqueue_or_consume_outbound_transfer(
        self,
        untrimmed_amount: UInt64,
        recipient_chain: UInt16,
        recipient: Bytes32,
        should_queue: Bool,
        transceiver_instructions: TransceiverInstructions,
        trimmed_amount: TrimmedAmount,
        message_id: Bytes32,
    ) -> Bool:
        return self._enqueue_or_consume_outbound_transfer(
            untrimmed_amount,
            recipient_chain,
            recipient,
            should_queue,
            transceiver_instructions,
            trimmed_amount,
            message_id
        )

    @abimethod
    def enqueue_or_consume_inbound_transfer(
        self,
        untrimmed_amount: UInt64,
        source_chain: UInt16,
        trimmed_amount: TrimmedAmount,
        recipient: Address,
        message_digest: Bytes32,
    ) -> Bool:
        return self._enqueue_or_consume_inbound_transfer(
            untrimmed_amount,
            source_chain,
            trimmed_amount,
            recipient,
            message_digest
        )

    @abimethod
    def delete_outbound_transfer(self, message_id: Bytes32) -> None:
        self._delete_outbound_transfer(message_id)

    @abimethod
    def delete_inbound_transfer(self, message_id: Bytes32) -> None:
        self._delete_inbound_transfer(message_id)
