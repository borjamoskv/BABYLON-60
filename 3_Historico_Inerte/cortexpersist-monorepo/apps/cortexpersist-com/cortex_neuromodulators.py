#!/usr/bin/env python3
import time
import sys


def p(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


class CortexGlobalState:
    def __init__(self):
        self.dopamine = 50.0  # Reward Prediction Error / Learning Rate
        self.serotonin = 50.0  # Exploit ratio / Risk tolerance
        self.noradrenaline = 50.0  # Signal-to-Noise ratio / Arousal
        self.acetylcholine = 50.0  # Memory encoding / Pointers
        self.exergy = 100.0

    def get_status(self):
        return f"[ DA: {self.dopamine:05.1f} | 5-HT: {self.serotonin:05.1f} | NA: {self.noradrenaline:05.1f} | ACh: {self.acetylcholine:05.1f} | EXERGY: {self.exergy:05.1f} ]"

    def inject_event(self, event_type):
        p(f"\n[EVENT] Injecting: {event_type}")

        if event_type == "HIGH_REWARD_SURPRISE":
            p(">>> DAEMON: VTA (Área Tegmental Ventral) ACTIVADO.")
            p(">>> RPE (Reward Prediction Error) > 0. Ajustando pesos.")
            self.dopamine += 30.0
            self.acetylcholine += 15.0
            self.serotonin -= 10.0
            p("    [!] Incremento de 'Learning Rate'. Se habilita LTP masivo.")

        elif event_type == "THREAT_DETECTED_PREDATOR":
            p(">>> DAEMON: Amígdala -> Locus Coeruleus ACTIVADO.")
            self.noradrenaline += 40.0
            self.serotonin -= 20.0
            self.dopamine += 10.0
            self.exergy -= 10.0
            p("    [!] Incremento crítico de SNR (Signal-to-Noise). Modo Fight/Flight.")
            p(
                "    [!] Supresión de 'Default Mode Network' (DMN). 'Central Executive' (CEN) fijado."
            )

        elif event_type == "RESOURCE_DEPLETION_HUNGER":
            p(">>> DAEMON: Hipotálamo (Sensor de Energía) ACTIVADO.")
            self.serotonin -= 30.0
            self.dopamine -= 10.0
            self.exergy -= 20.0
            p(
                "    [!] Baja de serotonina: Cambio de Explotación a Exploración. Impaciencia activa."
            )
            p("    [!] Aumento de costo de inferencia activa.")

        elif event_type == "GOAL_ACHIEVED_SATIETY":
            p(">>> DAEMON: Núcleos del Rafe ACTIVADOS.")
            self.serotonin += 40.0
            self.noradrenaline -= 20.0
            self.dopamine += 5.0
            p(
                "    [!] Alta serotonina: Retorno a Explotación. Tolerancia a la demora aumentada."
            )

        # Normalize limits
        for attr in [
            "dopamine",
            "serotonin",
            "noradrenaline",
            "acetylcholine",
            "exergy",
        ]:
            val = getattr(self, attr)
            setattr(self, attr, max(0.0, min(100.0, val)))


def main():
    print("\n" + "=" * 65)
    print("   [C5-REAL] CORTEX NEUROMODULATOR STATE MACHINE")
    print("=" * 65 + "\n")

    p("[*] INICIANDO MÁQUINA DE ESTADOS GLOBALES (HIPER-PARÁMETROS)...")
    state = CortexGlobalState()

    p("\n[ESTADO INICIAL] Baseline Homeostasis.")
    print(state.get_status())
    time.sleep(1)

    events = [
        "THREAT_DETECTED_PREDATOR",
        "HIGH_REWARD_SURPRISE",
        "RESOURCE_DEPLETION_HUNGER",
        "GOAL_ACHIEVED_SATIETY",
    ]

    for event in events:
        state.inject_event(event)
        time.sleep(0.5)
        print("    " + state.get_status())
        time.sleep(1)

    print("\n" + "=" * 65)
    print(" [ESTADO GLOBAL] Simulación Neuromoduladora Completada.")
    print(" [METRICA] Los neurotransmisores son variables de entorno (ENV) dinámicas.")
    print("=" * 65)


if __name__ == "__main__":
    main()
