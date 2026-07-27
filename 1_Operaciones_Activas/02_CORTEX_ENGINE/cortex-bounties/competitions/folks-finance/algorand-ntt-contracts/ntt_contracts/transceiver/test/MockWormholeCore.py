from algopy import Bytes, Contract, OnCompleteAction, Txn, UInt64, op
from algopy.arc4 import Bool, DynamicBytes, Struct, emit

from ...types import ARC4UInt64


# Events
class MessagePublished(Struct):
    payload: DynamicBytes
    nonce: ARC4UInt64
    sequence: ARC4UInt64

class VAAVerified(Struct):
    is_verified: Bool

class MockWormholeCore(Contract):
    def __init__(self) -> None:
        self.MessageFee = UInt64(0)

    def approval_program(self) -> bool:
        if Txn.application_id.id == 0:
            self.MessageFee = op.btoi(Txn.application_args(0))
        else:
            match Txn.application_args(0):
                case b"optIn":
                    assert Txn.on_completion == OnCompleteAction.OptIn

                    # initialise blob
                    op.AppLocal.put(0, Bytes.from_hex("00"), op.bzero(127))
                case b"publishMessage":
                    # increment sequence
                    sequence = op.extract_uint64(op.AppLocal.get_bytes(1, Bytes.from_hex("00")), 0) + 1
                    op.AppLocal.put(1, Bytes.from_hex("00"), op.replace(op.bzero(127), 0, op.itob(sequence)))

                    emit(MessagePublished(
                        DynamicBytes(Txn.application_args(1)),
                        ARC4UInt64(op.btoi(Txn.application_args(2))),
                        ARC4UInt64(sequence),
                    ))
                case b"verifyVAA":
                    emit(VAAVerified(Bool(True)))
                case _:
                    return False
        return True

    def clear_state_program(self) -> bool:
        return True
