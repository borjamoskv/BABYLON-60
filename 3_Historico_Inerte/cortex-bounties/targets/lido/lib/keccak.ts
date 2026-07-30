// C5-REAL EXERGY CERTIFIED
import { keccak256, toUtf8Bytes } from "ethers";

export function streccak(s: string) {
  return keccak256(toUtf8Bytes(s));
}
