import subprocess
from pathlib import Path
from typing import Any


def get_git_sentinel_hashes(repo_path: Path) -> set[str]:
    try:
        res = subprocess.run(
            ["git", "log", "--format=%H %s", "-n", "100"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.split(" ")[0] for line in res.stdout.strip().split("\n") if line}
    except subprocess.CalledProcessError:
        return set()


def verify_attestation(session_dir: Path, repo_path: Path) -> dict[str, Any]:
    session_id = session_dir.name
    transcript_path = session_dir / ".system_generated" / "logs" / "transcript.jsonl"
    if not transcript_path.exists():
        alt_path = session_dir / "transcript.jsonl"
        if alt_path.exists():
            transcript_path = alt_path
        else:
            return {"session_id": session_id, "status": "NO_TRANSCRIPT"}
    claimed_hashes = set()
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if "git commit" in line and "Hash:" in line:
                    parts = line.split("Hash:")
                    if len(parts) > 1:
                        h = parts[1].strip().split()[0][:40]
                        claimed_hashes.add(h)
    except OSError:
        pass
    actual_hashes = get_git_sentinel_hashes(repo_path)
    verified = claimed_hashes.intersection(actual_hashes)
    anergy = len(claimed_hashes) - len(verified)
    return {
        "session_id": session_id,
        "claimed_hashes": len(claimed_hashes),
        "verified": len(verified),
        "attestation_anergy": anergy * 50.0,
    }


if __name__ == "__main__":
    print("OPERA Attestation Engine Loaded. (Use via Swarm Auditor integration)")
