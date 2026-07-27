# [C5-REAL] Exergy-Maximized
"""Base-60 CLI subcommands with auto-detecting transducer."""

from __future__ import annotations

import uuid

import click

from babylon60.cli.common import cli, console
from babylon60.utils.base60 import (
    BASE60_ALPHABET,
    base60_check_to_bytes,
    base60_to_bytes,
    bytes_to_base60,
    bytes_to_base60_check,
    encoded_length,
)

BASE60_SET = set(BASE60_ALPHABET)

# Canonical widths (single source of truth: encoded_length).
# All detection widths are pairwise distinct -> zero routing ambiguity.
_HASH_HEX_LEN = 64
_HASH_B60_LEN = encoded_length(32)  # 44
_HASH_CHECK_LEN = encoded_length(32 + 2)  # 47
_UUID_B60_LEN = encoded_length(16)  # 22
_UUID_CHECK_LEN = encoded_length(16 + 2)  # 25


def _is_hex(s: str) -> bool:
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def _is_base60(s: str) -> bool:
    return all(char in BASE60_SET for char in s)


@cli.group(name="base60")
def base60_group():
    """Operations using the Base-60 (sexagesimal) representation.

    Residual visual ambiguity (0/o, 1/I) is acknowledged; transcription errors
    are detected via Base60Check (Detection > Prevention).
    """
    pass


@base60_group.command(name="convert")
@click.argument("val")
def convert_cmd(val: str):
    """Unified transducer: automatically converts hashes/UUIDs between Hex and Base-60.

    Auto-detects (by canonical width, all pairwise distinct):
      - 64-char Hex SHA-256 hash -> encodes to 44-char Base-60
      - 47-char Base60Check hash -> verifies checksum, decodes to 64-char Hex
      - 44-char Base-60 SHA-256 hash -> decodes to 64-char Hex
      - 36-char / 32-char Hex UUID -> encodes to 22-char Base-60
      - 25-char Base60Check UUID -> verifies checksum, decodes to standard UUID
      - 22-char Base-60 UUID -> decodes to standard UUID string
    """
    cleaned = val.strip()

    # Case 1: 64-character Hex Hash -> Base-60
    if len(cleaned) == _HASH_HEX_LEN and _is_hex(cleaned):
        try:
            raw_bytes = bytes.fromhex(cleaned)
            encoded = bytes_to_base60(raw_bytes)
            console.print(f"[bold green]▶ Base-60 Hash (SHA-256):[/bold green] {encoded}")
            return
        except ValueError as e:
            click.secho(f"Hex parsing error: {e}", fg="red", err=True)
            return

    # Case 2: 47-character Base60Check Hash -> Hex (checksum verified)
    if len(cleaned) == _HASH_CHECK_LEN and _is_base60(cleaned):
        try:
            raw_bytes = base60_check_to_bytes(cleaned, 32)
            console.print(
                f"[bold green]▶ Hex Hash (SHA-256, checksum OK):[/bold green] {raw_bytes.hex()}"
            )
        except ValueError as e:
            click.secho(f"Base60Check FAILED (transcription error?): {e}", fg="red", err=True)
        return

    # Case 3: 44-character Base-60 Hash -> Hex
    if len(cleaned) == _HASH_B60_LEN and _is_base60(cleaned):
        try:
            raw_bytes = base60_to_bytes(cleaned, 32)
            console.print(f"[bold green]▶ Hex Hash (SHA-256):[/bold green] {raw_bytes.hex()}")
            return
        except ValueError as e:
            click.secho(f"Base-60 decoding error: {e}", fg="red", err=True)
            return

    # Case 4: UUID representations
    # 4.1 Standard UUID string (36 chars) or compact Hex UUID (32 chars)
    if (len(cleaned) == 36 and cleaned.count("-") == 4) or (
        len(cleaned) == 32 and _is_hex(cleaned)
    ):
        try:
            u = uuid.UUID(cleaned)
            encoded = bytes_to_base60(u.bytes)
            console.print(f"[bold green]▶ Base-60 UUID:[/bold green] {encoded}")
            return
        except ValueError as e:
            click.secho(f"UUID parsing error: {e}", fg="red", err=True)
            return

    # 4.2 25-character Base60Check UUID -> Standard UUID (checksum verified)
    if len(cleaned) == _UUID_CHECK_LEN and _is_base60(cleaned):
        try:
            raw_bytes = base60_check_to_bytes(cleaned, 16)
            u = uuid.UUID(bytes=raw_bytes)
            console.print(f"[bold green]▶ UUID Standard (checksum OK):[/bold green] {u}")
        except ValueError as e:
            click.secho(f"Base60Check FAILED (transcription error?): {e}", fg="red", err=True)
        return

    # 4.3 22-character Base-60 UUID -> Standard UUID
    if len(cleaned) == _UUID_B60_LEN and _is_base60(cleaned):
        try:
            raw_bytes = base60_to_bytes(cleaned, 16)
            u = uuid.UUID(bytes=raw_bytes)
            console.print(f"[bold green]▶ UUID Standard:[/bold green] {u}")
            return
        except ValueError as e:
            click.secho(f"Base-60 UUID decoding error: {e}", fg="red", err=True)
            return

    # Fallback: Treat as standard text and encode it to Base-60
    try:
        raw_bytes = cleaned.encode("utf-8")
        encoded = bytes_to_base60(raw_bytes)
        console.print(
            f"[yellow]Auto-detection fell back to text-encoding.[/yellow]\n"
            f"[bold green]▶ Base-60 Encoded:[/bold green] {encoded}"
        )
    except Exception as e:  # noqa: BLE001
        click.secho(f"Fallback encoding error: {e}", fg="red", err=True)


