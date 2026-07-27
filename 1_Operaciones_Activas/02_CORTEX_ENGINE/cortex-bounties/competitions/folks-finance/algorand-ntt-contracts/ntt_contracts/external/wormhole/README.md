# External Contracts from Wormhole

This folder contains external smart contracts from Wormhole

## TmplSig

`TmplSig` is a logic signature account which is used to opt into various applications with its local state used for storage.

When publishing a message, the `TmplSig` account should be opted into and rekeyed to `WormholeCore`

- TMPL_ADDR_IDX = 0
- TMPL_EMITTER_ID = TransceiverAddress byte[32]

When verifying message in `WormholeCore.verifyVAA` call, the `TmplSig` account should be opted into and rekeyed to `WormholeCore`

- TMPL_ADDR_IDX = `WormholeCore.currentGuardianSetIndex`
- TPL_EMITTER_ID = "guardian" utf8 string stored in hex

**OUTDATED - CAN USE BOX STORAGE NOW**. When checking for duplicate received messages, the `TmplSig` account should be opted into and rekeyed to handler e.g. `TokenBridge`

- TMPL_ADDR_IDX = `int(vaa.sequence / MAX_BITS)`
- TMPL_EMITTER_ID = "guardian" utf8 string stored in hex

## VerifySigs

`VerifySigs` is a logic signature account which is used to verify the signatures of a VAA.
