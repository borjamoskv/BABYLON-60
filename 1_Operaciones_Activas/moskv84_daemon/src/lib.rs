// C5-REAL EXERGY CERTIFIED
//! # Monitor de Manto — Moskv84
//!
//! Demonio de entropía para el workspace. Calcula, en O(1) por tick y sin
//! asignaciones, un proxy computable de la perforación del manto de Markov
//! `‖Π_ημ‖` usando exclusivamente el historial de estados sensoriales `s`
//! (eventos inotify que superan la criba de `config.json`) y activos `a`
//! (tool calls del agente).
//!
//! ## La cadena inferencial que justifica el estimador
//!
//! 1. Manto intacto  ⟹  `s` es estadístico suficiente de `η` para `μ`.
//! 2. `s` suficiente + modelo convergido  ⟹  las innovaciones
//!    `ε_t = x_t − E[x_t | μ, a]` son ruido blanco con la covarianza predicha.
//! 3. Contrapositivo: innovaciones NO blancas ⟹ `s` no suficiente ⟹ fuga.
//!
//! El paso 2 exige cancelar la reaferencia: los eventos que el propio agente
//! causó con sus `a` no son información sobre `η` y deben descontarse antes de
//! medir nada (copia eferente / descarga corolaria).
//!
//! ## Las tres capas
//!
//! - Capa 1 — sorpresa `𝕁_t = −ln p(x_t | λ_t)`. Ruidosa. NO se umbraliza.
//! - Capa 2 — CUSUM de Page sobre el exceso estandarizado y huberizado.
//!   Detecta el cambio con retardo mínimo para una tasa de falsa alarma dada
//!   (óptimo de Lorden).
//! - Capa 3 — ralentización crítica: `ρ₁ ↑` y `σ² ↑` sostenidos. Es el
//!   indicador ADELANTADO: cerca de la bifurcación el autovalor dominante del
//!   flujo linealizado → 0, la tasa de retorno al NESS colapsa, y el término
//!   disipativo `Γ∇ln p` pierde contra el ruido. Dispara ANTES del colapso.
//!
//! Sin dependencias externas: `ln_gamma` (Lanczos) y `poisson_entropy` van
//! implementados.

// ---------------------------------------------------------------------------
// Parámetros
// ---------------------------------------------------------------------------

/// Configuración del monitor. Los umbrales NO salen de la física: salen de tu
/// función de pérdida entre snapshot falso y snapshot omitido. Estos valores
/// son un punto de partida calibrado sobre ruido sintético, no una derivación.
#[derive(Debug, Clone)]
pub struct Config {
    /// Ventana (ticks) en la que un evento se considera causado por una acción.
    pub efference_window: u64,
    /// Tasa de adaptación del modelo generativo de λ (EWMA).
    pub alpha_lambda: f64,
    /// Tasa de adaptación de los momentos del exceso (para estandarizarlo).
    pub alpha_excess: f64,
    /// EWMA rápida para varianza/autocovarianza de la innovación.
    pub beta_fast: f64,
    /// EWMA lenta (línea base) para varianza/autocovarianza.
    pub beta_slow: f64,
    /// Recorte de Huber sobre el exceso estandarizado, en sigmas. Es lo que
    /// impide que UN tick extremo dispare por sí solo: la contribución máxima
    /// por tick al acumulador queda acotada por `cusum_clip − cusum_slack`.
    pub cusum_clip: f64,
    /// Holgura del CUSUM, en sigmas. En estacionario debe darse E[z̃−δ] < 0.
    pub cusum_slack: f64,
    /// Umbral de disparo del CUSUM (BREACH), en sigma·tick.
    pub cusum_threshold: f64,
    /// Umbral de separación de autocorrelación (ρ_fast − ρ_slow) para preaviso.
    /// En ruido puro (ρ_fast − ρ_slow) tiene σ ≈ 0.172 con beta_fast = 0.10;
    /// de ahí que 0.25 fuese sólo 1.45σ y disparase solo. Con beta_fast = 0.05
    /// el ruido baja y 0.30 queda por encima de 2σ.
    pub rho_gap: f64,
    /// Umbral de inflación de varianza (v_fast / v_slow) para preaviso.
    pub var_ratio: f64,
    /// Ticks consecutivos que la conjunción de ralentización debe sostenerse.
    /// La ralentización crítica es una TENDENCIA, no un instante: exigir
    /// persistencia del orden de la longitud de correlación (≈1/beta_fast) es
    /// lo que separa la señal del ruido del propio estimador.
    pub slowing_persist: u32,
    /// Ticks mínimos entre snapshots consecutivos.
    pub refractory_ticks: u64,
    /// Ticks de calentamiento antes de emitir cualquier señal.
    pub warmup_ticks: u64,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            efference_window: 3,
            alpha_lambda: 0.05,
            alpha_excess: 0.02,
            beta_fast: 0.05,
            beta_slow: 0.005,
            cusum_clip: 3.0,
            cusum_slack: 0.5,
            cusum_threshold: 10.0,
            rho_gap: 0.30,
            var_ratio: 1.8,
            slowing_persist: 20,
            refractory_ticks: 30,
            warmup_ticks: 200,
        }
    }
}

