"""Remotion CLI arguments for this optional video demo; no core imports."""


def build_remotion_render_args(
    entry_point: str,
    composition_id: str,
    output_path: str,
    props_path: str,
    tier: str = "final",
    p_cores: int = 6,
) -> list[str]:
    """Bound concurrency to 1..6 and add the existing draft rendering flags."""
    bounded_concurrency = max(1, min(p_cores, 6))
    args = [
        "npx",
        "remotion",
        "render",
        entry_point,
        composition_id,
        output_path,
        f"--props={props_path}",
        f"--concurrency={bounded_concurrency}",
        "--timeout=120000",
    ]
    if tier == "draft":
        args.extend(["--scale=0.5", "--every-nth-frame=2"])
    return args
