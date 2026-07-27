export interface CortexEnv {
  CORTEX_KV: KVNamespace;
  CORTEX_ENV: string;
  CORTEX_VERSION: string;
  CORTEX_API_KEY: string;
}

export type Domain =
  | 'cortexpersist.com'
  | 'cortexpersist.dev'
  | 'cortexpersist.org'
  | 'agents.archi';

export const DOMAINS: Domain[] = [
  'cortexpersist.com',
  'cortexpersist.dev',
  'cortexpersist.org',
  'agents.archi',
];
