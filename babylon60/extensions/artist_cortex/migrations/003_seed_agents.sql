-- =========================
-- SEED AGENTS
-- =========================

INSERT OR IGNORE INTO cortex_agents (agent_key, role, config_json, active) VALUES
  ('generator_alpha', 'generator', '{"temperature": 0.8, "mode": "chaos"}', 1),
  ('critic_omega', 'critic', '{"strictness": 0.9}', 1),
  ('noise_injector', 'noise_injector', '{"entropy_level": 0.5}', 1),
  ('assembler_prime', 'assembler', '{"strategy": "seamless"}', 1);
