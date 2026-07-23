import yaml

path = "primitives/896_categorical_logic_primitives.yml"
with open(path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

prims = data["primitives"]
domains = data["domains"]

assert len(prims) == 896, f"Expected 896 primitives, got {len(prims)}"

ids = [p["id"] for p in prims]
codes = [p["code"] for p in prims]

assert len(ids) == len(set(ids)), "Duplicate primitive IDs detected!"
assert len(codes) == len(set(codes)), "Duplicate primitive codes detected!"
assert min(ids) == 1 and max(ids) == 896, f"ID bounds check failed: min={min(ids)}, max={max(ids)}"

print(f"VERIFICATION PASSED: Exactly 896 unique, valid primitives loaded from {path}")
