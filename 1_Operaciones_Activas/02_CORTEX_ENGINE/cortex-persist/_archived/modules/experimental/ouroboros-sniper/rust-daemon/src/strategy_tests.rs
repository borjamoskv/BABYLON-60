#[cfg(test)]
mod tests {
    use crate::strategy::{SovereignAlphaStrategy, StrategyConfig};
    use crate::types::{SovereignEvent, SovereignAction, Strategy};

    #[tokio::test]
    async fn test_v4_pool_deployment_trigger() {
        use std::sync::{Arc, Mutex};
        use crate::dashboard::Babylon60State;
        use crate::vsa_memory::VsaMemory;

        let state = Arc::new(Mutex::new(Babylon60State::default()));
        let vsa_memory = VsaMemory::new(state);

        let mut strategy = SovereignAlphaStrategy::new(StrategyConfig {
            snipe_amount_eth: 0.1,
            min_sell_multiplier: 3.0,
            blacklist: vec!["0xScam".to_string()],
            dry_run: true,
        }, vsa_memory);

        // Simular evento de creacion de Pool V4
        let event = SovereignEvent::UniswapV4PoolCreated {
            token: "0xAlpha123".to_string(),
            pool_key: "0xPoolKeyHash".to_string(),
        };

        let actions = strategy.process_event(event).await;

        // Verificar que emite una accion simulada (dry_run)
        assert_eq!(actions.len(), 1);
        if let SovereignAction::LogOnly(msg) = &actions[0] {
            assert!(msg.contains("[DRY-RUN] V4 Pool SNIPE"));
        } else {
            panic!("Deberia haber disparado LogOnly en dry_run");
        }
    }

    #[tokio::test]
    async fn test_alpha_signal_heuristics() {
        use std::sync::{Arc, Mutex};
        use crate::dashboard::Babylon60State;
        use crate::vsa_memory::VsaMemory;

        let state = Arc::new(Mutex::new(Babylon60State::default()));
        let vsa_memory = VsaMemory::new(state);

        let mut strategy = SovereignAlphaStrategy::new(StrategyConfig::default(), vsa_memory);

        let signal = "🔥 NUEVO GEM LISTING! Presale in 5 min. CA: 0x1234567890123456789012345678901234567890 100x incoming!";
        let event = SovereignEvent::AlphaSignal(signal.to_string());

        let actions = strategy.process_event(event).await;

        assert_eq!(actions.len(), 1);
        if let SovereignAction::LogOnly(msg) = &actions[0] {
            assert!(msg.contains("0x1234567890123456789012345678901234567890"));
        }
    }
}
