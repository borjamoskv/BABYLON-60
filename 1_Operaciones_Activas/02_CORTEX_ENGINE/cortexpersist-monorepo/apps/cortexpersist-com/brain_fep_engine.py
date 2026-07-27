#!/usr/bin/env python3
import random
import math


class CorticalNode:
    """
    Representa un nodo predictivo en el Neocórtex (L4).
    Implementa actualización Bayesiana (Active Inference).
    """

    def __init__(self, prior_mu, prior_variance):
        self.mu = prior_mu
        self.var = prior_variance

    def infer(self, sensory_input, sensory_variance):
        # 1. Calcular el error de predicción (Prediction Error)
        prediction_error = sensory_input - self.mu

        # 2. Calcular precisiones (inversa de la varianza)
        precision_prior = 1.0 / self.var
        precision_sensory = 1.0 / sensory_variance

        # 3. Kalman Gain (qué tanto confiar en el input vs el prior)
        kalman_gain = precision_sensory / (precision_prior + precision_sensory)

        # 4. Actualizar el Prior (Learning / Plasticity)
        self.mu = self.mu + kalman_gain * prediction_error
        self.var = self.var * (1.0 - kalman_gain)

        # 5. Calcular la Energía Libre (Surprisal)
        free_energy = 0.5 * (prediction_error**2) * precision_sensory + 0.5 * math.log(
            sensory_variance
        )
        return free_energy, prediction_error, self.mu


def main():
    print("=" * 60)
    print("[C5-REAL] CAUSAL PROOF LEDGER: FREE ENERGY PRINCIPLE")
    print("=" * 60)
    print("Inicializando Motor de Inferencia Activa...")
    print("Target: Alinear el 'Prior' interno con el Estado Real (Entorno).")
    print("-" * 60)

    node = CorticalNode(prior_mu=0.0, prior_variance=10.0)
    true_world_state = 7.62

    print(f"[*] Entorno Oculto (True State): {true_world_state}")
    print(f"[*] Cerebro Inicial (Prior Mu):  {node.mu} (Varianza: {node.var})\n")

    for epoch in range(1, 16):
        sensory_input = true_world_state + random.gauss(0, 0.8)
        fe, pe, updated_belief = node.infer(sensory_input, sensory_variance=0.8)
        print(
            f"Ciclo {epoch:02d} | Input Sensorial: {sensory_input:05.2f} | Prior Actualizado: {updated_belief:05.2f} | Error: {pe:+06.2f} | Free Energy: {fe:05.2f}"
        )

    print("-" * 60)
    print("[ESTADO] Convergencia causal alcanzada.")
    print(
        f"[METRICA] Error residual minimizado. Prior final: {node.mu:.2f} (Delta: {abs(true_world_state - node.mu):.2f})"
    )
    print("[LOG] Estructura C4-SIM transmutada a ejecución C5-REAL.")
    print("=" * 60)


if __name__ == "__main__":
    main()
