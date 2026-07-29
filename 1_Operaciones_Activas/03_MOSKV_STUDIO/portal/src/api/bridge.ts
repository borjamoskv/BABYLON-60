import { GrpcWebFetchTransport } from "@protobuf-ts/grpcweb-transport";
import { ExergyBridgeClient } from "./c5_exergy.client";
import { useC5Store } from "../store/c5_zustand_store";
import { LedgerRequest } from "./c5_exergy";

// URL del BABYLON-60 Tonic Server (asumimos el puerto gRPC-Web por defecto en dev)
const transport = new GrpcWebFetchTransport({
    baseUrl: "http://localhost:50051"
});

const client = new ExergyBridgeClient(transport);

export function startExergyStream() {
    console.log("[C5-REAL] Initiating Sovereign Exergy Stream...");

    const request: LedgerRequest = {
        fromSequence: BigInt(useC5Store.getState().sequenceId || 0)
    };

    const call = client.streamLedger(request);

    // Hydration listener
    call.responses.onMessage((message) => {
        // En un caso real, aquí validaríamos la prueba criptográfica.
        useC5Store.getState()._hydrateFromKernel({
            blockHash: message.blockHash,
            sequenceId: Number(message.sequenceId),
            exergyLevel: message.exergyLevel,
            cryptographicProof: message.cryptographicProof
        });
        console.debug("[C5-REAL] Hydrated block:", message.blockHash);
    });

    call.responses.onComplete(() => {
        console.warn("[C5-REAL] Exergy stream disconnected. Kernel might be down.");
        // Intentar reconectar tras un delay
        setTimeout(startExergyStream, 5000);
    });

    call.responses.onError((error) => {
        console.error("[C5-REAL] Exergy stream error:", error);
    });
}
