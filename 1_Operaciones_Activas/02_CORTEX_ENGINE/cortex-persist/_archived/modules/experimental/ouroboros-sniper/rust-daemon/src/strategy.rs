/// OUROBOROS STRATEGY — BABYLON60 ALPHA ARBITRAGE CORE
/// Lógica pura: SovereignEvent → Vec<SovereignAction>
/// Ley Ω₁: Frontera determinista. Sin I/O. Sin efectos secundarios.
/// Asimilado de paradigmxyz/artemis Strategy trait.

use anyhow::Result;
use async_trait::async_trait;
use std::collections::HashMap;

use crate::types::{SovereignAction, SovereignEvent, Strategy};
use crate::vsa_memory::VsaMemory;

// ── CONFIGURACIÓN DE ESTRATEGIA ──────────────────────────────────
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct StrategyConfig {
    /// ETH para cada snipe (en wei string, ej: "50000000000000000" = 0.05 ETH)
    pub snipe_amount_eth: f64,
    /// Multiplicador mínimo para activar sell (ej: 3.0 = 3x)
    pub min_sell_multiplier: f64,
    /// Lista negra de tokens conocidos como scam
    pub blacklist: Vec<String>,
    /// Modo simulación — no envía txs reales
    pub dry_run: bool,
}

impl Default for StrategyConfig {
    fn default() -> Self {
        Self {
            snipe_amount_eth: 0.05,
            min_sell_multiplier: 3.0,
            blacklist: Vec::new(),
            dry_run: true, // SEGURO por defecto. Cambiar a false para producción.
        }
    }
}

// ── ESTADO DE POSICIONES ABIERTAS ────────────────────────────────
#[derive(Debug, Default)]
#[allow(dead_code)]
pub struct PortfolioState {
    /// token_ca → precio_entrada_eth
    pub open_positions: HashMap<String, f64>,
    /// Contadores para el ledger
    pub total_snipes: u64,
    pub total_exits: u64,
    pub total_pnl_eth: f64,
}

// ── ESTRATEGIA SOBERANA ───────────────────────────────────────────
pub struct SovereignAlphaStrategy {
    pub config: StrategyConfig,
    pub portfolio: PortfolioState,
    pub vsa_memory: VsaMemory,
}

impl SovereignAlphaStrategy {
    pub fn new(config: StrategyConfig, vsa_memory: VsaMemory) -> Self {
        Self {
            config,
            portfolio: PortfolioState::default(),
            vsa_memory,
        }
    }

    fn is_blacklisted(&self, token: &str) -> bool {
        self.config.blacklist.iter().any(|b| b.eq_ignore_ascii_case(token))
    }

    fn score_alpha_signal(&self, signal: &str) -> bool {
        // Heurística rápida de scoring: keywords de alto yield
        let keywords = ["launch", "listing", "presale", "stealth", "gem", "100x", "1000x"];
        let lower = signal.to_lowercase();
        keywords.iter().any(|kw| lower.contains(kw))
    }
}

#[async_trait]
impl Strategy<SovereignEvent, SovereignAction> for SovereignAlphaStrategy {
    async fn sync_state(&mut self) -> Result<()> {
        // En producción: cargar portafolio desde ledger.jsonl
        Ok(())
    }

