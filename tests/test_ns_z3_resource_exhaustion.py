"""Real solver exhaustion must remain distinct from a proof of contradiction."""

from collections.abc import Callable
import struct

import pytest
import z3
from babylon60.kernel.ns_z3_firewall import NavierStokesZ3Firewall, SmtApoptosisError


class ResourceLimitedFirewall(NavierStokesZ3Firewall):
    def _create_solver(self) -> z3.Solver:
        solver = super()._create_solver()
        solver.set(rlimit=1)
        return solver


@pytest.mark.parametrize("operation", ["strain", "dissipation", "canary", "trace", "core"])
def test_resource_exhaustion_is_not_a_contradiction(operation: str) -> None:
    firewall = ResourceLimitedFirewall()
    calls: dict[str, Callable[[], object]] = {
        "strain": lambda: firewall.verify_strain_sos_bound(1, 1, -2, 0.5, 0, 0.5, 5),
        "dissipation": lambda: firewall.verify_lyapunov_dissipation(1, 0.985, 10, 0.05, 0.01),
        "canary": lambda: firewall.verify_taylor_green_canary(0, 1, 1, 0.05),
        "trace": lambda: firewall.verify_causality_trace([(0, 0, 2)]),
        "core": lambda: firewall.extract_fluid_unsat_core(0, 0, 0),
    }
    with pytest.raises(SmtApoptosisError, match="Z3_INCONCLUSIVE: .+"):
        calls[operation]()


def test_cli_rejects_unknown_without_claiming_a_paradox(capsys: pytest.CaptureFixture[str]) -> None:
    assert ResourceLimitedFirewall.eval_trace_bytes(struct.pack("<Q", 2)) == 1
    output = capsys.readouterr().out
    assert "Z3_INCONCLUSIVE:" in output
    assert "Z3_OK" not in output
    assert "Z3_PARADOX" not in output


def test_functional_trace_budget_does_not_change_production_default() -> None:
    assert NavierStokesZ3Firewall().timeout_ms == 50
    valid = struct.pack("<Q", 2)
    assert NavierStokesZ3Firewall.eval_trace_bytes(valid, timeout_ms=5000) == 0
    inverted = struct.pack("<QQ", (2 << 32) | 2, (1 << 32) | 2)
    assert NavierStokesZ3Firewall.eval_trace_bytes(inverted, timeout_ms=5000) == 2
