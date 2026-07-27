// C5-REAL EXERGY CERTIFIED
export function isHex(hex: string, bytesLength: number) {
  return hex.startsWith("0x") && hex.length - 2 === bytesLength * 2;
}
