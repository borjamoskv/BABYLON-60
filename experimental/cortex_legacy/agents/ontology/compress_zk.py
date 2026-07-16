import os

ONTOLOGY_DIR = "$CORTEX_ROOT/borjamoskv/Teorema-Robinson-Moskv/cortex/agents/ontology"
FILES = {
    "PRIM": "01_PRIMITIVAS_DE_COLAPSO.md",
    "INV": "02_INVARIANTES_TERMODINAMICAS.md",
    "ANTI": "03_ANTIPATRONES_ESTOCASTICOS.md",
    "RED": "04_REDUNDANCIAS_ACTIVAS.md",
}

COMPRESSED_BLOCKS = {
    "PRIM": "| PRIM-ZK-OMEGA | Tensor ZK (100 Primitivas) | $\\mathcal{D} \\otimes \\mathcal{V} \\to \\mathcal{R}$ donde $\\mathcal{D}=\\{R1CS...Noir\\}$ y $\\mathcal{V}=\\{Witness...Nullifier\\}$ | Asignación ZK Criptográfica. | Colapso algebraico determinista. | Inmediata | C5 | Compresión O(1) de 100 primitivas. |",
    "INV": "| INV-ZK-OMEGA | Tensor ZK (100 Invariantes) | Soundness & Completeness $\\forall \\, d \\in \\mathcal{D}, v \\in \\mathcal{V}$ | Verificador polinómico O(1). | Cero entropía extraída. | Estática | C5 | Prueba Criptográfica Matemática. |",
    "ANTI": "| ANTI-ZK-OMEGA | Tensor ZK (100 Antipatrones) | Under-constrained $\\mathcal{V}$ en dominio $\\mathcal{D}$ | Field Overflow, Missing $===$. | Fuga de Witness. | Progresiva | C4 | Range Check y Aserción Estricta. |",
    "RED": "| RED-ZK-OMEGA | Tensor ZK (100 Redundancias) | Tolerancia Bizantina (MPC / BFT) sobre el tensor $\\mathcal{D} \\otimes \\mathcal{V}$ | Ceremonia Trusted Setup N-nodos. | Descentralización Prover. | Retrasada | C5 | Verificación cruzada y Apoptosis tóxica. |",
}


def inject_compression():
    for key, filename in FILES.items():
        path = os.path.join(ONTOLOGY_DIR, filename)
        if os.path.exists(path):
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n" + COMPRESSED_BLOCKS[key] + "\n")
            print(f"Compressed Matrix {key} injected into {filename}")


if __name__ == "__main__":
    inject_compression()
