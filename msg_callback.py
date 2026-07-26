def message_callback(message, metadata):
    """Rewrite a commit message to Conventional Commit format and add BFT metadata.

    Args:
        message: Original commit message string.
        metadata: Dict provided by git‑filter‑repo – contains at least
            ``commit_timestamp`` which we use for ``Lamport‑T``.
    Returns:
        The new commit message.
    """
    lower = message.lower()
    if lower.startswith('add') or lower.startswith('implement'):
        typ = 'feat'
    elif lower.startswith('fix') or 'bug' in lower:
        typ = 'fix'
    elif lower.startswith('refactor'):
        typ = 'refactor'
    else:
        typ = 'chore'
    # Preserve the original first line as the subject
    subject = message.split('\n')[0].strip()
    new_msg = f"{typ}: {subject}\n\nCausal‑Taint: borjamoskv\nLamport‑T: {metadata.get('commit_timestamp', '')}"
    return new_msg
