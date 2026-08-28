# C5-REAL EXERGY CERTIFIED
import sys
import json
import subprocess
from typing import Dict, List, Any
import click
from babylon60.cli.common import cli, console
from rich.table import Table
from rich.panel import Panel
from primitives.bash_primitive import BashCommand

def run_gcloud_json(args: List[str]) -> Any:
    cmd = ["gcloud"] + args + ["--format=json"]
    try:
        res = BashCommand(binary=cmd[0], args=tuple(cmd[1:])).execute()
        return json.loads(res.stdout)
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error al ejecutar gcloud:[/bold red] {e.stderr}")
        return None
    except json.JSONDecodeError:
        console.print("[bold red]Error al decodificar la salida JSON de gcloud.[/bold red]")
        return None

def analyze_key_restrictions(key: Dict[str, Any]) -> Dict[str, Any]:
    key_name = key.get("name", "Unknown")
    display_name = key.get("displayName", "N/A")
    uid = key.get("uid", "N/A")
    restrictions = key.get("restrictions", {})

    has_api_restrictions = bool(restrictions.get("apiTargets"))
    has_browser_restrictions = bool(restrictions.get("browserKeyRestrictions"))
    has_server_restrictions = bool(restrictions.get("serverKeyRestrictions"))
    has_android_restrictions = bool(restrictions.get("androidKeyRestrictions"))
    has_ios_restrictions = bool(restrictions.get("iosKeyRestrictions"))

    has_app_restrictions = (
        has_browser_restrictions or
        has_server_restrictions or
        has_android_restrictions or
        has_ios_restrictions
    )

    is_unrestricted = not (has_api_restrictions or has_app_restrictions)

    return {
        "name": key_name,
        "displayName": display_name,
        "uid": uid,
        "has_api_restrictions": has_api_restrictions,
        "has_app_restrictions": has_app_restrictions,
        "is_unrestricted": is_unrestricted,
        "raw_restrictions": restrictions
    }

@cli.command(name="gcp_key_audit")
@click.option("--project", required=False, help="ID del Proyecto de Google Cloud (si no se proporciona, usa el default)")
@click.option("--restrict-uid", required=False, help="UID de la clave API para restringir automáticamente (modo remediación)")
@click.option("--api-service", required=False, default="apikeys.googleapis.com", help="Servicio API a habilitar en modo remediación")
def gcp_key_audit(project: str, restrict_uid: str, api_service: str):
    """Escanea y reporta el estado de seguridad de las claves API en GCP (C5-REAL)."""

    # 1. Determinar proyecto
    if not project:
        res = BashCommand(binary="gcloud", args=("config", "get-value", "project")).execute()
        project = res.stdout.strip()
        if not project or project == "(unset)":
            console.print("[bold red]Error:[/bold red] No hay proyecto GCP configurado y no se pasó --project.")
            sys.exit(1)

    # 2. Modo Remediación Directa
    if restrict_uid:
        console.print(f"[bold cyan]Aplicando restricción de API a clave {restrict_uid}...[/bold cyan]")
        cmd = [
            "gcloud", "services", "api-keys", "update", restrict_uid,
            f"--project={project}",
            f"--api-target=service={api_service}"
        ]
        res = BashCommand(binary=cmd[0], args=tuple(cmd[1:])).execute()
        if res.returncode == 0:
            console.print(f"[bold green]✓ Éxito:[/bold green] Restricción API '{api_service}' aplicada correctamente a {restrict_uid}.")
        else:
            console.print(f"[bold red]✗ Error al restringir clave:[/bold red] {res.stderr}")
        return

    # 3. Modo Escaneo (Auditoría)
    console.print(Panel(f"[bold cyan]Iniciando Escaneo C5-REAL de Claves API[/bold cyan]\nProyecto: [yellow]{project}[/yellow]", title="⚙️ GCP AUDITOR"))

    keys = run_gcloud_json(["services", "api-keys", "list", f"--project={project}"])
    if keys is None:
        sys.exit(1)

    if not keys:
        console.print("[green]No se encontraron claves API en el proyecto especificado.[/green]")
        return

    table = Table(title=f"Matriz de Auditoría de Claves API :: {project}")
    table.add_column("UID / Key ID", style="dim", no_wrap=True)
    table.add_column("Nombre Visible", style="bold")
    table.add_column("Restricción API", justify="center")
    table.add_column("Restricción App", justify="center")
    table.add_column("Estado Exergético", justify="center")

    unrestricted_count = 0

    for key in keys:
        analysis = analyze_key_restrictions(key)

        api_icon = "[green]✓ YES[/green]" if analysis["has_api_restrictions"] else "[red]✗ NO[/red]"
        app_icon = "[green]✓ YES[/green]" if analysis["has_app_restrictions"] else "[red]✗ NO[/red]"

        if analysis["is_unrestricted"]:
            unrestricted_count += 1
            status = "[bold red]CRÍTICO (Sin Restricción)[/bold red]"
        elif not analysis["has_api_restrictions"] or not analysis["has_app_restrictions"]:
            status = "[bold yellow]PARCIAL (Riesgo Moderado)[/bold yellow]"
        else:
            status = "[bold green]ÓPTIMO (Exergía Segura)[/bold green]"

        table.add_row(
            analysis["uid"],
            analysis["displayName"],
            api_icon,
            app_icon,
            status
        )

    console.print(table)
    console.print(f"\n[bold]Resumen de Auditoría:[/bold] Total Claves: {len(keys)} | [bold red]Sin Restricción: {unrestricted_count}[/bold red]")
