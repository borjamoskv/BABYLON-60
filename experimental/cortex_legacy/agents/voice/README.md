# █▄ BABYLON-60 VOICE TRANSDUCER (C5-REAL)

Agente de voz full-duplex **100% local**. Cero red, cero nube: el audio nunca abandona la máquina.

## Topología

```
mic ─► VAD adaptativo ─► Endpointer semántico ─► STT streaming (faster-whisper)
            │                    │ hang 200/480/900ms          │ parciales
            │                    ▼                             ▼
            │            SpeculativeExecutor ◄─── lanza LLM sobre el parcial
            │                    │ hit ⇒ tokens a coste ~0
            │                    ▼
            │            MLX Brain (stream) ─► ClauseChunker ─► Kokoro TTS ─► speaker
            │                                                        │
            └── barge-in <120ms: mata playback y abre turno ─────────┘
                                    ▼
                      VoiceLedger (aiosqlite WAL, UUID5, recibo por turno)
```

## Los cinco vectores que colapsan la latencia SOTA

1. **Endpointing semántico**: el hang-time se modula con la completitud sintáctica del parcial
   (frase terminada → 200ms; conector colgante → 900ms). Elimina el colchón fijo de ~700ms de
   las cascadas comerciales.
2. **Generación especulativa**: el LLM arranca sobre el parcial STT durante la ventana de
   silencio. Si el transcript final coincide (similitud ≥ 0.92), el primer token ya existe
   antes de que el usuario termine de hablar.
3. **Prefinal STT (v2)**: el decode final arranca a los 60ms de silencio, en paralelo al hang.
   El feed se congela durante la cola de silencio (gap-buffer reinyectable si el habla se
   reanuda), de modo que `finalize()` reutiliza el resultado: coste ~0 en el commit.
4. **Prefetch TTS (v2)**: el pump del draft especulativo pre-sintetiza la primera cláusula.
   En un hit, el primer audio ya existe al cerrar el endpoint.
5. **TTS incremental por cláusulas**: los chunks siguientes se sintetizan en fronteras
   prosódicas del stream, no al final de la respuesta.

## Benchmark (pipeline real, backends sintéticos, latencias inyectadas conservadoras)

| Configuración                             | TTFA p50  | hang    | spec |
|-------------------------------------------|-----------|---------|------|
| BABYLON-60 v2 (prefinal + prefetch TTS)    | **200ms** | 200ms   | 100% |
| BABYLON-60 v1 (especulación básica)        | 395ms     | 200ms   | 100% |
| Baseline endpoint fijo 700ms               | 1050ms    | 700ms   | 0%   |

Referencias voice-to-voice: humano ~230ms · S2S comercial ~500ms · cascada típica ~1100ms.
En v2 el TTFA converge al propio hang (200.4ms medido vs 200.2ms de hang): STT final, primer
token y primera síntesis ejecutan íntegros dentro de la ventana de silencio. Overhead de
orquestación: **<1ms**. Reproducir: `python -m cortex.agents.voice --benchmark`.

## Ignición

```bash
pip install -e ".[voice]"        # sounddevice + faster-whisper
pip install -e ".[voice-full]"   # + mlx-lm + kokoro (Apple Silicon)

python -m cortex.agents.voice                          # kokoro + mlx + whisper
python -m cortex.agents.voice --tts say --brain echo   # fallback zero-dep macOS
python -m cortex.agents.voice --benchmark              # sin hardware
```

## Invariantes

- FSM de turnos con tabla inmutable: transición inválida ⇒ `TurnProtocolError` (fail-fast).
- Todo turno emite un `TurnReceipt` con deltas por etapa (`speech_dur`, `hang`, `stt_final`,
  `first_token`, `ttfa`) anclado en `cortex_voice_ledger.db` (WAL, `INSERT OR IGNORE`, UUID5).
- `first_token_ms` negativo es legal: firma de un hit especulativo (el token precede al fin de habla).
- Sin AEC: el barge-in usa margen VAD elevado (+12dB) y ataque sostenido (120ms) durante playback.
- Tests sin hardware: `pytest tests/test_voice_transducer.py`.
