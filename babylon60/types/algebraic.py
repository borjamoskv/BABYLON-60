from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, NoReturn, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T
    causal_taint: str = "borjamoskv:adt_ok_c5"


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E
    causal_taint: str = "borjamoskv:adt_err_c5"


Result = Ok[T] | Err[E]


@dataclass(frozen=True)
class Some(Generic[T]):
    value: T
    causal_taint: str = "borjamoskv:adt_some_c5"


@dataclass(frozen=True)
class Nothing:
    causal_taint: str = "borjamoskv:adt_nothing_c5"


Option = Some[T] | Nothing


class AlgebraicCardinality:
    @staticmethod
    def sum_type_cardinality(*sub_cardinalities: int) -> int:
        return sum(sub_cardinalities)

    @staticmethod
    def product_type_cardinality(*sub_cardinalities: int) -> int:
        total = 1
        for card in sub_cardinalities:
            total *= card
        return total

    @staticmethod
    def exponential_type_cardinality(domain_cardinality: int, codomain_cardinality: int) -> int:
        return codomain_cardinality**domain_cardinality


def make_illegal_states_unrepresentable(value: NoReturn) -> NoReturn:
    raise RuntimeError(f"[C5-FAIL] Reached unreachable algebraic state: {value!r}")