@base60_group.command(name="check")
@click.argument("val")
def check_cmd(val: str):
    """Emit the Base60Check (checksummed) form for human transcription.

    Use this form whenever a hash or UUID will be read, written down, or
    dictated by a human: transcription errors (including the residual 0/o,
    1/I ambiguity) are detected on decode with P(escape) = 2**-16.

    Accepts:
      - 64-char Hex hash or 44-char Base-60 hash -> 47-char Base60Check
      - 36/32-char Hex UUID or 22-char Base-60 UUID -> 25-char Base60Check
      - 47/25-char Base60Check string -> verifies and confirms

    No text fallback: unrecognized input is an explicit error.
    """
    cleaned = val.strip()

    try:
        if len(cleaned) == _HASH_HEX_LEN and _is_hex(cleaned):
            raw_bytes = bytes.fromhex(cleaned)
        elif len(cleaned) == _HASH_B60_LEN and _is_base60(cleaned):
            raw_bytes = base60_to_bytes(cleaned, 32)
        elif (len(cleaned) == 36 and cleaned.count("-") == 4) or (
            len(cleaned) == 32 and _is_hex(cleaned)
        ):
            raw_bytes = uuid.UUID(cleaned).bytes
        elif len(cleaned) == _UUID_B60_LEN and _is_base60(cleaned):
            raw_bytes = base60_to_bytes(cleaned, 16)
        elif len(cleaned) == _HASH_CHECK_LEN and _is_base60(cleaned):
            raw_bytes = base60_check_to_bytes(cleaned, 32)
            console.print(
                f"[bold green]▶ Base60Check verified (hash):[/bold green] {raw_bytes.hex()}"
            )
            return
        elif len(cleaned) == _UUID_CHECK_LEN and _is_base60(cleaned):
            raw_bytes = base60_check_to_bytes(cleaned, 16)
            console.print(
                f"[bold green]▶ Base60Check verified (UUID):[/bold green] {uuid.UUID(bytes=raw_bytes)}"
            )
            return
        else:
            click.secho(
                f"Unrecognized input ({len(cleaned)} chars): expected a hash "
                f"(64 hex / 44 b60 / 47 check) or UUID (36/32 hex / 22 b60 / 25 check).",
                fg="red",
                err=True,
            )
            return
    except ValueError as e:
        click.secho(f"Base60Check FAILED: {e}", fg="red", err=True)
        return

    encoded = bytes_to_base60_check(raw_bytes)
    label = "Hash" if len(raw_bytes) == 32 else "UUID"
    console.print(
        f"[bold green]▶ Base60Check {label} ({len(encoded)}-char):[/bold green] {encoded}"
    )
