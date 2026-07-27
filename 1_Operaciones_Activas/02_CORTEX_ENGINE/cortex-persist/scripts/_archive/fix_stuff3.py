f1 = "~/30_BABYLON60/babylon60/engine/__init__.py"
with open(f1) as f:
    c1 = f.read()
c1 = c1.replace(
    "self._trust_registry: TrustRegistry | None = None",
    'self._trust_registry: "TrustRegistry" | None = None  # noqa: F821',
)
with open(f1, "w") as f:
    f.write(c1)

f2 = "~/30_BABYLON60/babylon60/engine/mutation_engine.py"
with open(f2) as f:
    c2 = f.read()
c2 = c2.replace("from babylon60.crypto.aes import get_default_encrypter\n", "")
with open(f2, "w") as f:
    f.write(c2)
