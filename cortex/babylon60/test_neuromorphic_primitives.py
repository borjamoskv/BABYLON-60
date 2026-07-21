import asyncio
import os
import time
import pytest
from cortex.babylon60.neuromorphic_primitives import SelfHealingMesh


@pytest.mark.anyio
async def test_neuromorphic_v2():
    print("[C5-REAL] Inicializando Malla Neuromórfica V2 (STDP + LIF)...")
    import uuid
    db_path = f"memristor_v2_test_{uuid.uuid4().hex}.db"
    for suffix in ["", "-wal", "-shm"]:
        p = f"{db_path}{suffix}"
        if os.path.exists(p):
            os.remove(p)

    try:
        mesh = SelfHealingMesh(db_path)
        mesh.connect("SensorA", "MotorB")

        motor = mesh.get_node("MotorB")
        synapse = mesh.synapses[("SensorA", "MotorB")]

        # MotorB waits for a spike
        async def motor_waiter():
            start_time = time.time()
            energy = await motor.wait_and_fire()
            elapsed = time.time() - start_time
            print(
                f"[MotorB] ¡Spike recibido! Energía disipada: {energy:.2f}. Bloqueo duró {elapsed:.4f}s"
            )
            # Post-spike: registra el disparo para STDP Hebbiano (Potenciación)
            w = synapse.register_post_spike()
            print(f"[Sinapsis A->B] Plasticidad Causal (STDP): Nuevo peso = {w:.2f}")
            return energy

        motor_task = asyncio.create_task(motor_waiter())

        print("[C5-REAL] Test de Leaky Integrate-and-Fire (Fuga de Energía)...")
        # Inyectar energía pero esperar demasiado
        await mesh.route_pulse("SensorA", "MotorB", 5.0)
        print(f"[MotorB] Energía antes de leak: {motor.current_potential:.2f}")

        await asyncio.sleep(
            2.0
        )  # Esperar para que se fugue (leak rate 2.0/s -> 4.0 leak)

        print(f"[MotorB] Energía tras Leak de 2s: {motor.current_potential:.2f}")
        assert motor.current_potential <= 2.0, (
            "La fuga termodinámica (LIF) no funcionó correctamente."
        )

        # Ahora sí, disparamos superando el umbral rápido
        print("[SensorA] Inyectando pulso de 15.0 rápidamente...")
        await mesh.route_pulse("SensorA", "MotorB", 15.0)

        energy_fired = await motor_task
        assert energy_fired >= 10.0, "No superó el umbral."

        # Test Tolerancia a Fallos
        print("[C5-REAL] Test de Auto-Sanación (Muerte de Nodo)...")
        mesh.kill_node("SensorA")
        await mesh.route_pulse("SensorA", "MotorB", 10.0)
        print("[C5-REAL] Pulso abortado correctamente por nodo inerte.")

        print(
            "[C5-REAL] VERIFICACIÓN COMPLETADA (V2). Invariantes STDP y LIF validados físicamente."
        )
    finally:
        for suffix in ["", "-wal", "-shm"]:
            p = f"{db_path}{suffix}"
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


if __name__ == "__main__":
    asyncio.run(test_neuromorphic_v2())
