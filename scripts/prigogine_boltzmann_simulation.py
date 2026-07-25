import hashlib
import json
import math
import random
from typing import Any


def run_boltzmann_entropy_simulation(steps: int = 200, num_particles: int = 1000) -> list[dict[str, Any]]:
    grid_size = 10
    particles = [[0, 0] for _ in range(num_particles)]
    history = []
    for step in range(steps):
        counts: dict[tuple[int, int], int] = {}
        for x, y in particles:
            counts[x, y] = counts.get((x, y), 0) + 1
        entropy = 0.0
        for _pos, count in counts.items():
            p = count / num_particles
            entropy -= p * math.log(p)
        history.append({"step": step, "entropy": round(entropy, 5), "unique_cells_occupied": len(counts)})
        for i in range(num_particles):
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0), (0, 0)])
            particles[i][0] = (particles[i][0] + dx) % grid_size
            particles[i][1] = (particles[i][1] + dy) % grid_size
    return history


def run_prigogine_brusselator(
    steps: int = 2000, dt: float = 0.01, a: float = 1.0, b: float = 3.0
) -> list[dict[str, Any]]:
    x = 1.5
    y = 2.0
    history = []
    for step in range(steps):
        if step % 10 == 0:
            history.append({"step": step, "x": round(x, 5), "y": round(y, 5), "r": round(math.sqrt(x**2 + y**2), 5)})
        dx = (a + x**2 * y - b * x - x) * dt
        dy = (b * x - x**2 * y) * dt
        x += dx
        y += dy
    return history


def main() -> None:
    random.seed(42)
    b_history = run_boltzmann_entropy_simulation()
    p_history = run_prigogine_brusselator()
    results = {
        "boltzmann_entropy_final": b_history[-1]["entropy"],
        "boltzmann_entropy_initial": b_history[0]["entropy"],
        "prigogine_final_x": p_history[-1]["x"],
        "prigogine_final_y": p_history[-1]["y"],
        "brusselator_stable_orbit_detected": len(set(round(h["x"], 1) for h in p_history[-50:])) <= 5,
    }
    payload = json.dumps(results, sort_keys=True)
    results_hash = hashlib.sha3_256(payload.encode()).hexdigest()
    output = {
        "metadata": {
            "author": "borjamoskv",
            "timestamp": "2026-07-17T19:25:00Z",
            "cortex_taint": f"borjamoskv:prigogine_boltzmann:{results_hash[:16]}",
        },
        "results": results,
        "results_hash": results_hash,
        "boltzmann_sample": b_history[::40],
        "prigogine_sample": p_history[::40],
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
