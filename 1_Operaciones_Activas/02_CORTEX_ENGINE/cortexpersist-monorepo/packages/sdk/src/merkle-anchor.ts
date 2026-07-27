import { sha256 } from '@noble/hashes/sha256';

export class MerkleAnchor {
  private leaves: string[] = [];

  add(hash: string): void {
    this.leaves.push(hash);
  }

  getRoot(): string {
    if (this.leaves.length === 0) return '0'.repeat(64);
    let layer = [...this.leaves];
    while (layer.length > 1) {
      const next: string[] = [];
      for (let i = 0; i < layer.length; i += 2) {
        const left = layer[i]!;
        const right = layer[i + 1] ?? left; // duplicate last if odd
        const combined = left + right;
        const hashBytes = sha256(new TextEncoder().encode(combined));
        next.push(Array.from(hashBytes).map(b => b.toString(16).padStart(2, '0')).join(''));
      }
      layer = next;
    }
    return layer[0]!;
  }

  getProof(index: number): string[] {
    const proof: string[] = [];
    let layer = [...this.leaves];
    let idx = index;
    while (layer.length > 1) {
      const next: string[] = [];
      const sibling = idx % 2 === 0 ? layer[idx + 1] ?? layer[idx] : layer[idx - 1];
      if (sibling) proof.push(sibling);
      for (let i = 0; i < layer.length; i += 2) {
        const left = layer[i]!;
        const right = layer[i + 1] ?? left;
        const combined = left + right;
        const hashBytes = sha256(new TextEncoder().encode(combined));
        next.push(Array.from(hashBytes).map(b => b.toString(16).padStart(2, '0')).join(''));
      }
      layer = next;
      idx = Math.floor(idx / 2);
    }
    return proof;
  }

  clear(): void { this.leaves = []; }
  getLeaves(): string[] { return [...this.leaves]; }
}
