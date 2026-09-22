// [AX-28] KERNEL: Zero-Float Bitmask Semantic Entropy Engine (Ring-0)
// Estructura C-ABI y evaluación determinista de clases de equivalencia NLI en espacio cociente S / ~_sem.
// Conforme a INV_C5 (Falsación Empírica) y estricto #![no_std] sin aritmética de punto flotante.
// Soporte para N <= 8 (u64) y extensión en cascada ADR-007 para N <= 16 ([u64; 4]).

/// Código de error de apoptosis por confabulación estocástica (0xDEAD_6060).
pub const ERR_CONFABULATION: u32 = 0xDEAD_6060;

/// Código de error de apoptosis por creencia errónea sistemática interceptada por SMT (0xDEAD_6061).
pub const ERR_INCORRECT_BELIEF: u32 = 0xDEAD_6061;

/// Código de estado verificado exitosamente (0x0000_0001).
pub const STATUS_VERIFIED: u32 = 0x0000_0001;

/// Umbral de entropía semántica en punto fijo Q16 (0.85 bits = 0.85 * 65536 = 55706)
pub const TAU_SEM_Q16: u32 = 55706;

/// Tabla de búsqueda entera exacta para - (c/n) * log2(c/n) * 65536 para n <= 16.
/// Garantiza cero disipación de Landauer y cero operaciones de punto flotante en Ring-0.
pub const ENTROPY_LUT_Q16: [[u32; 17]; 17] = [
    /* n= 0 */ [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n= 1 */ [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n= 2 */ [0, 32768, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n= 3 */ [0, 34624, 25557, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n= 4 */ [0, 32768, 32768, 20400, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n= 5 */ [0, 30434, 34654, 28979, 16878, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n= 6 */ [0, 28235, 34624, 32768, 25557, 14365, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n= 7 */ [0, 26283, 33842, 34333, 30235, 22724, 12493, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n= 8 */ [0, 24576, 32768, 34776, 32768, 27774, 20400, 11047, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n= 9 */ [0, 23083, 31602, 34624, 34077, 30875, 25557, 18481, 9899, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n=10 */ [0, 21771, 30434, 34150, 34654, 32768, 28979, 23606, 16878, 8966, 0, 0, 0, 0, 0, 0, 0],
    /* n=11 */ [0, 20611, 29306, 33503, 34780, 33885, 31260, 27195, 21898, 15523, 8192, 0, 0, 0, 0, 0, 0],
    /* n=12 */ [0, 19579, 28235, 32768, 34624, 34489, 32768, 29727, 25557, 20400, 14365, 7541, 0, 0, 0, 0, 0],
    /* n=13 */ [0, 18655, 27227, 31994, 34289, 34747, 33740, 31516, 28249, 24070, 19082, 13365, 6986, 0, 0, 0, 0],
    /* n=14 */ [0, 17823, 26283, 31210, 33842, 34767, 34333, 32768, 30235, 26855, 22724, 17915, 12493, 6506, 0, 0, 0],
    /* n=15 */ [0, 17069, 25401, 30434, 33325, 34624, 34654, 33628, 31698, 28979, 25557, 21505, 16878, 11726, 6088, 0, 0],
    /* n=16 */ [0, 16384, 24576, 29676, 32768, 34367, 34776, 34196, 32768, 30600, 27774, 24356, 20400, 15951, 11047, 5721, 0],
];

/// Veredicto formal emitido por el evaluador de Ring-0
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SemanticEntropyVerdict {
    /// Conocimiento genuino: Baja entropía semántica y validado formalmente (SAT).
    VerifiedGenuine {
        /// Entropía semántica calculada en escala de punto fijo Q16.
        h_sem_q16: u32,
        /// Número de clases de equivalencia de significado resultantes.
        num_classes: u8,
    },
    /// Polisemia legítima: Múltiples interpretaciones semánticas consistentes con el territorio.
    VerifiedPolysemy {
        /// Entropía semántica calculada en escala de punto fijo Q16.
        h_sem_q16: u32,
        /// Número de clases de equivalencia de significado resultantes.
        num_classes: u8,
    },
    /// Confabulación estocástica: Alta entropía semántica e inconsistente con el oráculo formal.
    ApoptosisConfabulation {
        /// Entropía semántica calculada en escala de punto fijo Q16.
        h_sem_q16: u32,
        /// Código mnemónico de apoptosis (0xDEAD_6060).
        code: u32,
    },
    /// Creencia errónea sistemática: Baja dispersión aparente pero inconsistente (UNSAT).
    ApoptosisIncorrectBelief {
        /// Entropía semántica calculada en escala de punto fijo Q16.
        h_sem_q16: u32,
        /// Código mnemónico de apoptosis (0xDEAD_6061).
        code: u32,
    },
}

/// Motor de Clustering y Cálculo de Entropía Semántica Zero-Float
pub struct BitmaskSemanticKernel;

impl BitmaskSemanticKernel {
    /// Convierte una matriz de 64 bits (N <= 8) a formato en cascada [u64; 4] (N <= 16).
    #[inline(always)]
    pub fn u64_to_cascaded_matrix(adj: u64, n: usize) -> [u64; 4] {
        let mut cascaded = [0u64; 4];
        let bound = n.min(8);
        for i in 0..bound {
            let row_8 = ((adj >> (i * 8)) & 0xFF) as u16;
            let u64_idx = i / 4;
            let shift = (i % 4) * 16;
            cascaded[u64_idx] |= (row_8 as u64) << shift;
        }
        cascaded
    }

    /// Particiona hasta N=8 realizaciones estocásticas codificadas en una matriz de adyacencia de 64 bits.
    /// Retorna: (entropía semántica en Q16, número de clases K)
    #[inline(always)]
    pub fn compute_quotient_entropy(adj_matrix: u64, n: usize) -> (u32, u8) {
        if n == 0 || n > 8 {
            return (0, 0);
        }

        let mut visited: u8 = 0;
        let mut class_sizes = [0u8; 8];
        let mut num_classes = 0usize;

        for i in 0..n {
            let mask_i = 1u8 << i;
            if (visited & mask_i) != 0 {
                continue;
            }

            // Fila i de la matriz de adyacencia NLI
            let row_i = ((adj_matrix >> (i * 8)) & 0xFF) as u8;
            let class_members = row_i & ((1u8 << n) - 1);
            let size = class_members.count_ones() as u8;

            visited |= class_members;
            class_sizes[num_classes] = size;
            num_classes += 1;
        }

        // Agregación de entropía sin división ni punto flotante vía LUT entera
        let mut total_h_q16: u32 = 0;
        for k in 0..num_classes {
            let c = class_sizes[k] as usize;
            if c > 0 && c <= n {
                total_h_q16 = total_h_q16.saturating_add(ENTROPY_LUT_Q16[n][c]);
            }
        }

        (total_h_q16, num_classes as u8)
    }

    /// Particiona hasta N=16 realizaciones estocásticas codificadas en una matriz de adyacencia en cascada [u64; 4] (256 bits).
    /// Cada u64 aloja 4 filas de 16 bits (4 * 16 = 64 bits).
    /// Retorna: (entropía semántica en Q16, número de clases K)
    #[inline(always)]
    pub fn compute_quotient_entropy_16(adj_matrix: &[u64; 4], n: usize) -> (u32, u8) {
        if n == 0 || n > 16 {
            return (0, 0);
        }

        let col_mask: u16 = if n == 16 {
            0xFFFF
        } else {
            (1u16 << n) - 1
        };

        let mut visited: u16 = 0;
        let mut class_sizes = [0u8; 16];
        let mut num_classes = 0usize;

        for i in 0..n {
            let mask_i = 1u16 << i;
            if (visited & mask_i) != 0 {
                continue;
            }

            // Extraer fila i desde la cascada [u64; 4]
            let u64_idx = i / 4;
            let shift = (i % 4) * 16;
            let row_i = ((adj_matrix[u64_idx] >> shift) & 0xFFFF) as u16;
            let class_members = row_i & col_mask;
            let size = class_members.count_ones() as u8;

            visited |= class_members;
            class_sizes[num_classes] = size;
            num_classes += 1;
        }

        // Agregación de entropía sin división ni punto flotante vía LUT entera
        let mut total_h_q16: u32 = 0;
        for k in 0..num_classes {
            let c = class_sizes[k] as usize;
            if c > 0 && c <= n {
                total_h_q16 = total_h_q16.saturating_add(ENTROPY_LUT_Q16[n][c]);
            }
        }

        (total_h_q16, num_classes as u8)
    }

    /// Evalúa la inferencia del agente sometiéndola al doble cortafuegos de Ring-0 (N <= 8).
    #[inline(always)]
    pub fn evaluate(
        adj_matrix: u64,
        n: usize,
        is_territory_sat: bool,
    ) -> SemanticEntropyVerdict {
        let (h_sem_q16, k) = Self::compute_quotient_entropy(adj_matrix, n);
        Self::verdict_from_entropy(h_sem_q16, k, is_territory_sat)
    }

    /// Evalúa la inferencia del agente con cascada ADR-007 para enjambres ampliados (N <= 16).
    #[inline(always)]
    pub fn evaluate_16(
        adj_matrix: &[u64; 4],
        n: usize,
        is_territory_sat: bool,
    ) -> SemanticEntropyVerdict {
        let (h_sem_q16, k) = Self::compute_quotient_entropy_16(adj_matrix, n);
        Self::verdict_from_entropy(h_sem_q16, k, is_territory_sat)
    }

    #[inline(always)]
    fn verdict_from_entropy(
        h_sem_q16: u32,
        k: u8,
        is_territory_sat: bool,
    ) -> SemanticEntropyVerdict {
        if h_sem_q16 > TAU_SEM_Q16 {
            if is_territory_sat {
                // Polisemia Legítima: Múltiples ramas, pero consistentes con el territorio
                SemanticEntropyVerdict::VerifiedPolysemy {
                    h_sem_q16,
                    num_classes: k,
                }
            } else {
                // Confabulación Estocástica pura (Farquhar et al., Nature 2024)
                SemanticEntropyVerdict::ApoptosisConfabulation {
                    h_sem_q16,
                    code: ERR_CONFABULATION,
                }
            }
        } else {
            if is_territory_sat {
                // Conocimiento Genuino: Baja dispersión y SAT
                SemanticEntropyVerdict::VerifiedGenuine {
                    h_sem_q16,
                    num_classes: k,
                }
            } else {
                // Creencia Errónea Sistemática (Falso conocimiento memorizado con H_sem ~ 0)
                SemanticEntropyVerdict::ApoptosisIncorrectBelief {
                    h_sem_q16,
                    code: ERR_INCORRECT_BELIEF,
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_genuine_knowledge_quadrant1() {
        // Clique completo 5x5 (todas las muestras equivalentes)
        let mut adj = 0u64;
        for i in 0..5 {
            adj |= (0b0001_1111u64) << (i * 8);
        }
        let verdict = BitmaskSemanticKernel::evaluate(adj, 5, true);
        assert_eq!(
            verdict,
            SemanticEntropyVerdict::VerifiedGenuine {
                h_sem_q16: 0,
                num_classes: 1
            }
        );
    }

    #[test]
    fn test_confabulation_quadrant2() {
        // Identidad 5x5 (todas las muestras contradictorias, K=5)
        let mut adj = 0u64;
        for i in 0..5 {
            adj |= (1u64 << i) << (i * 8);
        }
        let verdict = BitmaskSemanticKernel::evaluate(adj, 5, false);
        match verdict {
            SemanticEntropyVerdict::ApoptosisConfabulation { h_sem_q16, code } => {
                assert!(h_sem_q16 > TAU_SEM_Q16);
                assert_eq!(code, ERR_CONFABULATION);
            }
            _ => panic!("Debe detonar apoptosis por confabulación"),
        }
    }

    #[test]
    fn test_incorrect_belief_quadrant3() {
        // Clique completo 5x5 (H_sem = 0), pero UNSAT en territorio
        let mut adj = 0u64;
        for i in 0..5 {
            adj |= (0b0001_1111u64) << (i * 8);
        }
        let verdict = BitmaskSemanticKernel::evaluate(adj, 5, false);
        assert_eq!(
            verdict,
            SemanticEntropyVerdict::ApoptosisIncorrectBelief {
                h_sem_q16: 0,
                code: ERR_INCORRECT_BELIEF
            }
        );
    }

    #[test]
    fn test_polysemy_quadrant4() {
        // Partición en 2 clases (3 en C1, 2 en C2), SAT en territorio
        let mut adj = 0u64;
        for i in 0..3 {
            adj |= (0b0000_0111u64) << (i * 8);
        }
        for i in 3..5 {
            adj |= (0b0001_1000u64) << (i * 8);
        }
        let verdict = BitmaskSemanticKernel::evaluate(adj, 5, true);
        match verdict {
            SemanticEntropyVerdict::VerifiedPolysemy { h_sem_q16, num_classes } => {
                assert_eq!(num_classes, 2);
                assert_eq!(h_sem_q16, 63633); // 0.9709 bits en Q16
            }
            _ => panic!("Debe admitir polisemia legítima"),
        }
    }

    #[test]
    fn test_cascaded_n16_clique() {
        // N=16 clique completo: 16 muestras en 1 sola clase (H_sem = 0, K = 1)
        let mut cascaded = [0u64; 4];
        let full_row = 0xFFFFu64;
        for i in 0..16 {
            let u64_idx = i / 4;
            let shift = (i % 4) * 16;
            cascaded[u64_idx] |= full_row << shift;
        }

        let (h_q16, k) = BitmaskSemanticKernel::compute_quotient_entropy_16(&cascaded, 16);
        assert_eq!(k, 1);
        assert_eq!(h_q16, 0);

        let verdict = BitmaskSemanticKernel::evaluate_16(&cascaded, 16, true);
        assert_eq!(
            verdict,
            SemanticEntropyVerdict::VerifiedGenuine {
                h_sem_q16: 0,
                num_classes: 1
            }
        );
    }

    #[test]
    fn test_cascaded_n16_identity_max_entropy() {
        // N=16 matriz identidad: 16 clases de 1 muestra (H_sem = 4.0 bits = 262144 en Q16, K = 16)
        let mut cascaded = [0u64; 4];
        for i in 0..16 {
            let u64_idx = i / 4;
            let shift = (i % 4) * 16;
            cascaded[u64_idx] |= (1u64 << i) << shift;
        }

        let (h_q16, k) = BitmaskSemanticKernel::compute_quotient_entropy_16(&cascaded, 16);
        assert_eq!(k, 16);
        assert_eq!(h_q16, 262144); // Exactamente 4 * 65536 bits

        let verdict = BitmaskSemanticKernel::evaluate_16(&cascaded, 16, false);
        match verdict {
            SemanticEntropyVerdict::ApoptosisConfabulation { h_sem_q16, code } => {
                assert_eq!(h_sem_q16, 262144);
                assert_eq!(code, ERR_CONFABULATION);
            }
            _ => panic!("Debe detonar apoptosis por confabulación"),
        }
    }

    #[test]
    fn test_cascaded_n16_four_equal_classes() {
        // N=16: 4 clases de 4 muestras cada una (H_sem = 2.0 bits = 131072 en Q16, K = 4)
        let mut cascaded = [0u64; 4];
        for class_idx in 0..4 {
            let class_mask = (0xFu64) << (class_idx * 4);
            for i in 0..4 {
                let row = class_idx * 4 + i;
                let u64_idx = row / 4;
                let shift = (row % 4) * 16;
                cascaded[u64_idx] |= class_mask << shift;
            }
        }

        let (h_q16, k) = BitmaskSemanticKernel::compute_quotient_entropy_16(&cascaded, 16);
        assert_eq!(k, 4);
        assert_eq!(h_q16, 131072); // Exactamente 2 * 65536 bits
    }

    #[test]
    fn test_u64_to_cascaded_roundtrip() {
        // Comprobar que u64_to_cascaded_matrix produce exactamente la misma entropía
        let mut adj = 0u64;
        for i in 0..3 {
            adj |= (0b0000_0111u64) << (i * 8);
        }
        for i in 3..5 {
            adj |= (0b0001_1000u64) << (i * 8);
        }

        let (h1, k1) = BitmaskSemanticKernel::compute_quotient_entropy(adj, 5);
        let cascaded = BitmaskSemanticKernel::u64_to_cascaded_matrix(adj, 5);
        let (h2, k2) = BitmaskSemanticKernel::compute_quotient_entropy_16(&cascaded, 5);

        assert_eq!(k1, k2);
        assert_eq!(h1, h2);
        assert_eq!(h2, 63633);
    }
}