    async fn process_event(&mut self, event: SovereignEvent) -> Vec<SovereignAction> {
        match event {
            // ── Vector 1: Señal alpha cruda (Telegram/Discord/GitHub) ──
            SovereignEvent::AlphaSignal(signal) => {
                if !self.score_alpha_signal(&signal) {
                    return vec![SovereignAction::LogOnly(
                        format!("[STRATEGY] AlphaSignal RECHAZADA (score bajo): {}", &signal[..signal.len().min(40)])
                    )];
                }

                // Extraer CA de la señal — simplificado, en producción usar regex/NLP
                let token_ca = extract_ca_from_signal(&signal);
                if token_ca.is_empty() || self.is_blacklisted(&token_ca) {
                    return vec![SovereignAction::LogOnly(
                        format!("[STRATEGY] CA no encontrada o en blacklist en señal: {}", &signal[..signal.len().min(40)])
                    )];
                }

                if self.config.dry_run {
                    return vec![SovereignAction::LogOnly(
                        format!("[DRY-RUN] SNIPE simulado → CA:{}", &token_ca)
                    )];
                }

                self.portfolio.total_snipes += 1;
                vec![SovereignAction::FlashbotsSnipe {
                    token_ca,
                    amount_eth: self.config.snipe_amount_eth,
                }]
            },

            // ── Vector 2: Nuevo pool V4 deploy ──
            SovereignEvent::UniswapV4PoolCreated { token, pool_key } => {
                if self.is_blacklisted(&token) {
                    return vec![];
                }
                tracing::info!("[STRATEGY][V4] Pool detectado. Token:{} Pool:{}", token, pool_key);

                if self.config.dry_run {
                    return vec![SovereignAction::LogOnly(
                        format!("[DRY-RUN] V4 Pool SNIPE → Token:{}", token)
                    )];
                }

                self.portfolio.total_snipes += 1;
                vec![SovereignAction::FlashbotsSnipe {
                    token_ca: token,
                    amount_eth: self.config.snipe_amount_eth,
                }]
            },

            // ── Vector 3: Alpha wallet detectada en mempool ──
            SovereignEvent::AlphaTxDetected { wallet, token, amount_eth } => {
                tracing::info!(
                    "[STRATEGY][MIRROR] Alpha wallet {wallet} comprando {token} con {amount_eth}Ξ. Siguiendo."
                );

                if self.config.dry_run {
                    return vec![SovereignAction::LogOnly(
                        format!("[DRY-RUN] MIRROR SNIPE → Token:{} Amount:{}Ξ", token, amount_eth)
                    )];
                }

                // Copiamos al 50% del tamaño detectado, máximo config.snipe_amount_eth
                let copy_amount = (amount_eth * 0.5).min(self.config.snipe_amount_eth);
                self.portfolio.total_snipes += 1;
                vec![SovereignAction::FlashbotsSnipe {
                    token_ca: token,
                    amount_eth: copy_amount,
                }]
            },

            // ── Vector 4: Análisis de Bytecode (Brain Check) ──
            SovereignEvent::ContractDetected { ca, bytecode } => {
                if self.vsa_memory.is_honeypot(&bytecode) {
                    return vec![SovereignAction::LogOnly(
                        format!("[VSA] Honeypot detectado por patrón similar! CA:{}", ca)
                    )];
                }

                // [NUEVO] Detección Proactiva de Vulnerabilidades (Artemis-Ω Strike)
                if self.vsa_memory.has_vulnerability(&bytecode) {
                    return vec![SovereignAction::StrikeExploit {
                        ca,
                        payload: vec![], // El ejecutor generará el payload dinámico
                    }];
                }

                if self.config.dry_run {
                    return vec![SovereignAction::LogOnly(
                        format!("[DRY-RUN] Snipe validado por VSA → CA:{}", ca)
                    )];
                }

                self.portfolio.total_snipes += 1;
                vec![SovereignAction::FlashbotsSnipe {
                    token_ca: ca,
                    amount_eth: self.config.snipe_amount_eth,
                }]
            },

            // ── Vector 5: Nuevo bloque — reevaluación de posiciones ──
            SovereignEvent::NewBlock(block) => {
                tracing::debug!("[STRATEGY] Bloque #{block}. Posiciones abiertas: {}", self.portfolio.open_positions.len());
                // [Fase 3]: Consultar precios on-chain vía multicall y decidir exits
                vec![]
            },
        }
    }
}

/// Extrae un Contract Address de Ethereum de una cadena de texto.
/// Pattern: dirección de 42 caracteres (0x + 40 hex).
fn extract_ca_from_signal(signal: &str) -> String {
    // Regex habitual para encontrar direcciones EVM
    let chars: Vec<char> = signal.chars().collect();
    for i in 0..chars.len().saturating_sub(41) {
        if chars[i] == '0' && chars.get(i + 1) == Some(&'x') {
            let candidate: String = chars[i..i + 42].iter().collect();
            if candidate.chars().skip(2).all(|c| c.is_ascii_hexdigit()) {
                return candidate;
            }
        }
    }
    String::new()
}

#[cfg(test)]
#[path = "strategy_tests.rs"]
mod strategy_tests;
