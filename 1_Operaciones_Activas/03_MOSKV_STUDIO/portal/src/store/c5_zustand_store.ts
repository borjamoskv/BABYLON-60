import { create } from 'zustand';

// INV_C5_52: Inviolabilidad del Estado UI.
// Este store intercepta el stream gRPC proveniente de BABYLON-60.
// Ningún componente React puede mutar este estado directamente;
// solo el puente criptográfico (tonic/gRPC) tiene permisos de escritura.

interface ExergyState {
  blockHash: string | null;
  sequenceId: number;
  exergyLevel: number;
  cryptographicProof: Uint8Array | null;
}

interface C5Store extends ExergyState {
  // Función interna para que el cliente gRPC inyecte el estado certificado
  _hydrateFromKernel: (payload: ExergyState) => void;
}

export const useC5Store = create<C5Store>((set) => ({
  blockHash: null,
  sequenceId: 0,
  exergyLevel: 0.0,
  cryptographicProof: null,

  _hydrateFromKernel: (payload: ExergyState) => {
    // Verificación superficial de coherencia (el C5-REAL Kernel hace el resto)
    if (!payload.cryptographicProof) {
      console.error("[C5-REAL] TAINT DETECTED: Missing cryptographic proof from kernel.");
      return;
    }
    
    set({
      blockHash: payload.blockHash,
      sequenceId: payload.sequenceId,
      exergyLevel: payload.exergyLevel,
      cryptographicProof: payload.cryptographicProof
    });
  }
}));
