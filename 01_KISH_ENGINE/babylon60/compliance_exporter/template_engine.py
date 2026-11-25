"""
BABYLON-60 v4.0 Compliance Exporter — Decoupled Template Engine & SoC Architecture
Provides Jinja2-powered HTML compliance reports with transparent fallback to
deterministic stdlib string.Template engine and multi-theme support (dark HUD vs. legal paper).
"""

from __future__ import annotations

import html
import os
import string
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .i18n import get_translation

SUPPORTED_THEMES = ("dark", "dark_hud", "legal", "legal_paper")
DEFAULT_THEME = "dark"

# Embedded minimal CSS fallbacks in case template files are relocated
_FALLBACK_DARK_CSS = """
:root {
    --bg-color: #0b0f19;
    --card-bg: rgba(18, 26, 43, 0.85);
    --accent: #00F0FF;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --success: #10b981;
    --danger: #ef4444;
    --border: rgba(255, 255, 255, 0.1);
}
body { font-family: 'Inter', system-ui, sans-serif; background-color: var(--bg-color); color: var(--text); padding: 2rem; }
.container { max-width: 900px; margin: 0 auto; background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 2.5rem; }
.badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; }
.badge-success { background: rgba(16, 185, 129, 0.2); color: var(--success); border: 1px solid var(--success); }
.badge-danger { background: rgba(239, 68, 68, 0.2); color: var(--danger); border: 1px solid var(--danger); }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; }
.card { background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
th, td { text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); }
code { background: rgba(0, 240, 255, 0.1); color: var(--accent); padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; }
"""

_FALLBACK_LEGAL_CSS = """
:root {
    --bg-color: #f8fafc;
    --card-bg: #ffffff;
    --accent: #1e3a8a;
    --text: #0f172a;
    --muted: #475569;
    --success: #15803d;
    --danger: #b91c1c;
    --border: #cbd5e1;
}
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: var(--bg-color); color: var(--text); padding: 2rem; }
.container { max-width: 900px; margin: 0 auto; background: var(--card-bg); border: 1px solid var(--border); border-radius: 4px; padding: 3rem; }
.badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
.badge-success { background: #dcfce7; color: var(--success); border: 1px solid #86efac; }
.badge-danger { background: #fee2e2; color: var(--danger); border: 1px solid #fca5a5; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
.card { background: #f8fafc; border: 1px solid var(--border); border-radius: 4px; padding: 0.85rem; }
table { width: 100%; border-collapse: collapse; margin-top: 0.75rem; }
th, td { text-align: left; padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--border); }
code { background: #f1f5f9; color: #0f172a; padding: 0.15rem 0.35rem; border: 1px solid #e2e8f0; border-radius: 3px; font-family: monospace; }
"""


@dataclass
class ArticleComplianceItem:
    """DTO representing individual EU AI Act article audit assessment."""

    key: str
    title: str
    mechanism: str
    status: str
    status_display: str
    status_ok: bool
    evidence_hash: str
    evidence_hash_short: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "mechanism": self.mechanism,
            "status": self.status,
            "status_display": self.status_display,
            "status_ok": self.status_ok,
            "evidence_hash": self.evidence_hash,
            "evidence_hash_short": self.evidence_hash_short,
        }


