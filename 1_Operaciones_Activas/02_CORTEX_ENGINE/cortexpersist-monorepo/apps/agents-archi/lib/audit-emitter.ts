import { AuditEmitter } from '@cortex/sdk';

const apiKey = process.env.CORTEX_API_KEY || 'dummy-build-key';
const signingKey = process.env.CORTEX_SIGNING_PRIVATE_KEY || '00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000';

export const auditEmitter = new AuditEmitter({
  apiKey: apiKey,
  apiUrl: process.env.CORTEX_API_URL ?? 'https://api.cortexpersist.com',
  signingPrivateKey: signingKey,
  merkleAnchorInterval: 60_000,
  chainId: 'solana-mainnet',
});
