import { convertNumberToBytes, enc } from "./bytes.ts";

// AccessControl
export function getRoleBoxKey(role: Uint8Array): Uint8Array {
  if (role.length !== 16) throw Error("Role must be 16 bytes");
  return Uint8Array.from([...enc.encode("role_"), ...role]);
}

export function getAddressRolesBoxKey(role: Uint8Array, addressPk: Uint8Array): Uint8Array {
  if (role.length !== 16) throw Error("Role must be 16 bytes");
  if (addressPk.length !== 32) throw Error("Address must be 32 bytes");
  return Uint8Array.from([...enc.encode("address_roles_"), ...role, ...addressPk]);
}

// RateLimiter
export function getBucketBoxKey(bucketId: Uint8Array): Uint8Array {
  if (bucketId.length !== 32) throw Error("Bucket id must be 32 bytes");
  return Uint8Array.from([...enc.encode("rate_limit_buckets_"), ...bucketId]);
}

// WormholeTransceiver
export function getWormholePeersBoxKey(peerChainId: number | bigint): Uint8Array {
  return Uint8Array.from([...enc.encode("wormhole_peer_"), ...convertNumberToBytes(peerChainId, 2)]);
}

export function getVAAsConsumedBoxKey(digest: Uint8Array): Uint8Array {
  if (digest.length !== 32) throw Error("Digest must be 32 bytes");
  return Uint8Array.from([...enc.encode("vaas_consumed_"), ...digest]);
}

// TransceiverManager
export function getHandlerTransceiversBoxKey(messageHandler: number | bigint): Uint8Array {
  return Uint8Array.from([...enc.encode("handler_transceivers_"), ...convertNumberToBytes(messageHandler, 8)]);
}

export function getTransceiverAttestationsBoxKey(messageDigest: Uint8Array, transceiver: number | bigint): Uint8Array {
  if (messageDigest.length !== 32) throw Error("Message digest must be 32 bytes");
  return Uint8Array.from([...enc.encode("attestations_"), ...messageDigest, ...convertNumberToBytes(transceiver, 8)]);
}

export function getNumAttestationsBoxKey(messageDigest: Uint8Array): Uint8Array {
  if (messageDigest.length !== 32) throw Error("Message digest must be 32 bytes");
  return Uint8Array.from([...enc.encode("num_attestations_"), ...messageDigest]);
}

// MessageHandler
export function getMessagesExecutedBoxKey(messageDigest: Uint8Array): Uint8Array {
  if (messageDigest.length !== 32) throw Error("Message digest must be 32 bytes");
  return Uint8Array.from([...enc.encode("messages_executed_"), ...messageDigest]);
}

// NttRateLimiter
export function getOutboundQueuedTransfersBoxKey(messageId: Uint8Array): Uint8Array {
  if (messageId.length !== 32) throw Error("Message id must be 32 bytes");
  return Uint8Array.from([...enc.encode("outbound_queued_transfers_"), ...messageId]);
}

export function getInboundQueuedTransfersBoxKey(messageDigest: Uint8Array): Uint8Array {
  if (messageDigest.length !== 32) throw Error("Message digest must be 32 bytes");
  return Uint8Array.from([...enc.encode("inbound_queued_transfers_"), ...messageDigest]);
}

// NttManager
export function getNttManagerPeerBoxKey(peerChainId: number | bigint): Uint8Array {
  return Uint8Array.from([...enc.encode("ntt_manager_peer_"), ...convertNumberToBytes(peerChainId, 2)]);
}
