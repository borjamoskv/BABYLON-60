from __future__ import annotations
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar
__all__ = ['Err', 'Ok', 'Result', 'safe', 'safe_async']
T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')

@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:
        return self.value

    def map(self, fn: Callable[[T], U]) -> Result[U, Any]:
        return Ok(fn(self.value))

    def flat_map(self, fn: 'Callable[[T], Result[U, Any]]') -> Result[U, Any]:
        return fn(self.value)

    def map_err(self, _fn: Callable[[Any], Any]) -> Ok[T]:
        return self

    def __repr__(self) -> str:
        return f'Ok({self.value!r})'

@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> Any:
        raise ValueError(f'Called unwrap() on Err: {self.error}')

    def unwrap_or(self, default: Any) -> Any:
        return default

    def map(self, _fn: 'Callable[..., Any]') -> Err[E]:
        return self

    def flat_map(self, _fn: 'Callable[..., Any]') -> Err[E]:
        return self

    def map_err(self, fn: Callable[[E], U]) -> Err[U]:
        return Err(fn(self.error))

    def __repr__(self) -> str:
        return f'Err({self.error!r})'
Result = Ok[T] | Err[E]

def safe(fn: Callable[..., T]) -> Callable[..., Result[T, str]]:

    def wrapper(*args: Any, **kwargs: Any) -> Result[T, str]:
        try:
            return Ok(fn(*args, **kwargs))
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as exc:
            tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
            return Err(f"{type(exc).__name__}: {exc}\n{''.join(tb[-3:])}")
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper

def safe_async(fn: Callable[..., Any]) -> Callable[..., Any]:

    async def wrapper(*args: Any, **kwargs: Any) -> Result[T, str]:
        try:
            return Ok(await fn(*args, **kwargs))
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as exc:
            tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
            return Err(f"{type(exc).__name__}: {exc}\n{''.join(tb[-3:])}")
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper