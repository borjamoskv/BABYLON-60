import re

# 1. babylon60/engine/__init__.py
f1 = "~/30_BABYLON60/babylon60/engine/__init__.py"
with open(f1) as f:
    c1 = f.read()


# Fix B025
def fix_except(match):
    # Match has two except Exception as e blocks. We keep the second one (which raises)
    return match.group(1)


# Look for except Exception as e:\n ... \n except Exception as e:\n ...
pat = re.compile(
    r"(?:\s*except Exception as e:\s*logger\.debug\([^\)]+\))+(\s*except Exception as e:.*?(?=\s*(?:try:|#|logger|return|self|\Z)))",
    re.DOTALL,
)
c1 = pat.sub(r"\1", c1)

# Fix TrustRegistry F821
c1 = c1.replace(
    "self._trust_registry: TrustRegistry | None = None",
    'self._trust_registry: "TrustRegistry" | None = None',
)

with open(f1, "w") as f:
    f.write(c1)


# 2. babylon60/engine/mutation_engine.py
f2 = "~/30_BABYLON60/babylon60/engine/mutation_engine.py"
with open(f2) as f:
    c2 = f.read()

# Fix get_default_encrypter F821
if (
    "get_default_encrypter" in c2
    and "from babylon60." not in c2.split("class FactMutationEngine:")[0]
):
    # we need to import it. Let's find where it comes from first
    pass
