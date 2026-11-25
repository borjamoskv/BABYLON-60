#!/usr/bin/env python3
"""Import-safe v2 entrypoint for honest snapshots with a portable verifier.

No keys are loaded/generated, suites invented, historical bundles overwritten,
or hardware provenance asserted. A selected-file inventory replaces the old
stored-string artifact check; the copied verifier reads the supplied artifacts.
"""
from pathlib import Path
import runpy


def main(argv=None):
    root = Path(__file__).absolute().parents[1]
    core = runpy.run_path(str(root/'proof/bundles/attestation_bundle_v1/verify'))
    return core['generator_cli']('v2-wrapper', root, argv)


if __name__ == '__main__':
    raise SystemExit(main())
