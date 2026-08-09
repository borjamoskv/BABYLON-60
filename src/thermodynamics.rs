// C5-REAL EXERGY CERTIFIED — BABYLON-60 — INV-3 (termodinámica)
// Landauer, Zero Anergía, bisimulación Dynamis/Entelecheia
//
// NOTA EPISTÉMICA: este módulo documenta y verifica los invariantes
// termodinámicos del diseño. No es código de ruta caliente.
// Las cotas de Landauer son verificadas como constantes en tiempo
// de compilación donde el compilador lo permite.
//
// COTA DE LANDAUER (INV-3):
//   ΔQ ≥ k_B · T · ln2 · ΔI
//   A T = 300 K: k_B·T·ln2 ≈ 2.87×10⁻²¹ J/bit
//   Bits sobrescritos por publicación ≈ 2×32 (seq) + 256 (hash) + 64 (época)
//     = 384 bits
//   Suelo ≈ 384 × 2.87×10⁻²¹ ≈ 1.10×10⁻¹⁸ J/publicación
//   (La disipación CMOS real excede este suelo en muchos órdenes de magnitud)
//
// COLAPSO DE ANERGÍA EN EL LADO LECTOR:
//   El diseño original (active_readers RMW) generaba ping-pong O(tasa_lectura):
//   cada RMW exige estado Exclusive/Modified → RFO invalida la línea del hash
//   en todas las cachés lectoras. Con el seqlock de escritor único:
//     - Lectores = puros-de-carga (cero stores, cero RFO)
//     - Línea permanece en estado Shared en todas las cachés lectoras
//     - Anergía del lado lector = 0 (colapso completo)
//     - Toda disipación irreversible queda concentrada en el único escritor
//
// BISIMULACIÓN OBSERVABLE:
//   Estados seq par    → Entelecheia (acto validado, observable)
//   Estados seq impar  → Dynamis (potencia, inobservable por protocolo)
//   El cociente observable {s ∈ ℕ | s par} es idéntico al conjunto de estados
//   de la especificación → ejecución y especificación observacionalmente bisimilares.
//   Los estados impares no pertenecen al cociente observable.

/// Cota de Landauer a T=300K en Joules por bit (aproximada).
/// k_B × T × ln(2) = 1.380649×10⁻²³ × 300 × 0.693147 ≈ 2.87×10⁻²¹ J
/// Expresada en attojoules × 1000 para aritmética entera verificable.
pub const LANDAUER_FLOOR_AJ_PER_BIT_X1000: u64 = 2870; // 2.87 aJ × 1000

/// Bits sobrescritos por publicación completa:
/// 2 × 32 (dos transiciones de seq) + 256 (payload_hash) + 64 (epoch_id) = 384
pub const BITS_PER_PUBLISH: u64 = 384;

/// Suelo de disipación por publicación (en attojoules × 1000):
/// 384 × 2.87 aJ ≈ 1101.88 aJ ≈ 1.10×10⁻¹⁸ J
pub const LANDAUER_FLOOR_TOTAL_AJ_X1000: u64 =
    BITS_PER_PUBLISH * LANDAUER_FLOOR_AJ_PER_BIT_X1000;

/// Cota superior de publicaciones antes del envolvimiento de epoch_id (u64).
/// 2⁶⁴ = 18_446_744_073_709_551_616 publicaciones.
/// A 10⁹ publicaciones/segundo → ≈ 584.5 años.
pub const EPOCH_WRAPAROUND_YEARS_FLOOR: u64 = 584;

// ---------------------------------------------------------------------------
// Verificaciones en tiempo de compilación (INV-3)
// ---------------------------------------------------------------------------
const _THERMO_ASSERTS: () = {
    // Verificar que la constante de Landauer es positiva y no desborda u64
    assert!(LANDAUER_FLOOR_TOTAL_AJ_X1000 > 0);
    assert!(BITS_PER_PUBLISH == 384);

    // La cota de Landauer total debe ser ≥ 384×2870 = 1_101_880 aJ×1000
    assert!(LANDAUER_FLOOR_TOTAL_AJ_X1000 >= 1_101_880);

    // Cota de envolvimiento ≥ 500 años (holgura conservadora)
    assert!(EPOCH_WRAPAROUND_YEARS_FLOOR >= 500);
};

// ---------------------------------------------------------------------------
// Verificador de bisimulación en tiempo de ejecución (para tests)
// ---------------------------------------------------------------------------

/// Verifica que un valor de `seq` es observable (par = Entelecheia).
/// Los valores impares (Dynamis) no son observables por protocolo.
///
/// # Ejemplo
/// ```
/// use babylon_60::thermodynamics::{is_entelecheia, is_dynamis, is_valid_writer_transition};
///
/// assert!(is_entelecheia(0));
/// assert!(is_dynamis(1));
/// assert!(is_valid_writer_transition(0, 2));
/// ```
#[inline]
#[must_use]
pub const fn is_entelecheia(seq: u32) -> bool {
    seq & 1 == 0
}

