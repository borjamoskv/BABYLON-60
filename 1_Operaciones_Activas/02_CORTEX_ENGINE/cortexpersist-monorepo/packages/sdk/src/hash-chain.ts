import { sha256 } from '@noble/hashes/sha256';
import type { HashBlock } from './types';

export class HashChain {
  private blocks: HashBlock[] = [];

  append(data: string): HashBlock {
    const index = this.blocks.length;
    const prevHash = index === 0 ? '0'.repeat(64) : this.blocks[index - 1]!.hash;
    const timestamp = Date.now();
    const raw = `${index}:${prevHash}:${timestamp}:${data}`;
    const hashBytes = sha256(new TextEncoder().encode(raw));
    const hash = Array.from(hashBytes).map(b => b.toString(16).padStart(2, '0')).join('');
    const block: HashBlock = { index, hash, prevHash, timestamp, data };
    this.blocks.push(block);
    return block;
  }

  verify(): boolean {
    for (let i = 1; i < this.blocks.length; i++) {
      if (this.blocks[i]!.prevHash !== this.blocks[i - 1]!.hash) return false;
    }
    return true;
  }

  getBlocks(): HashBlock[] { return [...this.blocks]; }
  getLatest(): HashBlock | undefined { return this.blocks[this.blocks.length - 1]; }
}