@dataclass
class ReportContextDTO:
    """Comprehensive Data Transfer Object decoupling compliance cert data from rendering."""

    locale: str
    theme: str
    theme_css: str
    cert: Dict[str, Any]
    translations: Dict[str, Any]
    title: str
    certificate_id: str
    system_identifier: str
    operator: str
    issued_at: str
    valid_until: str
    compliance_standard: str
    supervisory_authority: str
    global_merkle_root: str
    cryptographic_fingerprint: str
    executive_summary_title: str
    executive_summary_text: str
    evidence_verification_title: str
    signature_title: str
    compliance_matrix_title: str
    certificate_id_label: str
    system_label: str
    operator_label: str
    issued_at_label: str
    ledger_label: str
    integrity_verified_label: str
    recomputed_merkle_root_label: str
    manifest_match_label: str
    verdict_label: str
    quarantine_status: str
    verification: Dict[str, Any]
    verdict: str
    verdict_ok: bool
    signature: Dict[str, Any]
    articles: List[ArticleComplianceItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts DTO into dictionary for template context injection."""
        return {
            "locale": self.locale,
            "theme": self.theme,
            "theme_css": self.theme_css,
            "cert": self.cert,
            "translations": self.translations,
            "title": self.title,
            "certificate_id": self.certificate_id,
            "system_identifier": self.system_identifier,
            "operator": self.operator,
            "issued_at": self.issued_at,
            "valid_until": self.valid_until,
            "compliance_standard": self.compliance_standard,
            "supervisory_authority": self.supervisory_authority,
            "global_merkle_root": self.global_merkle_root,
            "cryptographic_fingerprint": self.cryptographic_fingerprint,
            "executive_summary_title": self.executive_summary_title,
            "executive_summary_text": self.executive_summary_text,
            "evidence_verification_title": self.evidence_verification_title,
            "signature_title": self.signature_title,
            "compliance_matrix_title": self.compliance_matrix_title,
            "certificate_id_label": self.certificate_id_label,
            "system_label": self.system_label,
            "operator_label": self.operator_label,
            "issued_at_label": self.issued_at_label,
            "ledger_label": self.ledger_label,
            "integrity_verified_label": self.integrity_verified_label,
            "recomputed_merkle_root_label": self.recomputed_merkle_root_label,
            "manifest_match_label": self.manifest_match_label,
            "verdict_label": self.verdict_label,
            "quarantine_status": self.quarantine_status,
            "verification": self.verification,
            "verdict": self.verdict,
            "verdict_ok": self.verdict_ok,
            "signature": self.signature,
            "articles": [a.to_dict() for a in self.articles],
        }


def load_theme_css(theme: str = "dark", templates_dir: Optional[str] = None) -> str:
    """
    Loads theme stylesheet from disk, with embedded fallback.
    Supported themes: 'dark' (HUD cyberpunk) and 'legal' (sober paper report).
    """
    normalized = theme.lower().strip()
    if normalized in ("legal", "legal_paper"):
        filename = "legal_paper.css"
        fallback = _FALLBACK_LEGAL_CSS
    else:
        filename = "dark_hud.css"
        fallback = _FALLBACK_DARK_CSS

    if templates_dir is None:
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")

    theme_path = os.path.join(templates_dir, "themes", filename)
    if os.path.exists(theme_path):
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return fallback.strip()

    return fallback.strip()


class ComplianceTemplateEngine:
    """
    Decoupled Template Engine for BABYLON-60 compliance reporting.
    Uses Jinja2 when available with modular sub-templates, and provides
    a 100% deterministic stdlib fallback via string.Template.
    """

    def __init__(
        self,
        templates_dir: Optional[str] = None,
        force_fallback: bool = False,
    ) -> None:
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.templates_dir = templates_dir
        self.force_fallback = force_fallback

        self._jinja_env = None
        if not self.force_fallback:
            try:
                import jinja2

                self._jinja_env = jinja2.Environment(
                    loader=jinja2.FileSystemLoader(self.templates_dir),
                    # Incondicional: select_autoescape(["html","xml"]) no casa con
                    # "*.html.j2" (sufijo ".j2") y dejaba pasar HTML crudo del ledger.
                    autoescape=True,
                    trim_blocks=True,
                    lstrip_blocks=True,
                )
            except ImportError:
                self._jinja_env = None

    @property
    def has_jinja(self) -> bool:
        """Returns True if Jinja2 is actively available and loaded."""
        return self._jinja_env is not None

    def build_context(
        self,
        cert: Dict[str, Any],
        locale: str = "es",
        theme: str = "dark",
    ) -> ReportContextDTO:
        """Constructs a normalized ReportContextDTO from a compliance certificate."""
        t = get_translation(locale)
        v = cert.get("evidence_verification", {})
        sig = cert.get("signature", {})
        attestation = cert.get("cryptographic_attestation", {})

        theme_css = load_theme_css(theme, templates_dir=self.templates_dir)

        evidence_verification_title = t.get("evidence_verification_title", "Verificación Criptográfica de la Evidencia")
        signature_title = t.get("signature_title", "Firma Ed25519 del Certificado")
        compliance_matrix_title = t.get("compliance_matrix_title", "Matriz de Cumplimiento Normativo EU AI Act")
        certificate_id_label = t.get("certificate_id_label", "ID Certificado")
        system_label = t.get("system_label", "Sistema Auditado")
        operator_label = t.get("operator_label", "Operador / Entidad")
        issued_at_label = t.get("issued_at_label", "Fecha Emisión")
        ledger_label = t.get("ledger_label", "Ledger")
        integrity_verified_label = t.get("integrity_verified_label", "Cadena íntegra (verify_integrity)")
        recomputed_merkle_root_label = t.get("recomputed_merkle_root_label", "Merkle root recomputado")
        manifest_match_label = t.get("manifest_match_label", "Coincide con global_hash del manifiesto")
        verdict_label = t.get("verdict_label", "Veredicto")

        verdict_raw = str(v.get("detail", "UNVERIFIED"))
        verdict_ok = verdict_raw == "VERIFIED"

        article_items: List[ArticleComplianceItem] = []
        for art_key, art_val in cert.get("articles_compliance", {}).items():
            raw_status = str(art_val.get("status", ""))
            status_upper = raw_status.upper()
            status_ok = (
                "PASS" in status_upper
                or "CUMPLIDO" in status_upper
                or status_upper == "CONFORME"
                or status_upper == "COMPLIANT"
                or status_upper == "KONFORM"
            )
            ev_hash = str(art_val.get("evidence_hash", ""))
            ev_hash_short = f"{ev_hash[:16]}..." if len(ev_hash) >= 16 else ev_hash

            article_items.append(
                ArticleComplianceItem(
                    key=art_key,
                    title=str(art_val.get("title", "")),
                    mechanism=str(art_val.get("mechanism", "")),
                    status=raw_status,
                    status_display=raw_status,
                    status_ok=status_ok,
                    evidence_hash=ev_hash,
                    evidence_hash_short=ev_hash_short,
                )
            )

        return ReportContextDTO(
            locale=locale,
            theme=theme,
            theme_css=theme_css,
            cert=cert,
            translations=t,
            title=cert.get("title", t.get("title", "Compliance Report")),
            certificate_id=cert.get("certificate_id", ""),
            system_identifier=cert.get("system_identifier", ""),
            operator=cert.get("operator", ""),
            issued_at=cert.get("issued_at", ""),
            valid_until=cert.get("valid_until", ""),
            compliance_standard=cert.get("compliance_standard", t.get("compliance_standard", "")),
            supervisory_authority=cert.get("supervisory_authority", t.get("authority", "")),
            global_merkle_root=cert.get("global_merkle_root", ""),
            cryptographic_fingerprint=attestation.get("fingerprint", ""),
            executive_summary_title=t.get("executive_summary_title", "Resumen Ejecutivo"),
            executive_summary_text=t.get("executive_summary_text", ""),
            evidence_verification_title=evidence_verification_title,
            signature_title=signature_title,
            compliance_matrix_title=compliance_matrix_title,
            certificate_id_label=certificate_id_label,
            system_label=system_label,
            operator_label=operator_label,
            issued_at_label=issued_at_label,
            ledger_label=ledger_label,
            integrity_verified_label=integrity_verified_label,
            recomputed_merkle_root_label=recomputed_merkle_root_label,
            manifest_match_label=manifest_match_label,
            verdict_label=verdict_label,
            quarantine_status=cert.get("quarantine_status", ""),
            verification=v,
            verdict=verdict_raw,
            verdict_ok=verdict_ok,
            signature=sig,
            articles=article_items,
        )

    def render_report(
        self,
        cert: Dict[str, Any],
        locale: str = "es",
        theme: str = "dark",
        template_name: str = "base_report.html.j2",
    ) -> str:
        """
        Renders complete HTML report. Uses Jinja2 if available; falls back
        transparently to deterministic stdlib engine on any error or missing dependency.
        """
        ctx = self.build_context(cert, locale=locale, theme=theme)

        if self._jinja_env is not None and not self.force_fallback:
            try:
                tmpl = self._jinja_env.get_template(template_name)
                # Feed both dictionary keys and DTO instance for maximum template flexibility
                render_vars = ctx.to_dict()
                render_vars["ctx"] = ctx
                return tmpl.render(**render_vars)
            except Exception:
                # Fallback to stdlib engine if template loading or rendering encounters an issue
                return self._render_fallback(ctx)

        return self._render_fallback(ctx)

    def _render_fallback(self, ctx: ReportContextDTO) -> str:
        """
        Deterministic stdlib string.Template fallback engine.
        Guarantees 100% zero-dependency, fail-safe rendering matching Jinja2 output structure.
        """

        def esc(s: Any) -> str:
            return html.escape(str(s if s is not None else ""), quote=True)

        # Build Article rows
        rows: List[str] = []
        row_template = string.Template(
            "            <tr>\n"
            "                <td><strong>$title</strong></td>\n"
            "                <td>$mechanism</td>\n"
            "                <td>$status_badge</td>\n"
            "                <td><code>$evidence_hash</code></td>\n"
            "            </tr>"
        )
        for art in ctx.articles:
            if art.status_ok:
                badge = f'<span class="badge badge-success">✅ {esc(art.status_display)}</span>'
            else:
                badge = f'<span class="badge badge-danger">❌ {esc(art.status_display)}</span>'

            rows.append(
                row_template.substitute(
                    title=esc(art.title),
                    mechanism=esc(art.mechanism),
                    status_badge=badge,
                    evidence_hash=esc(art.evidence_hash_short),
                )
            )
        rendered_rows = "\n".join(rows)

        # Build verdict badge
        if ctx.verdict_ok:
            verdict_badge = f'<span class="badge badge-success">✅ {esc(ctx.verdict)}</span>'
        else:
            verdict_badge = f'<span class="badge badge-danger">❌ {esc(ctx.verdict)}</span>'

        # Modular sub-components via string.Template
        header_html = string.Template(
            '        <div class="header">\n'
            "            <h1>📜 $title</h1>\n"
            '            <p style="color: var(--accent); font-weight: 600; margin: 0;">$compliance_standard</p>\n'
            "        </div>"
        ).substitute(
            title=esc(ctx.title),
            compliance_standard=esc(ctx.compliance_standard),
        )

        grid_html = string.Template(
            '        <div class="grid">\n'
            '            <div class="card">\n'
            '                <div class="card-title">$certificate_id_label</div>\n'
            '                <div class="card-value">$certificate_id</div>\n'
            "            </div>\n"
            '            <div class="card">\n'
            '                <div class="card-title">$system_label</div>\n'
            '                <div class="card-value">$system_identifier</div>\n'
            "            </div>\n"
            '            <div class="card">\n'
            '                <div class="card-title">$operator_label</div>\n'
            '                <div class="card-value">$operator</div>\n'
            "            </div>\n"
            '            <div class="card">\n'
            '                <div class="card-title">$issued_at_label</div>\n'
            '                <div class="card-value">$issued_at</div>\n'
            "            </div>\n"
            "        </div>"
        ).substitute(
            certificate_id_label=esc(ctx.certificate_id_label),
            certificate_id=esc(ctx.certificate_id),
            system_label=esc(ctx.system_label),
            system_identifier=esc(ctx.system_identifier),
            operator_label=esc(ctx.operator_label),
            operator_label_val=esc(ctx.operator),
            operator=esc(ctx.operator),
            issued_at_label=esc(ctx.issued_at_label),
            issued_at=esc(ctx.issued_at),
        )

        summary_html = string.Template(
            "        <h2>$executive_summary_title</h2>\n"
            "        <p>$executive_summary_text</p>\n"
            "        <p><strong>Global Merkle Root:</strong> <code>$global_merkle_root</code></p>\n"
            "        <p><strong>Cryptographic Fingerprint:</strong> <code>$cryptographic_fingerprint</code></p>"
        ).substitute(
            executive_summary_title=esc(ctx.executive_summary_title),
            executive_summary_text=esc(ctx.executive_summary_text),
            global_merkle_root=esc(ctx.global_merkle_root),
            cryptographic_fingerprint=esc(ctx.cryptographic_fingerprint),
        )

        verification_html = string.Template(
            "        <h2>$evidence_verification_title</h2>\n"
            "        <table>\n"
            "            <tbody>\n"
            "                <tr><td><strong>$ledger_label</strong></td><td><code>$ledger_path</code></td></tr>\n"
            "                <tr><td><strong>$integrity_verified_label</strong></td><td><code>$integrity_verified</code></td></tr>\n"
            "                <tr><td><strong>$recomputed_merkle_root_label</strong></td><td><code>$recomputed_merkle_root</code></td></tr>\n"
            "                <tr><td><strong>$manifest_match_label</strong></td><td><code>$manifest_match</code></td></tr>\n"
            "                <tr><td><strong>$verdict_label</strong></td><td>$verdict_badge</td></tr>\n"
            "            </tbody>\n"
            "        </table>"
        ).substitute(
            evidence_verification_title=esc(ctx.evidence_verification_title),
            ledger_label=esc(ctx.ledger_label),
            ledger_path=esc(ctx.verification.get("ledger_path")),
            integrity_verified_label=esc(ctx.integrity_verified_label),
            integrity_verified=esc(ctx.verification.get("integrity_verified")),
            recomputed_merkle_root_label=esc(ctx.recomputed_merkle_root_label),
            recomputed_merkle_root=esc(ctx.verification.get("ledger_merkle_root")),
            manifest_match_label=esc(ctx.manifest_match_label),
            manifest_match=esc(ctx.verification.get("evidence_match")),
            verdict_label=esc(ctx.verdict_label),
            verdict_badge=verdict_badge,
        )

        sig_data = ctx.signature
        signature_html = string.Template(
            "        <h2>$signature_title</h2>\n"
            "        <table>\n"
            "            <tbody>\n"
            "                <tr><td><strong>Algoritmo</strong></td><td><code>$algorithm</code> (efímera: <code>$ephemeral</code>)</td></tr>\n"
            "                <tr><td><strong>Clave pública</strong></td><td><code>$public_key</code></td></tr>\n"
            "                <tr><td><strong>SHA-256 payload</strong></td><td><code>$signed_payload_sha256</code></td></tr>\n"
            "            </tbody>\n"
            "        </table>"
        ).substitute(
            signature_title=esc(ctx.signature_title),
            algorithm=esc(sig_data.get("algorithm")),
            ephemeral=esc(sig_data.get("ephemeral")),
            public_key=esc(sig_data.get("public_key")),
            signed_payload_sha256=esc(sig_data.get("signed_payload_sha256")),
        )

        matrix_html = string.Template(
            "        <h2>$compliance_matrix_title</h2>\n"
            "        <table>\n"
            "            <thead>\n"
            "                <tr>\n"
            "                    <th>Artículo / Requisito</th>\n"
            "                    <th>Mecanismo Técnico BABYLON-60</th>\n"
            "                    <th>Estado</th>\n"
            "                    <th>Evidencia Hash</th>\n"
            "                </tr>\n"
            "            </thead>\n"
            "            <tbody>\n"
            "$rows\n"
            "            </tbody>\n"
            "        </table>"
        ).substitute(
            compliance_matrix_title=esc(ctx.compliance_matrix_title),
            rows=rendered_rows,
        )

        footer_html = string.Template(
            '        <div class="footer">\n'
            "            BABYLON-60 v4.0 C5-REAL Compliance Transducer — $supervisory_authority\n"
            "        </div>"
        ).substitute(supervisory_authority=esc(ctx.supervisory_authority))

        # Assemble master template
        base_template = string.Template(
            "<!DOCTYPE html>\n"
            '<html lang="$locale">\n'
            "<head>\n"
            '    <meta charset="UTF-8">\n'
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            "    <title>$title - $certificate_id</title>\n"
            "    <style>\n"
            "$theme_css\n"
            "    </style>\n"
            "</head>\n"
            "<body>\n"
            '    <div class="container">\n'
            "$header\n"
            "$grid\n"
            "$summary\n"
            "$verification\n"
            "$signature\n"
            "$matrix\n"
            "$footer\n"
            "    </div>\n"
            "</body>\n"
            "</html>"
        )

        return base_template.substitute(
            locale=esc(ctx.locale),
            title=esc(ctx.title),
            certificate_id=esc(ctx.certificate_id),
            theme_css=ctx.theme_css,
            header=header_html,
            grid=grid_html,
            summary=summary_html,
            verification=verification_html,
            signature=signature_html,
            matrix=matrix_html,
            footer=footer_html,
        )
