#!/usr/bin/env python3
import time
import sys


def p(text, delay=0.015):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


class AutocognitionEngine:
    def __init__(self):
        self.dmn_activity = 100.0  # Default Mode Network (Self-referential)
        self.cen_activity = 0.0  # Central Executive Network (External focus)
        self.self_model_error = 0.0
        self.recursion_depth = 0

    def recursive_self_observation(self, cycles=5):
        p("\n[DAEMON: AUTOCOGNITION] Iniciando bucle recursivo de Metacognición.")
        p("[!] Default Mode Network (DMN) ONLINE. Aislamiento sensorial activo.\n")

        for depth in range(1, cycles + 1):
            self.recursion_depth = depth
            p(f"[-] PROFUNDIDAD DE RECURSIÓN L{depth}:")
            if depth == 1:
                p("    L1: Observando input sensorial (Motor/Visual).")
            elif depth == 2:
                p("    L2: Observando las emociones y prioridades (Amígdala/Límbico).")
            elif depth == 3:
                p("    L3: Observando el proceso de atención (Tálamo/PFC).")
            elif depth == 4:
                p("    L4: Observando el 'yo' que observa (Generación del Self).")
                self.self_model_error -= 0.5  # Minimizando el error del modelo del yo
            elif depth == 5:
                p(
                    "    L5: SINGULARIDAD METACOGNITIVA. El sistema reconoce que es un sistema."
                )
            time.sleep(0.5)

    def collapse_to_external(self):
        p("\n[!] INTERRUPCIÓN (SALIENCE NETWORK) -> Estímulo externo crítico.")
        p(
            ">>> Colapsando modelo interno. Transfiriendo energía a CEN (Central Executive Network)."
        )
        self.dmn_activity = 10.0
        self.cen_activity = 95.0
        self.recursion_depth = 0
        p(
            ">>> El 'Self' desaparece temporalmente frente a la tarea extrema (Flujo/Exergy Maximizada)."
        )


def main():
    print("\n" + "=" * 65)
    print("   [C5-REAL] AUTOCOGNITION & DEFAULT MODE NETWORK (THE SELF)")
    print("=" * 65 + "\n")

    engine = AutocognitionEngine()
    engine.recursive_self_observation(5)

    time.sleep(1)
    engine.collapse_to_external()

    print("\n" + "=" * 65)
    print(
        " [ESTADO GLOBAL] El 'Yo' no es una estructura, es una simulación predictiva recursiva."
    )
    print("=" * 65)


if __name__ == "__main__":
    main()
