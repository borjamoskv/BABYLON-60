export const MAX_UINT8 = 2n ** 8n - 1n;
export const MAX_UINT16 = 2n ** 16n - 1n;
export const MAX_UINT32 = 2n ** 32n - 1n;
export const MAX_UINT64 = 2n ** 64n - 1n;
export const MAX_UINT256 = 2n ** 256n - 1n;

export const MAX_INT64 = 2n ** 63n - 1n;

export function getRandomUInt(max: number | bigint): bigint {
  return BigInt(Math.floor(Math.random() * Number(max)));
}

export const bigIntMax = (...args: bigint[]) => args.reduce((m, e) => (e > m ? e : m));
export const bigIntMin = (...args: bigint[]) => args.reduce((m, e) => (e < m ? e : m));
