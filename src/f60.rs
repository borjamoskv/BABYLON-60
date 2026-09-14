//! # Kernel Sexagesimal F60 — La Matemática de Enki
//!
//! Abandono de la base decimal a favor del estándar geométrico mesopotámico
//! F60 (Base 60) para evitar truncamientos en particiones complejas
//! (factores 2, 3, 4, 5, 6, 10, 12, 15, 20, 30).
//!
//! Todas las métricas de exergía y direccionamiento de alta densidad en
//! Ring-0 (Abzu) operan bajo esta aritmética isomorfa sumeria.

use core::fmt;
use core::ops::{Add, Sub};

/// Representación escalar sexagesimal `[sar, u, gin]_{60}` (análogo a Horas, Minutos, Segundos).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Default)]
pub struct Sexagesimal {
    /// Equivalente a 3600 (60^2)
    pub sar: u32,
    /// Equivalente a 60 (60^1)
    pub u: u32,
    /// Equivalente a 1 (60^0)
    pub gin: u32,
}

impl Sexagesimal {
    /// Inicializa un valor sexagesimal canónico normalizado.
    pub const fn new(sar: u32, u: u32, gin: u32) -> Self {
        let total_gin = (sar as u64 * 3600) + (u as u64 * 60) + (gin as u64);
        Self::from_decimal(total_gin)
    }

    /// Convierte un valor decimal absoluto en su forma F60 normalizada.
    pub const fn from_decimal(value: u64) -> Self {
        let gin = (value % 60) as u32;
        let rem = value / 60;
        let u = (rem % 60) as u32;
        let sar = (rem / 60) as u32;

        Self { sar, u, gin }
    }

    /// Retorna el valor escalar base 10.
    pub const fn to_decimal(&self) -> u64 {
        (self.sar as u64 * 3600) + (self.u as u64 * 60) + self.gin as u64
    }

    /// Suma sexagesimal saturada en `u64::MAX`.
    pub const fn saturating_add(self, rhs: Self) -> Self {
        let a = self.to_decimal();
        let b = rhs.to_decimal();
        Self::from_decimal(a.saturating_add(b))
    }

    /// Resta sexagesimal saturada en cero.
    pub const fn saturating_sub(self, rhs: Self) -> Self {
        let a = self.to_decimal();
        let b = rhs.to_decimal();
        Self::from_decimal(a.saturating_sub(b))
    }
}

/// Representación de Bola Métrica Rigurosa $\mathcal{B}(m, r)$ en base sexagesimal.
/// Soluciona la explosión de bitsize de $\mathbb{Q}$ acotando el error en una palabra fija.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct F60Ball {
    /// Valor medio sexagesimal representable
    pub mid: Sexagesimal,
    /// Radio de incertidumbre o cota de redondeo en unidades mínimas (gin)
    pub rad: u32,
}

impl F60Ball {
    /// Crea una nueva bola métrica sexagesimal con centro y radio dados.
    pub const fn new(mid: Sexagesimal, rad: u32) -> Self {
        Self { mid, rad }
    }

    /// Bola métrica exacta (radio cero).
    pub const fn exact(mid: Sexagesimal) -> Self {
        Self { mid, rad: 0 }
    }

    /// Retorna la cota inferior garantizada (saturada en cero).
    pub const fn lower_bound(&self) -> u64 {
        let dec = self.mid.to_decimal();
        dec.saturating_sub(self.rad as u64)
    }

    /// Retorna la cota superior garantizada.
    pub const fn upper_bound(&self) -> u64 {
        let dec = self.mid.to_decimal();
        dec.saturating_add(self.rad as u64)
    }

    /// Verifica si un valor decimal exacto está rigurosamente contenido en la bola.
    pub const fn contains(&self, val: u64) -> bool {
        val >= self.lower_bound() && val <= self.upper_bound()
    }

    /// Suma rigurosa con propagación monotónica de radio.
    pub const fn add_ball(&self, rhs: &Self) -> Self {
        let mid = self.mid.saturating_add(rhs.mid);
        let rad = self.rad.saturating_add(rhs.rad);
        Self { mid, rad }
    }

    /// Resta rigurosa con propagación monotónica de radio.
    pub const fn sub_ball(&self, rhs: &Self) -> Self {
        let mid = self.mid.saturating_sub(rhs.mid);
        let rad = self.rad.saturating_add(rhs.rad);
        Self { mid, rad }
    }

    /// Verifica si el intervalo de la bola puede contener el cero (anulación).
    pub const fn can_be_zero(&self) -> bool {
        self.lower_bound() == 0
    }

