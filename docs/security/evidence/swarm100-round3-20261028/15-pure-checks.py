"""Reviewer 15: isolated Python/AST/mathematical checks, no product entrypoints."""
import ast
import json
import math
from pathlib import Path
import tempfile

ROOT = Path(__file__).absolute().parents[4]
RESULTS = []


def load_definitions(relative_path):
    path = ROOT / relative_path
    tree = ast.parse(path.read_text())
    tree.body = [node for node in tree.body if not isinstance(node, ast.If)]
    namespace = {"__name__": "reviewer15_isolated", "__file__": str(path)}
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace


pruner = load_definitions("01_KISH_ENGINE/babylon60/core/thermo_ast_pruner.py")
with tempfile.TemporaryDirectory(prefix="reviewer15-") as temporary:
    specimen = Path(temporary) / "docstring.py"
    specimen.write_text('def f():\n    "only docstring"\n')
    pruner["transmute_file"](str(specimen))
    generated = specimen.read_text()
    try:
        compile(generated, str(specimen), "exec")
        raise AssertionError("Expected empty suite to fail parsing")
    except SyntaxError as error:
        RESULTS.append({"candidate_id": "SW100-C0243", "generated": generated,
                        "observed": type(error).__name__, "passed": True})

source = "import os as operating\nimport signal as sig\ntry:\n    risky()\nexcept Exception:\n    pass\n"
tree = pruner["AnergiaPurger"]().visit(ast.parse(source))
text = ast.unparse(ast.fix_missing_locations(tree))
bindings = sorted(alias.asname or alias.name for node in tree.body
                  if isinstance(node, ast.Import) for alias in node.names)
assert "os" not in bindings and "signal" not in bindings
assert "os.kill(os.getpid(), signal.SIGKILL)" in text
RESULTS.append({"candidate_id": "SW100-C0244", "bindings": bindings,
                "generated": text, "passed": True,
                "scope": "Transformed AST inspected; kill handler was never executed."})

swarm = load_definitions("01_KISH_ENGINE/babylon60/bft/bayesian_swarm.py")["BayesianSwarm"](["a", "b"])
opinions = {"a": {"yes": 0.8, "no": 0.2}, "b": {"yes": 0.0, "no": 1.0}}
actual = swarm.logarithmic_opinion_pool(opinions, {"a": 1.0, "b": 0.0})
missing = swarm.logarithmic_opinion_pool(opinions, {"a": 1.0})
baseline = swarm.logarithmic_opinion_pool({"a": opinions["a"]}, {"a": 1.0})
assert actual["yes"] == 0 and missing["yes"] == 0 and baseline["yes"] > 0.79
RESULTS.append({"candidate_id": "SW100-C0346", "with_zero_weight": actual,
                "with_missing_weight": missing, "without_excluded_agent": baseline, "passed": True})

lean = load_definitions("scripts/c5_verifiers/inject_lean4_stubs.py")
axioms, theorems = lean["extract_axioms_and_theorems"]("Teorema 1: Every natural number equals zero\n")
code = lean["generate_lean_code"]("Counterexample", axioms, theorems)
assert ": True := by\n  trivial" in code
RESULTS.append({"candidate_id": "SW100-C0569", "input": theorems, "generated": code,
                "passed": True, "scope": "Generator only; no Lean compiler or proof runtime executed."})

# Analytic continuous sinusoid below Nyquist; sample values miss its maxima.
# x(t)=1.2*sin(pi*t/2 + pi/4); integer samples have absolute value 1.2/sqrt(2).
sample_peak = 1.2 / math.sqrt(2)
ceiling = 10 ** (-1 / 20)
gain = min(1.0, ceiling / sample_peak)
true_peak_after_gain = 1.2 * gain
assert sample_peak * gain < ceiling and true_peak_after_gain > 1.0
RESULTS.append({"candidate_id": "SW100-C0546", "sample_peak": sample_peak,
                "ceiling": ceiling, "documented_gain": gain,
                "analytic_true_peak_after_gain": true_peak_after_gain, "passed": True,
                "scope": "Pure mathematical counterexample to the documented formula; no audio runtime."})
print(json.dumps({"scope": "Isolated stdlib checks; product entrypoints, native runtimes, operator data and network untouched.",
                  "results": RESULTS}, indent=2))
