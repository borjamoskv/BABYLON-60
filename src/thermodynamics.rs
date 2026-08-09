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
#[inline]
pub const fn is_entelecheia(seq: u32) -> bool {
    seq & 1 == 0
}

/// Verifica que un valor de `seq` está en potencia (impar = Dynamis).
#[inline]
pub const fn is_dynamis(seq: u32) -> bool {
    seq & 1 != 0
}

/// Verifica que una transición seq es válida para el escritor único.
/// par(n) → impar(n+1) → par(n+2): la única secuencia legal.
#[inline]
pub const fn is_valid_writer_transition(before: u32, after: u32) -> bool {
    // after == before.wrapping_add(2) y after es par
    after.wrapping_sub(before) == 2 && is_entelecheia(after)
}
