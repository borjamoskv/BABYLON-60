#!/usr/bin/env python3
"""
PoC: BABYLON-60 Rust FFI & SharedManifest Topological Leap (Cambio 2)
Clasificación: C5-REAL Alta Exergía
Ruta: scripts/c5_demos/poc_rust_ffi_topological_leap.py

Esta prueba de concepto demuestra la semántica exacta del salto topológico:
1. Python ya no computa hashes de estado, delega al kernel C/Rust FFI.
2. SharedManifest: Un struct C de 64 bytes operado vía Seqlock SPMC.
3. Domain Separation: Merkle con \x00, \x01, \x02 + cardinalidad.
4. Fail-Stop Circuit Breaker en caso de violación causal.
"""

import ctypes
import hashlib
import uuid

# =====================================================================
# 1. STRUCT DE MEMORIA COMPARTIDA (C-ABI / Ring-0)
# =====================================================================

class SharedManifest(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("seqlock", ctypes.c_uint64),        # 8 bytes (Control SPMC)
        ("lamport_t", ctypes.c_uint64),      # 8 bytes (Reloj lógico causal)
        ("seq", ctypes.c_uint64),            # 8 bytes (Contigüidad estricta)
        ("merkle_root", ctypes.c_uint8 * 32),# 32 bytes (Estado global)
        ("halt_flag", ctypes.c_uint8),       # 1 byte  (Circuit Breaker)
        ("reserved", ctypes.c_uint8 * 7),    # 7 bytes (Padding a 64 bytes)
    ]

# =====================================================================
# 2. SIMULADOR DEL NÚCLEO RUST (FFI Mock)
# =====================================================================
class RustKernelMock:
    def __init__(self) -> None:
        self.manifest = SharedManifest()
        self.manifest.seqlock = 0
        self.manifest.lamport_t = 0
        self.manifest.seq = 0
        self.manifest.halt_flag = 0
        self._leaves: list[str] = []

    def _seqlock_write_begin(self) -> None:
        self.manifest.seqlock += 1

    def _seqlock_write_end(self) -> None:
        self.manifest.seqlock += 1

    def compute_cortex_hash(self, seq: int, event_id: str, prev_hash: str) -> str:
        h = hashlib.sha3_256(f"{seq}|{event_id}|{prev_hash}".encode('utf-8')).hexdigest()
        return h

    def build_merkle_tree(self, entry_hashes: list[str]) -> str:
        if not entry_hashes:
            return "0" * 64
        total_leaves = len(entry_hashes)
        layer = [bytes.fromhex(h) for h in entry_hashes]
        level = 0
        while len(layer) > 1:
            if len(layer) % 2 != 0:
                layer.append(layer[-1])
            next_layer = []
            for i in range(0, len(layer), 2):
                combined = layer[i] + layer[i+1]
                domain_tag = b'\x00' if level == 0 else b'\x01'
                next_layer.append(hashlib.sha3_256(domain_tag + combined).digest())
            layer = next_layer
            level += 1
        root_with_cardinal = b'\x02' + layer[0] + total_leaves.to_bytes(8, 'little')
        return hashlib.sha3_256(root_with_cardinal).hexdigest()

    def append_causal_event(self, seq: int, lamport_t: int, entry_hash: str) -> dict[str, str]:
        print(f"  [Rust Kernel/Ring-0] Evaluando transición: seq={seq}, lamport={lamport_t}")
        
        if self.manifest.halt_flag == 1:
            return {"status": "REJECTED", "reason": "SYSTEM_HALTED"}
            
        if seq != self.manifest.seq + 1:
            print("  [Rust Kernel/Ring-0] 🛑 VIOLACIÓN CAUSAL: Secuencia no contigua detectada.")
            self._trigger_fail_stop(f"Seq discontinuity: expected {self.manifest.seq + 1}, got {seq}")
            return {"status": "HALT", "receipt": "COSE_Sign1_RECEIPT"}
            
        if lamport_t <= self.manifest.lamport_t:
            print("  [Rust Kernel/Ring-0] 🛑 VIOLACIÓN CAUSAL: Retroceso en tiempo de Lamport.")
            self._trigger_fail_stop(f"Lamport violation: {lamport_t} <= {self.manifest.lamport_t}")
            return {"status": "HALT", "receipt": "COSE_Sign1_RECEIPT"}

        self._seqlock_write_begin()
        self.manifest.seq = seq
        self.manifest.lamport_t = lamport_t
        self._leaves.append(entry_hash)
        new_root = self.build_merkle_tree(self._leaves)
        root_bytes = bytes.fromhex(new_root)
        ctypes.memmove(self.manifest.merkle_root, root_bytes, 32)
        self._seqlock_write_end()
        
        print(f"  [Rust Kernel/Ring-0] Transición exitosa. Raíz Merkle: {new_root[:16]}...")
        return {"status": "OK", "merkle_root": new_root}

    def _trigger_fail_stop(self, reason: str) -> None:
        self._seqlock_write_begin()
        self.manifest.halt_flag = 1
        self._seqlock_write_end()
        print(f"  [Rust Kernel/Ring-0] ⚡ CIRCUIT BREAKER ACTIVADO. Razón: {reason}")
        print(f"  [Rust Kernel/Ring-0] Emisión de recibo forense COSE_Sign1...")

# =====================================================================
# 3. DEMOSTRACIÓN (Python Front-End)
# =====================================================================

def run_poc() -> None:
    print("=" * 80)
    print("🚀 Iniciando PoC: BABYLON-60 Rust FFI Topological Leap")
    print("=" * 80)
    
    rust_core = RustKernelMock()
    
    print("\n--- TEST 1: Transiciones Causales Legítimas (Evaluadas en C-ABI) ---")
    prev_hash = "0" * 64
    for i in range(1, 4):
        event_id = str(uuid.uuid4())
        h = rust_core.compute_cortex_hash(seq=i, event_id=event_id, prev_hash=prev_hash)
        res = rust_core.append_causal_event(seq=i, lamport_t=i*10, entry_hash=h)
        assert res["status"] == "OK"
        prev_hash = h
        
    print("\n--- TEST 2: Intento de Poda Discreta (Inyección Python Fraudulenta) ---")
    # El transductor Python intenta enviar el seq=5 saltándose el 4
    event_id = str(uuid.uuid4())
    h = rust_core.compute_cortex_hash(seq=5, event_id=event_id, prev_hash=prev_hash)
    res = rust_core.append_causal_event(seq=5, lamport_t=40, entry_hash=h)
    
    print(f"\nResultado devuelto a Python FFI: {res}")
    print(f"Estado del Halt Flag en Memoria C: {rust_core.manifest.halt_flag}")
    
    print("\n--- TEST 3: Intento de Recuperación Tras Halt (Inmunidad) ---")
    # Python intenta corregir y enviar el seq=4, pero el núcleo ya está sellado.
    h = rust_core.compute_cortex_hash(seq=4, event_id=str(uuid.uuid4()), prev_hash=prev_hash)
    res = rust_core.append_causal_event(seq=4, lamport_t=50, entry_hash=h)
    print(f"Resultado: {res}")

if __name__ == "__main__":
    run_poc()