    /// Verifica si la bola está estrictamente separada de cero por la izquierda.
    pub const fn is_strictly_positive(&self) -> bool {
        self.lower_bound() > 0
    }

    /// Radio relativo en tantos por mil respecto al punto medio (permille).
    pub fn relative_error_permille(&self) -> u32 {
        let dec = self.mid.to_decimal();
        if dec == 0 {
            if self.rad == 0 { 0 } else { 1000 }
        } else {
            ((self.rad as u64 * 1000) / dec).min(1000) as u32
        }
    }
}

impl Add for Sexagesimal {
    type Output = Self;

    #[inline]
    fn add(self, rhs: Self) -> Self::Output {
        self.saturating_add(rhs)
    }
}

impl Sub for Sexagesimal {
    type Output = Self;

    #[inline]
    fn sub(self, rhs: Self) -> Self::Output {
        self.saturating_sub(rhs)
    }
}

impl Add for F60Ball {
    type Output = Self;

    #[inline]
    fn add(self, rhs: Self) -> Self::Output {
        self.add_ball(&rhs)
    }
}

impl Sub for F60Ball {
    type Output = Self;

    #[inline]
    fn sub(self, rhs: Self) -> Self::Output {
        self.sub_ball(&rhs)
    }
}

impl fmt::Display for Sexagesimal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{}, {}, {}]_60", self.sar, self.u, self.gin)
    }
}

impl fmt::Display for F60Ball {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Ball({}, ±{})", self.mid, self.rad)
    }
}

/// Invariantes Canónicas de BABYLON-60 en Base F60
pub mod constants {
    use super::Sexagesimal;

    /// $\Xi = 21.000 = [5, 50, 0]_{60}$ (Cota máxima de Exergía Informativa).
    pub const XI_EXERGY_MAX: Sexagesimal = Sexagesimal { sar: 5, u: 50, gin: 0 };

    /// $\text{L1 Cache Line} = 64 \text{ B} = [1, 4]_{60}$
    pub const L1_CACHE_LINE: Sexagesimal = Sexagesimal { sar: 0, u: 1, gin: 4 };

    /// $\text{Hora Canónica} = 3600 \text{ s} = [1, 0, 0]_{60}$
    pub const CANONICAL_HOUR: Sexagesimal = Sexagesimal { sar: 1, u: 0, gin: 0 };
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sexagesimal_conversions() {
        let val = 3661; // 1*3600 + 1*60 + 1
        let s = Sexagesimal::from_decimal(val);
        assert_eq!(s, Sexagesimal { sar: 1, u: 1, gin: 1 });
        assert_eq!(s.to_decimal(), 3661);
    }

    #[test]
    fn test_sexagesimal_arithmetic() {
        let a = Sexagesimal::new(0, 30, 0); // 1800
        let b = Sexagesimal::new(0, 45, 0); // 2700
        let c = a + b;
        assert_eq!(c.to_decimal(), 4500); // 1 sar, 15 u
        assert_eq!(c, Sexagesimal { sar: 1, u: 15, gin: 0 });

        let d = b - a;
        assert_eq!(d, Sexagesimal { sar: 0, u: 15, gin: 0 });
    }

    #[test]
    fn test_f60_ball_rigorous_bounds() {
        let mid = Sexagesimal::new(1, 0, 0); // 3600
        let ball_a = F60Ball::new(mid, 10);
        assert_eq!(ball_a.lower_bound(), 3590);
        assert_eq!(ball_a.upper_bound(), 3610);
        assert!(ball_a.contains(3600));
        assert!(ball_a.contains(3590));
        assert!(ball_a.contains(3610));
        assert!(!ball_a.contains(3589));
        assert!(!ball_a.contains(3611));
        assert!(ball_a.is_strictly_positive());
        assert!(!ball_a.can_be_zero());

        let ball_b = F60Ball::new(Sexagesimal::new(0, 10, 0), 5); // 600 ± 5
        let ball_sum = ball_a + ball_b; // 4200 ± 15
        assert_eq!(ball_sum.mid.to_decimal(), 4200);
        assert_eq!(ball_sum.rad, 15);
        assert!(ball_sum.contains(4200));
        assert!(ball_sum.contains(4215));
        assert!(ball_sum.contains(4185));

        let ball_diff = ball_a - ball_b; // 3000 ± 15
        assert_eq!(ball_diff.mid.to_decimal(), 3000);
        assert_eq!(ball_diff.rad, 15);
    }
}

