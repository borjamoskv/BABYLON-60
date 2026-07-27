export type CortexConfig = {
  apiKey: string;
  apiUrl?: string | undefined;
  signingPrivateKey?: string | undefined;
  merkleAnchorInterval?: number | undefined;
  chainId?: string | undefined;
};

export type CortexEvent = {
  id?: string | undefined;
  type: string;
  payload: Record<string, unknown>;
  timestamp?: number | undefined;
  signature?: string | undefined;
  merkleRoot?: string | undefined;
};

export type AuditFinding = {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  protocol: string;
  auditor: string;
  title: string;
  description?: string;
  cve?: string;
  exploitable?: boolean;
  anchored?: boolean;
  merkleProof?: string[];
};

export type HashBlock = {
  index: number;
  hash: string;
  prevHash: string;
  timestamp: number;
  data: string;
};
