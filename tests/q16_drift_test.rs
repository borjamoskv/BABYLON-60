// tests/q16_drift_test.rs — Certificado de deriva entrópica Q16.16
// INVARIANTE: max_drift_zj <= DRIFT_BUDGET_ZJ antes de aprobar migración

pub type Q16_16 = i32;

const DRIFT_BUDGET_ZJ: u64 = 50; // Máximo 50 zJ de deriva tolerable por operación

/// Conversión con redondeo al entero más cercano (no truncamiento)
/// Truncamiento introduce sesgo sistemático negativo en energía → viola Landauer
pub const fn to_q16_16_from_x1000(val_x1000: u32) -> Q16_16 {
    // val_x1000 representa val * 1000
    // Q16.16 = val * 65536 = val_x1000 * 65536 / 1000
    // Redondeo: añadir 500 antes de dividir
    ((val_x1000 as u64 * 65536 + 500) / 1000) as Q16_16
}

pub fn from_q16_16(val_q16: Q16_16) -> f64 {
    val_q16 as f64 / 65536.0
}

pub fn landauer_zj_f64(temp_k: f64, bits: f64, kl: f64) -> f64 {
    const K_BOLTZMANN: f64 = 1.380649e-23;
    const LN_2: f64 = core::f64::consts::LN_2;
    let min_energy_joules = K_BOLTZMANN * temp_k * LN_2 * (bits + kl / LN_2);
    min_energy_joules * 1e21 // to zeptojoules
}

pub fn landauer_zj_q16(temp_k: u32, bits_q16: Q16_16, kl_q16: Q16_16) -> u64 {
    // inv_ln2 en Q16.16: (1 / 0.69314718) * 65536 = 94548
    let inv_ln2_q16: i64 = 94548;
    let kl_over_ln2_q16 = ((kl_q16 as i64 * inv_ln2_q16 + 32768) >> 16) as Q16_16;
    let total_bits_q16 = bits_q16 + kl_over_ln2_q16;
    
    // k_B * ln(2) * 1e21 = 0.009569926 zJ / K
    // En Q32.32 para no perder precisión en la constante termodinámica:
    // 0.009569926 * 2^32 = 41102555
    let k_b_ln2_zj_q32: u64 = 41102555;
    let zj_per_bit_q32 = temp_k as u64 * k_b_ln2_zj_q32;
    
    let energy_zj_q48 = total_bits_q16 as u64 * zj_per_bit_q32;
    (energy_zj_q48 + (1u64 << 47)) >> 48
}

#[test]
fn quantify_q16_thermodynamic_drift() {
    println!("Temp(K) | Bits_f64 | Bits_Q16 | ΔBits  | E_f64(zJ) | E_Q16(zJ) | ΔE(zJ)");
    println!("--------|----------|----------|--------|-----------|-----------|-------");
    
    let mut max_drift: u64 = 0;
    
    for temp_k in (300..=400).step_by(10) {
        for effective_bits_x1000 in [47300u32, 100000, 200000] { // 47.3, 100.0, 200.0 bits
            let kl_x1000: u32 = 892; // 0.892 nats × 1000
            
            // Cálculo f64 de referencia
            let bits_f64 = effective_bits_x1000 as f64 / 1000.0;
            let kl_f64 = kl_x1000 as f64 / 1000.0;
            let e_f64_zj = landauer_zj_f64(temp_k as f64, bits_f64, kl_f64);
            
            // Cálculo Q16.16
            let bits_q16 = to_q16_16_from_x1000(effective_bits_x1000);
            let kl_q16 = to_q16_16_from_x1000(kl_x1000);
            let e_q16_zj = landauer_zj_q16(temp_k, bits_q16, kl_q16);
            
            let drift = if e_f64_zj > e_q16_zj as f64 { 
                (e_f64_zj - e_q16_zj as f64).abs() as u64
            } else { 
                (e_q16_zj as f64 - e_f64_zj).abs() as u64
            };
            
            max_drift = max_drift.max(drift);
            
            println!("{:7} | {:8.3} | {:8.3} | {:6.4} | {:9.1} | {:9} | {:5}",
                temp_k, bits_f64, from_q16_16(bits_q16),
                (bits_f64 - from_q16_16(bits_q16)).abs(),
                e_f64_zj, e_q16_zj, drift);
        }
    }
    
    assert!(max_drift <= DRIFT_BUDGET_ZJ,
        "DERIVA EXCESIVA: {} zJ > budget {} zJ. Revisar conversión Q16.16.",
        max_drift, DRIFT_BUDGET_ZJ);
    
    println!("\n✅ Deriva máxima certificada: {} zJ (budget: {} zJ)", max_drift, DRIFT_BUDGET_ZJ);
}
