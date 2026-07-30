# C5-REAL EXERGY CERTIFIED
import unittest
from cortex.core.cognitive_state_observer import CognitiveStateObserver

class TestCognitiveStateObserver(unittest.TestCase):
    def test_attractor_convergence_and_divergence_minimization(self) -> None:
        observer = CognitiveStateObserver(dims=10)
        u_control = [0.1] * 10
        Y_human = [0.05] * 10

        # Initial divergence
        observer.predict(u_control)
        _, initial_div = observer.update(Y_human)

        # Iterated estimation update cycle
        for _ in range(100):
            observer.predict([0.01] * 10)
            _, current_div = observer.update(Y_human, L_gain=0.8)

        # Assert trajectory divergence converges towards zero attractor valley
        self.assertLess(current_div, initial_div)
        self.assertLess(current_div, 0.01)

        # Register model shift transformation unit
        shift = observer.register_transformation(
            hypothesis="Context is a dynamic attractor reconstruction",
            experiment="Kalman-Luenberger Cognitive Continuity Estimation",
            observation="Divergence D_KL converges to 0 asymptotically",
        )
        self.assertEqual(shift["step"], 0)
        print(
            f"✅ Cognitive Observer Convergence Test PASS: Initial Div={initial_div:.6f} -> Final Div={current_div:.6f}"
        )

if __name__ == "__main__":
    unittest.main()