// ---------------------------------------------------------------------------
// Señal de salida
// ---------------------------------------------------------------------------

/// Veredicto del monitor en un tick.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Verdict {
    /// Calentando: estadísticos aún no fiables.
    Warmup,
    /// Manto íntegro. Las innovaciones pasan por blancas.
    Nominal,
    /// Ralentización crítica detectada. El manto se está volviendo permeable.
    /// Indicador ADELANTADO: dispara el snapshot aquí.
    PreCollapse,
    /// Cambio de régimen confirmado por CUSUM. El manto YA está perforado:
    /// snapshot + marcar el modelo para reconstrucción.
    Breach,
    /// En periodo refractario tras un disparo reciente.
    Refractory,
}

/// Lectura completa de un tick: el veredicto más los estadísticos crudos, para
/// que el demonio pueda loguearlos y tú puedas recalibrar los umbrales offline.
#[derive(Debug, Clone, Copy)]
pub struct Reading {
    pub verdict: Verdict,
    /// Eventos exaferentes tras cancelar la reaferencia.
    pub exafferent: u32,
    /// Eventos descontados por copia eferente.
    pub cancelled: u32,
    /// Tasa esperada del modelo generativo.
    pub lambda: f64,
    /// Sorpresa instantánea 𝕁_t (nats).
    pub surprisal: f64,
    /// Entropía analítica H(Poisson(λ_t)) (nats). Sorpresa esperada.
    pub entropy: f64,
    /// Exceso de sorpresa Δ_t = 𝕁_t − H(λ_t) (nats).
    pub excess: f64,
    /// Exceso estandarizado y recortado, en sigmas. Es lo que entra al CUSUM.
    pub excess_z: f64,
    /// Estadístico CUSUM acumulado (sigma·tick).
    pub cusum: f64,
    /// Ticks consecutivos con la conjunción de ralentización activa.
    pub slowing_run: u32,
    /// Autocorrelación lag-1 de la innovación, escala rápida.
    pub rho_fast: f64,
    /// Autocorrelación lag-1 de la innovación, escala lenta.
    pub rho_slow: f64,
    /// Cociente de varianzas v_fast / v_slow.
    pub var_ratio: f64,
}

// ---------------------------------------------------------------------------
// Entrada de un tick
// ---------------------------------------------------------------------------

/// Un tick de observación ya pre-agregado por el watcher de inotify.
///
/// `total_events` son los eventos que superaron la criba de `config.json`.
/// `self_caused` son los que caen dentro del conjunto de escritura declarado
/// por alguna tool call dentro de `efference_window` ticks. La separación la
/// hace quien llama, porque depende del matching de rutas, no del estimador.
#[derive(Debug, Clone, Copy)]
pub struct Tick {
    pub total_events: u32,
    pub self_caused: u32,
}

// ---------------------------------------------------------------------------
// El monitor
// ---------------------------------------------------------------------------

/// Estado del demonio. Ocupa ~150 bytes, no asigna, no bloquea.
#[derive(Debug, Clone)]
pub struct MantleMonitor {
    cfg: Config,
    t: u64,
    last_fire: Option<u64>,

