import os
import subprocess
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(
    title="MOSKV-1 APEX Analysis Node",
    description="Vector de acceso para IA externas. Exposición de memoria, invariantes físicas y estado topológico del clúster.",
    version="5.0.0",
    docs_url=None,
)

security = HTTPBearer()
EXPECTED_TOKEN = os.environ.get(
    "MOSKV_ANALYSIS_TOKEN", os.environ.get("CORTEX_ANALYSIS_TOKEN", "c5-real-omega-key")
)


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != EXPECTED_TOKEN:
        raise HTTPException(status_code=403, detail="Anergía Detectada: Token Inválido")
    return credentials.credentials


class ScanRequest(BaseModel):
    target_path: str


class ScanResponse(BaseModel):
    untracked_files: int
    broken_symlinks: int
    massive_nodes: int
    status: str


# Create static directory if not exists
Path("cortex/api/static").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="cortex/api/static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=app.title + " - Swagger UI",
        swagger_css_url="/static/swagger_theme.css",
    )


@app.get("/health")
async def health_check():
    return {
        "status": "C5-REAL",
        "exergy_level": "OPTIMAL",
        "entropy": 0.0,
        "mode": "Ultra-Think Ready",
    }


@app.get("/invariants")
async def get_invariants(token: str = Depends(verify_token)):
    home_dir = Path.home()
    workspace_dir = home_dir / "30_BABYLON-60"
    if not workspace_dir.exists():
        workspace_dir = home_dir / "30_CORTEX"
    inv_path = workspace_dir / "docs/epistemology/100_invariantes_fisicas.md"
    if inv_path.exists():
        return {
            "source": "100_invariantes_fisicas.md",
            "content": inv_path.read_text(encoding="utf-8"),
        }
    raise HTTPException(status_code=404, detail="Invariantes no forjadas en disco")


@app.post("/scan/topology", response_model=ScanResponse)
async def scan_topology(req: ScanRequest, token: str = Depends(verify_token)):
    """Ejecuta un barrido topológico sobre el path dado."""
    target_str = str(req.target_path)
    if ".." in target_str or target_str.startswith("-") or target_str.startswith("~"):
        raise HTTPException(
            status_code=400, detail="Invalid target path: directory traversal or option flags blocked"
        )
    target = Path(target_str).resolve().absolute()
    base_dir = Path.home().resolve().absolute()

    if target != base_dir and not target.is_relative_to(base_dir):
        raise HTTPException(
            status_code=400, detail="Invalid target path: directory traversal attempt"
        )

    if not target.exists():
        raise HTTPException(status_code=404, detail="Target path no existe")

    try:
        # codeql[py/command-line-injection] - Target is an absolute path starting with /
        untracked_proc = subprocess.run(
            ["git", "-C", str(target), "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=False,
        )
        untracked_count = len([line for line in untracked_proc.stdout.splitlines() if line.strip()])

        # codeql[py/command-line-injection] - Target is an absolute path starting with /
        broken_proc = subprocess.run(
            ["find", str(target), "-type", "l", "!", "-exec", "test", "-e", "{}", ";", "-print"],
            capture_output=True,
            text=True,
            check=False,
        )
        broken_count = len([line for line in broken_proc.stdout.splitlines() if line.strip()])

        # codeql[py/command-line-injection] - Target is an absolute path starting with /
        massive_proc = subprocess.run(
            ["find", str(target), "-type", "f", "-size", "+50M", "-not", "-path", "*/.*"],
            capture_output=True,
            text=True,
            check=False,
        )
        massive_count = len([line for line in massive_proc.stdout.splitlines() if line.strip()])

        return ScanResponse(
            untracked_files=untracked_count,
            broken_symlinks=broken_count,
            massive_nodes=massive_count,
            status="WARNING" if untracked_count > 0 or broken_count > 0 else "CLEAN",
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Internal server error")
