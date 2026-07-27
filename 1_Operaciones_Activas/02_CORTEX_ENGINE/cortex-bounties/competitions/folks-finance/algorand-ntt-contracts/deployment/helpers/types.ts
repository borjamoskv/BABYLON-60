// C5-REAL EXERGY CERTIFIED
export enum NetworkType {
  MAINNET = "mainnet",
  TESTNET = "testnet",
}

export type NttPeerChain = {
  wormholeChainId: number;
  nttManager: string;
  wormholeTransceiver: string;
};