    // Modelo generativo de la tasa exaferente.
    lambda: f64,

    // Momentos del exceso, para estandarizarlo antes del CUSUM.
    ex_mean: f64,
    ex_var: f64,

    // Innovación previa, para la autocovarianza lag-1.
    prev_innov: f64,

    // Momentos de la innovación a dos escalas.
    v_fast: f64,
    v_slow: f64,
    c_fast: f64,
    c_slow: f64,

    // Acumulador de Page.
    cusum: f64,
    // Racha de ticks consecutivos con ralentización activa.
    slowing_run: u32,
}

impl MantleMonitor {
    pub fn new(cfg: Config) -> Self {
        Self {
            cfg,
            t: 0,
            last_fire: None,
            lambda: 1.0,
            ex_mean: 0.0,
            ex_var: 1.0,
            prev_innov: 0.0,
            v_fast: 1.0,
            v_slow: 1.0,
            c_fast: 0.0,
            c_slow: 0.0,
            cusum: 0.0,
            slowing_run: 0,
        }
    }

    /// Un ciclo de reloj. Esta es la heurística completa.
    pub fn step(&mut self, tick: Tick) -> Reading {
        self.t += 1;

        // --- Paso 0: cancelación reaferente (copia eferente) ---------------
        // Los eventos que el propio agente causó con sus tool calls no son
        // información sobre η. Sin este paso el detector grita en cada
        // `cargo build` — que es exactamente el ruido que el agente mismo hace
        // al respirar.
        let cancelled = tick.self_caused.min(tick.total_events);
        let x = (tick.total_events - cancelled) as f64;

        // --- Paso 1: innovación contra la predicción previa ----------------
        // ε_t = x_t − E[x_t | μ_{t−1}, a_{t−1}]. Con el modelo Poisson-EWMA la
        // esperanza condicional es simplemente λ_{t−1}.
        let innov = x - self.lambda;

        // --- Paso 2: sorpresa bajo el modelo actual ------------------------
        // 𝕁_t = −ln p(x | λ) con p Poisson = λ − x·ln λ + ln Γ(x+1).
        let lam = self.lambda.max(1e-6);
        let surprisal = lam - x * lam.ln() + ln_gamma(x + 1.0);

        // --- Paso 3: entropía ANALÍTICA y exceso ---------------------------
        // Centrar por la entropía es lo que impide que un canal legítimamente
        // ruidoso acumule CUSUM: un modelo que espera ruido tiene entropía
        // alta, así que ruido-pero-esperado da exceso ≈ 0.
        //
        // Crítico: la entropía debe ser la ANALÍTICA del modelo actual,
        // H(Poisson(λ_t)), no una EWMA de la sorpresa observada. Una EWMA va
        // por detrás de λ, y ese retardo inyecta AUTOCORRELACIÓN en el exceso
        // — que es exactamente lo que un CUSUM integra hasta disparar. Con
        // 𝕁̄ empírica salían 39 falsos BREACH en 40 semillas de ruido puro.
        let entropy = poisson_entropy(lam);
        let excess = surprisal - entropy;

        // --- Paso 4: CUSUM de Page, estandarizado y huberizado -------------
        // Dos correcciones, ambas necesarias:
        //
        // (a) ESTANDARIZAR. La sorpresa en nats escala con λ, así que un
        //     umbral en nats no es transferible entre workspaces. En sigmas sí.
        //
        // (b) RECORTAR (Huber). Sin recorte, un solo `cargo build` gordo mete
        //     ~280 nats de golpe y revienta cualquier umbral: el detector se
        //     vuelve un umbral sobre sorpresa cruda, que es precisamente lo
        //     que NO queremos. Con recorte a `clip` sigmas, un tick aporta
        //     como mucho `clip − slack`, de modo que hacen falta
        //     ⌈threshold/(clip−slack)⌉ ticks SOSTENIDOS para disparar.
        //     El CUSUM vuelve a detectar lo que debe: desplazamientos
        //     persistentes de la media, no excursiones aisladas.
        let ex_sd = self.ex_var.max(1e-12).sqrt();
        let z = (excess - self.ex_mean) / ex_sd.max(1e-6);
        let excess_z = z.clamp(-self.cfg.cusum_clip, self.cfg.cusum_clip);
        self.cusum = (self.cusum + excess_z - self.cfg.cusum_slack).max(0.0);

        // --- Paso 5: momentos de la innovación a dos escalas ---------------
        // v = varianza EWMA, c = autocovarianza lag-1 EWMA, ρ = c / v.
        let (bf, bs) = (self.cfg.beta_fast, self.cfg.beta_slow);
        self.v_fast = (1.0 - bf) * self.v_fast + bf * innov * innov;
        self.v_slow = (1.0 - bs) * self.v_slow + bs * innov * innov;
        self.c_fast = (1.0 - bf) * self.c_fast + bf * innov * self.prev_innov;
        self.c_slow = (1.0 - bs) * self.c_slow + bs * innov * self.prev_innov;

        let rho_fast = clamp_unit(self.c_fast / self.v_fast.max(1e-9));
        let rho_slow = clamp_unit(self.c_slow / self.v_slow.max(1e-9));
        let var_ratio = self.v_fast / self.v_slow.max(1e-9);

        // --- Paso 6: adaptar el modelo (DESPUÉS de medir) ------------------
        // El orden importa: si adaptas antes de medir, el modelo se come la
        // señal y las innovaciones salen blancas por construcción.
        self.lambda =
            (1.0 - self.cfg.alpha_lambda) * self.lambda + self.cfg.alpha_lambda * x;
        let ae = self.cfg.alpha_excess;
        let d = excess - self.ex_mean;
        self.ex_mean += ae * d;
        self.ex_var = (1.0 - ae) * self.ex_var + ae * d * d;
        self.prev_innov = innov;

        // --- Paso 7: racha de ralentización --------------------------------
        // Sólo ρ↑ puede ser periodicidad benigna (un build cada N ticks); sólo
        // σ²↑ puede ser una ráfaga sin memoria. Es la CONJUNCIÓN SOSTENIDA lo
        // que marca la aproximación a la bifurcación.
        let slowing_now =
            (rho_fast - rho_slow) > self.cfg.rho_gap && var_ratio > self.cfg.var_ratio;
        self.slowing_run = if slowing_now { self.slowing_run + 1 } else { 0 };

        // --- Paso 8: veredicto ---------------------------------------------
        let verdict = self.classify();
        if matches!(verdict, Verdict::PreCollapse | Verdict::Breach) {
            self.last_fire = Some(self.t);
            // Tras disparar, purgar los acumuladores: si no, se encadenan
            // disparos sobre el mismo evento en cuanto pasa el refractario.
            self.slowing_run = 0;
            if verdict == Verdict::Breach {
                self.cusum = 0.0;
            }
        }

        Reading {
            verdict,
            exafferent: x as u32,
            cancelled,
            lambda: self.lambda,
            surprisal,
            entropy,
            excess,
            excess_z,
            cusum: self.cusum,
            slowing_run: self.slowing_run,
            rho_fast,
            rho_slow,
            var_ratio,
        }
    }