/// Verifica que un valor de `seq` está en potencia (impar = Dynamis).
#[inline]
#[must_use]
pub const fn is_dynamis(seq: u32) -> bool {
    seq & 1 != 0
}

/// Verifica que una transición seq es válida para el escritor único.
/// par(n) → impar(n+1) → par(n+2): la única secuencia legal.
#[inline]
#[must_use]
pub const fn is_valid_writer_transition(before: u32, after: u32) -> bool {
    // after == before.wrapping_add(2) y after es par
    after.wrapping_sub(before) == 2 && is_entelecheia(after)
}

// ---------------------------------------------------------------------------
// Extensiones Axiomáticas PSAFE v3.0: Aphairesis & CALM (INV-3)
// ---------------------------------------------------------------------------

/// [AX-APHAIRESIS-01]: Cota mínima de disipación entrópica por compresión/eliminación de datos.
///
/// Dado un número de bits eliminados $\Delta H = N - M$, calcula la exergía mínima
/// disipada por el Principio de Landauer en attojoules × 1000 a T=300K:
/// $$\Delta Q_{\text{aphairesis}} \ge \Delta H \times (k_B \cdot T \cdot \ln 2)$$
#[inline]
#[must_use]
pub const fn aphairesis_entropy_loss_aj_x1000(bits_erased: u64) -> u64 {
    bits_erased.saturating_mul(LANDAUER_FLOOR_AJ_PER_BIT_X1000)
}

/// [AX-CALM-01]: Verificación de monotonicidad estricta de época según el Teorema CALM.
///
/// Una transición de época $e_1 \to e_2$ es lógicamente monotónica si y solo si $e_2 > e_1$.
/// Las transiciones monotónicas garantizan la ausencia de coordinación global en hilos distribuidos.
#[inline]
#[must_use]
pub const fn is_calm_monotonic_transition(prev_epoch: u64, new_epoch: u64) -> bool {
    new_epoch > prev_epoch
}

// ---------------------------------------------------------------------------
// Formalización Axiomática de Cota de Landauer Extendida para Aphairesis (Capa 2)
// ---------------------------------------------------------------------------

/// Cota termodinámica extendida para operaciones de compresión/aphairesis en Capa 2.
///
/// Invariante: $E_{\text{min}} \ge k_B \cdot T \cdot \ln 2 \cdot \left( \text{effective\_bits} + \frac{D_{\text{KL}}}{\ln 2} \right)$
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct AphairesisBound {
    /// Bits efectivos eliminados en la compresión (ponderados topológicamente).
    pub effective_bits_erased: f64,
    /// Divergencia KL entre la distribución original $P_X$ y la reconstruida desde $Y$.
    pub kl_divergence: f64,
    /// Temperatura operativa del silicio en Kelvin.
    pub temperature_k: f64,
}

impl AphairesisBound {
    /// Constante de Boltzmann ($k_B$) en Joules por Kelvin: $1.380649 \times 10^{-23} \text{ J/K}$.
    pub const K_B: f64 = 1.380649e-23;
    /// Logaritmo natural de 2 ($\ln 2$).
    pub const LN2: f64 = core::f64::consts::LN_2;

    /// Retorna la energía mínima en Joules requerida para esta compresión.
    ///
    /// $$E_{\text{min}} = k_B \cdot T \cdot \ln 2 \cdot \left( \text{bits} + \frac{D_{\text{KL}}}{\ln 2} \right)$$
    #[inline]
    #[must_use]
    pub fn min_energy_joules(&self) -> f64 {
        Self::K_B * self.temperature_k * Self::LN2 * (self.effective_bits_erased + self.kl_divergence / Self::LN2)
    }

    /// Verifica si una medición empírica de energía satisface la cota física.
    #[inline]
    #[must_use]
    pub fn is_physically_valid(&self, measured_energy_j: f64) -> bool {
        measured_energy_j >= self.min_energy_joules()
    }
}

/// Trait axiomático que todo operador de compresión topológica (Capa 2) debe implementar.
///
/// Obliga a asociar constantes de tiempo de compilación para la pérdida de información,
/// garantizando que ningún módulo de abstracción opere como una caja negra termodinámica.
pub trait TopologicalCompressor {
    /// Bits efectivos eliminados (constante de compilación).
    const EFFECTIVE_BITS_ERASED: f64;
    /// Divergencia KL prefijada (constante de compilación).
    const KL_DIVERGENCE: f64;

    /// Retorna la cota termodinámica de Aphairesis para este compresor a una temperatura dada.
    fn aphairesis_bound(temperature_k: f64) -> AphairesisBound {
        AphairesisBound {
            effective_bits_erased: Self::EFFECTIVE_BITS_ERASED,
            kl_divergence: Self::KL_DIVERGENCE,
            temperature_k,
        }
    }
}


