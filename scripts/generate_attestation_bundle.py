#!/usr/bin/env python3
"""Import-safe v1 entrypoint for new unsigned snapshots, never legacy re-signing."""
from pathlib import Path
import runpy


def main(argv=None):
    root = Path(__file__).absolute().parents[1]
    core = runpy.run_path(str(root/'proof/bundles/attestation_bundle_v1/verify'))
    return core['generator_cli']('v1-wrapper', root, argv)


if __name__ == '__main__':
    raise SystemExit(main())