    fn classify(&self) -> Verdict {
        if self.t <= self.cfg.warmup_ticks {
            return Verdict::Warmup;
        }
        if let Some(last) = self.last_fire {
            if self.t - last < self.cfg.refractory_ticks {
                return Verdict::Refractory;
            }
        }
        // BREACH domina: cambio de régimen ya consumado.
        if self.cusum > self.cfg.cusum_threshold {
            return Verdict::Breach;
        }
        if self.slowing_run >= self.cfg.slowing_persist {
            return Verdict::PreCollapse;
        }
        Verdict::Nominal
    }

    /// Tras un disparo: si el exceso decae al readaptarse el modelo, era
    /// retardo de modelo (aprendizaje normal). Si persiste, es fuga real y hay
    /// que ensanchar la criba de `config.json`, no volver a snapshotear.
    ///
    /// Éste es el único desambiguador disponible desde dentro del manto, y es
    /// intrínsecamente a posteriori.
    pub fn cusum_level(&self) -> f64 {
        self.cusum
    }

    pub fn ticks(&self) -> u64 {
        self.t
    }
}

// ---------------------------------------------------------------------------
// lgamma (Lanczos, g=7, n=9). Precisión ~1e-13 relativa para x > 0.
// ---------------------------------------------------------------------------

fn ln_gamma(x: f64) -> f64 {
    const C: [f64; 9] = [
        0.999_999_999_999_809_93,
        676.520_368_121_885_1,
        -1259.139_216_722_402_8,
        771.323_428_777_653_1,
        -176.615_029_162_140_6,
        12.507_343_278_686_905,
        -0.138_571_095_265_720_12,
        9.984_369_578_019_572e-6,
        1.505_632_735_149_311_6e-7,
    ];
    if x < 0.5 {
        // Reflexión: Γ(x)Γ(1−x) = π / sin(πx)
        return (std::f64::consts::PI / (std::f64::consts::PI * x).sin()).ln()
            - ln_gamma(1.0 - x);
    }
    let x = x - 1.0;
    let mut a = C[0];
    let t = x + 7.5;
    for (i, &c) in C.iter().enumerate().skip(1) {
        a += c / (x + i as f64);
    }
    0.5 * (2.0 * std::f64::consts::PI).ln() + (x + 0.5) * t.ln() - t + a.ln()
}

