import type { CortexConfig, CortexEvent } from './types';
import { Ed25519Signer } from './ed25519-signer';
import { HashChain } from './hash-chain';
import { MerkleAnchor } from './merkle-anchor';

export class CortexClient {
  private config: Required<CortexConfig>;
  private signer?: Ed25519Signer;
  private chain: HashChain;
  private anchor: MerkleAnchor;

  constructor(config: CortexConfig) {
    this.config = {
      apiUrl: 'https://api.cortexpersist.com',
      signingPrivateKey: '',
      merkleAnchorInterval: 60_000,
      chainId: 'solana-mainnet',
      ...config,
    };
    this.chain = new HashChain();
    this.anchor = new MerkleAnchor();
    if (this.config.signingPrivateKey) {
      this.signer = new Ed25519Signer(this.config.signingPrivateKey);
    }
  }

  async event(evt: CortexEvent): Promise<{
    id: string;
    hash: string;
    anchored: boolean;
    merkleRoot?: string | undefined;
    signature?: string | undefined;
    timestamp?: number | undefined;
  }> {
    const payload = JSON.stringify({
      ...evt,
      timestamp: evt.timestamp ?? Date.now(),
    });

    let signature: string | undefined;
    if (this.signer) {
      signature = await this.signer.sign(payload);
    }

    const block = this.chain.append(payload);
    this.anchor.add(block.hash);

    const body: CortexEvent = {
      ...evt,
      id: evt.id ?? block.hash.slice(0, 16),
      timestamp: block.timestamp,
      signature,
      merkleRoot: this.anchor.getRoot(),
    };

    const res = await fetch(`${this.config.apiUrl}/v1/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config.apiKey}`,
        'X-Cortex-Chain-Index': String(block.index),
        'X-Cortex-Block-Hash': block.hash,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      throw new Error(`CortexClient: API error ${res.status} — ${await res.text()}`);
    }

    return {
      id: body.id!,
      hash: block.hash,
      anchored: !!body.merkleRoot,
      merkleRoot: body.merkleRoot,
      signature: body.signature,
      timestamp: body.timestamp,
    };
  }

  getChain() { return this.chain.getBlocks(); }
  getMerkleRoot() { return this.anchor.getRoot(); }
}
