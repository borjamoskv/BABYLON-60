# [C5-REAL] Exergy-Maximized
"""CLI bootstrap with tolerant command-module loading.

This keeps the root CLI usable even when some subcommand modules are
temporarily broken by unresolved merge conflicts elsewhere in the tree.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path

from babylon60.cli.common import cli

logger = logging.getLogger(__name__)

_COMMAND_MODULE_SUFFIX = "_cmds"
_COMMAND_DIR = Path(__file__).parent
_LEGACY_COMMAND_MODULES = (
    "crud",
    "ledger",
    "purge",
    "slow_tip",
    "vote_ledger",
    "apoptosis",
    "telemetry",
)


def _discover_command_modules() -> list[str]:
    modules: set[str] = set()
    for module_info in pkgutil.iter_modules([str(_COMMAND_DIR)]):
        if module_info.ispkg:
            continue
        if module_info.name.endswith(_COMMAND_MODULE_SUFFIX):
            modules.add(module_info.name)

    for module_name in _LEGACY_COMMAND_MODULES:
        if (_COMMAND_DIR / f"{module_name}.py").exists():
            modules.add(module_name)

    return sorted(modules)


def _load_command_modules() -> tuple[list[str], dict[str, str]]:
    loaded: list[str] = []
    failed: dict[str, str] = {}

    for module_name in _discover_command_modules():
        full_name = f"babylon60.cli.{module_name}"
        try:
            importlib.import_module(full_name)
            loaded.append(module_name)
        except Exception as err:  # noqa: BLE001
            failed[module_name] = f"{type(err).__name__}: {err}"
            logger.debug("Skipping CLI module %s: %s", full_name, err)

    return loaded, failed


LOADED_COMMAND_MODULES: list[str] = []
FAILED_COMMAND_MODULES: dict[str, str] = {}


class LazyCommandsDict(dict):
    """A dictionary that lazily triggers command module loading on access."""

    def __init__(self, command_to_module: dict[str, str]) -> None:
        self._command_to_module = command_to_module
        super().__init__()

    def __bool__(self) -> bool:
        return True

    def _load_command(self, cmd_name: str) -> None:
        module_name = self._command_to_module.get(cmd_name)
        if (
            module_name
            and module_name not in LOADED_COMMAND_MODULES
            and module_name not in FAILED_COMMAND_MODULES
        ):
            full_name = f"babylon60.cli.{module_name}"
            try:
                importlib.import_module(full_name)
                LOADED_COMMAND_MODULES.append(module_name)
            except Exception as err:  # noqa: BLE001
                FAILED_COMMAND_MODULES[module_name] = f"{type(err).__name__}: {err}"
                logger.debug("Skipping CLI module %s: %s", full_name, err)

    def __getitem__(self, key):
        if key in self._command_to_module:
            self._load_command(key)
        return super().__getitem__(key)

    def __delitem__(self, key) -> None:
        in_module_map = key in self._command_to_module
        if in_module_map:
            del self._command_to_module[key]
        if super().__contains__(key):
            super().__delitem__(key)
        elif not in_module_map:
            raise KeyError(key)

    def pop(self, key, *args):
        if key in self._command_to_module:
            self._load_command(key)
            del self._command_to_module[key]
        return super().pop(key, *args)

    def __len__(self) -> int:
        return len(set(self._command_to_module.keys()) | set(super().keys()))

    def __contains__(self, key) -> bool:
        return key in self._command_to_module or super().__contains__(key)

    def __iter__(self):
        return iter(set(self._command_to_module.keys()) | set(super().keys()))

    def keys(self):
        return set(self._command_to_module.keys()) | set(super().keys())

    def values(self):
        for cmd_name in list(self._command_to_module.keys()):
            self._load_command(cmd_name)
        return super().values()

    def items(self):
        for cmd_name in list(self._command_to_module.keys()):
            self._load_command(cmd_name)
        return super().items()

    def get(self, key, default=None):
        if key in self._command_to_module:
            self._load_command(key)
        return super().get(key, default)


# Build command to module map
command_to_module: dict[str, str] = {}
for mname in _discover_command_modules():
    cmd_name = mname[:-5] if mname.endswith(_COMMAND_MODULE_SUFFIX) else mname
    command_to_module[cmd_name] = mname
    if "_" in cmd_name:
        command_to_module[cmd_name.replace("_", "-")] = mname
    if cmd_name == "ledger":
        command_to_module["trust-ledger"] = mname
    elif cmd_name == "verification":
        command_to_module["verify-files"] = mname
        command_to_module["verify-ledger"] = mname
    elif cmd_name == "public_verifier":
        command_to_module["verify-ledger-export"] = mname
    elif cmd_name == "public_export":
        command_to_module["export-ledger"] = mname
    elif cmd_name == "verify":
        command_to_module["verify-bundle"] = mname
    elif cmd_name == "crud":
        command_to_module["list"] = mname
        command_to_module["edit"] = mname
        command_to_module["delete"] = mname
        command_to_module["inspect"] = mname
    elif cmd_name == "sync":
        command_to_module["export"] = mname
        command_to_module["writeback"] = mname
        command_to_module["obsidian"] = mname

# Preserve any commands already registered, then replace with lazy loader.
existing_commands = cli.commands
if type(existing_commands).__name__ != "LazyCommandsDict":
    cli.commands = LazyCommandsDict(command_to_module)
    if existing_commands:
        cli.commands.update(existing_commands)

# Backward compatibility attributes
cli.loaded_command_modules = LOADED_COMMAND_MODULES  # type: ignore[attr-defined]
cli.failed_command_modules = FAILED_COMMAND_MODULES  # type: ignore[attr-defined]

__all__ = ["FAILED_COMMAND_MODULES", "LOADED_COMMAND_MODULES", "cli"]