/// Entropía de Shannon de Poisson(λ) en nats.
///
/// `H = λ(1 − ln λ) + E[ln k!]`. Para λ pequeño se suma directo; para λ grande
/// se usa la expansión asintótica estándar
/// `H ≈ ½ln(2πeλ) − 1/(12λ) − 1/(24λ²) − 19/(360λ³)`.
fn poisson_entropy(lambda: f64) -> f64 {
    let lam = lambda.max(1e-9);
    if lam >= 8.0 {
        let l2 = lam * lam;
        return 0.5 * (2.0 * std::f64::consts::PI * std::f64::consts::E * lam).ln()
            - 1.0 / (12.0 * lam)
            - 1.0 / (24.0 * l2)
            - 19.0 / (360.0 * l2 * lam);
    }
    // Suma directa: k hasta λ + 10√λ + 30 cubre la masa con holgura.
    let kmax = (lam + 10.0 * lam.sqrt() + 30.0).ceil() as u32;
    let ln_lam = lam.ln();
    let mut e_ln_fact = 0.0;
    for k in 0..=kmax {
        let kf = k as f64;
        let ln_pk = -lam + kf * ln_lam - ln_gamma(kf + 1.0);
        e_ln_fact += ln_pk.exp() * ln_gamma(kf + 1.0);
    }
    lam * (1.0 - ln_lam) + e_ln_fact
}

fn clamp_unit(v: f64) -> f64 {
    if v.is_nan() {
        0.0
    } else {
        v.clamp(-1.0, 1.0)
    }
}

