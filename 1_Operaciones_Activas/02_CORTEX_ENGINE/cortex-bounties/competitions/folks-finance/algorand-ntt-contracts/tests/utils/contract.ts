import type { AlgorandFixture } from "@algorandfoundation/algokit-utils/types/testing";
import { sha256 } from "@noble/hashes/sha2";
import { type Address, OnApplicationComplete, encodeUint64, getApplicationAddress } from "algosdk";
import { readFileSync } from "node:fs";

import { enc } from "./bytes.ts";

export async function deployDummyContract(localnet: AlgorandFixture, creator: string | Address): Promise<bigint> {
  const teal = "#pragma version 11\nint 1";
  const compiled = await localnet.algorand.app.compileTeal(teal);
  const result = await localnet.algorand.send.appCreate({
    sender: creator,
    approvalProgram: compiled.compiledBase64ToBytes,
    clearStateProgram: compiled.compiledBase64ToBytes,
    onComplete: OnApplicationComplete.NoOpOC,
    args: [],
  });
  return result.appId;
}

export async function deployWormholeCore(
  localnet: AlgorandFixture,
  creator: string | Address,
  messageFee: number | bigint,
): Promise<bigint> {
  const approvalTeal = Buffer.from(
    readFileSync("specs/teal/transceiver/test/MockWormholeCore.approval.teal"),
  ).toString();
  const clearTeal = Buffer.from(readFileSync("specs/teal/transceiver/test/MockWormholeCore.clear.teal")).toString();
  const approval = await localnet.algorand.app.compileTeal(approvalTeal);
  const clear = await localnet.algorand.app.compileTeal(clearTeal);
  const result = await localnet.algorand.send.appCreate({
    sender: creator,
    approvalProgram: approval.compiledBase64ToBytes,
    clearStateProgram: clear.compiledBase64ToBytes,
    onComplete: OnApplicationComplete.NoOpOC,
    args: [encodeUint64(messageFee)],
    schema: {
      globalInts: 1,
      globalByteSlices: 0,
      localInts: 0,
      localByteSlices: 1,
    },
  });
  return result.appId;
}

export async function getWormholeEmitterLSig(
  localnet: AlgorandFixture,
  emitterAppId: number | bigint,
  wormholeCoreAppId: number | bigint,
) {
  const { compiledBase64ToBytes: compiledEmitterLogicSig } = await localnet.algorand.app.compileTealTemplate(
    readFileSync("ntt_contracts/external/wormhole/TmplSig.teal").toString(),
    {
      ADDR_IDX: 0,
      EMITTER_ID: getApplicationAddress(emitterAppId).publicKey,
      APP_ID: wormholeCoreAppId,
      APP_ADDRESS: getApplicationAddress(wormholeCoreAppId).publicKey,
    },
  );
  return localnet.algorand.account.logicsig(compiledEmitterLogicSig);
}

export const PAGE_SIZE = 4096;

export function calculateProgramSha256(approvalProgram: Uint8Array, clearStateProgram: Uint8Array): Uint8Array {
  // build
  let program = enc.encode("approval");
  for (let i = 0; i < approvalProgram.length; i += PAGE_SIZE) {
    program = Uint8Array.from([...program, ...sha256(approvalProgram.slice(i, i + PAGE_SIZE))]);
  }
  program = Uint8Array.from([...program, ...enc.encode("clear")]);
  for (let i = 0; i < clearStateProgram.length; i += PAGE_SIZE) {
    program = Uint8Array.from([...program, ...sha256(clearStateProgram.slice(i, i + PAGE_SIZE))]);
  }

  // hash result
  return sha256(program);
}
