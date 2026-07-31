// C5-REAL EXERGY CERTIFIED — ISOMORPHIC DOMAIN KERNEL (F# IRPAutomata → JS ES6)

export const Gravity = {
  C2_FriccionComputacional: 'C2_FriccionComputacional',
  C3_FluctuacionTermica: 'C3_FluctuacionTermica',
  C4_DegradacionGeometrica: 'C4_DegradacionGeometrica',
  C5_ColapsoOntologico: 'C5_ColapsoOntologico'
};

export class MembraneState {
  static Stable(entropyLevel) {
    return { type: 'Stable', entropyLevel };
  }
  static Smoothing(variance) {
    return { type: 'Smoothing', variance };
  }
  static Rollback(targetHash) {
    return { type: 'Rollback', targetHash };
  }
  static Apoptosis(taintLog) {
    return { type: 'Apoptosis', taintLog };
  }
}

/**
 * Pure state transition function (matches IRPAutomata.fs applyThermalStress)
 */
export function applyThermalStress(currentState, gravity) {
  switch (gravity) {
    case Gravity.C2_FriccionComputacional:
      if (currentState.type === 'Stable') {
        return MembraneState.Stable(parseFloat((currentState.entropyLevel + 0.01).toFixed(4)));
      }
      return currentState;

    case Gravity.C3_FluctuacionTermica:
      if (currentState.type === 'Stable') {
        return MembraneState.Smoothing(parseFloat((currentState.entropyLevel * 1.5).toFixed(4)));
      }
      if (currentState.type === 'Smoothing') {
        return MembraneState.Smoothing(parseFloat((currentState.variance + 0.1).toFixed(4)));
      }
      return currentState;

    case Gravity.C4_DegradacionGeometrica:
      if (currentState.type === 'Apoptosis') {
        return currentState;
      }
      return MembraneState.Rollback('LATEST_BFT_CHECKPOINT');

    case Gravity.C5_ColapsoOntologico:
      return MembraneState.Apoptosis('TAINT:C5_REAL_TRUNCATED');

    default:
      return currentState;
  }
}

/**
 * Pure commit boundary emitter (matches IRPAutomata.fs commitBoundary)
 */
export function commitBoundary(state) {
  switch (state.type) {
    case 'Stable':
      return `STATUS:OK|ENTROPY:${state.entropyLevel.toFixed(4)}`;
    case 'Smoothing':
      return `STATUS:SMOOTHING|VARIANCE:${state.variance.toFixed(4)}`;
    case 'Rollback':
      return `STATUS:ROLLBACK|HASH:${state.targetHash}`;
    case 'Apoptosis':
      return `STATUS:APOPTOSIS|TAINT:${state.taintLog}`;
    default:
      return `STATUS:UNKNOWN`;
  }
}

/**
 * Web Crypto SHA-256 helper for LedgerValidation
 */
export async function sha256Hex(message) {
  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Ledger Validation (matches F# LedgerValidation.validateAndAppend)
 */
export const GENESIS_ID = '0'.repeat(64);

export async function validateAndAppendNode(nodesMap, parentId, claim, payloadHash) {
  if (parentId !== GENESIS_ID && !nodesMap.has(parentId)) {
    throw new Error(`ParentNotFound: ${parentId}`);
  }
  if (!claim || claim.length > 64) {
    throw new Error(`InvalidClaimLength: ${claim}`);
  }
  if (!payloadHash || payloadHash.length !== 64) {
    throw new Error(`InvalidHashLength: ${payloadHash}`);
  }

  const rawContent = `${parentId}:${claim}:${payloadHash}`;
  const nodeId = await sha256Hex(rawContent);

  if (nodesMap.has(nodeId)) {
    throw new Error(`DuplicateNodeId: ${nodeId}`);
  }

  const newNode = {
    nodeId,
    parentId,
    claimSummary: claim,
    payloadHash,
    timestamp: new Date().toLocaleTimeString()
  };

  const newNodesMap = new Map(nodesMap);
  newNodesMap.set(nodeId, newNode);

  return { newNodesMap, newNode };
}
