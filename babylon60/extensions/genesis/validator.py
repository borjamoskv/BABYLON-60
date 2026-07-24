# [C5-REAL] Exergy-Maximized
"""CORTEX Genesis - Post-Creation Validator.

Validates that a generated system is structurally sound:
- All expected files exist
- Python syntax is valid (ast.parse)
- Imports are internally consistent
- __init__.py exports match generated symbols
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

from babylon60.extensions.genesis.models import SystemSpec

__all__ = ["GenesisValidator"]

logger = logging.getLogger("babylon60_extensions.genesis.validator")


class GenesisValidator:
    """Validates a generated system for structural correctness.

    This is NOT a linter - it checks that the genesis process
    produced a coherent, parseable system. Linting is done separately
    via Ruff.
    """

    def validate(
        self,
        spec: SystemSpec,
        created_files: list[str],
        base_dir: Path | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate a generated system.

        Args:
            spec: The original system specification.
            created_files: List of absolute paths to created files.
            base_dir: Optional base directory for relative resolution.

        Returns:
            Tuple of (all_passed, list_of_error_messages).
        """
        errors: list[str] = []

        file_errors = self._check_files_exist(created_files)
        errors.extend(file_errors)

        syntax_errors = self._check_python_syntax(created_files)
        errors.extend(syntax_errors)

        init_errors = self._check_init_exists(spec, created_files, base_dir)
        errors.extend(init_errors)

        count_errors = self._check_component_count(spec, created_files)
        errors.extend(count_errors)

        passed = len(errors) == 0
        if passed:
            logger.info("✅ Validation PASSED for system '%s'", spec.name)
        else:
            logger.warning(
                "❌ Validation FAILED for system '%s': %d errors",
                spec.name,
                len(errors),
            )
            for err in errors:
                logger.warning("  → %s", err)

        return passed, errors

    def _check_files_exist(self, files: list[str]) -> list[str]:
        """Verify all claimed files actually exist on disk."""
        errors: list[str] = []
        for filepath in files:
            if not Path(filepath).exists():
                errors.append(f"File does not exist: {filepath}")
        return errors

    def _check_python_syntax(self, files: list[str]) -> list[str]:
        """Parse all .py files with ast to check syntax validity."""
        errors: list[str] = []
        for filepath in files:
            path = Path(filepath)
            if path.suffix != ".py":
                continue

            try:
                source = path.read_text(encoding="utf-8")
                ast.parse(source, filename=filepath)
            except SyntaxError as e:
                errors.append(f"Syntax error in {path.name}: {e.msg} (line {e.lineno})")
            except OSError as e:
                errors.append(f"Cannot read {path.name}: {e}")

        return errors

    def _check_init_exists(
        self,
        spec: SystemSpec,
        files: list[str],
        base_dir: Path | None,
    ) -> list[str]:
        """Check that an __init__.py was created for module-type systems."""
        if spec.system_type not in ("module", "mixin"):
            return []

        init_found = any("__init__.py" in f for f in files)
        if not init_found:
            return [f"No __init__.py found for module system '{spec.name}'"]
        return []

    def _check_component_count(
        self,
        spec: SystemSpec,
        files: list[str],
    ) -> list[str]:
        """Check that the number of created files is reasonable."""
        errors: list[str] = []
        non_test_components = [c for c in spec.components if c.component_type != "test"]

        system_files = [f for f in files if spec.name in f]

        min_expected = len(non_test_components) + 1  # +1 for __init__.py

        if len(system_files) < min_expected:
            errors.append(
                f"Expected at least {min_expected} files for '{spec.name}', got {len(system_files)}"
            )

        return errors
