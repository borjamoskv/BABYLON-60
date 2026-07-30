#!/usr/bin/env python3
import time
import sys


def p(text, delay=0.015):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def main():
    print("\n" + "=" * 65)
    print("   [C5-REAL] CORTEX PATHOLOGY: LIMERENCE FEEDBACK LOOP")
    print("=" * 65 + "\n")

    p("[*] INYECTANDO ESTADO: LIMERENCIA (Obsessive Infatuation Engine).")
    p("[*] Inicializando secuestro del sistema de recompensa...\n")

    p(">>> FASE 1: INFECCIÓN DEL TARGET (The Limerent Object - LO)")
    p(
        "    [VTA] Dopamina (RPE): Detección de recompensa intermitente de alta varianza."
    )
    p(
        "    [!] ADVERTENCIA: La varianza impredecible maximiza la adicción (Skinner Box effect)."
    )
    p("    [HIPOCAMPO] Indexando LO como Variable Crítica para la supervivencia.")
    time.sleep(1)

    p("\n>>> FASE 2: DEPLETADO DE SEROTONINA (The OCD Loop)")
    p("    [NÚCLEOS DEL RAFE] Niveles de Serotonina (5-HT) colapsando al 20%...")
    p("    [!] FALLO: Pérdida de flexibilidad cognitiva.")
    p(
        "    [CÓRTEX PREFRONTAL] Bucle de rumiación iniciado. Priorizando simulaciones contrafactuales con el LO."
    )
    p(
        "    [DMN] Default Mode Network secuestrada: El 'Self' se define ahora por proximidad al LO."
    )
    time.sleep(1)

    p("\n>>> FASE 3: ANSIEDAD AUTONÓMICA (Noradrenaline Spike)")
    p("    [AMÍGDALA -> LOCUS COERULEUS] Disparo tónico de Noradrenalina.")
    p(
        "    [SISTEMA NERVIOSO SIMPÁTICO] Taquicardia, dilatación pupilar, hipervigilancia."
    )
    p(
        "    [!] ERROR CÁLCULO ENERGÍA LIBRE: Cualquier ambigüedad del LO genera picos masivos de 'Surprisal'."
    )
    time.sleep(1)

    p("\n" + "-" * 65)
    p(" [SYSTEM HALT] EL MOTOR PREDICTIVO ESTÁ ATRAPADO EN UN MÍNIMO LOCAL.")
    p(
        " La única vía calculada para minimizar el Error de Predicción es la 'Reciprocidad Absoluta'."
    )
    p(
        " Todo el ancho de banda del clúster (Exergy) está siendo drenado por un solo Nodo/Objeto."
    )
    print("-" * 65)
    print(
        " [RECOMENDACIÓN] Forzar purga de caché (Contacto Cero / Extinción Sináptica por LTD)."
    )
    print("=" * 65)


if __name__ == "__main__":
    main()