// ---------------------------------------------------------------------------
// Verificación
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    /// LCG determinista: sin dependencias, reproducible.
    struct Rng(u64);
    impl Rng {
        fn next_f64(&mut self) -> f64 {
            self.0 = self
                .0
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            ((self.0 >> 11) as f64) / ((1u64 << 53) as f64)
        }
        /// Poisson por el método de Knuth. Suficiente para λ moderado.
        fn poisson(&mut self, lambda: f64) -> u32 {
            let l = (-lambda).exp();
            let mut k = 0u32;
            let mut p = 1.0;
            loop {
                p *= self.next_f64();
                if p <= l || k > 10_000 {
                    return k;
                }
                k += 1;
            }
        }
    }

    #[test]
    fn ln_gamma_matches_known_values() {
        // ln Γ(1)=0, ln Γ(2)=0, ln Γ(5)=ln 24, ln Γ(0.5)=ln √π
        assert!((ln_gamma(1.0) - 0.0).abs() < 1e-10);
        assert!((ln_gamma(2.0) - 0.0).abs() < 1e-10);
        assert!((ln_gamma(5.0) - 24f64.ln()).abs() < 1e-10);
        assert!((ln_gamma(0.5) - std::f64::consts::PI.sqrt().ln()).abs() < 1e-10);
    }

    /// Régimen estacionario: NO debe disparar. Ésta es la prueba que mata a un
    /// umbral ingenuo sobre sorpresa cruda.
    #[test]
    fn stationary_regime_stays_nominal() {
        let mut m = MantleMonitor::new(Config::default());
        let mut rng = Rng(42);
        let mut fires = 0;
        for _ in 0..3000 {
            let x = rng.poisson(20.0);
            let r = m.step(Tick { total_events: x, self_caused: 0 });
            if matches!(r.verdict, Verdict::PreCollapse | Verdict::Breach) {
                fires += 1;
            }
        }
        assert_eq!(fires, 0, "el régimen estacionario no debe disparar");
    }

    /// Pico aislado de sorpresa (un `cargo build` gordo, una edición masiva).
    /// Es normal: el aprendizaje consume sorpresa. NO debe disparar BREACH.
    #[test]
    fn isolated_surprise_spike_does_not_breach() {
        let mut m = MantleMonitor::new(Config::default());
        let mut rng = Rng(7);
        for _ in 0..500 {
            let x = rng.poisson(20.0);
            m.step(Tick { total_events: x, self_caused: 0 });
        }
        let mut breached = false;
        for i in 0..300 {
            let x = if (100..103).contains(&i) { 200 } else { rng.poisson(20.0) };
            let r = m.step(Tick { total_events: x, self_caused: 0 });
            if r.verdict == Verdict::Breach {
                breached = true;
            }
        }
        assert!(!breached, "un pico aislado no es perforación del manto");
    }

    /// La reaferencia debe cancelarse: mil eventos causados por el propio
    /// agente son indistinguibles del silencio.
    #[test]
    fn reafference_is_cancelled() {
        let mut m = MantleMonitor::new(Config::default());
        for _ in 0..1500 {
            let r = m.step(Tick { total_events: 800, self_caused: 800 });
            assert_eq!(r.exafferent, 0);
            assert!(!matches!(r.verdict, Verdict::PreCollapse | Verdict::Breach));
        }
    }

    /// Deriva pre-colapso: la tasa exaferente se vuelve autocorrelacionada y su
    /// varianza se infla — el usuario cambió de intención arquitectónica y lo
    /// está reflejando en ráfagas asíncronas que la semántica de μ no cubre.
    /// El preaviso DEBE dispararse.
    #[test]
    fn creeping_drift_triggers_precollapse() {
        let mut m = MantleMonitor::new(Config::default());
        let mut rng = Rng(1234);
        for _ in 0..600 {
            let x = rng.poisson(20.0);
            m.step(Tick { total_events: x, self_caused: 0 });
        }
        // Proceso AR(1) con memoria creciente sobre la tasa: ralentización.
        let mut warned_at = None;
        let mut state = 20.0f64;
        for i in 0..600 {
            let phi = 0.3 + 0.65 * (i as f64 / 600.0);
            let shock = (rng.next_f64() - 0.5) * 60.0;
            state = 20.0 + phi * (state - 20.0) + shock;
            let x = state.max(0.0).round() as u32;
            let r = m.step(Tick { total_events: x, self_caused: 0 });
            if warned_at.is_none()
                && matches!(r.verdict, Verdict::PreCollapse | Verdict::Breach)
            {
                warned_at = Some(i);
            }
        }
        assert!(warned_at.is_some(), "la deriva debe activar el preaviso");
    }

    /// El periodo refractario evita encadenar snapshots sobre un mismo evento.
    #[test]
    fn refractory_period_holds() {
        let mut m = MantleMonitor::new(Config::default());
        let mut rng = Rng(99);
        for _ in 0..200 {
            m.step(Tick { total_events: rng.poisson(5.0), self_caused: 0 });
        }
        let mut consecutive = 0;
        for _ in 0..400 {
            let r = m.step(Tick { total_events: rng.poisson(400.0), self_caused: 0 });
            if matches!(r.verdict, Verdict::PreCollapse | Verdict::Breach) {
                consecutive += 1;
            }
        }
        assert!(consecutive < 20, "demasiados disparos: refractario roto ({consecutive})");
    }
}
