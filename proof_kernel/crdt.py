from typing import Any

from proof_kernel.canonicalizer import hash_evidence


class LWWRegister:
    def __init__(self, value: Any, lamport: int):
        self.value = value
        self.lamport = lamport

    def merge(self, other: "LWWRegister") -> "LWWRegister":
        if self.lamport > other.lamport:
            return self
        elif other.lamport > self.lamport:
            return other
        else:
            h_self = hash_evidence(self.value)
            h_other = hash_evidence(other.value)
            return self if h_self >= h_other else other

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "lamport": self.lamport}


class CRDTMap:
    def __init__(self, state: dict[str, LWWRegister] | None = None):
        self.state = state or {}

    def set(self, key: str, value: Any, lamport: int) -> None:
        new_reg = LWWRegister(value, lamport)
        if key in self.state:
            self.state[key] = self.state[key].merge(new_reg)
        else:
            self.state[key] = new_reg

    def get(self, key: str) -> Any:
        return self.state[key].value if key in self.state else None

    def merge(self, other: "CRDTMap") -> "CRDTMap":
        merged = CRDTMap(dict(self.state))
        for k, v in other.state.items():
            if k in merged.state:
                merged.state[k] = merged.state[k].merge(v)
            else:
                merged.state[k] = v
        return merged

    def measure_entropy(self, max_entropy_microbits: int = 1000000) -> int:
        from proof_kernel.canonicalizer import canonicalize_cbor

        cbor_bytes = canonicalize_cbor(self.to_dict())
        info_density = len(cbor_bytes) * 100
        residual = max_entropy_microbits - info_density
        return max(0, residual)

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self.state.items()}
