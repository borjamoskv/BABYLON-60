import { etc, sign, getPublicKey } from '@noble/ed25519';
import { sha512 } from '@noble/hashes/sha512';

// Required for @noble/ed25519 in Node.js
etc.sha512Sync = (...msgs) => sha512(etc.concatBytes(...msgs));

export class Ed25519Signer {
  private privKey: Uint8Array;

  constructor(privateKeyHex: string) {
    this.privKey = hexToBytes(privateKeyHex);
  }

  async sign(message: string): Promise<string> {
    const msgBytes = new TextEncoder().encode(message);
    const sig = await sign(msgBytes, this.privKey);
    return bytesToHex(sig);
  }

  getPublicKey(): string {
    return bytesToHex(getPublicKey(this.privKey));
  }
}

function hexToBytes(hex: string): Uint8Array {
  const clean = hex.startsWith('0x') ? hex.slice(2) : hex;
  return new Uint8Array(clean.match(/.{1,2}/g)!.map(b => parseInt(b, 16)));
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}
