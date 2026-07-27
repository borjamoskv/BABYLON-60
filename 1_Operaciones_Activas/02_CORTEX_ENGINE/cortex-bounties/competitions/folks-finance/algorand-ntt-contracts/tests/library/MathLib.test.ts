import { algorandFixture } from "@algorandfoundation/algokit-utils/testing";
import type { TransactionSignerAccount } from "@algorandfoundation/algokit-utils/types/account";
import type { Account, Address } from "algosdk";

import { MathLibExposedClient, MathLibExposedFactory } from "../../specs/client/MathLibExposed.client.ts";
import { MAX_UINT8, MAX_UINT64 } from "../utils/uint.ts";

describe("TrimmedAmountLib", () => {
  const localnet = algorandFixture();

  let factory: MathLibExposedFactory;
  let client: MathLibExposedClient;
  let appId: bigint;

  let creator: Address & Account & TransactionSignerAccount;

  beforeAll(async () => {
    await localnet.newScope();
    const { algorand, generateAccount } = localnet.context;

    creator = await generateAccount({ initialFunds: (100).algo() });

    factory = algorand.client.getTypedAppFactory(MathLibExposedFactory, {
      defaultSender: creator,
      defaultSigner: creator.signer,
    });
  });

  test("deploys with correct state", async () => {
    const { appClient, result } = await factory.deploy();
    appId = result.appId;
    client = appClient;
    expect(appId).not.toEqual(0n);
  });

  describe("max uint8", () => {
    test.each([
      { a: 0, b: 0, expected: 0 },
      { a: 15, b: 15, expected: 15 },
      { a: 1, b: 0, expected: 1 },
      { a: 0, b: 1, expected: 1 },
      { a: MAX_UINT8, b: 15, expected: Number(MAX_UINT8) },
      { a: 15, b: MAX_UINT8, expected: Number(MAX_UINT8) },
    ])("of $a and $b is $expected", async ({ a, b, expected }) => {
      expect(await client.maxUint8({ args: [a, b] })).toEqual(expected);
    });
  });

  describe("min uint8", () => {
    test.each([
      { a: 0, b: 0, expected: 0 },
      { a: 15, b: 15, expected: 15 },
      { a: 1, b: 0, expected: 0 },
      { a: 0, b: 1, expected: 0 },
      { a: MAX_UINT8, b: 15, expected: 15 },
      { a: 15, b: MAX_UINT8, expected: 15 },
    ])("of $a and $b is $expected", async ({ a, b, expected }) => {
      expect(await client.minUint8({ args: [a, b] })).toEqual(expected);
    });
  });

  describe("max uint64", () => {
    test.each([
      { a: 0n, b: 0n, expected: 0n },
      { a: 123456n, b: 123456n, expected: 123456n },
      { a: 1, b: 0, expected: 1n },
      { a: 0, b: 1, expected: 1n },
      { a: MAX_UINT64, b: 123456n, expected: MAX_UINT64 },
      { a: 123456n, b: MAX_UINT64, expected: MAX_UINT64 },
    ])("of $a and $b is $expected", async ({ a, b, expected }) => {
      expect(await client.maxUint64({ args: [a, b] })).toEqual(expected);
    });
  });

  describe("min uint64", () => {
    test.each([
      { a: 0n, b: 0n, expected: 0n },
      { a: 123456n, b: 123456n, expected: 123456n },
      { a: 1, b: 0, expected: 0n },
      { a: 0, b: 1, expected: 0n },
      { a: MAX_UINT64, b: 123456n, expected: 123456n },
      { a: 123456n, b: MAX_UINT64, expected: 123456n },
    ])("of $a and $b is $expected", async ({ a, b, expected }) => {
      expect(await client.minUint64({ args: [a, b] })).toEqual(expected);
    });
  });
});
