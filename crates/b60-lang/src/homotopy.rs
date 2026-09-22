// ============================================================================
// B60 HOMOTOPY TYPE VERIFIER (HoTT ON S1/Z60: FUNDAMENTAL GROUP π1 & CANONICAL REDUCTION)
// ============================================================================

#[derive(Debug, PartialEq, Eq)]
pub enum HomotopyResult {
    /// Geodésica contráctil o lazo que cierra ciclo en Z60 con número de enrollamiento entero
    ContractibleGeodesic {
        topological_winding: i32,
        entropy_bound_fj: u64,
    },
    /// Trayectoria no contráctil / ciclo abierto que no cierra fase en Z60
    NonContractibleInfiniteLoopDetected {
        topological_winding: i32,
    },
}

pub struct HomotopyVerifier;

impl HomotopyVerifier {
    /// Verifica la homotopía de una trayectoria discreta sobre el círculo S1 discretizado en Z60.
    /// Realiza:
    /// 1. Reducción libre de homotopía 1-dimensional (cancelación de pares de retroceso e · e⁻¹ = id).
    /// 2. Verificación de clausura de lazo (condición de frontera modulo 60).
    /// 3. Cálculo del grado topológico de Brouwer / número de enrollamiento (winding number) w ∈ π1(S1).
    pub fn verify_path(steps_in_z60: &[i32]) -> HomotopyResult {
        if steps_in_z60.is_empty() {
            return HomotopyResult::ContractibleGeodesic {
                topological_winding: 0,
                entropy_bound_fj: 0,
            };
        }

        // 1. Reducción de palabras en el grupo libre (reducción homotópica de pares inversos adyacentes)
        let mut reduced_path: Vec<i32> = Vec::with_capacity(steps_in_z60.len());
        let mut total_winding_phase: i32 = 0;

        for &step in steps_in_z60 {
            total_winding_phase += step;

            if let Some(&last) = reduced_path.last() {
                if last == -step {
                    reduced_path.pop(); // Reducción de homotopía libre (retracción al punto base)
                    continue;
                }
            }
            reduced_path.push(step);
        }

        // 2. Condición de lazo cerrado en Z60: la suma de fases debe cerrar exactamente en 0 mod 60
        if total_winding_phase % 60 == 0 {
            let winding = total_winding_phase / 60;
            HomotopyResult::ContractibleGeodesic {
                topological_winding: winding,
                entropy_bound_fj: (reduced_path.len() as u64) * 60, // Cota de disipación proporcional a la longitud irreductible
            }
        } else {
            HomotopyResult::NonContractibleInfiniteLoopDetected {
                topological_winding: total_winding_phase,
            }
        }
    }

    /// Comprueba si una trayectoria reducida es estrictamente contráctil al punto base (homotópica a refl, w = 0)
    pub fn is_strictly_null_homotopic(steps_in_z60: &[i32]) -> bool {
        match Self::verify_path(steps_in_z60) {
            HomotopyResult::ContractibleGeodesic { topological_winding, entropy_bound_fj } => {
                topological_winding == 0 && entropy_bound_fj == 0
            }
            _ => false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_homotopy_cancellation_refl() {
        // Trayectoria que avanza y retrocede: 10, -10, 25, -25 -> se cancela completamente a refl (w = 0)
        let steps = [10, -10, 25, -25];
        assert!(HomotopyVerifier::is_strictly_null_homotopic(&steps));
    }

    #[test]
    fn test_homotopy_closed_loop_winding_1() {
        // Lazo canónico que recorre Z60 una vez completa: 15 + 20 + 25 = 60 (w = 1)
        let steps = [15, 20, 25];
        let res = HomotopyVerifier::verify_path(&steps);
        assert_eq!(res, HomotopyResult::ContractibleGeodesic {
            topological_winding: 1,
            entropy_bound_fj: 180,
        });
    }

    #[test]
    fn test_homotopy_open_loop_rejected() {
        // Trayectoria que no cierra en Z60: 10 + 20 + 15 = 45 != 0 mod 60
        let steps = [10, 20, 15];
        let res = HomotopyVerifier::verify_path(&steps);
        assert_eq!(res, HomotopyResult::NonContractibleInfiniteLoopDetected {
            topological_winding: 45,
        });
    }
}
