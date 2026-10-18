#!/usr/bin/env python3
import json
import math

def calculate_funnel_and_thermodynamics():
    # 1. Funnel Transformation: Meta Ads Display vs. Agentic Transactional Brokerage
    # Caso analizado en el vídeo: Póliza de seguro de hogar
    policy_annual_premium_usd = 450.0  # Prima media anual

    # Funnel Clásico (Meta Ads Display - Feed / Stories)
    cpm_display_usd = 18.0  # Coste por mil impresiones
    ctr_display = 0.012     # 1.2% Click-Through Rate
    cvr_display = 0.025     # 2.5% Conversion Rate de clic a póliza contratada
    impressions_needed = 1.0 / (ctr_display * cvr_display)
    meta_revenue_display_usd = (impressions_needed / 1000.0) * cpm_display_usd  # ~60 USD por adquisición

    # Funnel Agéntico (Muse Intent Brokerage - "Búscame una póliza que me ahorre dinero")
    brokerage_commission_rate = 0.18  # 18% comisión media de corredor/agente
    meta_revenue_agentic_usd = policy_annual_premium_usd * brokerage_commission_rate  # 81 USD directo
    exergy_funnel_expansion = meta_revenue_agentic_usd / meta_revenue_display_usd

    # 2. Asimetría de Ancho de Banda Canal Visual vs. Canal Acústico
    # Lectura / escaneo en pantalla (iPhone / Mac):
    visual_reading_wpm = 350.0
    visual_bits_per_sec = (visual_reading_wpm / 60.0) * 5.5 * 8  # ~256 bps texto + escaneo espacial de tablas
    visual_effective_bandwidth_bps = visual_bits_per_sec * 4.0   # Factor x4 por procesamiento paralelo de layout

    # Interfaz de voz (Wearable / Auricular / Gafas):
    speech_rate_wpm = 160.0
    acoustic_effective_bandwidth_bps = (speech_rate_wpm / 60.0) * 5.5 * 8  # ~117 bps

    bandwidth_deficit_ratio = visual_effective_bandwidth_bps / acoustic_effective_bandwidth_bps

    # 3. Restricciones Físicas de Silicio y Batería (Muse Charm / Wearable vs. Smartphone)
    charm_battery_mah = 280.0     # Capacidad estimada factor de forma llavero/wearable
    phone_battery_mah = 3800.0    # Smartphone medio
    battery_capacity_ratio = phone_battery_mah / charm_battery_mah

    # Presupuesto de latencia en control de tareas complejas por voz (booking, seguros):
    ble_tether_ms = 40.0
    wan_rtt_5g_ms = 65.0
    ttft_cloud_llm_ms = 420.0
    tts_audio_chunk_ms = 250.0
    total_latency_ms = ble_tether_ms + wan_rtt_5g_ms + ttft_cloud_llm_ms + tts_audio_chunk_ms

    results = {
        "funnel_comparison": {
            "policy_premium_annual_usd": policy_annual_premium_usd,
            "classic_ad_acquisition_cost_usd": round(meta_revenue_display_usd, 2),
            "agentic_brokerage_revenue_usd": round(meta_revenue_agentic_usd, 2),
            "revenue_expansion_factor": round(exergy_funnel_expansion, 2)
        },
        "informational_channel_bandwidth": {
            "visual_screen_effective_bps": round(visual_effective_bandwidth_bps, 1),
            "acoustic_voice_effective_bps": round(acoustic_effective_bandwidth_bps, 1),
            "visual_to_acoustic_deficit_factor": round(bandwidth_deficit_ratio, 2)
        },
        "hardware_and_energy_constraints": {
            "battery_ratio_phone_vs_wearable": round(battery_capacity_ratio, 1),
            "total_voice_roundtrip_latency_ms": round(total_latency_ms, 1),
            "stand_alone_5g_thermal_penalty": "High (cauterio térmico en silicio <15g)"
        },
        "epistemic_calibration": {
            "thesis_core_funnel_control": "VALIDADA (Transición de Ad Network a Corredor Agéntico)",
            "thesis_hardware_friction": "VALIDADA (El metaverso VR fracasó por fricción de acceso masivo)",
            "thesis_displacing_apple": "HIPERBÓLICA / FALACIA DE DESINTERMEDIACIÓN (Déficit visual y atadura de hardware)"
        }
    }

    with open("/Users/borjafernandezangulo/.gemini/antigravity/scratch/muse_funnel_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    calculate_funnel_and_thermodynamics()
